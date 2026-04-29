import numpy as np
from typing import List, Dict, Any
from sklearn.metrics.pairwise import cosine_similarity
from backend.core.config import settings

_llm = None
_embeddings_model = None

def _get_llm():
    global _llm
    if _llm is None:
        if settings.GROQ_API_KEY and settings.GROQ_API_KEY != "YOUR_GROQ_API_KEY":
            from langchain_groq import ChatGroq
            _llm = ChatGroq(
                api_key=settings.GROQ_API_KEY,
                model=settings.GROQ_MODEL
            )
        else:
            # Fallback to a clear error if no LLM is available
            raise ValueError("Groq API Key is required when Ollama is disabled.")
    return _llm

def _get_embeddings_model():
    global _embeddings_model
    if _embeddings_model is None:
        from sentence_transformers import SentenceTransformer
        # all-MiniLM-L6-v2 is a fast and accurate local model
        _embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embeddings_model

def get_embedding(text: str) -> List[float]:
    """Get semantic embedding using local sentence-transformers"""
    try:
        model = _get_embeddings_model()
        embedding = model.encode(text)
        return embedding.tolist()
    except Exception as e:
        print(f"Embedding model not available (Offline or Error). Using fallback matching. Error: {e}")
        return None

def get_match_analysis(resume_text: str, job_description: str) -> str:
    prompt = f"""As a recruiter, analyze the match between this resume and job.
Provide a 2-sentence summary of fit.

Resume: {resume_text[:800]}
Job: {job_description[:800]}
"""
    try:
        response = _get_llm().invoke(prompt)
        return response.content.strip()
    except Exception as e:
        print(f"Ollama chat error: {e}")
        return f"Analysis unavailable: {str(e)}"

def match_resume_with_jobs(resume_text: str, jobs: List[Dict[str, Any]], top_n: int = 10) -> List[Dict[str, Any]]:
    if not jobs: return []
    
    print("Attempting semantic matching...")
    resume_emb_list = get_embedding(resume_text)
    
    # If embedding model failed, use simple keyword matching fallback
    if resume_emb_list is None:
        print("AI Model unavailable. Falling back to keyword-based matching...")
        return _keyword_match_fallback(resume_text, jobs, top_n)

    resume_emb = np.array(resume_emb_list).reshape(1, -1)
    
    job_embs = []
    for job in jobs:
        emb = get_embedding(job.get("description", ""))
        if emb is None: # Fallback if individual job fails
            job_embs.append([0.0] * 384)
        else:
            job_embs.append(emb)
    
    job_embs = np.array(job_embs)
    similarities = cosine_similarity(resume_emb, job_embs)[0]
    
    matches = []
    for i, job in enumerate(jobs):
        matches.append({
            **job,
            "score": round(float(similarities[i]), 4)
        })
    
    matches.sort(key=lambda x: x["score"], reverse=True)
    top_matches = matches[:top_n]
    
    for i in range(min(3, len(top_matches))):
        top_matches[i]["analysis"] = get_match_analysis(resume_text, top_matches[i]["description"])
            
    return top_matches

def _keyword_match_fallback(resume_text: str, jobs: List[Dict[str, Any]], top_n: int = 10) -> List[Dict[str, Any]]:
    """Simple keyword frequency matching when AI models are unavailable"""
    resume_words = set(resume_text.lower().split())
    matches = []
    
    for job in jobs:
        job_text = (job.get("title", "") + " " + job.get("description", "")).lower()
        job_words = job_text.split()
        
        # Count overlapping words
        overlap = sum(1 for word in job_words if word in resume_words)
        score = min(0.9, overlap / 50.0) # Simple normalization
        
        matches.append({**job, "score": score})
    
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:top_n]

def get_resume_improvement_chat(resume_text: str, message: str, history: List[Dict[str, str]] = []) -> str:
    """Get resume improvement suggestions from Groq LLM"""
    system_prompt = f"""You are a professional career coach and resume expert. 
You are helping a candidate improve their resume. 
The candidate's resume content is:
{resume_text}

Provide specific, actionable advice to improve the resume based on the candidate's questions. 
ALWAYS structure your response using Markdown:
- Use **bold** for emphasis.
- Use bullet points for lists.
- Use headers if the response is long.
- Keep your responses professional, encouraging, and concise.
"""

    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
    
    messages = [SystemMessage(content=system_prompt)]
    for h in history:
        if h.get("role") == "user":
            messages.append(HumanMessage(content=h["content"]))
        else:
            messages.append(AIMessage(content=h["content"]))
    
    messages.append(HumanMessage(content=message))
    
    try:
        response = _get_llm().invoke(messages)
        return response.content
    except Exception as e:
        print(f"Chat error: {e}")
        return f"Sorry, I couldn't process that request: {str(e)}"

def extract_search_terms(resume_text: str) -> List[str]:
    """Extract 3-5 job search terms from the resume using Groq"""
    prompt = f"""Based on the following resume text, identify the top 3-5 job titles or roles this person is qualified for.
Return ONLY a comma-separated list of titles. No explanation, no numbering.

Resume: {resume_text[:2000]}
"""
    try:
        response = _get_llm().invoke(prompt)
        terms = [t.strip() for t in response.content.split(",")]
        return terms[:5]
    except Exception as e:
        print(f"Error extracting search terms: {e}")
        return ["Software Engineer", "Developer"]
