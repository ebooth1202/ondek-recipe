// frontend/src/pages/AIChat.jsx - Updated with recipe list pagination
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

const AIChat = () => {
  const { isAuthenticated, user, apiBaseUrl } = useAuth();
  const navigate = useNavigate();
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const fileInputRef = useRef(null);

  // State management
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isUploadingFile, setIsUploadingFile] = useState(false);
  const [aiStatus, setAiStatus] = useState(null);
  const [error, setError] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);

  // Authentication check
  useEffect(() => {
    if (!isAuthenticated()) {
      navigate('/login');
    }
  }, [isAuthenticated, navigate]);

  // Check AI service status on mount
  useEffect(() => {
    checkAiStatus();
  }, []);

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  const checkAiStatus = async () => {
    try {
      const response = await axios.get(`${apiBaseUrl}/ai/status`);
      setAiStatus(response.data);

      if (!response.data.ai_configured) {
        setError('AI service is not configured. Please contact the administrator.');
      }
    } catch (error) {
      console.error('Error checking AI status:', error);
      setError('Unable to connect to AI service.');
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // File handling functions
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      setSelectedFile(files[0]);
    }
  };

  const validateFile = (file) => {
    const maxSize = 10 * 1024 * 1024; // 10MB
    const allowedTypes = [
      'application/pdf',
      'image/jpeg',
      'image/jpg',
      'image/png',
      'image/bmp',
      'image/tiff',
      'text/plain',
      'text/csv',
      'text/markdown'
    ];

    if (file.size > maxSize) {
      return 'File size must be less than 10MB';
    }

    const fileExtension = file.name.toLowerCase().split('.').pop();
    const allowedExtensions = ['pdf', 'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'txt', 'csv', 'md'];

    if (!allowedExtensions.includes(fileExtension) && !allowedTypes.includes(file.type)) {
      return 'Unsupported file type. Please upload PDF, images (JPG, PNG, etc.), or text files.';
    }

    return null;
  };

  const uploadFile = async () => {
    if (!selectedFile) return;

    const validationError = validateFile(selectedFile);
    if (validationError) {
      alert(validationError);
      setSelectedFile(null);
      return;
    }

    try {
      setIsUploadingFile(true);

      // Add user message showing file upload
      const fileMessage = {
        id: Date.now(),
        type: 'user',
        content: `📎 Uploaded file: ${selectedFile.name} (${(selectedFile.size / 1024 / 1024).toFixed(2)} MB)`,
        timestamp: new Date(),
        actionButtons: [],
        isFile: true,
        fileName: selectedFile.name
      };
      setMessages(prev => [...prev, fileMessage]);

      // Create form data
      const formData = new FormData();
      formData.append('file', selectedFile);

      // Upload and parse file
      const response = await axios.post(`${apiBaseUrl}/ai/upload-recipe-file`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // Generate AI response based on the parsing result
      let aiResponseContent = '';
      let actionButtons = [];

      if (response.data.success) {
        if (response.data.temp_id && response.data.recipe_data) {
          // Successfully parsed recipe
          const recipeName = response.data.recipe_data.recipe_name || 'Unknown Recipe';
          const ingredientCount = response.data.recipe_data.ingredients?.length || 0;
          const instructionCount = response.data.recipe_data.instructions?.length || 0;

          aiResponseContent = `🎉 Excellent! I successfully extracted a recipe from your file "${selectedFile.name}"!

**Recipe Found:** ${recipeName}
- **Ingredients:** ${ingredientCount} items
- **Instructions:** ${instructionCount} steps
- **Serves:** ${response.data.recipe_data.serving_size || 'Not specified'}
- **Category:** ${(response.data.recipe_data.genre || 'Not specified').charAt(0).toUpperCase() + (response.data.recipe_data.genre || 'Not specified').slice(1)}

The recipe data has been prepared and is ready to be added to your collection! Click the button below to review and save it to your recipe database.`;

          actionButtons = [{
            type: "action_button",
            text: `Add Recipe from ${selectedFile.name}`,
            action: "create_recipe_from_file",
            url: `/add-recipe?temp_id=${response.data.temp_id}`
          }];

        } else {
          // File processed but no recipe found
          aiResponseContent = `I processed your file "${selectedFile.name}" but couldn't extract a complete recipe from it.

${response.data.parsed_content ? `Here's what I found:\n${response.data.parsed_content}` : ''}

You can try:
- Uploading a clearer image if it was a photo
- Providing a file with more structured recipe information  
- Manually entering the recipe information using the Add Recipe form`;

          actionButtons = [{
            type: "action_button",
            text: "Add Recipe Manually",
            action: "create_recipe",
            url: "/add-recipe"
          }];
        }
      } else {
        // Error processing file
        aiResponseContent = `I encountered an issue processing your file "${selectedFile.name}": ${response.data.error}

Please try:
- Uploading a different file format (PDF, JPG, PNG, TXT)
- Ensuring the file contains clear, readable recipe information
- Using the manual recipe entry form instead`;

        actionButtons = [{
          type: "action_button",
          text: "Add Recipe Manually",
          action: "create_recipe",
          url: "/add-recipe"
        }];
      }

      // Add AI response to chat
      const aiMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: aiResponseContent,
        timestamp: new Date(),
        actionButtons: actionButtons
      };

      setMessages(prev => [...prev, aiMessage]);

    } catch (error) {
      console.error('Error uploading file:', error);

      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: `Sorry, I encountered an error while processing your file "${selectedFile.name}". Please try again or contact support if the issue persists.`,
        timestamp: new Date(),
        actionButtons: []
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsUploadingFile(false);
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const clearSelectedFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Function to parse action buttons from AI response
  const parseActionButtons = (text) => {
    const actionButtonRegex = /\[ACTION_BUTTON:({.*?})\]/g;
    const buttons = [];
    let match;

    while ((match = actionButtonRegex.exec(text)) !== null) {
      try {
        const buttonData = JSON.parse(match[1]);
        buttons.push(buttonData);
      } catch (e) {
        console.error('Error parsing action button:', e);
      }
    }

    return buttons;
  };

  // Function to remove action button markers from text
  const cleanResponseText = (text) => {
    return text.replace(/\[ACTION_BUTTON:({.*?})\]/g, '').trim();
  };

  // NEW: Function to handle "Show All" action specifically
  const handleShowAllRecipes = async (button) => {
    if (!button.metadata || !button.metadata.temp_id) {
      console.error('Missing temp_id in show all button metadata');
      return;
    }

    try {
      setIsLoading(true);

      // Determine action type based on button action
      const actionType = button.action === 'show_all_external_recipes' ? 'show_all_external_recipes' : 'show_all_recipes';
      const isExternal = button.action === 'show_all_external_recipes';

      // Add a user message indicating the action
      const actionMessage = {
        id: Date.now(),
        type: 'user',
        content: `📋 Show all ${button.metadata.total_count} ${isExternal ? 'external ' : ''}recipes`,
        timestamp: new Date(),
        actionButtons: [],
        isAction: true
      };
      setMessages(prev => [...prev, actionMessage]);

      // Send request to backend with action type and metadata
      const conversationHistory = messages.slice(-10).map(msg => ({
        role: msg.type === 'user' ? 'user' : 'assistant',
        content: msg.content
      }));

      const response = await axios.post(`${apiBaseUrl}/ai/chat`, {
        message: '',  // Empty message since this is an action
        conversation_history: conversationHistory,
        action_type: actionType,
        action_metadata: {
          temp_id: button.metadata.temp_id
        }
      });

      // Parse the response and add to messages
      const rawResponse = response.data.response;
      const actionButtons = parseActionButtons(rawResponse);
      const cleanedResponse = cleanResponseText(rawResponse);

      const aiMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: cleanedResponse,
        timestamp: new Date(response.data.timestamp),
        actionButtons: actionButtons
      };

      setMessages(prev => [...prev, aiMessage]);

    } catch (error) {
      console.error('Error handling show all recipes:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: 'Sorry, I encountered an error while retrieving all recipes. Please try again.',
        timestamp: new Date(),
        actionButtons: []
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Function to handle action button clicks
  const handleActionButtonClick = (button) => {
    // NEW: Handle both "show all recipes" actions specially
    if (button.action === 'show_all_recipes' || button.action === 'show_all_external_recipes') {
      handleShowAllRecipes(button);
      return;
    }

    // Handle other action types (existing logic)
    if (button.url) {
      if (button.url.startsWith('http')) {
        // External URL
        window.open(button.url, '_blank');
      } else {
        // Internal route
        navigate(button.url);
      }
    }
  };

  // Component to render action buttons
  const ActionButtons = ({ buttons }) => {
    if (!buttons || buttons.length === 0) return null;

    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem',
        marginTop: '1rem'
      }}>
        {buttons.map((button, index) => {
          // Different styling for "Show All" buttons
          const isShowAllButton = button.action === 'show_all_recipes' || button.action === 'show_all_external_recipes';

          return (
            <button
              key={index}
              onClick={() => handleActionButtonClick(button)}
              style={{
                padding: '10px 16px',
                backgroundColor: isShowAllButton ? '#28a745' : '#003366',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500',
                transition: 'all 0.3s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem'
              }}
              onMouseEnter={(e) => {
                e.target.style.backgroundColor = isShowAllButton ? '#218838' : '#0066cc';
                e.target.style.transform = 'translateY(-1px)';
              }}
              onMouseLeave={(e) => {
                e.target.style.backgroundColor = isShowAllButton ? '#28a745' : '#003366';
                e.target.style.transform = 'translateY(0)';
              }}
            >
              <span>{isShowAllButton ? '📋' : '🍳'}</span>
              {button.text || 'Action'}
            </button>
          );
        })}
      </div>
    );
  };

  const sendMessage = async () => {
    if ((!inputMessage.trim() && !selectedFile) || isLoading) return;

    // If there's a file selected, upload it instead
    if (selectedFile) {
      await uploadFile();
      return;
    }

    const userMessage = inputMessage.trim();
    setInputMessage('');

    // Add user message to chat
    const newUserMessage = {
      id: Date.now(),
      type: 'user',
      content: userMessage,
      timestamp: new Date(),
      actionButtons: []
    };

    setMessages(prev => [...prev, newUserMessage]);
    setIsLoading(true);
    setError('');

    try {
      // Prepare conversation history (last 10 messages)
      const conversationHistory = messages.slice(-10).map(msg => ({
        role: msg.type === 'user' ? 'user' : 'assistant',
        content: msg.content
      }));

      const response = await axios.post(`${apiBaseUrl}/ai/chat`, {
        message: userMessage,
        conversation_history: conversationHistory
      });

      // Parse action buttons from response
      const rawResponse = response.data.response;
      const actionButtons = parseActionButtons(rawResponse);
      const cleanedResponse = cleanResponseText(rawResponse);

      // Add AI response to chat
      const aiMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: cleanedResponse,
        timestamp: new Date(response.data.timestamp),
        actionButtons: actionButtons
      };

      setMessages(prev => [...prev, aiMessage]);

    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: 'Sorry, I encountered an error while processing your request. Please try again.',
        timestamp: new Date(),
        actionButtons: []
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setError('');
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Quick action buttons for common queries
  const quickActions = [
    { label: "🍽️ Show me dinner recipes", query: "What dinner recipes do you have?" },
    { label: "⚡ Quick meals under 30 minutes", query: "Show me recipes that take less than 30 minutes" },
    { label: "🥗 Healthy options", query: "What are some healthy recipe options?" },
    { label: "🍰 Dessert recipes", query: "Show me dessert recipes" },
    { label: "🥘 Popular recipes", query: "What are the most popular recipes?" }
  ];

  const handleQuickAction = (query) => {
    setInputMessage(query);
    // Auto-send the message
    setTimeout(() => {
      sendMessage();
    }, 100);
  };

  // Styles matching the app theme
  const containerStyle = {
    padding: '1.25rem',
    backgroundColor: '#f0f8ff',
    minHeight: 'calc(100vh - 80px)',
    display: 'flex',
    flexDirection: 'column'
  };

  const headerStyle = {
    background: 'white',
    border: '2px solid #003366',
    borderRadius: '15px',
    padding: '1.25rem',
    marginBottom: '1.25rem',
    boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)',
    textAlign: 'center'
  };

  const titleStyle = {
    color: '#003366',
    fontSize: '1.8rem',
    marginBottom: '0.5rem'
  };

  const chatContainerStyle = {
    background: 'white',
    border: '2px solid #003366',
    borderRadius: '15px',
    padding: '1.5rem',
    boxShadow: '0 4px 12px rgba(0, 51, 102, 0.1)',
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    minHeight: '500px',
    maxHeight: '750px'
  };

  const messagesAreaStyle = {
    flex: 1,
    overflowY: 'auto',
    paddingRight: '0.5rem',
    marginBottom: '1rem'
  };

  const messageStyle = (type) => ({
    marginBottom: '1rem',
    display: 'flex',
    justifyContent: type === 'user' ? 'flex-end' : 'flex-start'
  });

  const messageBubbleStyle = (type) => ({
    maxWidth: '70%',
    padding: '1rem',
    borderRadius: '15px',
    backgroundColor: type === 'user' ? '#003366' : type === 'error' ? '#f8d7da' : '#f0f8ff',
    color: type === 'user' ? 'white' : type === 'error' ? '#721c24' : '#333',
    border: type === 'user' ? 'none' : type === 'error' ? '1px solid #f5c6cb' : '1px solid #003366'
  });

  const inputAreaStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem'
  };

  const inputRowStyle = {
    display: 'flex',
    gap: '1rem',
    alignItems: 'flex-end'
  };

  const inputStyle = {
    flex: 1,
    padding: '12px',
    border: '2px solid #003366',
    borderRadius: '10px',
    fontSize: '16px',
    resize: 'none',
    minHeight: '50px',
    maxHeight: '120px'
  };

  const buttonStyle = {
    padding: '12px 24px',
    backgroundColor: '#003366',
    color: 'white',
    border: 'none',
    borderRadius: '10px',
    cursor: 'pointer',
    fontSize: '16px',
    fontWeight: '500',
    minHeight: '50px'
  };

  const selectedFileStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    padding: '0.5rem',
    backgroundColor: '#e6f0ff',
    border: '1px solid #003366',
    borderRadius: '8px',
    fontSize: '12px',
    marginBottom: '0.5rem'
  };

  const quickActionsStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '0.3rem',
    marginBottom: '0.5rem'
  };

  const quickActionButtonStyle = {
    padding: '5px 8px',
    backgroundColor: '#f0f8ff',
    color: '#003366',
    border: '1px solid #003366',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '12px',
    textAlign: 'left',
    transition: 'all 0.3s ease'
  };

  // Render guard
  if (!isAuthenticated()) {
    return null;
  }

  return (
    <div style={containerStyle}>
      <div style={{ maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
        {/* Header */}
        <div style={headerStyle}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '1rem',
            marginBottom: '0.5rem',
            flexWrap: 'wrap'
          }}>
            <h1 style={titleStyle}>🤖 Rupert the Recipe Assistant</h1>
            {/* AI Status */}
            {aiStatus && (
              <div style={{
                display: 'inline-block',
                padding: '4px 10px',
                backgroundColor: aiStatus.ai_configured ? '#d4edda' : '#f8d7da',
                color: aiStatus.ai_configured ? '#155724' : '#721c24',
                borderRadius: '6px',
                fontSize: '12px',
                border: `1px solid ${aiStatus.ai_configured ? '#c3e6cb' : '#f5c6cb'}`,
                whiteSpace: 'nowrap',
                flexShrink: 0
              }}>
                {aiStatus.ai_configured ? '✅ Rupert is Ready' : '❌ Rupert is Not Available'}
              </div>
            )}
          </div>

          <p style={{ fontSize: '0.95rem', color: '#666', marginBottom: '0.5rem' }}>
            Hello <strong style={{ color: '#003366' }}>{user?.username}</strong>!
            I'm Rupert, your personal recipe assistant. Ask me about recipes, cooking tips, or upload recipe files!
          </p>

          {/* Quick Actions */}
          <div style={{ marginTop: '0.75rem' }}>
            <h3 style={{ color: '#003366', marginBottom: '0.5rem', fontSize: '0.95rem' }}>
              💡 Quick Actions
            </h3>
            <div style={quickActionsStyle}>
              {quickActions.map((action, index) => (
                <button
                  key={index}
                  onClick={() => handleQuickAction(action.query)}
                  style={quickActionButtonStyle}
                  onMouseEnter={(e) => {
                    e.target.style.backgroundColor = '#003366';
                    e.target.style.color = 'white';
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.backgroundColor = '#f0f8ff';
                    e.target.style.color = '#003366';
                  }}
                >
                  {action.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div style={{
            background: '#f8d7da',
            color: '#721c24',
            padding: '1rem',
            borderRadius: '8px',
            marginBottom: '1rem',
            border: '1px solid #f5c6cb',
            textAlign: 'center'
          }}>
            {error}
          </div>
        )}

        {/* Chat Container */}
        <div
          style={chatContainerStyle}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {/* Chat Header */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '1rem',
            paddingBottom: '1rem',
            borderBottom: '1px solid #f0f8ff'
          }}>
            <h3 style={{ color: '#003366', margin: 0 }}>
              💬 Chat with Rupert
            </h3>
            {messages.length > 0 && (
              <button
                onClick={clearChat}
                style={{
                  padding: '6px 12px',
                  backgroundColor: '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                🗑️ Clear Chat
              </button>
            )}
          </div>

          {/* Messages Area */}
          <div style={messagesAreaStyle}>
            {messages.length === 0 ? (
              <div style={{
                textAlign: 'center',
                padding: '3rem',
                color: '#666'
              }}>
                <h3 style={{ color: '#003366', marginBottom: '1rem' }}>
                  👋 Welcome! I'm Rupert, your Recipe Assistant!
                </h3>
                <p>
                  I can help you find recipes, suggest cooking ideas, and parse recipes from uploaded files.
                </p>
                <p style={{ marginTop: '1rem', fontSize: '14px', fontStyle: 'italic' }}>
                  Try asking me something like "Show me chicken recipes" or upload a recipe file!
                </p>
              </div>
            ) : (
              messages.map((message) => (
                <div key={message.id} style={messageStyle(message.type)}>
                  <div style={messageBubbleStyle(message.type)}>
                    <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.5' }}>
                      {message.content}
                    </div>

                    {/* Render Action Buttons */}
                    <ActionButtons buttons={message.actionButtons} />

                    <div style={{
                      fontSize: '12px',
                      opacity: 0.7,
                      marginTop: '0.5rem',
                      textAlign: message.type === 'user' ? 'right' : 'left'
                    }}>
                      {formatTimestamp(message.timestamp)}
                    </div>
                  </div>
                </div>
              ))
            )}

            {/* Loading indicator */}
            {(isLoading || isUploadingFile) && (
              <div style={messageStyle('ai')}>
                <div style={{
                  ...messageBubbleStyle('ai'),
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}>
                  <div style={{
                    width: '20px',
                    height: '20px',
                    border: '2px solid #f0f8ff',
                    borderTop: '2px solid #003366',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                  }}></div>
                  <span>{isUploadingFile ? 'Processing your file...' : 'Rupert is thinking...'}</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div style={inputAreaStyle}>
            {/* Show selected file info if file is selected */}
            {selectedFile && (
              <div style={selectedFileStyle}>
                <span>📎</span>
                <span>{selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)</span>
                <button
                  onClick={clearSelectedFile}
                  style={{
                    marginLeft: 'auto',
                    background: 'none',
                    border: 'none',
                    color: '#dc3545',
                    cursor: 'pointer',
                    fontSize: '16px'
                  }}
                >
                  ✕
                </button>
              </div>
            )}

            {/* Text Input Row */}
            <div style={inputRowStyle}>
              <textarea
                ref={inputRef}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={selectedFile ? "Click Send to upload file or type a message..." : "Ask Rupert about recipes, ingredients, cooking tips..."}
                style={inputStyle}
                disabled={isLoading || isUploadingFile}
              />
              <button
                onClick={sendMessage}
                disabled={isLoading || isUploadingFile || (!inputMessage.trim() && !selectedFile)}
                style={{
                  ...buttonStyle,
                  backgroundColor: (isLoading || isUploadingFile || (!inputMessage.trim() && !selectedFile)) ? '#ccc' : '#003366',
                  cursor: (isLoading || isUploadingFile || (!inputMessage.trim() && !selectedFile)) ? 'not-allowed' : 'pointer'
                }}
              >
                {isUploadingFile ? '⏳' : selectedFile ? '📎' : '🚀'}
              </button>
            </div>

            {/* Bottom Row: Tips and Upload Button */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: '1rem'
            }}>
              {/* Tips */}
              <div style={{
                fontSize: '12px',
                color: '#666',
                flex: 1
              }}>
                💡 Tip: Press Enter to send, Shift+Enter for new line
              </div>

              {/* Small Upload Button */}
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <input
                  ref={fileInputRef}
                  type="file"
                  onChange={handleFileSelect}
                  accept=".pdf,.jpg,.jpeg,.png,.bmp,.tiff,.txt,.csv,.md"
                  style={{ display: 'none' }}
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isLoading || isUploadingFile}
                  title="Upload recipe file (PDF, images, text files)"
                  style={{
                    padding: '8px 12px',
                    backgroundColor: isLoading || isUploadingFile ? '#ccc' : '#28a745',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: isLoading || isUploadingFile ? 'not-allowed' : 'pointer',
                    fontSize: '14px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.3rem',
                    transition: 'background-color 0.3s ease'
                  }}
                  onMouseEnter={(e) => {
                    if (!isLoading && !isUploadingFile) {
                      e.target.style.backgroundColor = '#218838';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isLoading && !isUploadingFile) {
                      e.target.style.backgroundColor = '#28a745';
                    }
                  }}
                >
                  📎 Upload
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Add CSS animation for loading spinner */}
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default AIChat;