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

class FactRequest(BaseModel):
    category: str = "random"
    exclude_facts: list[str] = []  # To avoid repeats

# Free fact API endpoints and local database fallback
FACT_SOURCES = {
    "science": [
        {"type": "api", "url": "https://science-facts.herokuapp.com/api/v1/facts/random"},
        {"type": "local", "facts": [
            "A teaspoon of neutron star material would weigh about 6 billion tons.",
            "There are more atoms in a single glass of water than glasses of water in all the oceans on Earth.",
            "The human body contains enough carbon to make 900 pencils."
        ]}
    ],
    "history": [
        {"type": "api", "url": "https://history-facts.herokuapp.com/api/v1/facts/random"},
        {"type": "local", "facts": [
            "Cleopatra lived closer in time to the Moon landing than to the building of the Great Pyramid.",
            "The shortest war in history was between Britain and Zanzibar in 1896. Zanzibar surrendered after 38 minutes.",
            "The Titanic's distress signals were ignored by a nearby ship whose radio operator had gone to bed."
        ]}
    ],
    "animal": [
        {"type": "api", "url": "https://animal-facts-api.herokuapp.com/facts/random"},
        {"type": "local", "facts": [
            "A blue whale's heart is so large that a human could swim through its arteries.",
            "Cows have best friends and get stressed when separated.",
            "Octopuses have three hearts and blue blood."
        ]}
    ],
    "random": [
        {"type": "api", "url": "https://uselessfacts.jsph.pl/random.json?language=en"},
        {"type": "local", "facts": []}  # Will be filled from other categories
    ]
}

# Initialize random category with all facts
all_facts = []
for category in ["science", "history", "animal"]:
    for source in FACT_SOURCES[category]:
        if source["type"] == "local":
            all_facts.extend(source["facts"])
FACT_SOURCES["random"][1]["facts"] = all_facts

# Cache to avoid hitting rate limits
fact_cache = {
    "science": {"facts": [], "last_updated": None},
    "history": {"facts": [], "last_updated": None},
    "animal": {"facts": [], "last_updated": None},
    "random": {"facts": [], "last_updated": None}
}

CACHE_EXPIRY = timedelta(minutes=30)

def fetch_facts_from_source(category):
    """Fetch facts from APIs and combine with local facts"""
    try:
        facts = []
        
        # Get from APIs first
        for source in FACT_SOURCES[category]:
            if source["type"] == "api":
                try:
                    response = requests.get(source["url"], timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, list):
                            facts.extend([item["fact"] if "fact" in item else item["text"] for item in data])
                        else:
                            if "text" in data:
                                facts.append(data["text"])
                            elif "fact" in data:
                                facts.append(data["fact"])
                except Exception as e:
                    logger.warning(f"Failed to fetch from {source['url']}: {str(e)}")
        
        # Add local facts
        for source in FACT_SOURCES[category]:
            if source["type"] == "local":
                facts.extend(source["facts"])
        
        if facts:
            fact_cache[category]["facts"] = facts
            fact_cache[category]["last_updated"] = datetime.now()
            return facts
        return None
    except Exception as e:
        logger.error(f"Error fetching facts: {str(e)}")
        return None

def get_fresh_fact(category, exclude_list):
    """Get a fresh fact that's not in the exclude list"""
    # Check if cache needs refresh
    if (fact_cache[category]["last_updated"] is None or 
        datetime.now() - fact_cache[category]["last_updated"] > CACHE_EXPIRY or
        len(fact_cache[category]["facts"]) < 3):
        fetch_facts_from_source(category)
    
    available_facts = [f for f in fact_cache[category]["facts"] if f not in exclude_list]
    
    if not available_facts:
        available_facts = fact_cache[category]["facts"]  # Fallback to possibly repeated facts
    
    return random.choice(available_facts) if available_facts else "The human brain is the only object that can contemplate itself."

@app.get("/health")
async def health_check():
    return {"status": "healthy", "cache_counts": {k: len(v["facts"]) for k, v in fact_cache.items()}}

@app.get("/categories")
async def get_categories():
    return {"categories": list(FACT_SOURCES.keys())}

@app.post("/generate")
async def generate_fact(request: FactRequest):
    try:
        category = request.category if request.category in FACT_SOURCES else "random"
        fact = get_fresh_fact(category, request.exclude_facts)
        
        return {
            "success": True,
            "fact": fact,
            "category": category
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "fallback": "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly good to eat."
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)