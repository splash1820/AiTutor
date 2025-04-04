# app.py
from flask import Flask, request, jsonify, send_file,render_template
from flask_cors import CORS
import json
import os
import io
import uuid
from datetime import datetime
from agents.planner import PlannerAgent
from agents.coding import CodingAgent
from agents.theory import TheoryAgent
from agents.debugging import DebuggingAgent
from agents.test import TestAgent

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize agents
planner_agent = PlannerAgent()
coding_agent = CodingAgent()
theory_agent = TheoryAgent()
debugging_agent = DebuggingAgent()
test_agent = TestAgent()

# Storage for generated content and tests
CONTENT_DIR = "generated_content"
TEST_DIR = "generated_tests"
RESULTS_DIR = "test_results"

# Create directories if they don't exist
for directory in [CONTENT_DIR, TEST_DIR, RESULTS_DIR]:
    os.makedirs(directory, exist_ok=True)

@app.route('/api/generate-content', methods=['POST'])
def generate_content():
    """Endpoint to generate educational content based on user query"""
    data = request.json
    query = data.get('query')
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    # Step 1: Planner agent creates the structure
    structure = planner_agent.plan_content(query)
    print(structure)
    
    # Step 2: Process each section according to its type
    completed_sections = []
    
    for section in structure['sections']:
        section_type = section['type']
        section_topic = section['topic']
        
        if section_type == 'code':
            # Request code from coding agent
            code_content = coding_agent.generate_code(section_topic)
            
            # Debug the code
            debugged_code = debugging_agent.debug_code(code_content)
            
            section['content'] = debugged_code
            
        elif section_type == 'theory':
            # Request theory content
            theory_content = theory_agent.generate_theory(
                section_topic, 
                difficulty=section.get('difficulty', 'medium')
            )
            section['content'] = theory_content
        
        completed_sections.append(section)
    
    # Step 3: Final assembly by planner
    final_content = planner_agent.assemble_content(completed_sections)
    
    # Save content with unique ID
    content_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{content_id}_{timestamp}.json"
    
    with open(os.path.join(CONTENT_DIR, filename), 'w') as f:
        json.dump(final_content, f, indent=2)
    
    return jsonify({
        "content_id": content_id,
        "content": final_content
    })

@app.route('/api/generate-test', methods=['POST'])
def generate_test():
    """Endpoint to generate a test based on content or topic"""
    data = request.json
    topic = data.get('topic')
    content_id = data.get('content_id')
    difficulty = data.get('difficulty', 'medium')
    num_questions = data.get('num_questions', 5)
    
    if not topic and not content_id:
        return jsonify({"error": "Either topic or content_id must be provided"}), 400
    
    # If content_id is provided, load that content
    content = None
    if content_id:
        # Find the file with matching ID prefix
        for filename in os.listdir(CONTENT_DIR):
            if filename.startswith(content_id):
                with open(os.path.join(CONTENT_DIR, filename), 'r') as f:
                    content = json.load(f)
                break
    
    # Generate test using test agent
    test = test_agent.generate_test(
        topic=topic,
        content=content,
        difficulty=difficulty,
        num_questions=num_questions
    )
    
    # Save test with unique ID
    test_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{test_id}_{timestamp}.json"
    
    
    with open(os.path.join(TEST_DIR, filename), 'w') as f:
        json.dump(test, f, indent=2)
    options = []
    for question in test['questions']:
      if 'options' in question:
        options.append(question['options'])
    
    return jsonify({
        "test_id": test_id,
        "test": test,
        "extracted_options":options
    })

@app.route('/api/submit-test', methods=['POST'])
def submit_test():
    """Endpoint to evaluate user's test answers"""
    data = request.json
    test_id = data.get('test_id')
    user_answers = data.get('answers', [])
    
    if not test_id:
        return jsonify({"error": "No test_id provided"}), 400
    
    # Find the test file
    test_data = None
    for filename in os.listdir(TEST_DIR):
        if filename.startswith(test_id):
            with open(os.path.join(TEST_DIR, filename), 'r') as f:
                test_data = json.load(f)
            break
    
    if not test_data:
        return jsonify({"error": "Test not found"}), 404
    
    # Evaluate each answer with the appropriate agent
    results = []
    for i, question in enumerate(test_data['questions']):
        question_type = question['type']
        question_id = question['id']
        user_answer = next((a for a in user_answers if a['question_id'] == question_id), None)
        
        if not user_answer:
            result = {
                "question_id": question_id,
                "question_number": i + 1,
                "evaluation": "not_answered",
                "correct_answer": question['answer'],
                "score": 0
            }
        else:
            if question_type == 'mcq':
                # Evaluate MCQ with theory agent
                evaluation = theory_agent.evaluate_mcq(
                    question=question['text'],
                    options=question['options'],
                    correct_answer=question['answer'],
                    user_answer=user_answer['answer']
                )
            elif question_type == 'code':
                # Evaluate code with debugging agent
                evaluation = debugging_agent.evaluate_code(
                    expected_code=question['answer'],
                    user_code=user_answer['answer'],
                    test_cases=question.get('test_cases', [])
                )
            elif question_type == 'descriptive':
                # Evaluate descriptive answer with theory agent
                evaluation = theory_agent.evaluate_descriptive(
                    question=question['text'],
                    model_answer=question['answer'],
                    user_answer=user_answer['answer']
                )
            
            result = {
                "question_id": question_id,
                "question_number": i + 1,
                "evaluation": evaluation['status'],  # 'correct', 'wrong', or 'partially_correct'
                "feedback": evaluation['feedback'],
                "correct_answer": question['answer'],
                "score": evaluation['score']
            }
        
        results.append(result)
    
    # Calculate overall score
    total_score = sum(r['score'] for r in results)
    max_score = len(results) * 100
    percentage = (total_score / max_score) * 100 if max_score > 0 else 0
    
    final_result = {
        "test_id": test_id,
        "total_score": total_score,
        "max_score": max_score,
        "percentage": percentage,
        "questions_results": results
    }
    
    # Save results
    result_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{result_id}_{timestamp}.json"
    
    with open(os.path.join(RESULTS_DIR, filename), 'w') as f:
        json.dump(final_result, f, indent=2)
    
    return jsonify({
        "result_id": result_id,
        "results": final_result
    })

@app.route('/api/export-content/<content_id>', methods=['GET'])
def export_content(content_id):
    """Endpoint to export generated content in various formats"""
    format_type = request.args.get('format', 'json')

    # Find content file
    content_data = None
    for filename in os.listdir(CONTENT_DIR):
        if filename.startswith(content_id):
            with open(os.path.join(CONTENT_DIR, filename), 'r') as f:
                content_data = json.load(f)
            break

    if not content_data:
        return jsonify({"error": "Content not found"}), 404

    if format_type == 'json':
        return jsonify(content_data)

    elif format_type == 'pdf':
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        import io

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, 
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=72)
        
        styles = getSampleStyleSheet()
        # Create custom styles with a unique name
        styles.add(ParagraphStyle(
            name='CustomCode',  # Changed from 'Code' to 'CustomCode'
            fontName='Courier',
            fontSize=9,
            spaceAfter=12,
            backColor=colors.lightgrey,
            borderPadding=5,
            leading=14
        ))
        
        story = []
        
        # Add title
        title = Paragraph(f"<b>{content_data['title']}</b>", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 0.25*inch))
        
        # Process sections
        for section in content_data['sections']:
            # Section heading
            heading = Paragraph(f"<b>{section['topic']}</b>", styles['Heading2'])
            story.append(heading)
            story.append(Spacer(1, 0.1*inch))
            
            content = section['content']
            
            if section['type'] == 'code':
                # Format code section
                if isinstance(content, str):
                    code_text = content
                elif isinstance(content, dict):
                    code_text = "\n".join([f"{key}: {str(value)}" for key, value in content.items()])
                elif isinstance(content, list):
                    code_text = "\n".join([str(item) for item in content])
                else:
                    code_text = str(content)
                
                # Use Preformatted for code to preserve spacing
                code = Preformatted(code_text, styles['CustomCode'])  # Updated to use CustomCode
                story.append(code)
                
            else:
                # Format theory/text content
              if isinstance(content, str):
                  # Convert markdown-style formatting
                  text_content = content
                  
                  # First handle bold (4 asterisks or double asterisks)
                  # Process **** style (convert to <b>)
                  while '****' in text_content:
                      parts = text_content.split('****', 1)
                      if len(parts) > 1:
                          second_parts = parts[1].split('****', 1)
                          if len(second_parts) > 1:
                              text_content = parts[0] + '<b>' + second_parts[0] + '</b>' + second_parts[1]
                          else:
                              # No closing tag found, leave as is
                              break
                  
                  # Process ** style (convert to <b>)
                  while '**' in text_content:
                      parts = text_content.split('**', 1)
                      if len(parts) > 1:
                          second_parts = parts[1].split('**', 1)
                          if len(second_parts) > 1:
                              text_content = parts[0] + '<b>' + second_parts[0] + '</b>' + second_parts[1]
                          else:
                              # No closing tag found, leave as is
                              break
                  
                  # Then handle italic (single asterisks)
                  # Process * style (convert to <i>)
                  while '*' in text_content:
                      parts = text_content.split('*', 1)
                      if len(parts) > 1:
                          second_parts = parts[1].split('*', 1)
                          if len(second_parts) > 1:
                              text_content = parts[0] + '<i>' + second_parts[0] + '</i>' + second_parts[1]
                          else:
                              # No closing tag found, leave as is
                              break
                  
                  # Split by paragraphs and create paragraph objects
                  paragraphs = text_content.split('\n\n')
                  for para in paragraphs:
                      if para.strip():
                          # Ensure any < > characters are properly escaped to avoid XML parsing issues
                          para = para.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                          # Then re-insert the actual HTML tags we want
                          para = para.replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')
                          para = para.replace('&lt;i&gt;', '<i>').replace('&lt;/i&gt;', '</i>')
                          para = para.replace('&lt;br/&gt;', '<br/>')
                          
                          p = Paragraph(para.replace('\n', '<br/>'), styles['Normal'])
                          story.append(p)
                          story.append(Spacer(1, 0.1*inch))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            mimetype='application/pdf',
            download_name=f"content_{content_id}.pdf"
        )

    elif format_type == 'markdown':
        # Convert to markdown
        markdown = f"# {content_data['title']}\n\n"
        for section in content_data['sections']:
            markdown += f"## {section['topic']}\n\n"
            
            content = section['content']
            if section['type'] == 'code':
                if isinstance(content, str):
                    markdown += f"```\n{content}\n```\n\n"
                elif isinstance(content, dict):
                    markdown += "```\n"
                    for key, value in content.items():
                        markdown += f"{key}: {str(value)}\n"
                    markdown += "```\n\n"
                elif isinstance(content, list):
                    markdown += "```\n"
                    for item in content:
                        markdown += f"{str(item)}\n"
                    markdown += "```\n\n"
                else:
                    markdown += f"```\n{str(content)}\n```\n\n"
            else:
                if isinstance(content, str):
                    markdown += f"{content}\n\n"
                elif isinstance(content, dict):
                    for key, value in content.items():
                        markdown += f"**{key}**: {str(value)}\n\n"
                elif isinstance(content, list):
                    for item in content:
                        markdown += f"- {str(item)}\n"
                    markdown += "\n"
                else:
                    markdown += f"{str(content)}\n\n"

        return send_file(
            io.BytesIO(markdown.encode('utf-8')),
            as_attachment=True,
            mimetype='text/markdown',
            download_name=f"content_{content_id}.md"
        )

    else:
        return jsonify({"error": "Unsupported format"}), 400



@app.route('/api/export-test/<test_id>', methods=['GET'])
def export_test(test_id):
    """Endpoint to export test in various formats"""
    format_type = request.args.get('format', 'json')
    
    # Find test file
    test_data = None
    for filename in os.listdir(TEST_DIR):
        if filename.startswith(test_id):
            with open(os.path.join(TEST_DIR, filename), 'r') as f:
                test_data = json.load(f)
            break
    
    if not test_data:
        return jsonify({"error": "Test not found"}), 404
    
    if format_type == 'json':
        return jsonify(test_data)
    
    elif format_type == 'pdf':
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        import io
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, 
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=72)
        
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='Question',
            fontName='Helvetica-Bold',
            fontSize=12,
            spaceAfter=6
        ))
        styles.add(ParagraphStyle(
            name='Option',
            fontName='Helvetica',
            fontSize=10,
            leftIndent=20,
            spaceAfter=3
        ))
        
        story = []
        
        # Add title
        title = Paragraph(f"<b>{test_data['title']}</b>", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 0.25*inch))
        
        # Add test description if available
        if 'description' in test_data and test_data['description']:
            desc = Paragraph(test_data['description'], styles['Normal'])
            story.append(desc)
            story.append(Spacer(1, 0.25*inch))
        
        # Add questions
        for i, question in enumerate(test_data['questions']):
            # Question text
            q_text = question['text']
            
            # Make sure to handle any HTML-sensitive characters
            q_text = q_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            # Question number and text
            heading = Paragraph(f"Question {i+1}", styles['Heading2'])
            story.append(heading)
            story.append(Spacer(1, 0.1*inch))
            
            q_para = Paragraph(q_text, styles['Question'])
            story.append(q_para)
            story.append(Spacer(1, 0.1*inch))
            
            # Add options for MCQ
            if question['type'] == 'mcq':
                for j, option in enumerate(question['options']):
                    # Make sure to handle any HTML-sensitive characters
                    option_text = option.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    
                    opt = Paragraph(f"{chr(65+j)}. {option_text}", styles['Option'])
                    story.append(opt)
                
                # Add correct answer if available
                if 'correct_answer' in question:
                    correct = Paragraph(f"<b>Correct Answer: {chr(65 + question['correct_answer'])}</b>", styles['Normal'])
                    story.append(Spacer(1, 0.1*inch))
                    story.append(correct)
            
            elif question['type'] == 'short_answer':
                # For short answer questions, add a blank space for answers
                story.append(Paragraph("Answer: _______________________________", styles['Normal']))
                
                # Add correct answer if available
                if 'correct_answer' in question:
                    correct = Paragraph(f"<b>Correct Answer: {question['correct_answer']}</b>", styles['Normal'])
                    story.append(Spacer(1, 0.1*inch))
                    story.append(correct)
            
            story.append(Spacer(1, 0.2*inch))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            mimetype='application/pdf',
            download_name=f"test_{test_id}.pdf"
        )
    
    elif format_type == 'markdown':
        # Convert to markdown
        markdown = f"# {test_data['title']}\n\n"
        
        # Add description if available
        if 'description' in test_data and test_data['description']:
            markdown += f"{test_data['description']}\n\n"
        
        for i, question in enumerate(test_data['questions']):
            markdown += f"## Question {i+1}\n\n"
            markdown += f"{question['text']}\n\n"
            
            if question['type'] == 'mcq':
                for j, option in enumerate(question['options']):
                    markdown += f"{chr(65+j)}. {option}\n"
                
                # Include correct answer if available
                if 'correct_answer' in question:
                    markdown += f"\n**Correct Answer: {chr(65 + question['correct_answer'])}**\n"
            
            elif question['type'] == 'short_answer':
                markdown += "Answer: _______________________________\n"
                
                # Include correct answer if available
                if 'correct_answer' in question:
                    markdown += f"\n**Correct Answer: {question['correct_answer']}**\n"
            
            markdown += "\n"
        
        return send_file(
            io.BytesIO(markdown.encode('utf-8')),
            as_attachment=True,
            mimetype='text/markdown',
            download_name=f"test_{test_id}.md"
        )
    
    else:
        return jsonify({"error": "Unsupported format"}), 400

@app.route('/api/debug-code', methods=['POST'])
def debug_code():
    """Endpoint to debug code directly"""
    data = request.json
    code = data.get('code')
    language = data.get('language', 'python')
    
    if not code:
        return jsonify({"error": "No code provided"}), 400
    
    # Use debugging agent to debug the code
    result = debugging_agent.debug_code(code, language)
    
    return jsonify({
        "original_code": code,
        "debugged_code": result['code'],
        "issues": result['issues'],
        "explanation": result['explanation']
    })

@app.route('/api/get-expected-answer', methods=['POST'])
def get_expected_answer():
    """Endpoint to get the expected answer for a test question"""
    data = request.json
    test_id = data.get('test_id')
    question_id = data.get('question_id')
    
    if not test_id or not question_id:
        return jsonify({"error": "Both test_id and question_id are required"}), 400
    
    # Find the test file
    test_data = None
    for filename in os.listdir(TEST_DIR):
        if filename.startswith(test_id):
            with open(os.path.join(TEST_DIR, filename), 'r') as f:
                test_data = json.load(f)
            break
    
    if not test_data:
        return jsonify({"error": "Test not found"}), 404
    
    # Find the question
    question = next((q for q in test_data['questions'] if q['id'] == question_id), None)
    
    if not question:
        return jsonify({"error": "Question not found"}), 404
    
    # Get detailed explanation based on question type
    if question['type'] == 'mcq':
        explanation = theory_agent.explain_mcq_answer(question)
    elif question['type'] == 'code':
        explanation = coding_agent.explain_code_answer(question)
    elif question['type'] == 'descriptive':
        explanation = theory_agent.explain_descriptive_answer(question)
    
    return jsonify({
        "question_id": question_id,
        "question_text": question['text'],
        "correct_answer": question['answer'],
        "explanation": explanation
    })

@app.route('/api/converse/<agent_type>', methods=['POST'])
def converse_with_agent(agent_type):
    data = request.json
    user_message = data.get('message', '')
    history = data.get('history', [])
    
    if agent_type == 'theory':
        # Initialize theory agent
        theory_agent = TheoryAgent()
        response = theory_agent.converse(user_message, history)
        return jsonify({"response": response})
    
    elif agent_type == 'planner':
        # Initialize planner agent (if you have one)
        # planner_agent = PlannerAgent()
        # response = planner_agent.converse(user_message, history)
        return jsonify({"response": "Planner agent response would go here."})
    
    elif agent_type == 'test':
        # Initialize test agent (if you have one)
        # test_agent = TestAgent()
        # response = test_agent.converse(user_message, history)
        return jsonify({"response": "Test agent response would go here."})
    
    else:
        return jsonify({"error": "Unknown agent type"}), 400

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)


