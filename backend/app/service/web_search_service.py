import http.client
import json
import os
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

class WebSearchService:
    """Service for performing web searches using the Serper API"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize the WebSearchService with API key.
        
        Args:
            api_key: API key for Serper.dev. If not provided, will attempt to read from environment.
        """
        self.api_key = api_key or os.environ.get('SERPER_API_KEY')
        self.host = "google.serper.dev"
        self.headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def search(self, 
              query: str, 
              gl: str = "cn", 
              hl: str = "zh-cn", 
              autocorrect: bool = True, 
              page: int = 1,
              search_type: str = "search") -> Dict[str, Any]:
        """
        Perform a web search using Serper API.
        
        Args:
            query: Search query text
            gl: Google country code (default: "us")
            hl: Language code (default: "en")
            autocorrect: Whether to enable autocorrection (default: True)
            page: Search result page number (default: 1)
            search_type: Type of search (default: "search")
            
        Returns:
            Search results as a dictionary
        """
        conn = http.client.HTTPSConnection(self.host)
        
        payload = json.dumps({
            "q": query,
            "gl": gl,
            "hl": hl,
            "autocorrect": autocorrect,
            "page": page,
            "type": search_type
        })
        
        try:
            conn.request("POST", "/search", payload, self.headers)
            res = conn.getresponse()
            data = res.read()
            return json.loads(data.decode("utf-8"))
        except Exception as e:
            return {
                "error": True,
                "message": f"Search failed: {str(e)}"
            }
        finally:
            conn.close()
    
    def extract_search_results(self, search_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract formatted search results from the API response.
        
        Args:
            search_results: Full API response from search method
            
        Returns:
            List of simplified search result items
        """
        results = []
        
        # Add knowledge graph if present
        if "knowledgeGraph" in search_results:
            kg = search_results["knowledgeGraph"]
            results.append({
                "type": "knowledgeGraph",
                "title": kg.get("title", ""),
                "description": kg.get("description", ""),
                "source": kg.get("descriptionSource", ""),
                "link": kg.get("descriptionLink", ""),
                "attributes": kg.get("attributes", {})
            })
            
        # Add organic search results
        if "organic" in search_results:
            for item in search_results["organic"]:
                results.append({
                    "type": "organic",
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "position": item.get("position", 0)
                })
                
        # Add people also ask
        if "peopleAlsoAsk" in search_results:
            for item in search_results["peopleAlsoAsk"]:
                results.append({
                    "type": "peopleAlsoAsk",
                    "question": item.get("question", ""),
                    "snippet": item.get("snippet", ""),
                    "title": item.get("title", ""),
                    "link": item.get("link", "")
                })
                
        # Add related searches
        if "relatedSearches" in search_results and search_results["relatedSearches"]:
            related = [item.get("query", "") for item in search_results["relatedSearches"] if "query" in item]
            if related:
                results.append({
                    "type": "relatedSearches",
                    "queries": related
                })
                
        return results 