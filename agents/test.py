import google.generativeai as genai
import os
import uuid
import json
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestAgent:
    def __init__(self):
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def generate_test(self, topic: str = None, content: dict = None, difficulty: str = "medium", num_questions: int = 5) -> dict:
        """
        Generate a test based on a topic or content
        """
        try:
            # Instead of trying to get JSON directly, let's ask for components separately
            questions = self._generate_questions(topic, content, difficulty, num_questions)
            
            # Create the test structure manually
            test_data = {
                "title": f"Test on {topic or 'Educational Content'}",
                "difficulty": difficulty,
                "questions": questions
            }
            
            return test_data
            
        except Exception as e:
            logger.error(f"Error generating test: {str(e)}")
            return self._create_fallback_test(topic, difficulty, num_questions)
    
    def _generate_questions(self, topic, content, difficulty, num_questions):
        """Generate questions separately to avoid complex JSON parsing"""
        content_text = self._format_content_text(content)
        
        # Create a template for each question type
        mcq_template = {
            "id": "{id}",
            "type": "mcq",
            "text": "{question}",
            "options": ["{option1}", "{option2}", "{option3}", "{option4}"],
            "answer": "{answer}",
            "explanation": "{explanation}"
        }
        
        code_template = {
            "id": "{id}",
            "type": "code",
            "text": "{question}",
            "answer": "{answer}",
            "test_cases": ["{test_case1}", "{test_case2}"],
            "explanation": "{explanation}"
        }
        
        descriptive_template = {
            "id": "{id}",
            "type": "descriptive",
            "text": "{question}",
            "answer": "{answer}",
            "explanation": "{explanation}"
        }
        
        # Generate different question types
        questions = []
        types = ["mcq", "code", "descriptive"]
        
        # Distribute question types evenly
        for i in range(num_questions):
            q_type = types[i % len(types)]
            question = self._generate_single_question(topic, content_text, difficulty, q_type)
            questions.append(question)
        
        return questions
    
    def _generate_single_question(self, topic, content_text, difficulty, question_type):
        """Generate a single question of the specified type"""
        if question_type == "mcq":
            return self._generate_mcq(topic, content_text, difficulty)
        elif question_type == "code":
            return self._generate_code_question(topic, content_text, difficulty)
        else:  # descriptive
            return self._generate_descriptive_question(topic, content_text, difficulty)
    
    def _generate_mcq(self, topic, content_text, difficulty):
        """Generate a multiple choice question"""
        prompt = f"""
        You are creating a multiple choice question about {"topic: " + topic if topic else "the following content:"}.
        {content_text if content_text else ""}
        Difficulty level: {difficulty}
        
        Generate:
        1. A clear question statement
        2. Four distinct answer options
        3. The correct answer (must be one of the four options)
        4. A brief explanation of why the answer is correct
        
        Format your response in exactly this order:
        QUESTION: (the question text)
        OPTION A: (first option)
        OPTION B: (second option)
        OPTION C: (third option)
        OPTION D: (fourth option)
        CORRECT: (the correct option letter: A, B, C, or D)
        EXPLANATION: (brief explanation)
        """
        
        response = self.model.generate_content(prompt)
        response_text = response.text
        
        # Extract components using regex
        question_match = re.search(r'QUESTION:\s*(.*?)(?=OPTION A:|$)', response_text, re.DOTALL)
        optionA_match = re.search(r'OPTION A:\s*(.*?)(?=OPTION B:|$)', response_text, re.DOTALL)
        optionB_match = re.search(r'OPTION B:\s*(.*?)(?=OPTION C:|$)', response_text, re.DOTALL)
        optionC_match = re.search(r'OPTION C:\s*(.*?)(?=OPTION D:|$)', response_text, re.DOTALL)
        optionD_match = re.search(r'OPTION D:\s*(.*?)(?=CORRECT:|$)', response_text, re.DOTALL)
        correct_match = re.search(r'CORRECT:\s*([A-D])', response_text)
        explanation_match = re.search(r'EXPLANATION:\s*(.*?)$', response_text, re.DOTALL)
        
        # Extract and clean the matched texts
        question = self._clean_text(question_match.group(1) if question_match else "Question placeholder")
        optionA = self._clean_text(optionA_match.group(1) if optionA_match else "Option A")
        optionB = self._clean_text(optionB_match.group(1) if optionB_match else "Option B")
        optionC = self._clean_text(optionC_match.group(1) if optionC_match else "Option C")
        optionD = self._clean_text(optionD_match.group(1) if optionD_match else "Option D")
        
        # Map the correct answer letter to the actual option text
        correct_letter = correct_match.group(1) if correct_match else "A"
        options = [optionA, optionB, optionC, optionD]
        option_map = {"A": optionA, "B": optionB, "C": optionC, "D": optionD}
        correct_answer = option_map.get(correct_letter, optionA)
        
        explanation = self._clean_text(explanation_match.group(1) if explanation_match else "Explanation placeholder")
        
        # Create MCQ question object
        mcq = {
            "id": str(uuid.uuid4()),
            "type": "mcq",
            "text": question,
            "options": options,
            "answer": correct_answer,
            "explanation": explanation
        }
        
        return mcq
    
    def _generate_code_question(self, topic, content_text, difficulty):
        """Generate a code question"""
        prompt = f"""
        You are creating a coding question about {"topic: " + topic if topic else "the following content:"}.
        {content_text if content_text else ""}
        Difficulty level: {difficulty}
        
        Generate:
        1. A clear coding problem statement
        2. The expected solution code (preferably in Python)
        3. A brief explanation of the solution
        4. Two simple test cases to verify the solution
        
        Format your response in exactly this order:
        QUESTION: (the coding problem statement)
        SOLUTION: 
        ```python
        (the expected solution code)
        ```
        EXPLANATION: (brief explanation)
        TEST CASE 1: (first test case)
        TEST CASE 2: (second test case)
        """
        
        response = self.model.generate_content(prompt)
        response_text = response.text
        
        # Extract components using regex
        question_match = re.search(r'QUESTION:\s*(.*?)(?=SOLUTION:|$)', response_text, re.DOTALL)
        solution_match = re.search(r'SOLUTION:\s*```python\s*(.*?)```', response_text, re.DOTALL)
        if not solution_match:
            solution_match = re.search(r'SOLUTION:\s*(.*?)(?=EXPLANATION:|$)', response_text, re.DOTALL)
        explanation_match = re.search(r'EXPLANATION:\s*(.*?)(?=TEST CASE 1:|$)', response_text, re.DOTALL)
        test_case1_match = re.search(r'TEST CASE 1:\s*(.*?)(?=TEST CASE 2:|$)', response_text, re.DOTALL)
        test_case2_match = re.search(r'TEST CASE 2:\s*(.*?)$', response_text, re.DOTALL)
        
        # Extract and clean the matched texts
        question = self._clean_text(question_match.group(1) if question_match else "Code question placeholder")
        solution = self._clean_text(solution_match.group(1) if solution_match else "def solution():\n    pass")
        explanation = self._clean_text(explanation_match.group(1) if explanation_match else "Explanation placeholder")
        test_case1 = self._clean_text(test_case1_match.group(1) if test_case1_match else "Test case 1")
        test_case2 = self._clean_text(test_case2_match.group(1) if test_case2_match else "Test case 2")
        
        # Create code question object
        code_question = {
            "id": str(uuid.uuid4()),
            "type": "code",
            "text": question,
            "answer": solution,
            "test_cases": [test_case1, test_case2],
            "explanation": explanation
        }
        
        return code_question
    
    def _generate_descriptive_question(self, topic, content_text, difficulty):
        """Generate a descriptive question"""
        prompt = f"""
        You are creating a descriptive question about {"topic: " + topic if topic else "the following content:"}.
        {content_text if content_text else ""}
        Difficulty level: {difficulty}
        
        Generate:
        1. A clear question that requires an explanatory answer
        2. A model answer that would get full marks
        3. Key points that should be included in a good answer
        
        Format your response in exactly this order:
        QUESTION: (the question text)
        MODEL ANSWER: (a comprehensive model answer)
        KEY POINTS: (key points that should be included)
        """
        
        response = self.model.generate_content(prompt)
        response_text = response.text
        
        # Extract components using regex
        question_match = re.search(r'QUESTION:\s*(.*?)(?=MODEL ANSWER:|$)', response_text, re.DOTALL)
        answer_match = re.search(r'MODEL ANSWER:\s*(.*?)(?=KEY POINTS:|$)', response_text, re.DOTALL)
        key_points_match = re.search(r'KEY POINTS:\s*(.*?)$', response_text, re.DOTALL)
        
        # Extract and clean the matched texts
        question = self._clean_text(question_match.group(1) if question_match else "Descriptive question placeholder")
        answer = self._clean_text(answer_match.group(1) if answer_match else "Model answer placeholder")
        key_points = self._clean_text(key_points_match.group(1) if key_points_match else "Key points placeholder")
        
        # Create descriptive question object
        descriptive_question = {
            "id": str(uuid.uuid4()),
            "type": "descriptive",
            "text": question,
            "answer": answer,
            "explanation": f"A good answer should include these key points: {key_points}"
        }
        
        return descriptive_question
    
    def _clean_text(self, text):
        """Clean extracted text"""
        if text is None:
            return ""
        return text.strip()
    
    def _format_content_text(self, content):
        """Format content for prompts"""
        if not content:
            return ""
            
        content_text = f"Title: {content['title']}\n\n"
        for section in content['sections']:
            content_text += f"Section: {section['topic']}\n"
            content_text += f"Content: {section['content']}\n\n"
        
        return content_text
    
    def _create_fallback_test(self, topic, difficulty, num_questions):
        """Create a fallback test when generation fails"""
        logger.info("Creating fallback test")
        basic_test = {
            "title": f"Test on {topic or 'Educational Content'}",
            "difficulty": difficulty,
            "questions": []
        }
        
        question_types = ['mcq', 'descriptive', 'code']
        for i in range(num_questions):
            question_type = question_types[i % len(question_types)]
            
            if question_type == "mcq":
                basic_test["questions"].append({
                    "id": str(uuid.uuid4()),
                    "type": "mcq",
                    "text": f"Question about {topic or 'the content'}",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "answer": "Option A",
                    "explanation": "This is the correct answer because it accurately describes the concept."
                })
            elif question_type == "descriptive":
                basic_test["questions"].append({
                    "id": str(uuid.uuid4()),
                    "type": "descriptive",
                    "text": f"Explain the concept of {topic or 'the main topic in the content'}",
                    "answer": "A detailed answer discussing key points and examples.",
                    "explanation": "A good answer covers definitions, examples, and practical applications."
                })
            else:  # code
                basic_test["questions"].append({
                    "id": str(uuid.uuid4()),
                    "type": "code",
                    "text": f"Write a function related to {topic or 'the content'}",
                    "answer": "def solution():\n    pass",
                    "test_cases": ["Test case 1", "Test case 2"],
                    "explanation": "Implement the function as per the problem statement."
                })
            
        return basic_test