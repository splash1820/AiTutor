# agents/coding.py
import google.generativeai as genai
import os

class CodingAgent:
    def __init__(self):
        # Initialize Google Gemini API
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("gemini-1.5-flash")
    
    def generate_code(self, topic: str, language: str = "python") -> str:
        """
        Generate code examples for a given topic
        
        Args:
            topic: The topic to generate code for
            language: Programming language to use
        
        Returns:
            Generated code as a string
        """
        prompt = f"""
        You are a Coding Agent for an educational system. Generate clear, well-commented
        code examples for the following topic:
        
        TOPIC: {topic}
        LANGUAGE: {language}
        
        Requirements:
        1. The code should be educational and demonstrate best practices
        2. Include detailed comments explaining the code
        3. Make the examples practical and relevant to real-world use cases
        4. The code should be complete, runnable, and error-free
        """
        
        response = self.model.generate_content(prompt)
        
        # Extract code from response
        code = response.text
        
        # Remove any markdown code block indicators if present
        import re
        code = re.sub(r'```\w*\n', '', code)
        code = re.sub(r'```', '', code)
        
        return code.strip()
    
    def explain_code_answer(self, question: dict) -> str:
        """
        Provide a detailed explanation for a code-based test question
        
        Args:
            question: The question object containing the code problem and answer
        
        Returns:
            Detailed explanation of the answer
        """
        prompt = f"""
        You are a Coding Agent for an educational system. Provide a detailed explanation
        for the following coding question and its solution:
        
        QUESTION: {question['text']}
        
        CORRECT SOLUTION:
        {question['answer']}
        
        Provide a step-by-step explanation of:
        1. The approach used to solve the problem
        2. Why this approach works
        3. Any alternative approaches that could work
        4. Common mistakes students might make
        """
        
        response = self.model.generate_content(prompt)
        return response.text