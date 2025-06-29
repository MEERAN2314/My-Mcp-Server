from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import random
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JokeRequest(BaseModel):
    category: str = "random"
    exclude_jokes: list[str] = []  # To avoid repeats

# Free joke API endpoints
JOKE_APIS = {
    "general": [
        "https://official-joke-api.appspot.com/jokes/random",
        "https://v2.jokeapi.dev/joke/Any?type=single"
    ],
    "dad": [
        "https://icanhazdadjoke.com/",
        "https://v2.jokeapi.dev/joke/Dark?type=single"
    ],
    "programming": [
        "https://v2.jokeapi.dev/joke/Programming?type=single",
        "https://official-joke-api.appspot.com/jokes/programming/random"
    ],
    "random": [
        "https://v2.jokeapi.dev/joke/Any?type=single",
        "https://official-joke-api.appspot.com/jokes/random"
    ]
}

# Cache to avoid hitting rate limits
joke_cache = {
    "general": {"jokes": [], "last_updated": None},
    "dad": {"jokes": [], "last_updated": None},
    "programming": {"jokes": [], "last_updated": None},
    "random": {"jokes": [], "last_updated": None}
}

CACHE_EXPIRY = timedelta(minutes=30)

def fetch_jokes_from_api(category):
    """Fetch multiple jokes from free APIs and cache them"""
    try:
        jokes = []
        for api_url in JOKE_APIS[category]:
            try:
                headers = {"Accept": "application/json"} if "icanhazdadjoke" in api_url else {}
                response = requests.get(api_url, headers=headers, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        jokes.extend([item["joke"] if "joke" in item else item["setup"] + " " + item["punchline"] for item in data])
                    else:
                        if "joke" in data:
                            jokes.append(data["joke"])
                        elif "setup" in data:
                            jokes.append(data["setup"] + " " + data["delivery"])
                        elif "joke" in data:
                            jokes.append(data["joke"])
            except Exception as e:
                logger.warning(f"Failed to fetch from {api_url}: {str(e)}")
        
        if jokes:
            joke_cache[category]["jokes"] = jokes
            joke_cache[category]["last_updated"] = datetime.now()
            return jokes
        return None
    except Exception as e:
        logger.error(f"Error fetching jokes: {str(e)}")
        return None

def get_fresh_joke(category, exclude_list):
    """Get a fresh joke that's not in the exclude list"""
    # Check if cache needs refresh
    if (joke_cache[category]["last_updated"] is None or 
        datetime.now() - joke_cache[category]["last_updated"] > CACHE_EXPIRY or
        len(joke_cache[category]["jokes"]) < 3):
        fetch_jokes_from_api(category)
    
    available_jokes = [j for j in joke_cache[category]["jokes"] if j not in exclude_list]
    
    if not available_jokes:
        available_jokes = joke_cache[category]["jokes"]  # Fallback to possibly repeated jokes
    
    return random.choice(available_jokes) if available_jokes else "Why did the developer go broke? Because he used up all his cache!"

@app.get("/health")
async def health_check():
    return {"status": "healthy", "cache_counts": {k: len(v["jokes"]) for k, v in joke_cache.items()}}

@app.get("/categories")
async def get_categories():
    return {"categories": list(JOKE_APIS.keys())}

@app.post("/generate")
async def generate_joke(request: JokeRequest):
    try:
        category = request.category if request.category in JOKE_APIS else "random"
        joke = get_fresh_joke(category, request.exclude_jokes)
        
        return {
            "success": True,
            "joke": joke,
            "category": category
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "fallback": "Why don't scientists trust atoms? Because they make up everything!"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)