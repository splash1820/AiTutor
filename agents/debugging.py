# agents/debugging.py
import google.generativeai as genai
import os

class DebuggingAgent:
    def __init__(self):
        # Initialize Google Gemini API
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("gemini-1.5-flash")
    
    def debug_code(self, code: str, language: str = "python") -> dict:
        """
        Debug code and identify issues
        
        Args:
            code: The code to debug
            language: The programming language
            
        Returns:
            Dictionary with debugged code, issues found, and explanation
        """
        prompt = f"""
        You are a Debugging Agent for an educational system. Debug the following code and identify issues:
        
        LANGUAGE: {language}
        
        CODE:
        {code}
        
        Provide:
        1. Fixed version of the code
        2. List of issues found
        3. Explanation of each issue and how it was fixed
        
        Format your response as a JSON object with keys:
        - "code": the fixed code
        - "issues": array of issues found
        - "explanation": detailed explanation
        """
        
        response = self.model.generate_content(prompt)
        
        # Parse the JSON response - in a production system, add better error handling
        try:
            import json
            import re
            
            # Find JSON content between triple backticks if present
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response.text)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Otherwise try to find anything that looks like JSON
                json_str = re.search(r'(\{[\s\S]*\})', response.text).group(1)
            
            debug_result = json.loads(json_str)
            return debug_result
            
        except Exception as e:
            # Fallback if parsing fails
            return {
                "code": code,  # Return original if we couldn't parse the response
                "issues": ["Could not parse debugging results"],
                "explanation": "The debugging process encountered an error."
            }
    
    def evaluate_code(self, expected_code: str, user_code: str, test_cases: list = None) -> dict:
        """
        Evaluate user's code submission
        
        Args:
            expected_code: The model solution
            user_code: The user's submitted code
            test_cases: Optional list of test cases to run
            
        Returns:
            Evaluation with status, feedback, and score
        """
        test_cases_str = "No test cases provided."
        if test_cases:
            test_cases_str = "Test Cases:\n" + "\n".join([str(tc) for tc in test_cases])
        
        prompt = f"""
        You are evaluating a student's code submission. Compare the student's code to the expected solution.
        
        EXPECTED SOLUTION:
        {expected_code}
        
        STUDENT'S CODE:
        {user_code}
        
        {test_cases_str}
        
        Evaluate the student's code and respond with a JSON object containing:
        1. "status": one of "correct", "partially_correct", or "wrong"
        2. "feedback": specific feedback on the code's strengths and weaknesses
        3. "score": a score from 0 to 100
        
        Base your evaluation on:
        - Correctness (does it accomplish the task)
        - Code quality and style
        - Efficiency of the solution
        - Proper handling of edge cases
        """
        
        response = self.model.generate_content(prompt)
        
        # Parse the JSON response - in a production system, add better error handling
        try:
            import json
            import re
            
            # Find JSON content between triple backticks if present
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response.text)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Otherwise try to find anything that looks like JSON
                json_str = re.search(r'(\{[\s\S]*\})', response.text).group(1)
            
            evaluation = json.loads(json_str)
            return evaluation
            
        except Exception as e:
            # Fallback evaluation if parsing fails
            code_similarity = self._calculate_code_similarity(expected_code, user_code)
            
            if code_similarity > 0.8:
                status = "correct"
                score = 90
            elif code_similarity > 0.5:
                status = "partially_correct"
                score = 50
            else:
                status = "wrong"
                score = 20
                
            return {
                "status": status,
                "feedback": "Your code was evaluated automatically. The similarity with the expected solution was calculated.",
                "score": score
            }
    
    def _calculate_code_similarity(self, code1: str, code2: str) -> float:
        """
        Calculate a simple similarity score between two code snippets
        
        This is a basic implementation - in a production system you'd
        use a more sophisticated approach
        
        Args:
            code1: First code snippet
            code2: Second code snippet
            
        Returns:
            Similarity score between 0 and 1
        """
        # Remove comments, extra whitespace, and normalize
        import re
        
        def normalize_code(code):
            # Remove comments
            code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
            # Remove extra whitespace
            code = re.sub(r'\s+', ' ', code)
            return code.strip().lower()
        
        normalized1 = normalize_code(code1)
        normalized2 = normalize_code(code2)
        
        # Convert to sets of words/tokens
        tokens1 = set(normalized1.split())
        tokens2 = set(normalized2.split())
        
        # Calculate Jaccard similarity
        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        
        return intersection / union if union > 0 else 0

# agents/test.py
import google.generativeai as genai
import os
import uuid

class TestAgent:
    def __init__(self):
        # Initialize Google Gemini API
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-pro')
    
    def generate_test(self, topic: str = None, content: dict = None, difficulty: str = "medium", num_questions: int = 5) -> dict:
        """
        Generate a test based on a topic or content
        
        Args:
            topic: The topic for the test (optional if content is provided)
            content: The content to base the test on (optional if topic is provided)
            difficulty: Difficulty level (beginner, medium, advanced)
            num_questions: Number of questions to generate
            
        Returns:
            Test structure with questions
        """
        content_text = ""
        if content:
            # Extract text from content
            content_text = f"Title: {content['title']}\n\n"
            for section in content['sections']:
                content_text += f"Section: {section['topic']}\n"
                content_text += f"Content: {section['content']}\n\n"
        
        prompt = f"""
        You are a Test Agent for an educational system. Generate a comprehensive test based on the following:
        
        {"TOPIC: " + topic if topic else ""}
        {"CONTENT: " + content_text if content_text else ""}
        DIFFICULTY: {difficulty}
        NUMBER OF QUESTIONS: {num_questions}
        
        Create a mix of question types:
        1. Multiple choice questions (MCQs) with 4 options each
        2. Code-based questions where the student needs to write code
        3. Descriptive questions where the student needs to explain concepts
        
        Format your response as a JSON object with:
        - "title": title of the test
        - "difficulty": difficulty level
        - "questions": array of question objects, where each question has:
          - "id": unique question ID
          - "type": "mcq", "code", or "descriptive"
          - "text": the question text
          - "options": array of options (for MCQ only)
          - "answer": the correct answer or model solution
          - "test_cases": array of test cases (for code questions only, optional)
          - "explanation": brief explanation of the answer
        """
        
        response = self.model.generate_content(prompt)
        
        # Parse the JSON response - in a production system, add better error handling
        try:
            import json
            import re
            
            # Find JSON content between triple backticks if present
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response.text)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Otherwise try to find anything that looks like JSON
                json_str = re.search(r'(\{[\s\S]*\})', response.text).group(1)
            
            test_data = json.loads(json_str)
            
            # Ensure each question has a unique ID
            for question in test_data['questions']:
                if 'id' not in question:
                    question['id'] = str(uuid.uuid4())
            
            return test_data
            
        except Exception as e:
            # Fallback to a basic test if parsing fails
            basic_test = {
                "title": f"Test on {topic or 'Educational Content'}",
                "difficulty": difficulty,
                "questions": []
            }
            
            # Generate a very basic set of questions
            for i in range(min(num_questions, 3)):
                question_id = str(uuid.uuid4())
                question_type = ["mcq", "descriptive", "code"][i % 3]
                
                if question_type == "mcq":
                    basic_test["questions"].append({
                        "id": question_id,
                        "type": "mcq",
                        "text": f"Question {i+1} about {topic or 'the content'}",
                        "options": ["Option A", "Option B", "Option C", "Option D"],
                        "answer": "Option A",
                        "explanation": "This is the correct option because it accurately describes the concept."
                    })
                elif question_type == "descriptive":
                    basic_test["questions"].append({
                        "id": question_id,
                        "type": "descriptive",
                        "text": f"Explain the concept of {topic or 'the main topic in the content'}",
                        "answer": "A model answer would discuss key points, principles, and examples.",
                        "explanation": "A good answer should cover the definition, examples, and applications."
                    })
                else:  # code
                    basic_test["questions"].append({
                        "id": question_id,
                        "type": "code",
                        "text": f"Write a function to solve the following problem related to {topic or 'the content'}",
                        "answer": "def solution():\n    # A sample solution\n    return 'result'",
                        "test_cases": ["test case 1", "test case 2"],
                        "explanation": "The solution should implement the algorithm efficiently."
                    })
            
            return basic_test