export interface Message {
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  language: 'english' | 'tamil' | 'telugu' | 'hindi' | null;
}

export type Language = 'english' | 'tamil' | 'telugu' | 'hindi';

export interface StoredChatState {
  messages: Array<Omit<Message, 'timestamp'> & { timestamp: string }>;
  language: Language | null;
}