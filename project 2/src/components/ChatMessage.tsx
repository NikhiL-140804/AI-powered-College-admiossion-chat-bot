import React from 'react';
import { MessageCircle, Bot } from 'lucide-react';
import { Message } from '../types';

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === 'user';
  
  return (
    <div className={`flex items-start gap-4 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
        isUser ? 'bg-orange-500' : 'bg-orange-600'
      }`}>
        {isUser ? 
          <MessageCircle className="w-6 h-6 text-white" /> : 
          <Bot className="w-6 h-6 text-white" />
        }
      </div>
      <div className={`max-w-[80%] rounded-lg p-4 ${
        isUser ? 'bg-orange-100' : 'bg-gray-100'
      }`}>
        <p className="text-gray-800 leading-relaxed">{message.content}</p>
        <span className="text-xs text-gray-500 mt-2 block">
          {new Date(message.timestamp).toLocaleTimeString()}
        </span>
      </div>
    </div>
  );
}