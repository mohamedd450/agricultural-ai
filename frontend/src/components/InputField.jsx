import React, { useState, useRef } from 'react';

const InputField = ({ onSend, isLoading }) => {
  const [text, setText] = useState('');
  const textareaRef = useRef(null);

  const handleSend = () => {
    if (!text.trim() || isLoading) return;
    onSend(text.trim());
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleChange = (e) => {
    setText(e.target.value);
    const ta = e.target;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 120) + 'px';
  };

  return (
    <div className="input-area">
      <textarea
        ref={textareaRef}
        value={text}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder="اكتب سؤالك الزراعي هنا... (Enter للإرسال، Shift+Enter لسطر جديد)"
        disabled={isLoading}
        rows={1}
      />
      <button
        className="send-button"
        onClick={handleSend}
        disabled={!text.trim() || isLoading}
        title="إرسال"
      >
        ➤
      </button>
    </div>
  );
};

export default InputField;
