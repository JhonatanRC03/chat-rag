import React from 'react';
import ChatInterface from './components/ChatInterface';
import './ChatPage.css';

const ChatPage: React.FC = () => {
  return (
    <div className="chat-page">
      <div className="chat-page-background">
        <ChatInterface />
      </div>
    </div>
  );
};

export default ChatPage;