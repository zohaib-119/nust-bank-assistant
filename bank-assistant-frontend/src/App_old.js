import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, Menu, X, LogOut, Lock, Upload, RefreshCw, 
  MessageCircle, ShieldAlert, CheckCircle, AlertCircle, Loader
} from 'lucide-react';
import './App.css';

function App() {
  // Auth state
  const [isAdmin, setIsAdmin] = useState(false);
  const [authToken, setAuthToken] = useState(localStorage.getItem('authToken') || '');
  const [showAdminLogin, setShowAdminLogin] = useState(false);
  const [loginUsername, setLoginUsername] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);

  // Chat state
  const [messages, setMessages] = useState([
    { 
      id: 1, 
      text: 'Welcome to NUST Bank Assistant. I\'m here to help you with banking services, account information, and support. How can I assist you today?', 
      sender: 'bot' 
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);

  // Admin panel state (separate from login)
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
  }, []);

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
        setIsLoggedIn(true);
        setIsAdmin(true);
      } else {
        setAuthToken('');
        localStorage.removeItem('authToken');
        setIsLoggedIn(false);
        setIsAdmin(false);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setAuthToken('');
      localStorage.removeItem('authToken');
      setIsLoggedIn(false);
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
        setIsLoggedIn(true);
        setIsAdmin(true);
        localStorage.setItem('authToken', data.token);
        setLoginUsername('');
        setLoginPassword('');
        setSidebarOpen(false);
      } else {
        setLoginError('Invalid admin credentials');
      }
    } catch (error) {
      setLoginError('Login failed. Please try again.');
    } finally {
      setLoginLoading(false);
    }
  };

  const handleLogout = async () => {
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

    setIsLoggedIn(false);
    setIsAdmin(false);
    setAuthToken('');
    localStorage.removeItem('authToken');
    setShowAdminPanel(false);
    setSidebarOpen(false);
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMessage = { id: messages.length + 1, text: inputValue, sender: 'user' };
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: inputValue })
      });

      const data = await response.json();
      const botMessage = {
        id: messages.length + 2,
        text: data.answer || 'Sorry, I could not process your request.',
        sender: 'bot'
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage = {
        id: messages.length + 2,
        text: 'Error connecting to the server. Please ensure the backend is running.',
        sender: 'bot'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadFile = async () => {
    if (!uploadFile || !authToken) return;

    setUploadStatus('Uploading...');
    const formData = new FormData();
    formData.append('file', uploadFile);

    try {
      const response = await fetch(`${API_URL}/api/upload`, {
        method: 'POST',
        headers: {
          'X-Auth-Token': authToken
        },
        body: formData
      });

      const data = await response.json();
      if (response.ok) {
        setUploadStatus('File uploaded and indexed successfully!');
        setUploadFile(null);
        setTimeout(() => setUploadStatus(''), 3000);
      } else {
        setUploadStatus(`Upload failed: ${data.detail || 'Unknown error'}`);
      }
    } catch (error) {
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
      setRebuildStatus('Rebuild failed. Please try again.');
    }
  };

  // Login View
  if (!isLoggedIn) {
    return (
      <div className="App login-view">
        <div className="login-container">
          <div className="login-box">
            <div className="login-header">
              <div className="bank-logo">
                <ShieldAlert size={48} />
              </div>
              <h1>NUST Bank</h1>
              <p>Assistant Management</p>
            </div>

            <form onSubmit={handleLogin} className="login-form">
              <div className="form-group">
                <label>Admin Username</label>
                <input
                  type="text"
                  value={loginUsername}
                  onChange={(e) => setLoginUsername(e.target.value)}
                  placeholder="Enter admin username"
                  disabled={loginLoading}
                />
              </div>

              <div className="form-group">
                <label>Admin Password</label>
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
                  {loginError}
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

            <div className="login-info">
              <p>Demo credentials available for testing</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Main Chat View
  return (
    <div className="App chat-view">
      {/* Header */}
      <header className="app-header">
        <div className="header-left">
          <button 
            className="menu-button"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
          <div className="header-title">
            <MessageCircle size={24} />
            <h1>NUST Bank Assistant</h1>
          </div>
        </div>
        <div className="header-right">
          {isAdmin && (
            <button 
              className="admin-button"
              onClick={() => setShowAdminPanel(!showAdminPanel)}
              title="Admin Panel"
            >
              <Lock size={20} />
            </button>
          )}
          <button 
            className="logout-button"
            onClick={handleLogout}
            title="Logout"
          >
            <LogOut size={20} />
          </button>
        </div>
      </header>

      <div className="main-container">
        {/* Sidebar */}
        {sidebarOpen && (
          <aside className="sidebar">
            <div className="sidebar-header">
              <h2>Menu</h2>
              <button onClick={() => setSidebarOpen(false)}>
                <X size={20} />
              </button>
            </div>

            <nav className="sidebar-nav">
              <button 
                className="nav-item"
                onClick={() => {
                  setMessages([{ 
                    id: 1, 
                    text: 'Chat cleared. How can I help you today?', 
                    sender: 'bot' 
                  }]);
                  setSidebarOpen(false);
                }}
              >
                <MessageCircle size={18} />
                New Chat
              </button>

              {isAdmin && (
                <button 
                  className="nav-item admin"
                  onClick={() => {
                    setShowAdminPanel(!showAdminPanel);
                    setSidebarOpen(false);
                  }}
                >
                  <Lock size={18} />
                  Admin Panel
                </button>
              )}
            </nav>

            <div className="sidebar-footer">
              <button className="logout-nav" onClick={handleLogout}>
                <LogOut size={18} />
                Logout
              </button>
            </div>
          </aside>
        )}

        {/* Admin Panel */}
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
                  {uploadStatus}
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
                  {rebuildStatus}
                </div>
              )}
            </div>
          </aside>
        )}

        {/* Chat Container */}
        <div className="chat-container">
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
