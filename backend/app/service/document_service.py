import os
import requests
from typing import List, Dict, Any, Optional

class DocumentService:
    def __init__(self, base_url: str, api_key: str):
        """
        Initialize the DocumentService with the API base URL and authorization key.
        
        Args:
            base_url: Base URL for the API (e.g., 'http://localhost:9380')
            api_key: API key for authorization
        """
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}'
        }
    
    def upload_document(self, dataset_id: str, file_path: str) -> Dict[str, Any]:
        """
        Upload a document to a specific dataset.
        
        Args:
            dataset_id: ID of the dataset to upload to
            file_path: Path to the file to upload
            
        Returns:
            API response as a dictionary
        """
        url = f"{self.base_url}/api/v1/datasets/{dataset_id}/documents"
        
        # Prepare multipart form with file
        files = {
            'file': (os.path.basename(file_path), open(file_path, 'rb'))
        }
        
        headers = self.headers.copy()
        
        # Make POST request
        response = requests.post(url, headers=headers, files=files)
        return response.json()
    
    def parse_documents(self, dataset_id: str, document_ids: List[str]) -> Dict[str, Any]:
        """
        Parse documents to create chunks.
        
        Args:
            dataset_id: ID of the dataset containing the documents
            document_ids: List of document IDs to parse
            
        Returns:
            API response as a dictionary
        """
        url = f"{self.base_url}/api/v1/datasets/{dataset_id}/chunks"
        
        payload = {
            "document_ids": document_ids
        }
        
        headers = self.headers.copy()
        headers['Content-Type'] = 'application/json'
        
        # Make POST request
        response = requests.post(url, headers=headers, json=payload)
        return response.json()
    
    def get_documents(self, 
                      dataset_id: str, 
                      page: int = 1, 
                      page_size: int = 30, 
                      orderby: str = "create_time", 
                      desc: bool = True,
                      keywords: str = None,
                      document_id: str = None,
                      document_name: str = None) -> Dict[str, Any]:
        """
        Get list of documents in a dataset with various filtering options.
        
        Args:
            dataset_id: (Path parameter) ID of the dataset
            page: (Filter parameter) Page number for pagination. Defaults to 1.
            page_size: (Filter parameter) Number of items per page. Defaults to 30.
            orderby: (Filter parameter) Field to order by. Available options:
                     - create_time (default)
                     - update_time
            desc: (Filter parameter) Whether to sort in descending order. Defaults to True.
            keywords: (Filter parameter) Keywords to filter by matching document titles.
            document_id: (Filter parameter) Specific document ID to filter (id parameter in API)
            document_name: (Filter parameter) Document name to filter by (name parameter in API)
            
        Returns:
            API response as a dictionary
        """
        url = f"{self.base_url}/api/v1/datasets/{dataset_id}/documents"
        
        # Build query parameters
        params = {'page': page, 'page_size': page_size}
        if orderby:
            params['orderby'] = orderby
        if desc is not None:
            params['desc'] = desc
        if keywords:
            params['keywords'] = keywords
        if document_id:
            params['id'] = document_id
        if document_name:
            params['name'] = document_name
        
        # Make GET request
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()
    
    def delete_documents(self, dataset_id: str, document_ids: List[str]) -> Dict[str, Any]:
        """
        Delete documents from a dataset.
        
        Args:
            dataset_id: ID of the dataset
            document_ids: List of document IDs to delete
            
        Returns:
            API response as a dictionary
        """
        url = f"{self.base_url}/api/v1/datasets/{dataset_id}/documents"
        
        payload = {
            "ids": document_ids
        }
        
        headers = self.headers.copy()
        headers['Content-Type'] = 'application/json'
        
        # Make DELETE request
        response = requests.delete(url, headers=headers, json=payload)
        return response.json()
    
    def retrieve_documents(self, 
                          question: str, 
                          dataset_ids: List[str] = None, 
                          document_ids: List[str] = None) -> Dict[str, Any]:
        """
        Retrieve documents based on a question.
        
        Args:
            question: The query text for retrieval
            dataset_ids: List of dataset IDs to search in
            document_ids: List of specific document IDs to search in
            
        Returns:
            API response as a dictionary
        """
        url = f"{self.base_url}/api/v1/retrieval"
        
        payload = {
            "question": question
        }
        
        if dataset_ids:
            payload["dataset_ids"] = dataset_ids
        if document_ids:
            payload["document_ids"] = document_ids
        
        headers = self.headers.copy()
        headers['Content-Type'] = 'application/json'
        
        # Make POST request
        response = requests.post(url, headers=headers, json=payload)
        return response.json() 