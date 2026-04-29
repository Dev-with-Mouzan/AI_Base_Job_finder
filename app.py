import uvicorn
import os
import sys

# Add current directory to path so backend can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("Starting AI Job Matcher...")
    print("URL: http://localhost:8000")
    
    # Run the FastAPI app
    uvicorn.run("backend.main:app", reload=True)
