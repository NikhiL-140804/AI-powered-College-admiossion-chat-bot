import { Message, ChatState, StoredChatState } from '../types';

const CHAT_STORAGE_KEY = 'scsvmv_chat_history';

export function loadChatHistory(): Partial<ChatState> {
  try {
    const stored = localStorage.getItem(CHAT_STORAGE_KEY);
    if (!stored) return {};

    const data: StoredChatState = JSON.parse(stored);
    return {
      messages: data.messages.map(msg => ({
        ...msg,
        timestamp: new Date(msg.timestamp)
      })),
      language: data.language
    };
  } catch (error) {
    console.error('Error loading chat history:', error);
    return {};
  }
}

export function saveChatHistory(state: ChatState) {
  try {
    const dataToStore: StoredChatState = {
      messages: state.messages.map(msg => ({
        ...msg,
        timestamp: msg.timestamp.toISOString()
      })),
      language: state.language
    };
    localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(dataToStore));
  } catch (error) {
    console.error('Error saving chat history:', error);
  }
}