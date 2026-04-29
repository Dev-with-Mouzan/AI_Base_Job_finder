import requests
import time
from typing import List, Dict, Any
from bs4 import BeautifulSoup

def get_sample_jobs() -> List[Dict[str, Any]]:
    """Return sample jobs for testing when scraping fails"""
    return [
        {
            "title": "Software Engineer",
            "company": "Tech Corp",
            "url": "https://linkedin.com/jobs/software-engineer-1",
            "description": "We are looking for a software engineer with experience in Python, Java, and cloud technologies. Must have strong problem-solving skills and ability to work in a team environment."
        },
        {
            "title": "Data Scientist",
            "company": "Data Inc",
            "url": "https://linkedin.com/jobs/data-scientist-1",
            "description": "Seeking a data scientist with expertise in machine learning, statistics, and data analysis. Strong Python and SQL skills required. Experience with TensorFlow or PyTorch preferred."
        },
        {
            "title": "Machine Learning Engineer",
            "company": "AI Solutions",
            "url": "https://linkedin.com/jobs/ml-engineer-1",
            "description": "Looking for an ML engineer to build and deploy machine learning models. Experience with deep learning, NLP, and computer vision. Strong Python and cloud experience needed."
        }
    ]

def fetch_jobs_free(search_terms: List[str] = None) -> List[Dict[str, Any]]:
    """Fetch job listings from LinkedIn Guest API (Free)"""
    if not search_terms:
        search_terms = ["software engineer"]
    
    all_jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # Use only the first 2 search terms to avoid rate limits
    for term in search_terms[:2]:
        try:
            print(f"Scraping LinkedIn Guest API for: {term}")
            # Public LinkedIn Guest Job Search API
            url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={term}&location=United%20States&start=0"
            
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"Failed to fetch jobs for {term}: HTTP {response.status_code}")
                continue

            soup = BeautifulSoup(response.text, "lxml")
            job_cards = soup.find_all("li")

            for card in job_cards:
                try:
                    title_tag = card.find("h3", class_="base-search-card__title")
                    company_tag = card.find("h4", class_="base-search-card__subtitle")
                    link_tag = card.find("a", class_="base-card__full-link")
                    
                    if title_tag and company_tag and link_tag:
                        title = title_tag.get_text(strip=True)
                        company = company_tag.get_text(strip=True)
                        job = {
                            "title": title,
                            "company": company,
                            "url": link_tag["href"],
                            "description": f"Job Title: {title} at {company}. This position is listed on LinkedIn. Please visit the link for the full job description and requirements."
                        }
                        all_jobs.append(job)
                except Exception as e:
                    continue

            # Respectful delay
            time.sleep(1)
            
        except Exception as e:
            print(f"Error scraping LinkedIn for {term}: {e}")
            continue

    return all_jobs

def fetch_job_listings(search_terms: List[str] = None) -> List[Dict[str, Any]]:
    """
    Primary job fetching function. 
    Uses the free scraper and falls back to samples if needed.
    """
    print("Attempting job scraping...")
    jobs = fetch_jobs_free(search_terms)
    
    if jobs:
        print(f"Successfully fetched {len(jobs)} jobs.")
        return jobs

    print("Scraping failed or returned no results. Falling back to sample jobs.")
    return get_sample_jobs()
