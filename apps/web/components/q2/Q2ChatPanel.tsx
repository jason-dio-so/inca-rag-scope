/**
 * Q2ChatPanel - Chat Interface for Q2 Coverage Limit Comparison
 *
 * Purpose: Allow users to input coverage query via chat
 * Rules:
 * - Deterministic slot parsing (NO LLM)
 * - Handle coverage candidates (0/1/2~3)
 * - NO preset buttons
 */

'use client';

import { useState, useRef, useEffect } from 'react';

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: Date;
}

interface Q2ChatPanelProps {
  messages: ChatMessage[];
  onSendMessage: (message: string) => void;
  loading?: boolean;
  disabled?: boolean;
}

export function Q2ChatPanel({ messages, onSendMessage, loading, disabled }: Q2ChatPanelProps) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading || disabled) return;

    onSendMessage(input.trim());
    setInput('');
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="bg-purple-50 border-b border-purple-100 px-4 py-3">
        <h3 className="text-sm font-semibold text-gray-900">
          담보 보장한도 비교
        </h3>
        <p className="text-xs text-gray-600 mt-1">
          담보명, 연령대, 성별을 입력하세요
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-sm text-gray-500 mb-2">
              비교하고 싶은 담보를 말씀해 주세요
            </p>
            <div className="text-xs text-gray-400 space-y-1">
              <p>예: "암직접입원비 40대 남자"</p>
              <p>예: "뇌졸중진단비 30대 여성"</p>
              <p>예: "암진단비 50대 남성"</p>
            </div>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-2 ${
                  msg.role === 'user'
                    ? 'bg-purple-600 text-white'
                    : msg.role === 'system'
                    ? 'bg-yellow-50 border border-yellow-200 text-gray-900'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                {msg.timestamp && (
                  <p className="text-xs opacity-70 mt-1">
                    {msg.timestamp.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}
                  </p>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="border-t border-gray-200 p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="메시지를 입력하세요..."
            disabled={disabled || loading}
            className="flex-1 px-4 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading || disabled}
            className="px-6 py-2 text-sm font-medium text-white bg-purple-600 rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? '처리중...' : '전송'}
          </button>
        </div>
      </form>
    </div>
  );
}
