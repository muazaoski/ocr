"""
Example Python client for the OCR API Service.

Usage:
    pip install requests
    python example_client.py
"""

import requests
from pathlib import Path


class OCRClient:
    """Client for interacting with the OCR API."""
    
    def __init__(self, base_url: str, api_key: str):
        """
        Initialize the OCR client.
        
        Args:
            base_url: API base URL (e.g., "http://localhost:8000")
            api_key: Your OCR API key
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"X-API-Key": api_key}
    
    def extract_text(
        self,
        image_path: str,
        language: str = "eng",
        preprocess: bool = True
    ) -> dict:
        """
        Extract text from an image.
        
        Args:
            image_path: Path to the image file
            language: OCR language code
            preprocess: Apply image preprocessing
        
        Returns:
            Dict with text, confidence, and processing time
        """
        url = f"{self.base_url}/ocr/extract"
        params = {"language": language, "preprocess": preprocess}
        
        with open(image_path, "rb") as f:
            files = {"file": (Path(image_path).name, f)}
            response = requests.post(
                url,
                headers=self.headers,
                params=params,
                files=files
            )
        
        response.raise_for_status()
        return response.json()
    
    def extract_detailed(
        self,
        image_path: str,
        language: str = "eng"
    ) -> dict:
        """
        Extract text with word-level data.
        
        Args:
            image_path: Path to the image file
            language: OCR language code
        
        Returns:
            Dict with text, words with positions, and confidence
        """
        url = f"{self.base_url}/ocr/extract/detailed"
        params = {"language": language}
        
        with open(image_path, "rb") as f:
            files = {"file": (Path(image_path).name, f)}
            response = requests.post(
                url,
                headers=self.headers,
                params=params,
                files=files
            )
        
        response.raise_for_status()
        return response.json()
    
    def batch_extract(
        self,
        image_paths: list[str],
        language: str = "eng"
    ) -> dict:
        """
        Extract text from multiple images.
        
        Args:
            image_paths: List of image file paths
            language: OCR language code
        
        Returns:
            Dict with batch results
        """
        url = f"{self.base_url}/ocr/batch"
        params = {"language": language}
        
        files = []
        file_handles = []
        
        try:
            for path in image_paths:
                f = open(path, "rb")
                file_handles.append(f)
                files.append(("files", (Path(path).name, f)))
            
            response = requests.post(
                url,
                headers=self.headers,
                params=params,
                files=files
            )
        finally:
            for f in file_handles:
                f.close()
        
        response.raise_for_status()
        return response.json()
    
    def get_languages(self) -> dict:
        """Get available OCR languages."""
        url = f"{self.base_url}/ocr/languages"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> dict:
        """Check API health status."""
        url = f"{self.base_url}/health"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()


# Example usage
if __name__ == "__main__":
    # Configuration
    API_URL = "http://localhost:8000"
    API_KEY = "ocr_your_api_key_here"  # Replace with your actual API key
    
    # Initialize client
    client = OCRClient(API_URL, API_KEY)
    
    # Check health
    print("🏥 Health Check:")
    health = client.health_check()
    print(f"   Status: {health['status']}")
    print(f"   Tesseract: {health['tesseract_version']}")
    print()
    
    # Example: Extract text from an image
    # Uncomment and update the path to test
    
    # print("📝 Extracting text...")
    # result = client.extract_text("path/to/your/image.png")
    # print(f"   Text: {result['text'][:100]}...")
    # print(f"   Confidence: {result['confidence']:.1f}%")
    # print(f"   Time: {result['processing_time_ms']:.1f}ms")
    
    # Example: Get detailed results
    # print("\n📊 Detailed extraction...")
    # detailed = client.extract_detailed("path/to/your/image.png")
    # print(f"   Words found: {detailed['word_count']}")
    # for word in detailed['words'][:5]:
    #     print(f"     - '{word['text']}' at ({word['left']}, {word['top']})")
    
    print("✅ Client ready! Update the API_KEY and test with your images.")
