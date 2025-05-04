import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage } from './components/ChatMessage';
import { ChatInput } from './components/ChatInput';
import { Message, ChatState, Language } from './types';
import { getAIResponse } from './services/api';
import { loadChatHistory, saveChatHistory } from './services/chatStorage';

function App() {
  const [chatState, setChatState] = useState<ChatState>(() => ({
    messages: [],
    isLoading: false,
    language: null,
    ...loadChatHistory()
  }));

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatState.messages]);

  useEffect(() => {
    saveChatHistory(chatState);
  }, [chatState.messages, chatState.language]);

  const handleLanguageSelect = (language: Language) => {
    const welcomeMessage: Message = {
      role: 'assistant',
      content: 
        language === 'tamil' 
          ? 'வணக்கம்! SCSVMV பல்கலைக்கழக சேர்க்கை உதவியாளருக்கு வரவேற்கிறோம்! எங்கள் படிப்புகள், சேர்க்கை செயல்முறை, வளாக வாழ்க்கை மற்றும் பலவற்றைப் பற்றிய தகவல்களுடன் நான் உங்களுக்கு உதவ முடியும். நான் எவ்வாறு உங்களுக்கு உதவ முடியும்?'
          : language === 'hindi'
          ? 'नमस्कार! SCSVMV विश्वविद्यालय प्रवेश सहायक में आपका स्वागत है! मैं आपको हमारे कार्यक्रमों, प्रवेश प्रक्रिया, कैंपस जीवन और बहुत कुछ के बारे में जानकारी के साथ मदद कर सकता हूं। मैं आपकी कैसे सहायता कर सकता हूं?'
          : language === 'telugu'
          ? 'నమస్కారం! SCSVMV విశ్వవిద్యాలయం ప్రవేశ సహాయకుడికి స్వాగతం! మా కోర్సులు, ప్రవేశ విధానం, క్యాంపస్ జీవితం మరియు మరిన్ని వాటి గురించిన సమాచారంతో నేను మీకు సహాయం చేయగలను. నేను మీకు ఎలా సహాయపడగలను?'
          : 'Welcome to SCSVMV University Admissions Assistant! I can help you with information about our programs, admission process, campus life, and more. How may I assist you today?',
      timestamp: new Date(),
    };

    setChatState(prev => ({
      ...prev,
      language,
      messages: [welcomeMessage],
    }));
  };

  const handleSendMessage = async (content: string) => {
    if (!chatState.language) return;

    const userMessage: Message = {
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setChatState(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage],
      isLoading: true,
    }));

    try {
      const aiResponse = await getAIResponse(content, chatState.language);
      
      const botResponse: Message = {
        role: 'assistant',
        content: aiResponse,
        timestamp: new Date(),
      };

      setChatState(prev => ({
        ...prev,
        messages: [...prev.messages, botResponse],
        isLoading: false,
      }));
    } catch (error) {
      const errorMessage: Message = {
        role: 'assistant',
        content: 
          chatState.language === 'tamil'
            ? 'மன்னிக்கவும், சர்வருடன் இணைப்பதில் சிக்கல் உள்ளது. பிறகு முயற்சிக்கவும்.'
            : chatState.language === 'hindi'
            ? 'क्षमा करें, सर्वर से कनेक्ट करने में समस्या हो रही है। कृपया बाद में पुनः प्रयास करें।'
            : chatState.language === 'telugu'
            ? 'క్షమించండి, సర్వర్‌కు కనెక్ట్ చేయడంలో సమస్య ఉంది. దయచేసి తర్వాత మళ్లీ ప్రయత్నించండి.'
            : 'I apologize, but I\'m having trouble connecting to the server. Please try again later.',
        timestamp: new Date(),
      };

      setChatState(prev => ({
        ...prev,
        messages: [...prev.messages, errorMessage],
        isLoading: false,
      }));
    }
  };

  const handleClearHistory = () => {
    const welcomeMessage: Message = {
      role: 'assistant',
      content: 
        chatState.language === 'tamil' 
          ? 'வணக்கம்! SCSVMV பல்கலைக்கழக சேர்க்கை உதவியாளருக்கு வரவேற்கிறோம்! எங்கள் படிப்புகள், சேர்க்கை செயல்முறை, வளாக வாழ்க்கை மற்றும் பலவற்றைப் பற்றிய தகவல்களுடன் நான் உங்களுக்கு உதவ முடியும். நான் எவ்வாறு உங்களுக்கு உதவ முடியும்?'
          : chatState.language === 'hindi'
          ? 'नमस्कार! SCSVMV विश्वविद्यालय प्रवेश सहायक में आपका स्वागत है! मैं आपको हमारे कार्यक्रमों, प्रवेश प्रक्रिया, कैंपस जीवन और बहुत कुछ के बारे में जानकारी के साथ मदद कर सकता हूं। मैं आपकी कैसे सहायता कर सकता हूं?'
          : chatState.language === 'telugu'
          ? 'నమస్కారం! SCSVMV విశ్వవిద్యాలయం ప్రవేశ సహాయకుడికి స్వాగతం! మా కోర్సులు, ప్రవేశ విధానం, క్యాంపస్ జీవితం మరియు మరిన్ని వాటి గురించిన సమాచారంతో నేను మీకు సహాయం చేయగలను. నేను మీకు ఎలా సహాయపడగలను?'
          : 'Welcome to SCSVMV University Admissions Assistant! I can help you with information about our programs, admission process, campus life, and more. How may I assist you today?',
      timestamp: new Date(),
    };

    setChatState(prev => ({
      ...prev,
      messages: [welcomeMessage],
    }));
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-orange-50 to-orange-100">
      <div className="max-w-4xl mx-auto p-4">
        {/* Header with Logo */}
        <div className="bg-white rounded-t-lg p-6 border-b shadow-sm">
          <div className="flex items-center justify-between">
            {/* Left side with Logo and University Info */}
            <div className="flex flex-col md:flex-row items-center gap-6">
              {/* University Logo */}
              <img 
                src="https://www.kanchiuniv.ac.in/images/logo.png" 
                alt="SCSVMV University Logo" 
                className="w-24 h-24 object-contain"
              />

              {/* University Information */}
              <div>
                <div className="text-center md:text-left">
                  <h1 className="text-2xl font-bold text-gray-800">SCSVMV University</h1>
                  <div className="flex flex-col md:flex-row md:items-center gap-1 md:gap-2">
                    <p className="text-sm text-gray-600">Sri Chandrasekharendra Saraswathi Viswa Mahavidyalaya</p>
                    <span className="hidden md:inline text-gray-400">•</span>
                    <p className="text-sm text-orange-600 font-semibold">Kanchipuram</p>
                  </div>
                  <div className="mt-2 flex items-center justify-center md:justify-start gap-2 text-xs text-gray-500">
                    <span className="px-2 py-1 bg-orange-100 rounded-full">NAAC 'A' Grade</span>
                    <span className="px-2 py-1 bg-orange-100 rounded-full">NBA Accredited</span>
                    <span className="px-2 py-1 bg-orange-100 rounded-full">UGC Approved</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Right side with Language Selector and Clear History */}
            <div className="flex flex-col items-end gap-4">
              <div className="flex items-center gap-2 bg-orange-50 px-4 py-2 rounded-lg border border-orange-200">
                <span className="text-sm text-orange-700 font-medium">🌐</span>
                <select
                  value={chatState.language || ''}
                  onChange={(e) => handleLanguageSelect(e.target.value as Language)}
                  className="bg-transparent border-none focus:ring-0 text-orange-700 font-medium cursor-pointer"
                >
                  <option value="" className="text-gray-500">Select Language</option>
                  <option value="english" className="text-orange-700">English</option>
                  <option value="tamil" className="text-orange-700">தமிழ் (Tamil)</option>
                  <option value="hindi" className="text-orange-700">हिंदी (Hindi)</option>
                  <option value="telugu" className="text-orange-700">తెలుగు (Telugu)</option>
                </select>
              </div>
              
              {chatState.language && chatState.messages.length > 0 && (
                <button
                  onClick={handleClearHistory}
                  className="px-4 py-2 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
                >
                  Clear History
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Chat Messages */}
        <div className="relative bg-white h-[600px] overflow-y-auto p-6 border-x">
          {/* Background Image Container */}
          <div 
            className="absolute inset-0 pointer-events-none opacity-5"
            style={{
              backgroundImage: 'url(https://www.kanchiuniv.ac.in/images/logo.png)',
              backgroundRepeat: 'no-repeat',
              backgroundPosition: 'center',
              backgroundSize: '300px'
            }}
          />
          {/* Messages Container */}
          <div className="relative z-10 space-y-6">
            {chatState.messages.map((message, index) => (
              <ChatMessage key={index} message={message} />
            ))}
          </div>
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="bg-white rounded-b-lg p-6 border shadow-sm">
          <ChatInput
            onSendMessage={handleSendMessage}
            disabled={chatState.isLoading || chatState.language === null}
            placeholder={
              chatState.language === 'tamil'
                ? 'SCSVMV பல்கலைக்கழக சேர்க்கை பற்றி கேளுங்கள்...'
                : chatState.language === 'hindi'
                ? 'SCSVMV विश्वविद्यालय प्रवेश के बारे में पूछें...'
                : chatState.language === 'telugu'
                ? 'SCSVMV విశ్వవిద్యాలయం ప్రవేశం గురించి అడగండి...'
                : 'Ask about SCSVMV University admissions...'
            }
          />
        </div>
      </div>
    </div>
  );
}

export default App;