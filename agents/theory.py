# agents/theory.py
import google.generativeai as genai
import os

class TheoryAgent:
    def __init__(self):
        # Initialize Google Gemini API
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("gemini-1.5-flash")
    
    def generate_theory(self, topic: str, difficulty: str = "medium") -> str:
        """
        Generate theory content for a given topic
        
        Args:
            topic: The topic to generate theory for
            difficulty: Difficulty level (beginner, medium, advanced)
        
        Returns:
            Generated theory content as a string
        """
        prompt = f"""
        You are a Theory Agent for an educational system. Generate comprehensive theory content
        for the following topic:
        
        TOPIC: {topic}
        DIFFICULTY: {difficulty}
        
        Requirements:
        1. Explain concepts clearly with examples
        2. Highlight potentially difficult parts and provide additional explanation
        3. Use analogies where appropriate to make complex concepts easier to understand
        4. For {difficulty} level students
        5. Include real-world applications where relevant
        """
        
        response = self.model.generate_content(prompt)
        return response.text
    
    def evaluate_mcq(self, question: str, options: list, correct_answer: str, user_answer: str) -> dict:
        """
        Evaluate a user's answer to an MCQ question
        
        Args:
            question: The question text
            options: List of available options
            correct_answer: The correct answer
            user_answer: The user's answer
        
        Returns:
            Evaluation result with status and feedback
        """
        # Simple exact match evaluation
        is_correct = user_answer == correct_answer
        
        if is_correct:
            status = "correct"
            feedback = "Your answer is correct!"
            score = 100
        else:
            status = "wrong"
            feedback = f"Your answer is incorrect. The correct answer is: {correct_answer}"
            score = 0
        
        return {
            "status": status,
            "feedback": feedback,
            "score": score
        }
    
    def evaluate_descriptive(self, question: str, model_answer: str, user_answer: str) -> dict:
        """
        Evaluate a user's descriptive answer
        
        Args:
            question: The question text
            model_answer: The model answer to compare against
            user_answer: The user's answer
        
        Returns:
            Evaluation result with status, feedback and score
        """
        prompt = f"""
        You are evaluating a student's answer to a descriptive question.
        
        QUESTION: {question}
        
        MODEL ANSWER: {model_answer}
        
        STUDENT'S ANSWER: {user_answer}
        
        Evaluate the student's answer and respond with a JSON object containing:
        1. "status": one of "correct", "partially_correct", or "wrong"
        2. "feedback": specific feedback on the answer's strengths and weaknesses
        3. "score": a score from 0 to 100
        
        Base your evaluation on:
        - Accuracy of information
        - Completeness of answer
        - Understanding of concepts
        - Clarity of explanation
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
            similarity = self._calculate_similarity(model_answer, user_answer)
            
            if similarity > 0.8:
                status = "correct"
                score = 90
            elif similarity > 0.5:
                status = "partially_correct"
                score = 50
            else:
                status = "wrong"
                score = 10
                
            return {
                "status": status,
                "feedback": "Your answer was evaluated automatically.",
                "score": score
            }
        
    def converse(self, user_message: str, conversation_history: list = None) -> str:
      """
      Have a conversation with the Theory Agent about educational topics
      
      Args:
          user_message: The user's message or question
          conversation_history: List of previous conversation exchanges (optional)
          
      Returns:
          The agent's response as a string
      """
      # Initialize history if not provided
      if conversation_history is None:
          conversation_history = []
      
      # Format conversation history for context
      history_text = ""
      if conversation_history:
          for entry in conversation_history:
              if 'user' in entry:
                  history_text += f"User: {entry['user']}\n"
              if 'agent' in entry:
                  history_text += f"Theory Agent: {entry['agent']}\n"
      
      prompt = f"""
      You are a Theory Agent for an educational system, specializing in explaining concepts clearly.
      You excel at breaking down complex topics, providing examples, and making connections to help
      students understand difficult material.
      
      CONVERSATION HISTORY:
      {history_text}
      
      USER MESSAGE: {user_message}
      
      Respond helpfully, focusing on educational content. Your strengths include:
      1. Clear explanations with examples
      2. Breaking down complex topics into manageable parts
      3. Making connections between concepts
      4. Answering follow-up questions with patience
      5. Suggesting related topics to explore
      
      Keep your response concise yet thorough. Use markdown formatting for clarity.
      """
      
      response = self.model.generate_content(prompt)
      return response.text
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate a simple similarity score between two texts
        
        This is a basic implementation - in a production system you'd
        use a more sophisticated approach like cosine similarity with embeddings
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        # Convert to lowercase and split into words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0
    
    def explain_mcq_answer(self, question: dict) -> str:
        """
        Provide a detailed explanation for an MCQ question
        
        Args:
            question: The question object containing the MCQ and answer
            
        Returns:
            Detailed explanation of the answer
        """
        options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(question['options'])])
        
        prompt = f"""
        You are a Theory Agent for an educational system. Provide a detailed explanation
        for why the following multiple-choice question has the answer it does:
        
        QUESTION: {question['text']}
        
        OPTIONS:
        {options_text}
        
        CORRECT ANSWER: {question['answer']}
        
        Provide:
        1. Why the correct answer is right
        2. Why each of the other options is wrong
        3. The key concept being tested
        4. Any tips for remembering this information
        """
        
        response = self.model.generate_content(prompt)
        return response.text
    
    def explain_descriptive_answer(self, question: dict) -> str:
        """
        Provide a detailed explanation for a descriptive question
        
        Args:
            question: The question object containing the descriptive question and model answer
            
        Returns:
            Detailed explanation of the answer
        """
        prompt = f"""
        You are a Theory Agent for an educational system. Provide a detailed explanation
        for the following descriptive question:
        
        QUESTION: {question['text']}
        
        MODEL ANSWER:
        {question['answer']}
        
        Provide:
        1. A breakdown of why this is a good answer
        2. The key points that should be included
        3. How to structure such an answer effectively
        4. Common misconceptions about this topic
        """
        
        response = self.model.generate_content(prompt)
        return response.text