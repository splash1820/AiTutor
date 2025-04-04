import google.generativeai as genai
import os
from typing import List, Dict, Any

class PlannerAgent:
    def __init__(self):
        # Initialize Google Gemini API
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("gemini-1.5-flash")
    
    def plan_content(self, query: str) -> Dict[str, Any]:
        """
        Create a structure for content based on user query
        
        Args:
            query: User's request for educational content
        
        Returns:
            Dictionary with title and sections to cover
        """
        prompt = f"""
        You are a Planner Agent for an educational content system. Given the user query below,
        create a detailed plan for educational content:
        
        USER QUERY: {query}
        
        Your response should be a JSON structure with:
        1. A clear, concise title
        2. An array of sections, where each section has:
           - type: either 'theory' or 'code'
           - topic: specific topic for this section
           - difficulty: 'beginner', 'intermediate', or 'advanced'
        
        For code sections, indicate which programming language should be used.
        if query is specific about a topic generate only required parts.
        """
        
        response = self.model.generate_content(prompt)
        
        # Parse the JSON response - in a production system, add better error handling
        # and response validation
        try:
            result = response.text
            # Clean up the response to extract just the JSON part
            import json
            import re
            
            # Find JSON content between triple backticks if present
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', result)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Otherwise try to find anything that looks like JSON
                json_str = re.search(r'(\{[\s\S]*\})', result).group(1)
            
            content_plan = json.loads(json_str)
            
            # Validate the structure
            if 'title' not in content_plan or 'sections' not in content_plan:
                raise ValueError("Invalid content plan structure")
            
            return content_plan
            
        except Exception as e:
            # Fallback to a basic structure if parsing fails
            return {
                "title": f"Content about: {query}",
                "sections": [
                    {
                        "type": "theory",
                        "topic": f"Introduction to {query}",
                        "difficulty": "beginner"
                    }
                ]
            }
    
    def assemble_content(self, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Assemble the final content from all completed sections
        
        Args:
            sections: List of completed sections with content
        
        Returns:
            Complete assembled content
        """
        # Here we could add more processing, like adding transitions between sections,
        # but for now we'll just assemble the sections into the final structure
        
        # Extract the title from the first section or use a default
        title = "Educational Content"
        if sections and 'topic' in sections[0]:
            title = sections[0]['topic']
        
        return {
            "title": title,
            "sections": sections,
            "metadata": {
                "created_at": "",  # We'll let the server fill this
                "version": "1.0"
            }
        }