// Main script for AI Tutoring System
document.addEventListener('DOMContentLoaded', function() {
  // API base URL - change this to match your Flask server
  const API_BASE_URL = 'http://localhost:5000/api';
  
  // Track generated content for reference in test creation
  let generatedContents = [];
  
  // Track conversation history
  let conversationHistory = [];
  
  // Current active agent
  let currentAgent = null;
  
  // Setup event listeners for all main actions
  setupEventListeners();
  
  // Load any previously generated content for the content reference dropdown
  loadGeneratedContents();
  
  /**
   * Set up all event listeners for buttons and interactive elements
   */
  function setupEventListeners() {
      // Theme toggle
      document.getElementById('theme-toggle').addEventListener('click', toggleTheme);
      
      // Export button
      document.getElementById('export-btn').addEventListener('click', showExportModal);
      
      // Agent selection
      setupAgentSelection();
      
      // Search functionality
      document.getElementById('search-btn').addEventListener('click', handleSearch);
      document.getElementById('search-input').addEventListener('keypress', function(e) {
          if (e.key === 'Enter') {
              handleSearch();
          }
      });
      
      // Content Generation
      document.getElementById('generate-content-btn').addEventListener('click', generateContent);
      document.getElementById('export-content-pdf').addEventListener('click', () => exportContent('pdf'));
      document.getElementById('export-content-md').addEventListener('click', () => exportContent('markdown'));
      document.getElementById('create-test-from-content').addEventListener('click', createTestFromContent);
      
      // Test Creation
      document.getElementById('generate-test-btn').addEventListener('click', generateTest);
      document.getElementById('take-test').addEventListener('click', takeTest);
      document.getElementById('submit-test-btn').addEventListener('click', submitTest);
      
      // Debug Section
      document.getElementById('debug-code-btn').addEventListener('click', debugCode);
      
      // Chat functionality
      document.getElementById('send-message-btn').addEventListener('click', sendChatMessage);
      document.getElementById('chat-input').addEventListener('keypress', function(e) {
          if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              sendChatMessage();
          }
      });
      
      // Export functionality
      document.getElementById('export-pdf-btn').addEventListener('click', () => exportConversation('pdf'));
      document.getElementById('export-text-btn').addEventListener('click', () => exportConversation('text'));
      
      // Modal functionality
      setupModalFunctionality();
      
      // Results section - view answer
      document.addEventListener('click', function(e) {
          if (e.target && e.target.classList.contains('view-answer-btn')) {
              const questionId = e.target.getAttribute('data-question-id');
              const testId = e.target.getAttribute('data-test-id');
              showExpectedAnswer(testId, questionId);
          }
      });
  }
  
  /**
   * Toggle between light and dark theme
   */
  function toggleTheme() {
      const body = document.body;
      const themeToggleIcon = document.querySelector('#theme-toggle i');
      
      if (body.classList.contains('dark-mode')) {
          body.classList.remove('dark-mode');
          themeToggleIcon.className = 'fas fa-moon';
          localStorage.setItem('theme', 'light');
      } else {
          body.classList.add('dark-mode');
          themeToggleIcon.className = 'fas fa-sun';
          localStorage.setItem('theme', 'dark');
      }
  }
  
  /**
   * Load saved theme preference
   */
  function loadThemePreference() {
      const savedTheme = localStorage.getItem('theme');
      const themeToggleIcon = document.querySelector('#theme-toggle i');
      
      if (savedTheme === 'dark') {
          document.body.classList.add('dark-mode');
          themeToggleIcon.className = 'fas fa-sun';
      }
  }
  
  // Load theme preference on startup
  loadThemePreference();
  
  /**
   * Set up agent selection functionality
   */
  function setupAgentSelection() {
      const agentItems = document.querySelectorAll('.agent-item');
      
      agentItems.forEach(item => {
          item.addEventListener('click', function() {
              const agentType = this.getAttribute('data-agent');
              
              // Remove active class from all agents
              agentItems.forEach(agent => agent.classList.remove('active'));
              
              // Add active class to selected agent
              this.classList.add('active');
              
              // Set current agent
              currentAgent = agentType;
              
              // Show appropriate section based on agent type
              showAgentSection(agentType);
          });
      });
  }
  
  /**
   * Show appropriate section based on selected agent
   */
  function showAgentSection(agentType) {
      // Hide all sections
      document.querySelectorAll('main > section').forEach(section => {
          section.classList.add('hidden-section');
          section.classList.remove('active-section');
      });
      
      // Show appropriate section based on agent type
      switch (agentType) {
          case 'planner':
              document.getElementById('content-section').classList.remove('hidden-section');
              document.getElementById('content-section').classList.add('active-section');
              break;
          case 'theory':
              showAgentDetails('Theory Agent', 'Learn concepts and theories with comprehensive explanations', 'book');
              break;
          case 'code':
              showAgentDetails('Code Agent', 'Generate and understand code examples across multiple languages', 'code');
              break;
          case 'debugging':
              document.getElementById('debug-section').classList.remove('hidden-section');
              document.getElementById('debug-section').classList.add('active-section');
              break;
          case 'query':
              showChatInterface('Query Agent');
              break;
          case 'test':
              document.getElementById('test-section').classList.remove('hidden-section');
              document.getElementById('test-section').classList.add('active-section');
              break;
          default:
              // Default to welcome section
              document.getElementById('welcome-section').classList.remove('hidden-section');
              document.getElementById('welcome-section').classList.add('active-section');
      }
  }
  
  /**
   * Show agent details section with specific agent information
   */
  function showAgentDetails(agentName, description, iconName) {
      const detailsSection = document.getElementById('agent-details-section');
      const detailsTitle = document.getElementById('agent-details-title');
      const detailsSubtitle = document.getElementById('agent-details-subtitle');
      const detailsContent = document.getElementById('agent-details-content');
      
      // Set title and subtitle
      detailsTitle.textContent = agentName;
      detailsSubtitle.textContent = description;
      
      // Create agent card content
      let content = `
          <div class="agent-card">
              <div class="agent-icon-large">
                  <i class="fas fa-${iconName}"></i>
              </div>
              <div class="agent-info">
                  <h3>${agentName}</h3>
                  <p>${description}</p>
                  <button id="start-chat-with-agent" class="primary-btn">
                      <i class="fas fa-comments"></i> Start Conversation
                  </button>
              </div>
          </div>
          <div class="agent-capabilities">
              <h3>Capabilities</h3>
      `;
      
      // Add capabilities based on agent type
      if (agentName.includes('Theory')) {
          content += `
              <div class="capability-item">
                  <div class="capability-icon">
                      <i class="fas fa-lightbulb"></i>
                  </div>
                  <div>
                      <h4>Concept Explanation</h4>
                      <p>Provides clear and detailed explanations of complex theoretical concepts.</p>
                  </div>
              </div>
              <div class="capability-item">
                  <div class="capability-icon">
                      <i class="fas fa-project-diagram"></i>
                  </div>
                  <div>
                      <h4>Relationship Mapping</h4>
                      <p>Helps you understand how different concepts relate to each other.</p>
                  </div>
              </div>
              <div class="capability-item">
                  <div class="capability-icon">
                      <i class="fas fa-history"></i>
                  </div>
                  <div>
                      <h4>Historical Context</h4>
                      <p>Provides historical background and evolution of important concepts.</p>
                  </div>
              </div>
          `;
      } else if (agentName.includes('Code')) {
          content += `
              <div class="capability-item">
                  <div class="capability-icon">
                      <i class="fas fa-code"></i>
                  </div>
                  <div>
                      <h4>Code Generation</h4>
                      <p>Creates code examples in multiple programming languages.</p>
                  </div>
              </div>
              <div class="capability-item">
                  <div class="capability-icon">
                      <i class="fas fa-comment-code"></i>
                  </div>
                  <div>
                      <h4>Code Explanation</h4>
                      <p>Explains how code works line by line with detailed comments.</p>
                  </div>
              </div>
              <div class="capability-item">
                  <div class="capability-icon">
                      <i class="fas fa-exchange-alt"></i>
                  </div>
                  <div>
                      <h4>Language Translation</h4>
                      <p>Converts code between different programming languages.</p>
                  </div>
              </div>
          `;
      }
      
      content += `</div>`;
      
      // Set content
      detailsContent.innerHTML = content;
      
      // Add event listener to start chat button
      setTimeout(() => {
          const startChatBtn = document.getElementById('start-chat-with-agent');
          if (startChatBtn) {
              startChatBtn.addEventListener('click', () => {
                  showChatInterface(agentName);
              });
          }
      }, 100);
      
      // Show the section
      detailsSection.classList.remove('hidden-section');
      detailsSection.classList.add('active-section');
  }
  
  /**
   * Show chat interface for interacting with an agent
   */
  function showChatInterface(agentName) {
      const chatSection = document.getElementById('chat-section');
      const chatAgentName = document.getElementById('chat-agent-name');
      const chatMessages = document.getElementById('chat-messages');
      
      // Set agent name
      chatAgentName.textContent = `Chat with ${agentName}`;
      
      // Clear previous messages
      chatMessages.innerHTML = '';
      
      // Add welcome message
      addChatMessage(`Hi there! I'm the ${agentName}. How can I help you today?`, 'ai');
      
      // Show chat section
      document.querySelectorAll('main > section').forEach(section => {
          section.classList.add('hidden-section');
          section.classList.remove('active-section');
      });
      
      chatSection.classList.remove('hidden-section');
      chatSection.classList.add('active-section');
      
      // Focus on input
      document.getElementById('chat-input').focus();
  }
  
  /**
   * Add a message to the chat interface
   */
  function addChatMessage(message, sender) {
      const chatMessages = document.getElementById('chat-messages');
      const messageDiv = document.createElement('div');
      
      messageDiv.className = `message ${sender}-message`;
      messageDiv.textContent = message;
      
      chatMessages.appendChild(messageDiv);
      
      // Save to conversation history
      conversationHistory.push({
          sender: sender,
          message: message,
          timestamp: new Date().toISOString()
      });
      
      // Scroll to bottom
      chatMessages.scrollTop = chatMessages.scrollHeight;
  }
  
  /**
   * Send a chat message
   */
  function sendChatMessage() {
      const chatInput = document.getElementById('chat-input');
      const message = chatInput.value.trim();
      
      if (!message) return;
      
      // Add user message to chat
      addChatMessage(message, 'user');
      
      // Clear input
      chatInput.value = '';
      
      // In a real implementation, you would send this to your backend
      // For now, we'll simulate a response
      setTimeout(() => {
          const responses = {
              'planner': "I'll help you structure your learning path. What topic would you like to explore?",
              'theory': "I can explain theoretical concepts in detail. What would you like to learn about?",
              'code': "I can generate code examples or explain code. What programming task are you working on?",
              'debugging': "I'll help you find and fix bugs in your code. What issues are you experiencing?",
              'query': "I can answer any questions you have. What would you like to know?",
              'test': "I can create tests to evaluate your knowledge. What topic should I test you on?"
          };
          
          const response = responses[currentAgent] || "How can I assist you today?";
          addChatMessage(response, 'ai');
      }, 1000);
  }
  
  /**
   * Handle search functionality
   */
  function handleSearch() {
      const searchInput = document.getElementById('search-input');
      const query = searchInput.value.trim();
      
      if (!query) return;
      
      // In a real implementation, you would send this to your backend
      // For now, we'll simulate by showing the chat interface with the query
      
      // Set current agent to query agent
      currentAgent = 'query';
      
      // Update active agent in sidebar
      document.querySelectorAll('.agent-item').forEach(item => {
          item.classList.remove('active');
          if (item.getAttribute('data-agent') === 'query') {
              item.classList.add('active');
          }
      });
      
      // Show chat interface
      showChatInterface('Query Agent');
      
      // Add the search query as a user message
      addChatMessage(query, 'user');
      
      // Simulate response
      setTimeout(() => {
          addChatMessage(`I found some information about "${query}". What specific aspects would you like to know?`, 'ai');
      }, 1000);
      
      // Clear search input
      searchInput.value = '';
  }
  
  /**
   * Show export modal
   */
  function showExportModal() {
      document.getElementById('export-modal').classList.remove('hidden');
  }
  
  /**
   * Export conversation history
   */
  function exportConversation(format) {
      if (conversationHistory.length === 0) {
          alert('No conversation to export');
          return;
      }
      
      if (format === 'pdf') {
          // Use jsPDF to generate PDF
          const { jsPDF } = window.jspdf;
          const doc = new jsPDF();
          
          let y = 20;
          doc.setFontSize(16);
          doc.text('AI Tutoring System - Conversation Export', 20, y);
          y += 10;
          
          doc.setFontSize(12);
          doc.text(`Date: ${new Date().toLocaleDateString()}`, 20, y);
          y += 10;
          
          doc.setFontSize(10);
          
          conversationHistory.forEach(msg => {
              const sender = msg.sender === 'user' ? 'You' : 'AI';
              const text = `${sender}: ${msg.message}`;
              
              // Split long text into multiple lines
              const textLines = doc.splitTextToSize(text, 170);
              
              // Check if we need a new page
              if (y + (textLines.length * 5) > 280) {
                  doc.addPage();
                  y = 20;
              }
              
              doc.text(textLines, 20, y);
              y += (textLines.length * 6) + 5;
          });
          
          // Save the PDF
          doc.save('conversation-export.pdf');
      } else if (format === 'text') {
          // Generate text file
          let text = 'AI Tutoring System - Conversation Export\n';
          text += `Date: ${new Date().toLocaleDateString()}\n\n`;
          
          conversationHistory.forEach(msg => {
              const sender = msg.sender === 'user' ? 'You' : 'AI';
              text += `${sender}: ${msg.message}\n\n`;
          });
          
          // Create download link
          const blob = new Blob([text], { type: 'text/plain' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = 'conversation-export.txt';
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
      }
      
      // Hide modal
      document.getElementById('export-modal').classList.add('hidden');
  }
  
  /**
   * Set up the modal functionality
   */
  function setupModalFunctionality() {
      const modals = document.querySelectorAll('.modal');
      const closeButtons = document.querySelectorAll('.close-modal, .close-modal-btn');
      
      closeButtons.forEach(button => {
          button.addEventListener('click', function() {
              modals.forEach(modal => {
                  modal.classList.add('hidden');
              });
          });
      });
      
      // Close modal when clicking outside
      modals.forEach(modal => {
          modal.addEventListener('click', function(e) {
              if (e.target === this) {
                  this.classList.add('hidden');
              }
          });
      });
  }
  
  /**
   * Generate educational content based on user query
   */
  async function generateContent() {
      const query = document.getElementById('content-query').value.trim();
      
      if (!query) {
          alert('Please enter a topic or question');
          return;
      }
      
      // Show loading state
      document.getElementById('content-loading').classList.remove('hidden');
      document.getElementById('content-result').classList.add('hidden');
      
      try {
          const response = await fetch(`${API_BASE_URL}/generate-content`, {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json'
              },
              body: JSON.stringify({ query })
          });
          
          const data = await response.json();
          
          if (response.ok) {
              displayGeneratedContent(data);
              // Save the content reference for later use in test creation
              saveContentReference(data);
          } else {
              alert(`Error: ${data.error || 'Failed to generate content'}`);
          }
      } catch (error) {
          console.error('Content generation error:', error);
          alert('Failed to connect to the server. Please try again later.');
      } finally {
          document.getElementById('content-loading').classList.add('hidden');
      }
  }
  
  /**
   * Display the generated content in the UI
   */
  function displayGeneratedContent(data) {
      const contentResult = document.getElementById('content-result');
      const contentTitle = document.getElementById('content-title');
      const contentSections = document.getElementById('content-sections');
      
      // Set title
      contentTitle.textContent = data.content.title;
      
      // Clear existing sections
      contentSections.innerHTML = '';
      
      // Add each section
      data.content.sections.forEach(section => {
          const sectionDiv = document.createElement('div');
          sectionDiv.className = 'content-section';
          
          const sectionTitle = document.createElement('h4');
          sectionTitle.textContent = section.topic;
          sectionDiv.appendChild(sectionTitle);
          
          const sectionContent = document.createElement('div');
          
          if (section.type === 'code') {
              // For code sections, use syntax highlighting
              const pre = document.createElement('pre');
              const code = document.createElement('code');
              code.className = 'language-python'; // Default to python
              code.textContent = section.content;
              pre.appendChild(code);
              sectionContent.appendChild(pre);
              
              // Initialize syntax highlighting for this element
              hljs.highlightElement(code);
          } else {
              // For theory sections, render markdown
              const converter = new showdown.Converter();
              sectionContent.innerHTML = converter.makeHtml(section.content);
          }
          
          sectionDiv.appendChild(sectionContent);
          contentSections.appendChild(sectionDiv);
      });
      
      // Show the result
      contentResult.classList.remove('hidden');
  }
  
  /**
   * Save content reference for later use in test creation
   */
  function saveContentReference(data) {
      // Store the content ID and title for later reference
      const contentRef = {
          id: data.content_id,
          title: data.content.title
      };
      
      // Add to our tracking array
      generatedContents.push(contentRef);
      
      // Update the content reference dropdown in the test section
      updateContentReferenceDropdown();
      
      // Save to localStorage for persistence
      localStorage.setItem('generatedContents', JSON.stringify(generatedContents));
  }
  
  /**
   * Load previously generated contents from localStorage
   */
  function loadGeneratedContents() {
      const savedContents = localStorage.getItem('generatedContents');
      if (savedContents) {
          generatedContents = JSON.parse(savedContents);
          // Update dropdown
          updateContentReferenceDropdown();
      }
  }
  
  /**
   * Update the content reference dropdown with available content
   */
  function updateContentReferenceDropdown() {
      const dropdown = document.getElementById('content-reference');
      
      // Keep the first option (None)
      const firstOption = dropdown.options[0];
      dropdown.innerHTML = '';
      dropdown.appendChild(firstOption);
      
      // Add each content as an option
      generatedContents.forEach(content => {
          const option = document.createElement('option');
          option.value = content.id;
          option.textContent = content.title;
          dropdown.appendChild(option);
      });
  }
  
  /**
   * Export content in specified format
   */
  async function exportContent(format) {
      // Get the content ID from the currently displayed content
      const contentTitle = document.getElementById('content-title').textContent;
      const contentRef = generatedContents.find(c => c.title === contentTitle);
      
      if (!contentRef) {
          alert('Content reference not found');
          return;
      }
      
      // Create a URL for the export endpoint
      const url = `${API_BASE_URL}/export-content/${contentRef.id}?format=${format}`;
      
      // Either open in new tab or trigger download
      if (format === 'pdf') {
          window.open(url, '_blank');
      } else {
          // For other formats, trigger a download
          const a = document.createElement('a');
          a.href = url;
          a.download = `content_${contentRef.id}.${format === 'markdown' ? 'md' : format}`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
      }
  }
  
  /**
   * Create a test from currently displayed content
   */
  function createTestFromContent() {
      // Get the content ID from the currently displayed content
      const contentTitle = document.getElementById('content-title').textContent;
      const contentRef = generatedContents.find(c => c.title === contentTitle);
      
      if (!contentRef) {
          alert('Content reference not found');
          return;
      }
      
      // Switch to test section
      showAgentSection('test');
      
      // Set the content reference in the dropdown
      document.getElementById('content-reference').value = contentRef.id;
      
      // Set the test topic to match the content title
      document.getElementById('test-topic').value = contentTitle;
  }
  
  /**
   * Generate a test based on user input
   */
  async function generateTest() {
      const topic = document.getElementById('test-topic').value.trim();
      const difficulty = document.getElementById('test-difficulty').value;
      const numQuestions = document.getElementById('test-questions').value;
      const contentId = document.getElementById('content-reference').value;
      
      if (!topic && !contentId) {
          alert('Please enter a topic or select a content reference');
          return;
      }
      
      // Show loading state
      document.getElementById('test-loading').classList.remove('hidden');
      document.getElementById('test-result').classList.add('hidden');
      
      try {
          const response = await fetch(`${API_BASE_URL}/generate-test`, {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                  topic,
                  content_id: contentId,
                  difficulty,
                  num_questions: parseInt(numQuestions)
              })
          });
          
          const data = await response.json();
          
          if (response.ok) {
              displayGeneratedTest(data);
          } else {
              alert(`Error: ${data.error || 'Failed to generate test'}`);
          }
      } catch (error) {
          console.error('Test generation error:', error);
          alert('Failed to connect to the server. Please try again later.');
      } finally {
          document.getElementById('test-loading').classList.add('hidden');
      }
  }
  
  /**
   * Display the generated test in the UI
   */
  function displayGeneratedTest(data) {
      const testResult = document.getElementById('test-result');
      const testTitle = document.getElementById('test-title');
      const testPreview = document.getElementById('test-preview');
      
      // Store the test ID for later use
      testResult.setAttribute('data-test-id', data.test_id);
      
      // Set title
      testTitle.textContent = data.test.title;
      
      // Clear preview
      testPreview.innerHTML = '';
      
      // Add a preview of each question
      data.test.questions.forEach((question, index) => {
          const questionDiv = document.createElement('div');
          questionDiv.className = 'test-question-preview';
          
          const questionNumber = document.createElement('span');
          questionNumber.className = 'question-number';
          questionNumber.textContent = `Q${index + 1}.`;
          
          const questionText = document.createElement('span');
          questionText.className = 'question-text';
          questionText.textContent = question.text.substring(0, 100) + (question.text.length > 100 ? '...' : '');
          
          const questionType = document.createElement('span');
          questionType.className = 'question-type';
          questionType.textContent = getQuestionTypeLabel(question.type);
          
          questionDiv.appendChild(questionNumber);
          questionDiv.appendChild(questionText);
          questionDiv.appendChild(questionType);
          
          testPreview.appendChild(questionDiv);
      });
      
      // Show the result
      testResult.classList.remove('hidden');
  }
  
  /**
   * Convert question type to readable label
   */
  function getQuestionTypeLabel(type) {
      switch (type) {
          case 'mcq': return 'Multiple Choice';
          case 'code': return 'Coding';
          case 'descriptive': return 'Descriptive';
          default: return type;
      }
  }
  
  /**
   * Start taking the test
   */
  function takeTest() {
      // Get test ID
      const testResult = document.getElementById('test-result');
      const testId = testResult.getAttribute('data-test-id');
      
      if (!testId) {
          alert('Test ID not found');
          return;
      }
      
      // Fetch test details
      fetch(`${API_BASE_URL}/export-test/${testId}`)
          .then(response => response.json())
          .then(data => {
              if (data.error) {
                  throw new Error(data.error);
              }
              
              // Set up the test taking interface
              setupTestTakingInterface(testId, data);
              
              // Hide test section and show test taking section
              document.getElementById('test-section').classList.add('hidden-section');
              document.getElementById('test-taking-section').classList.remove('hidden-section');
              
              // Set test title
              document.getElementById('active-test-title').textContent = data.title;
          })
          .catch(error => {
              console.error('Error setting up test:', error);
              alert(`Error: ${error.message || 'Failed to start test'}`);
          });
  }
  
  /**
   * Set up the test taking interface with questions
   */
  function setupTestTakingInterface(testId, testData) {
      const questionsContainer = document.getElementById('test-questions-container');
      questionsContainer.innerHTML = '';
      
      // Set test ID for later submission
      questionsContainer.setAttribute('data-test-id', testId);
      
      // Create each question
      testData.questions.forEach((question, index) => {
          const questionDiv = document.createElement('div');
          questionDiv.className = 'test-question';
          questionDiv.setAttribute('data-question-id', question.id);
          
          // Question header
          const header = document.createElement('div');
          header.className = 'question-header';
          
          const questionNumber = document.createElement('span');
          questionNumber.className = 'question-number';
          questionNumber.textContent = `Question ${index + 1}`;
          
          const questionType = document.createElement('span');
          questionType.className = 'question-badge';
          questionType.textContent = getQuestionTypeLabel(question.type);
          
          header.appendChild(questionNumber);
          header.appendChild(questionType);
          questionDiv.appendChild(header);
          
          // Question text
          const textDiv = document.createElement('div');
          textDiv.className = 'question-text';
          
          // Use markdown for question text
          const converter = new showdown.Converter();
          textDiv.innerHTML = converter.makeHtml(question.text);
          
          questionDiv.appendChild(textDiv);
          
          // Answer section depends on question type
          const answerDiv = document.createElement('div');
          answerDiv.className = 'question-answer';
          
          if (question.type === 'mcq') {
              const optionsDiv = document.createElement('div');
              optionsDiv.className = 'question-options';
              
              question.options.forEach((option, optIndex) => {
                  const optionLabel = document.createElement('label');
                  optionLabel.className = 'option-label';
                  
                  const radio = document.createElement('input');
                  radio.type = 'radio';
                  radio.name = `question_${question.id}`;
                  radio.value = option;
                  
                  const optionText = document.createElement('span');
                  optionText.textContent = option;
                  
                  optionLabel.appendChild(radio);
                  optionLabel.appendChild(optionText);
                  optionsDiv.appendChild(optionLabel);
              });
              
              answerDiv.appendChild(optionsDiv);
          } else if (question.type === 'code') {
              const textarea = document.createElement('textarea');
              textarea.className = 'code-editor';
              textarea.placeholder = 'Write your code solution here...';
              answerDiv.appendChild(textarea);
          } else { // descriptive
              const textarea = document.createElement('textarea');
              textarea.className = 'descriptive-answer';
              textarea.placeholder = 'Write your answer here...';
              answerDiv.appendChild(textarea);
          }
          
          questionDiv.appendChild(answerDiv);
          questionsContainer.appendChild(questionDiv);
      });
  }
  
  /**
   * Submit test answers for evaluation
   */
  async function submitTest() {
      const questionsContainer = document.getElementById('test-questions-container');
      const testId = questionsContainer.getAttribute('data-test-id');
      
      if (!testId) {
          alert('Test ID not found');
          return;
      }
      
      // Collect answers for each question
      const answers = [];
      const questionDivs = questionsContainer.querySelectorAll('.test-question');
      
      questionDivs.forEach(div => {
          const questionId = div.getAttribute('data-question-id');
          let answer = null;
          
          // Check if it's MCQ (radio buttons)
          const selectedRadio = div.querySelector('input[type="radio"]:checked');
          if (selectedRadio) {
              answer = selectedRadio.value;
          } else {
              // Check if it's a textarea (code or descriptive)
              const textarea = div.querySelector('textarea');
              if (textarea) {
                  answer = textarea.value.trim();
              }
          }
          
          if (answer) {
              answers.push({
                  question_id: questionId,
                  answer: answer
              });
          }
      });
      
      // Submit answers to API
      try {
          const response = await fetch(`${API_BASE_URL}/submit-test`, {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                  test_id: testId,
                  answers: answers
              })
          });
          
          const data = await response.json();
          
          if (response.ok) {
              // Display results
              displayTestResults(data);
              
              // Switch to results section
              document.getElementById('test-taking-section').classList.add('hidden-section');
              document.getElementById('results-section').classList.remove('hidden-section');
              document.getElementById('results-section').classList.add('active-section');
          } else {
              alert(`Error: ${data.error || 'Failed to submit test'}`);
          }
      } catch (error) {
          console.error('Test submission error:', error);
          alert('Failed to connect to the server. Please try again later.');
      }
  }
  
  /**
   * Display test results in the results section
   */
  function displayTestResults(data) {
      const noResults = document.getElementById('no-results');
      const testResults = document.getElementById('test-results');
      const resultTestTitle = document.getElementById('result-test-title');
      const resultPercentage = document.getElementById('result-percentage');
      const resultTotalScore = document.getElementById('result-total-score');
      const resultMaxScore = document.getElementById('result-max-score');
      const resultsTableBody = document.getElementById('results-table-body');
      
      // Hide no results message
      noResults.classList.add('hidden');
      
      // Set basic result data
      resultTestTitle.textContent = `Test Results: ${data.results.test_id}`;
      resultPercentage.textContent = `${Math.round(data.results.percentage)}%`;
      resultTotalScore.textContent = data.results.total_score;
      resultMaxScore.textContent = data.results.max_score;
      
      // Clear previous results
      resultsTableBody.innerHTML = '';
      
      // Add each question result
      data.results.questions_results.forEach(result => {
          const row = document.createElement('tr');
          
          // Question number
          const numCell = document.createElement('td');
          numCell.textContent = result.question_number;
          row.appendChild(numCell);
          
          // Evaluation status
          const evalCell = document.createElement('td');
          const evalStatus = document.createElement('span');
          evalStatus.className = `status-badge ${result.evaluation}`;
          evalStatus.textContent = formatEvaluationStatus(result.evaluation);
          evalCell.appendChild(evalStatus);
          row.appendChild(evalCell);
          
          // Feedback
          const feedbackCell = document.createElement('td');
          feedbackCell.textContent = result.feedback || 'No feedback provided';
          row.appendChild(feedbackCell);
          
          // Action button
          const actionCell = document.createElement('td');
          const viewButton = document.createElement('button');
          viewButton.className = 'view-answer-btn secondary-btn';
          viewButton.textContent = 'View Answer';
          viewButton.setAttribute('data-test-id', data.results.test_id);
          viewButton.setAttribute('data-question-id', result.question_id);
          actionCell.appendChild(viewButton);
          row.appendChild(actionCell);
          
          resultsTableBody.appendChild(row);
      });
      
      // Show results section
      testResults.classList.remove('hidden');
  }
  
  /**
   * Format evaluation status for display
   */
  function formatEvaluationStatus(status) {
      switch (status) {
          case 'correct': return 'Correct';
          case 'wrong': return 'Incorrect';
          case 'partially_correct': return 'Partially Correct';
          case 'not_answered': return 'Not Answered';
          default: return status;
      }
  }
  
  /**
   * Show expected answer for a question
   */
  async function showExpectedAnswer(testId, questionId) {
      try {
          const response = await fetch(`${API_BASE_URL}/get-expected-answer`, {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                  test_id: testId,
                  question_id: questionId
              })
          });
          
          const data = await response.json();
          
          if (response.ok) {
              // Populate modal
              document.getElementById('modal-question-text').textContent = data.question_text;
              
              // Convert markdown for answer and explanation
              const converter = new showdown.Converter();
              
              const answerText = document.getElementById('modal-answer-text');
              answerText.innerHTML = converter.makeHtml(data.correct_answer);
              
              const explanationText = document.getElementById('modal-explanation-text');
              explanationText.innerHTML = converter.makeHtml(data.explanation);
              
              // Show modal
              document.getElementById('answer-modal').classList.remove('hidden');
              
              // Handle code highlighting if present
              document.querySelectorAll('#modal-answer-text pre code').forEach(block => {
                  hljs.highlightElement(block);
              });
          } else {
              alert(`Error: ${data.error || 'Failed to get answer details'}`);
          }
      } catch (error) {
          console.error('Get answer error:', error);
          alert('Failed to connect to the server. Please try again later.');
      }
  }
  
  /**
   * Debug code submitted by the user
   */
  async function debugCode() {
      const code = document.getElementById('code-input').value.trim();
      const language = document.getElementById('code-language').value;
      
      if (!code) {
          alert('Please enter code to debug');
          return;
      }
      
      // Show loading
      document.getElementById('debug-loading').classList.remove('hidden');
      document.getElementById('debug-result').classList.add('hidden');
      
      try {
          const response = await fetch(`${API_BASE_URL}/debug-code`, {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                  code,
                  language
              })
          });
          
          const data = await response.json();
          
          if (response.ok) {
              displayDebugResults(data, language);
          } else {
              alert(`Error: ${data.error || 'Failed to debug code'}`);
          }
      } catch (error) {
          console.error('Debug error:', error);
          alert('Failed to connect to the server. Please try again later.');
      } finally {
          document.getElementById('debug-loading').classList.add('hidden');
      }
  }
  
  /**
   * Display debugging results
   */
  function displayDebugResults(data, language) {
      const debugResult = document.getElementById('debug-result');
      const issuesList = document.getElementById('debug-issues-list');
      const originalCode = document.getElementById('original-code');
      const debuggedCode = document.getElementById('debugged-code');
      const explanationText = document.getElementById('debug-explanation-text');
      
      // Clear previous issues
      issuesList.innerHTML = '';
      
      // Add each issue
      data.issues.forEach(issue => {
          const li = document.createElement('li');
          li.textContent = issue;
          issuesList.appendChild(li);
      });
      
      // Set original and debugged code with syntax highlighting
      originalCode.className = `language-${language}`;
      originalCode.textContent = data.original_code;
      
      debuggedCode.className = `language-${language}`;
      debuggedCode.textContent = data.debugged_code;
      
      // Set explanation
      const converter = new showdown.Converter();
      explanationText.innerHTML = converter.makeHtml(data.explanation);
      
      // Apply syntax highlighting
      hljs.highlightElement(originalCode);
      hljs.highlightElement(debuggedCode);
      
      // Show result
      debugResult.classList.remove('hidden');
  }
});