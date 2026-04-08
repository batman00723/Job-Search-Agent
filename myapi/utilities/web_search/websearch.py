import requests
import json
from backend.config import settings

class WebSearch:
    @staticmethod
    def search_the_web(query: str):
        api_key = settings.tavily_api_key.get_secret_value()
   
        url = "https://api.tavily.com/search"
        
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": "basic", 
            "max_results": 5,
            "include_images": False,
            "include_answer": False,
            "include_raw_content": False,
            "include_domains": [],
            "exclude_domains": []
        }
        
        try:
           
            response = requests.post(
                url, 
                data=json.dumps(payload), 
                headers=headers, 
                timeout=(5, 10),
            )
            
       
            if response.status_code != 200:
                print(f"DEBUG TAVILY REJECTION: {response.text}")
                return f"Tavily Error {response.status_code}: {response.text}"
                
            results_json = response.json()
            search_results = results_json.get('results', [])
            
            if not search_results:
                return []

            
            return search_results

        except Exception as e:
            print(f"SYSTEM ERROR IN WEBSEARCH: {str(e)}")
            return f"Web search failed: {str(e)}"