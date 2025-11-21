import requests
from ddgs import DDGS

class ToolsManager:
    def __init__(self):
        self.ddgs = DDGS()

    def get_weather(self, city="Singapore"):
        """
        Get current weather for a city using wttr.in
        """
        try:
            # Format: wttr.in/City?format=3 (returns "City: +25°C")
            # format=j1 returns JSON
            url = f"https://wttr.in/{city}?format=%C+%t"
            response = requests.get(url)
            if response.status_code == 200:
                # Replace degree symbol to avoid encoding artifacts (Â°) in Windows console
                weather_data = response.text.strip().replace('°', ' degrees')
                return f"The weather in {city} is {weather_data}."
            return "Sorry, I couldn't fetch the weather data."
        except Exception as e:
            return f"Weather error: {e}"

    def search_web(self, query):
        """
        Search the web using DuckDuckGo and return the top result summary
        """
        try:
            # region="us-en" forces English results to avoid encoding issues in console
            results = self.ddgs.text(query, region="us-en", max_results=1)
            if results:
                res = results[0]
                return f"Found this: {res['body']} (Source: {res['title']})"
            return "I couldn't find anything relevant on the web."
        except Exception as e:
            return f"Search error: {e}"

if __name__ == "__main__":
    # Test
    tools = ToolsManager()
    print(tools.get_weather("Singapore"))
    print(tools.search_web("Who won the super bowl 2024?"))
