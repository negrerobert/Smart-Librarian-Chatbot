import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send, Library, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import './App.css';

const API_BASE = 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const [conversationHistory, setConversationHistory] = useState([]);
  const [hasInitialized, setHasInitialized] = useState(false);
  const messagesEndRef = useRef(null);

  const exampleQueries = [
    { text: 'I want a book about freedom and social control', category: 'Assignment Queries' },
    { text: 'What do you recommend if I love fantasy stories?', category: 'Assignment Queries' },
    { text: 'What is 1984?', category: 'Assignment Queries' },
    { text: 'Books about friendship and magic', category: 'Quick Examples' },
    { text: 'Tell me about The Great Gatsby', category: 'Quick Examples' }
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (!hasInitialized) {
      setHasInitialized(true);
      initializeApp();
    }
  }, [hasInitialized]);

  const initializeApp = async () => {
    const bookCount = await checkConnection();
    addWelcomeMessage(bookCount);
  };

  const checkConnection = async () => {
    try {
      const response = await axios.get(`${API_BASE}/health`, { timeout: 5000 });
      if (response.status === 200) {
        setConnectionStatus('connected');
        const data = response.data;
        if (data.database_info && data.database_info.document_count) {
          return data.database_info.document_count;
        }
      }
      return 0;
    } catch (error) {
      setConnectionStatus('disconnected');
      console.error('Backend connection failed:', error);
      return 0;
    }
  };

  const addWelcomeMessage = (bookCount = 0) => {
    const bookCountText = bookCount > 0 
      ? `\n\n🎉 I'm connected and ready to help! I have ${bookCount} books in my library, all loaded and ready for your questions!`
      : '';

    const welcomeMessage = {
      id: Date.now(),
      content: `Welcome! 👋 I'm your personal book recommendation assistant. I can:

📖 Find books by theme - "Books about freedom and dystopia"
🔍 Search by genre - "Fantasy stories with magic"  
📚 Explain specific books - "Tell me about 1984"
✨ Give personalized recommendations${bookCountText}

Try one of the example queries below or ask me anything about books!`,
      isUser: false,
      timestamp: new Date()
    };
    setMessages([welcomeMessage]);
  };

  const addMessage = (content, isUser, metadata = null) => {
    const newMessage = {
      id: Date.now() + Math.random(),
      content,
      isUser,
      metadata,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const handleSendMessage = async (message = null) => {
    const messageToSend = message || inputMessage.trim();
    if (!messageToSend) return;

    addMessage(messageToSend, true);
    setInputMessage('');
    setIsLoading(true);

    const newHistory = [...conversationHistory, { role: 'user', content: messageToSend }];
    setConversationHistory(newHistory);

    try {
      const response = await axios.post(`${API_BASE}/chat`, {
        message: messageToSend,
        conversation_history: newHistory.slice(-10) 
      });

      if (response.data.success) {
        addMessage(response.data.message, false, {
          function_calls: response.data.function_calls,
          search_results: response.data.search_results,
          filtered: response.data.filtered
        });

        setConversationHistory(prev => [
          ...prev,
          { role: 'assistant', content: response.data.message }
        ]);
      } else {
        addMessage(`Error: ${response.data.message || 'Unknown error occurred'}`, false);
      }
    } catch (error) {
      console.error('Error:', error);
      setConnectionStatus('disconnected');
      addMessage(
        `Sorry, I couldn't connect to the Smart Librarian backend.

Please make sure:
1. The backend server is running (python run_server.py)
2. The server is accessible at http://localhost:8000
3. Check the console for more details

Error: ${error.message}`,
        false
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleExampleClick = (query) => {
    setInputMessage(query);
    handleSendMessage(query);
  };

  const formatMessage = (content) => {
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');
  };

  return (
    <div className="app">
      <div className="chat-container">
        {/* Header */}
        <div className="chat-header">
          <div className="header-content">
            <div className="header-left">
              <div className="header-icon">
                <Library size={32} />
              </div>
              <div>
                <h1>Smart Librarian</h1>
                <p>Discover your next favorite book with AI-powered recommendations</p>
              </div>
            </div>
            <div className="header-right">
              {connectionStatus === 'connected' && (
                <div className="connection-status">
                  <CheckCircle size={18} />
                  <span>Connected</span>
                </div>
              )}
              {connectionStatus === 'disconnected' && (
                <div className="connection-status disconnected">
                  <AlertCircle size={18} />
                  <span>Disconnected</span>
                </div>
              )}
              {connectionStatus === 'connecting' && (
                <div className="connection-status connecting">
                  <Loader2 size={18} className="spinning" />
                  <span>Connecting</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="messages-container">
          {messages.map((message) => (
            <div key={message.id} className={`message ${message.isUser ? 'user' : 'bot'}`}>
              <div className="message-avatar">
                {message.isUser ? (
                  <div className="avatar-user">U</div>
                ) : (
                  <div className="avatar-bot">AI</div>
                )}
              </div>
              <div className="message-content">
                <div 
                  className="message-text"
                  dangerouslySetInnerHTML={{ __html: formatMessage(message.content) }}
                />
                
                {message.metadata && !message.isUser && message.metadata.filtered && (
                  <div className="message-metadata">
                    <div className="content-filtered">
                      <strong>🛡️ Content Filter:</strong> Keeping our conversation friendly!
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="message bot">
              <div className="message-avatar">
                <div className="avatar-bot">AI</div>
              </div>
              <div className="message-content">
                <div className="typing-indicator">
                  <div className="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <span className="typing-text">Smart Librarian is thinking...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Example Queries */}
        <div className="example-queries">
          <div className="queries-section">
            <h3>Try these examples:</h3>
            <div className="query-buttons">
              {exampleQueries.map((query, index) => (
                <button
                  key={index}
                  className="example-query"
                  onClick={() => handleExampleClick(query.text)}
                  disabled={isLoading}
                >
                  {query.text}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Input */}
        <div className="chat-input">
          <div className="input-container">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me about books, themes, genres, or specific titles..."
              disabled={isLoading}
              className="message-input"
            />
            <button
              onClick={() => handleSendMessage()}
              disabled={isLoading || !inputMessage.trim()}
              className="send-button"
            >
              {isLoading ? (
                <Loader2 size={20} className="spinning" />
              ) : (
                <Send size={20} />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;