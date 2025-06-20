// frontend/src/pages/AIChat.jsx
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

const AIChat = () => {
  const { isAuthenticated, user, apiBaseUrl } = useAuth();
  const navigate = useNavigate();
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // State management
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [aiStatus, setAiStatus] = useState(null);
  const [error, setError] = useState('');

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

  // Function to handle action button clicks
  const handleActionButtonClick = (button) => {
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
        {buttons.map((button, index) => (
          <button
            key={index}
            onClick={() => handleActionButtonClick(button)}
            style={{
              padding: '10px 16px',
              backgroundColor: '#003366',
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
              e.target.style.backgroundColor = '#0066cc';
              e.target.style.transform = 'translateY(-1px)';
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = '#003366';
              e.target.style.transform = 'translateY(0)';
            }}
          >
            <span>🍳</span>
            {button.text || 'Action'}
          </button>
        ))}
      </div>
    );
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

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

  // Styles matching the app theme - Updated with smaller header
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
    minHeight: '600px',
    maxHeight: '75vh'
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
        {/* Header - Made more compact */}
        <div style={headerStyle}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '1rem',
            marginBottom: '0.5rem',
            flexWrap: 'wrap'
          }}>
            <h1 style={titleStyle}>🤖 Ralph the Recipe Assistant</h1>
            {/* AI Status - moved inline */}
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
                {aiStatus.ai_configured ? '✅ Ralph is Ready' : '❌ Ralph is Not Available'}
              </div>
            )}
          </div>

          <p style={{ fontSize: '0.95rem', color: '#666', marginBottom: '0.5rem' }}>
            Hello <strong style={{ color: '#003366' }}>{user?.username}</strong>!
            I'm Ralph, your personal recipe assistant. Ask me about recipes, cooking tips, or ingredient suggestions!
          </p>

          {/* Quick Actions - Made more compact */}
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
        <div style={chatContainerStyle}>
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
              💬 Chat with Ralph
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
                  👋 Welcome! I'm Ralph, your Recipe Assistant!
                </h3>
                <p>
                  I can help you find recipes, suggest cooking ideas, and answer questions about the recipes in your collection.
                </p>
                <p style={{ marginTop: '1rem', fontSize: '14px', fontStyle: 'italic' }}>
                  Try asking me something like "Show me chicken recipes" or "What can I make for dinner?"
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
            {isLoading && (
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
                  <span>Ralph is thinking...</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div style={inputAreaStyle}>
            <textarea
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask Ralph about recipes, ingredients, cooking tips..."
              style={inputStyle}
              disabled={isLoading}
            />
            <button
              onClick={sendMessage}
              disabled={isLoading || !inputMessage.trim()}
              style={{
                ...buttonStyle,
                backgroundColor: (isLoading || !inputMessage.trim()) ? '#ccc' : '#003366',
                cursor: (isLoading || !inputMessage.trim()) ? 'not-allowed' : 'pointer'
              }}
            >
              {isLoading ? '⏳' : '🚀'}
            </button>
          </div>

          {/* Tips */}
          <div style={{
            fontSize: '12px',
            color: '#666',
            marginTop: '0.5rem',
            textAlign: 'center'
          }}>
            💡 Tip: Press Enter to send, Shift+Enter for new line
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