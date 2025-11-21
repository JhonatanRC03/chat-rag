// types/chat.ts
export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

export interface ConversationHistory {
  role: string;
  content: string;
}

export interface ChatRequest {
  message: string;
  conversation_history?: ConversationHistory[];
}

export interface ChatResponse {
  response: string;
  success: boolean;
}

export interface StreamData {
  chunk: string;
  done: boolean;
  error?: string;
}

export interface ChatService {
  sendMessage: (message: string, history?: ConversationHistory[]) => Promise<ReadableStreamDefaultReader<Uint8Array>>;
  sendMessageSimple: (message: string, history?: ConversationHistory[]) => Promise<ChatResponse>;
}