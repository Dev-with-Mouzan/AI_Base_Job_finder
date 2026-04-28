import requests
from typing import List, Dict, Any
from backend.core.config import settings
from apify_client import ApifyClient

def get_sample_jobs() -> List[Dict[str, Any]]:
    """Return sample jobs for testing when Apify is not available"""
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

def fetch_jobs_from_apify(search_terms: List[str] = None) -> List[Dict[str, Any]]:
    """Fetch job listings from Apify API using the official client"""
    if not search_terms:
        search_terms = ["software engineer"]

    try:
        if not settings.APIFY_API_KEY or settings.APIFY_API_KEY == "YOUR_APIFY_API_KEY":
            print("Apify API key missing, using sample jobs")
            return get_sample_jobs()

        client = ApifyClient(settings.APIFY_API_KEY)
        
        # Prepare Actor input
        run_input = {
            "searchTerms": search_terms,
            "locations": ["United States"],
            "limit": 15,
            "maxConcurrency": 5
        }

        print(f"Starting Apify scraper for: {search_terms}")
        # Run the Actor and wait for it to finish
        run = client.actor("junglee/linkedin-job-scraper").call(run_input=run_input, timeout_secs=120)

        # Fetch results from the run's dataset
        print(f"Scraper finished. Fetching results from dataset: {run['defaultDatasetId']}")
        dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
        
        if not dataset_items:
            print("No jobs found in scrape results")
            return get_sample_jobs()
            
        return dataset_items

    except Exception as e:
        print(f"Apify Client error: {e}")
        return get_sample_jobs()
