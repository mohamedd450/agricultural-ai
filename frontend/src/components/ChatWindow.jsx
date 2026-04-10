import React, { useState, useEffect } from 'react';
import MessageList from './MessageList';
import InputField from './InputField';
import { sendMessage } from '../services/api';
import '../styles/chat.css';

const ChatWindow = ({ conversationId, setConversationId, initialMessages = [] }) => {
  const [messages, setMessages] = useState(initialMessages);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    setMessages(initialMessages);
    setError(null);
  }, [conversationId, initialMessages]);

  const handleSend = async (text) => {
    setError(null);

    const tempUserMsg = {
      tempId: Date.now(),
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setIsLoading(true);

    try {
      const data = await sendMessage(text, conversationId);
      if (!conversationId) {
        setConversationId(data.conversation_id);
      }

      const assistantMsg = {
        tempId: Date.now() + 1,
        role: 'assistant',
        content: data.reply,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      const errMsg =
        err?.response?.data?.detail ||
        'حدث خطأ في الاتصال. يرجى التحقق من إعدادات API والمحاولة مرة أخرى.';
      setError(errMsg);
      setMessages((prev) => prev.filter((m) => m.tempId !== tempUserMsg.tempId));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-window">
      <div className="chat-header">
        <span style={{ fontSize: '1.8rem' }}>🌱</span>
        <div>
          <h2>المستشار الزراعي الذكي</h2>
          <div className="subtitle">Agricultural AI Advisor — مدعوم بـ OpenAI</div>
        </div>
      </div>

      <MessageList messages={messages} isLoading={isLoading} />

      {error && (
        <div style={{ padding: '0 24px 8px' }}>
          <div className="error-message">⚠️ {error}</div>
        </div>
      )}

      <InputField onSend={handleSend} isLoading={isLoading} />
    </div>
  );
};

export default ChatWindow;
