import React, { useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

const MessageList = ({ messages, isLoading }) => {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const formatTime = (isoString) => {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' });
  };

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="welcome-screen">
        <div className="icon">🌱</div>
        <h3>مرحباً بك في المستشار الزراعي الذكي</h3>
        <p>
          أنا هنا للإجابة على جميع أسئلتك الزراعية. يمكنك سؤالي عن المحاصيل،
          التربة، الري، مكافحة الآفات، والكثير من المواضيع الزراعية.
        </p>
        <div className="welcome-suggestions">
          <span className="suggestion-chip">🌾 كيف أزرع القمح؟</span>
          <span className="suggestion-chip">🐛 كيف أتخلص من الحشرات؟</span>
          <span className="suggestion-chip">💧 ما هي أفضل طرق الري؟</span>
          <span className="suggestion-chip">🌿 ما أفضل الأسمدة للخضروات؟</span>
        </div>
      </div>
    );
  }

  return (
    <div className="message-list">
      {messages.map((msg) => (
        <div key={msg.id || msg.tempId} className={`message ${msg.role}`}>
          <div className="message-avatar">
            {msg.role === 'user' ? '👤' : '🤖'}
          </div>
          <div>
            <div className="message-bubble">
              {msg.role === 'assistant' ? (
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              ) : (
                <p>{msg.content}</p>
              )}
            </div>
            {msg.created_at && (
              <div className="message-time">{formatTime(msg.created_at)}</div>
            )}
          </div>
        </div>
      ))}
      {isLoading && (
        <div className="message assistant">
          <div className="message-avatar">🤖</div>
          <div className="typing-indicator">
            <span>جاري الكتابة</span>
            <div className="typing-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
};

export default MessageList;
