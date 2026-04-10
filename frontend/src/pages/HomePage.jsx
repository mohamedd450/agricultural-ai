import React, { useState, useEffect, useCallback } from 'react';
import ChatWindow from '../components/ChatWindow';
import { getConversations, getConversation, deleteConversation } from '../services/api';
import '../styles/chat.css';

const HomePage = () => {
  const [conversationId, setConversationId] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [currentMessages, setCurrentMessages] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const loadConversations = useCallback(async () => {
    try {
      const data = await getConversations();
      setConversations(data);
    } catch (err) {
      console.error('Failed to load conversations:', err);
    }
  }, []);

  useEffect(() => {
    loadConversations();
  }, [loadConversations, conversationId]);

  const handleSelectConversation = async (id) => {
    try {
      const data = await getConversation(id);
      setConversationId(id);
      setCurrentMessages(data.messages);
      setSidebarOpen(false);
    } catch (err) {
      console.error('Failed to load conversation:', err);
    }
  };

  const handleNewChat = () => {
    setConversationId(null);
    setCurrentMessages([]);
    setSidebarOpen(false);
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    try {
      await deleteConversation(id);
      if (conversationId === id) {
        handleNewChat();
      }
      loadConversations();
    } catch (err) {
      console.error('Failed to delete conversation:', err);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header style={{
        background: 'linear-gradient(135deg, #1b4332, #2d6a4f)',
        color: 'white',
        padding: '12px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        height: '64px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '1.5rem' }}>🌾</span>
          <span style={{ fontWeight: 700, fontSize: '1.1rem' }}>Agricultural AI</span>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={handleNewChat}
            style={{
              background: 'rgba(255,255,255,0.15)',
              border: '1px solid rgba(255,255,255,0.3)',
              color: 'white',
              padding: '6px 14px',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '0.875rem',
            }}
          >
            + محادثة جديدة
          </button>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            style={{
              background: 'rgba(255,255,255,0.15)',
              border: '1px solid rgba(255,255,255,0.3)',
              color: 'white',
              padding: '6px 14px',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '0.875rem',
            }}
          >
            📜 السجل
          </button>
        </div>
      </header>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {sidebarOpen && (
          <aside style={{
            width: '280px',
            background: 'white',
            borderLeft: '1px solid #e2e8f0',
            overflowY: 'auto',
            flexShrink: 0,
          }}>
            <div style={{ padding: '16px', borderBottom: '1px solid #e2e8f0' }}>
              <strong style={{ color: '#1b4332' }}>📜 المحادثات السابقة</strong>
            </div>
            {conversations.length === 0 ? (
              <div style={{ padding: '20px', color: '#888', textAlign: 'center', fontSize: '0.875rem' }}>
                لا توجد محادثات سابقة
              </div>
            ) : (
              conversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => handleSelectConversation(conv.id)}
                  style={{
                    padding: '12px 16px',
                    cursor: 'pointer',
                    borderBottom: '1px solid #f0f0f0',
                    background: conversationId === conv.id ? '#f0fdf4' : 'white',
                    transition: 'background 0.15s',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                  }}
                >
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{
                      fontSize: '0.875rem',
                      color: '#1b4332',
                      fontWeight: 500,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}>
                      {conv.title}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#888', marginTop: '4px' }}>
                      {conv.message_count} رسالة
                    </div>
                  </div>
                  <button
                    onClick={(e) => handleDelete(e, conv.id)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#e53e3e',
                      cursor: 'pointer',
                      fontSize: '0.875rem',
                      padding: '2px 6px',
                      marginRight: '4px',
                    }}
                    title="حذف"
                  >
                    🗑️
                  </button>
                </div>
              ))
            )}
          </aside>
        )}

        <main style={{ flex: 1, padding: '16px', overflow: 'hidden' }}>
          <ChatWindow
            conversationId={conversationId}
            setConversationId={setConversationId}
            initialMessages={currentMessages}
          />
        </main>
      </div>
    </div>
  );
};

export default HomePage;
