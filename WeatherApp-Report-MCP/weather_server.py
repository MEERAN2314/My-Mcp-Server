from fastapi import FastAPI, Query
from pydantic import BaseModel
import requests
from mcp.server.fastmcp import FastMCP

app = FastAPI()

# ---- MCP-like model agent ----

class WeatherAgent:
    """
    This acts like an MCP model node.
    You can swap the source: OpenWeatherMap, WeatherAPI, Scraper, or static data.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_weather(self, city: str) -> dict:
        """Fetch weather data from OpenWeatherMap."""
        url = (
            f"https://api.openweathermap.org/data/2.5/weather?"
            f"q={city}&appid={self.api_key}&units=metric"
        )
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return {
            "city": city,
            "temperature_C": data["main"]["temp"],
            "weather": data["weather"][0]["description"]
        }

# ---- MCP Orchestrator ----

class WeatherMCP:
    """
    Orchestrator that holds model context and routes.
    """

    def __init__(self, agent: WeatherAgent):
        self.agent = agent

    def handle_weather_request(self, city: str) -> dict:
        return self.agent.get_weather(city)

# ---- Instantiate MCP ----

# Use your own API key here
weather_agent = WeatherAgent(api_key="bcc39de31b1d0ae7af44fe6609b6acec")
mcp = WeatherMCP(agent=weather_agent)

# ---- API route ----

@app.get("/weather")
def get_weather(city: str = Query(..., description="City name")):
    """
    Example: GET /weather?city=London
    """
    try:
        result = mcp.handle_weather_request(city)
        return result
    except Exception as e:
        return {"error": str(e)}
