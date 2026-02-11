"""
Mock LLM Client - Shared mock implementation for testing
"""

from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt."""
        pass
    
    @abstractmethod
    def generate_batch(self, prompts: List[str], **kwargs) -> List[str]:
        """Generate text from multiple prompts."""
        pass


class MockLLMClient(BaseLLMClient):
    """Mock LLM client for testing without API calls."""
    
    def __init__(self, response_delay: float = 0.1):
        """
        Initialize mock client.
        
        Args:
            response_delay: Delay in seconds before returning response
        """
        self.response_delay = response_delay
        self.call_count = 0
        self.last_prompt = None
        self.responses: Dict[str, str] = {}
    
    def set_response(self, prompt_pattern: str, response: str) -> None:
        """
        Set a mock response for a prompt pattern.
        
        Args:
            prompt_pattern: Pattern to match (or exact string)
            response: Response to return
        """
        self.responses[prompt_pattern] = response
    
    def clear_responses(self) -> None:
        """Clear all mock responses."""
        self.responses.clear()
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate a mock response.
        
        Args:
            prompt: Input prompt
            
        Returns:
            Mock response or default placeholder
        """
        import time
        time.sleep(self.response_delay)
        
        self.call_count += 1
        self.last_prompt = prompt
        
        # Check for exact match first
        if prompt in self.responses:
            return self.responses[prompt]
        
        # Return default based on prompt content
        return self._generate_default_response(prompt)
    
    def generate_batch(self, prompts: List[str], **kwargs) -> List[str]:
        """
        Generate mock responses for multiple prompts.
        
        Args:
            prompts: List of input prompts
            
        Returns:
            List of mock responses
        """
        return [self.generate(p, **kwargs) for p in prompts]
    
    def _generate_default_response(self, prompt: str) -> str:
        """Generate a default mock response based on prompt content."""
        prompt_lower = prompt.lower()
        
        if "scene" in prompt_lower and ("breakdown" in prompt_lower or "summary" in prompt_lower):
            return """{
  "scenes": [
    {
      "id": "scene-mocked-1",
      "number": 1,
      "summary": "Introduction scene",
      "location": "Unknown location",
      "characters": [],
      "text_range": {"start": 0, "end": 50}
    }
  ]
}"""
        
        elif "character" in prompt_lower and "extract" in prompt_lower:
            return """[
                {
                    "id": "char-001",
                    "name": "Unknown Character",
                    "aliases": [],
                    "appearance": {"age": "unknown", "hair": "unknown"},
                    "frequency": 1
                }
            ]"""
        
        elif "panel" in prompt_lower and ("description" in prompt_lower or "breakdown" in prompt_lower):
            return """[
                {
                    "id": "p1-1",
                    "type": "establishing",
                    "description": "Wide establishing shot",
                    "camera": "wide-angle",
                    "mood": "neutral"
                }
            ]"""
        
        elif "storyboard" in prompt_lower or "visual" in prompt_lower:
            return """{
                "pages": [
                    {
                        "page_number": 1,
                        "panels": [
                            {
                                "panel_id": "p1-1",
                                "type": "establishing",
                                "description": "Scene setup",
                                "camera": "wide",
                                "mood": "neutral",
                                "dialogue": [],
                                "narration": ""
                            }
                        ]
                    }
                ]
            }"""
        
        elif "chapter" in prompt_lower and "segment" in prompt_lower:
            return """[
                {
                    "id": "chapter-1",
                    "number": 1,
                    "title": "Chapter One",
                    "start_line": 0,
                    "end_line": 100
                }
            ]"""
        
        else:
            return '{"result": "mock_response", "status": "success"}'
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics.
        
        Returns:
            Dictionary with call count and last prompt
        """
        return {
            "call_count": self.call_count,
            "last_prompt_length": len(self.last_prompt) if self.last_prompt else 0,
            "response_count": len(self.responses)
        }
    
    def reset_stats(self) -> None:
        """Reset call statistics."""
        self.call_count = 0
        self.last_prompt = None


class StreamingMockLLMClient(MockLLMClient):
    """Mock LLM client that simulates streaming responses."""
    
    def generate_streaming(self, prompt: str, chunk_size: int = 10, **kwargs):
        """
        Generate a mock streaming response.
        
        Args:
            prompt: Input prompt
            chunk_size: Size of each chunk to yield
            Yields:
                Chunks of the response
        """
        import time
        response = self.generate(prompt, **kwargs)
        
        # Split into chunks
        words = response.split()
        current_chunk = []
        
        for word in words:
            current_chunk.append(word)
            if len(current_chunk) >= chunk_size:
                yield " ".join(current_chunk)
                current_chunk = []
                time.sleep(0.01)  # Simulate streaming delay
        
        # Yield remaining
        if current_chunk:
            yield " ".join(current_chunk)
