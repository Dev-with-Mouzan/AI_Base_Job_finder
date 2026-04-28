import numpy as np
from typing import List, Dict, Any
from sklearn.metrics.pairwise import cosine_similarity
from backend.core.config import settings

_llm = None
_embeddings = None

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
            from langchain_ollama import ChatOllama
            _llm = ChatOllama(model=settings.LLM_MODEL)
    return _llm

def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        from langchain_ollama import OllamaEmbeddings
        _embeddings = OllamaEmbeddings(model=settings.EMBED_MODEL)
    return _embeddings

def get_ollama_embedding(text: str) -> List[float]:
    try:
        return _get_embeddings().embed_query(text)
    except Exception as e:
        print(f"Ollama embedding error: {e}")
        return [0.0] * 768

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
    
    print("Generating resume embedding...")
    resume_emb = np.array(get_ollama_embedding(resume_text)).reshape(1, -1)
    
    print("Generating job embeddings...")
    job_embs = []
    for job in jobs:
        emb = get_ollama_embedding(job.get("description", ""))
        job_embs.append(emb)
    
    job_embs = np.array(job_embs)
    
    print("Calculating similarities...")
    similarities = cosine_similarity(resume_emb, job_embs)[0]
    
    matches = []
    for i, job in enumerate(jobs):
        matches.append({
            **job,
            "score": round(float(similarities[i]), 4)
        })
    
    matches.sort(key=lambda x: x["score"], reverse=True)
    top_matches = matches[:top_n]
    
    print("Generating analysis for top matches...")
    for i in range(min(3, len(top_matches))):
        top_matches[i]["analysis"] = get_match_analysis(resume_text, top_matches[i]["description"])
            
    return top_matches

def get_resume_improvement_chat(resume_text: str, message: str, history: List[Dict[str, str]] = []) -> str:
    """Get resume improvement suggestions from Groq LLM"""
    system_prompt = f"""You are a professional career coach and resume expert. 
You are helping a candidate improve their resume. 
The candidate's resume content is:
{resume_text}

Provide specific, actionable advice to improve the resume based on the candidate's questions. 
If they ask about specific sections (like 'Experience' or 'Skills'), refer to their current content.
Keep your responses professional, encouraging, and concise.
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
