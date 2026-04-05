import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, Menu, X, LogOut, Lock, Upload, RefreshCw, 
  MessageCircle, ShieldAlert, CheckCircle, AlertCircle, Loader
} from 'lucide-react';
import './App.css';

function App() {
  // Auth state - admin only
  const [isAdmin, setIsAdmin] = useState(false);
  const [authToken, setAuthToken] = useState(localStorage.getItem('authToken') || '');

  // Admin login modal state
  const [showAdminLogin, setShowAdminLogin] = useState(false);
  const [loginUsername, setLoginUsername] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);

  // Chat state - always visible for everyone
  const [messages, setMessages] = useState([
    { 
      id: 1, 
      text: 'Welcome to NUST Bank Assistant. I\'m here to help you with banking services, account information, and support. How can I assist you today?', 
      sender: 'bot' 
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);

  // Admin panel state
  const [showAdminPanel, setShowAdminPanel] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [rebuildStatus, setRebuildStatus] = useState('');
  const [uploadStatus, setUploadStatus] = useState('');

  const messagesEndRef = useRef(null);
  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  // Check if token is valid on mount
  useEffect(() => {
    if (authToken) {
      checkAuthStatus();
    }
  }, [authToken]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const checkAuthStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/api/auth/check`, {
        method: 'GET',
        headers: {
          'X-Auth-Token': authToken
        }
      });

      const data = await response.json();
      if (data.is_admin) {
        setIsAdmin(true);
      } else {
        setAuthToken('');
        localStorage.removeItem('authToken');
        setIsAdmin(false);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setAuthToken('');
      localStorage.removeItem('authToken');
      setIsAdmin(false);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError('');
    setLoginLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          username: loginUsername, 
          password: loginPassword 
        })
      });

      const data = await response.json();

      if (response.ok && data.is_admin) {
        setAuthToken(data.token);
        setIsAdmin(true);
        localStorage.setItem('authToken', data.token);
        setLoginUsername('');
        setLoginPassword('');
        setShowAdminLogin(false);
        setLoginError('');
      } else {
        setLoginError(data.detail || 'Invalid credentials. Please try again.');
      }
    } catch (error) {
      console.error('Login error:', error);
      setLoginError('Unable to process your request. Please try again later.');
    } finally {
      setLoginLoading(false);
    }
  };

  const handleLogout = async () => {
    if (!authToken) return;

    try {
      await fetch(`${API_URL}/api/auth/logout`, {
        method: 'POST',
        headers: {
          'X-Auth-Token': authToken
        }
      });
    } catch (error) {
      console.error('Logout error:', error);
    }

    setAuthToken('');
    localStorage.removeItem('authToken');
    setIsAdmin(false);
    setShowAdminPanel(false);
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || loading) return;

    const userMessage = {
      id: messages.length + 1,
      text: inputValue,
      sender: 'user'
    };

    setMessages([...messages, userMessage]);
    setInputValue('');
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMessage.text })
      });

      const data = await response.json();

      const botMessage = {
        id: messages.length + 2,
        text: data.answer || 'Sorry, I could not process your request. Please try again.',
        sender: 'bot'
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Query error:', error);
      const errorMessage = {
        id: messages.length + 2,
        text: 'I apologize, I am temporarily unavailable. Please try your question again in a moment.',
        sender: 'bot'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadFile = async () => {
    if (!uploadFile || !authToken) {
      setUploadStatus('Please select a file and login as admin');
      return;
    }

    setUploadStatus('Uploading...');

    try {
      const formData = new FormData();
      formData.append('file', uploadFile);

      const response = await fetch(`${API_URL}/api/upload`, {
        method: 'POST',
        headers: {
          'X-Auth-Token': authToken
        },
        body: formData
      });

      const data = await response.json();
      if (response.ok) {
        setUploadStatus('File uploaded and index rebuilt successfully!');
        setUploadFile(null);
        setTimeout(() => setUploadStatus(''), 3000);
      } else {
        setUploadStatus(`Upload failed: ${data.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Upload error:', error);
      setUploadStatus('Upload failed. Please try again.');
    }
  };

  const handleRebuildIndex = async () => {
    if (!authToken) return;

    setRebuildStatus('Rebuilding...');

    try {
      const response = await fetch(`${API_URL}/api/rebuild`, {
        method: 'POST',
        headers: {
          'X-Auth-Token': authToken
        }
      });

      const data = await response.json();
      if (response.ok) {
        setRebuildStatus('Index rebuilt successfully!');
        setTimeout(() => setRebuildStatus(''), 3000);
      } else {
        setRebuildStatus(`Rebuild failed: ${data.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Rebuild error:', error);
      setRebuildStatus('Rebuild failed. Please try again.');
    }
  };

  // ==================== MAIN LAYOUT ====================
  // Chat is always visible for everyone
  // Admin button appears in header to show admin panel

  return (
    <div className="App">
      {/* Admin Login Modal */}
      {showAdminLogin && (
        <div className="modal-overlay" onClick={() => setShowAdminLogin(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Admin Login</h2>
              <button onClick={() => setShowAdminLogin(false)}>
                <X size={24} />
              </button>
            </div>

            <form onSubmit={handleLogin} className="login-form">
              <div className="form-group">
                <label>Username</label>
                <input
                  type="text"
                  value={loginUsername}
                  onChange={(e) => setLoginUsername(e.target.value)}
                  placeholder="Enter admin username"
                  disabled={loginLoading}
                  autoFocus
                />
              </div>

              <div className="form-group">
                <label>Password</label>
                <input
                  type="password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  placeholder="Enter admin password"
                  disabled={loginLoading}
                />
              </div>

              {loginError && (
                <div className="error-message">
                  <AlertCircle size={16} />
                  <span>{loginError}</span>
                </div>
              )}

              <button 
                type="submit" 
                className="login-button"
                disabled={loginLoading}
              >
                {loginLoading ? (
                  <>
                    <Loader size={18} className="spinner" />
                    Logging in...
                  </>
                ) : (
                  <>
                    <Lock size={18} />
                    Login as Admin
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="app-header">
        <div className="header-left">
          <div className="header-title">
            <MessageCircle size={24} />
            <h1>NUST Bank Assistant</h1>
          </div>
        </div>
        <div className="header-right">
          {isAdmin ? (
            <>
              <button 
                className="admin-button active"
                onClick={() => setShowAdminPanel(!showAdminPanel)}
                title="Admin Panel"
              >
                <Lock size={20} />
                <span>Admin</span>
              </button>
              <button 
                className="logout-button"
                onClick={handleLogout}
                title="Logout"
              >
                <LogOut size={20} />
              </button>
            </>
          ) : (
            <button 
              className="admin-button"
              onClick={() => setShowAdminLogin(true)}
              title="Admin Login"
            >
              <Lock size={20} />
              <span>Admin</span>
            </button>
          )}
        </div>
      </header>

      <div className="main-container">
        {/* Admin Panel - Only visible when logged in as admin */}
        {isAdmin && showAdminPanel && (
          <aside className="admin-panel">
            <div className="admin-header">
              <h2>Admin Controls</h2>
              <button onClick={() => setShowAdminPanel(false)}>
                <X size={20} />
              </button>
            </div>

            <div className="admin-section">
              <h3>Upload & Rebuild</h3>
              <p className="admin-description">Keep existing data and add newly uploaded documents</p>
              
              <div className="file-input-group">
                <input
                  type="file"
                  id="file-upload"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  accept=".xlsx,.json,.txt,.md,.pdf"
                />
                <label htmlFor="file-upload" className="file-label">
                  <Upload size={18} />
                  Choose File
                </label>
              </div>

              {uploadFile && (
                <div className="file-selected">
                  <CheckCircle size={16} className="success-icon" />
                  <span>{uploadFile.name}</span>
                </div>
              )}

              <button 
                className="action-button upload"
                onClick={handleUploadFile}
                disabled={!uploadFile}
              >
                <Upload size={18} />
                Upload & Rebuild
              </button>

              {uploadStatus && (
                <div className={`status-message ${uploadStatus.includes('successfully') ? 'success' : 'error'}`}>
                  {uploadStatus.includes('successfully') ? (
                    <CheckCircle size={16} />
                  ) : (
                    <AlertCircle size={16} />
                  )}
                  <span>{uploadStatus}</span>
                </div>
              )}
            </div>

            <div className="admin-section">
              <h3>Rebuild Index</h3>
              <p className="admin-description">Reprocess all existing data from scratch</p>
              
              <button 
                className="action-button rebuild"
                onClick={handleRebuildIndex}
              >
                <RefreshCw size={18} />
                Rebuild Index
              </button>

              {rebuildStatus && (
                <div className={`status-message ${rebuildStatus.includes('successfully') ? 'success' : 'error'}`}>
                  {rebuildStatus.includes('successfully') ? (
                    <CheckCircle size={16} />
                  ) : (
                    <AlertCircle size={16} />
                  )}
                  <span>{rebuildStatus}</span>
                </div>
              )}
            </div>
          </aside>
        )}

        {/* Chat Container - Always visible */}
        <div className={`chat-container ${showAdminPanel && isAdmin ? 'with-admin' : ''}`}>
          <div className="messages-container">
            {messages.map(msg => (
              <div key={msg.id} className={`message ${msg.sender}`}>
                <div className="message-bubble">
                  <p>{msg.text}</p>
                </div>
              </div>
            ))}
            {loading && (
              <div className="message bot">
                <div className="message-bubble typing">
                  <div className="typing-indicator">
                    <span></span><span></span><span></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form className="input-form" onSubmit={handleSendMessage}>
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask about accounts, transfers, rates, or any banking service..."
              disabled={loading}
              autoFocus
            />
            <button type="submit" disabled={loading} className="send-button">
              <Send size={20} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;
