"use client";

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Paperclip, Send, Bot, User, X } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

export default function AgentChat() {
  const [isOpen, setIsOpen] = useState(true); // Default to open for now
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = { id: Date.now().toString(), role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    // SSE Streaming Logic
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/chat/stream`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ input: userMessage.content }),
          credentials: 'include',
        }
      );

      if (!response.body) {
        throw new Error('No response body');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantMessageContent = '';
      let assistantMessageId = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.substring(6);
            if (jsonStr.trim() === '[DONE]') continue;
            try {
              const data = JSON.parse(jsonStr);
              if (data.event === 'on_chat_model_stream') {
                const chunkContent = data.data.chunk.content;
                if(chunkContent) {
                  assistantMessageContent += chunkContent;
                  if (!assistantMessageId) {
                    assistantMessageId = Date.now().toString() + '-ai';
                    setMessages((prev) => [...prev, { id: assistantMessageId, role: 'assistant', content: assistantMessageContent }]);
                  } else {
                    setMessages((prev) =>
                      prev.map((msg) =>
                        msg.id === assistantMessageId ? { ...msg, content: assistantMessageContent } : msg
                      )
                    );
                  }
                }
              }
            } catch (e) {
              // Ignore parsing errors for incomplete JSON
            }
          }
        }
      }
    } catch (error) {
      console.error('SSE Error:', error);
      const errorMessage: Message = { id: Date.now().toString(), role: 'assistant', content: 'Sorry, I encountered an error.' };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ y: '100%', opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: '100%', opacity: 0 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          className="fixed bottom-8 right-8 w-[400px] h-[600px] flex flex-col bg-black/30 backdrop-blur-xl border border-white/20 rounded-2xl shadow-2xl z-50"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-white/10 flex-shrink-0">
            <h3 className="text-lg font-bold text-white">AI Assistant</h3>
            <button onClick={() => setIsOpen(false)} className="text-neutral-400 hover:text-white transition-colors">
              <X size={20} />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 p-4 overflow-y-auto space-y-4">
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex items-start gap-3 ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {message.role === 'assistant' && <Bot className="w-6 h-6 text-primary flex-shrink-0 mt-1" />}
                <div
                  className={`max-w-[80%] p-3 rounded-2xl ${
                    message.role === 'user'
                      ? 'bg-gradient-to-br from-primary to-secondary text-white rounded-br-lg'
                      : 'bg-white/10 text-neutral-200 rounded-bl-lg'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                </div>
                {message.role === 'user' && <User className="w-6 h-6 text-neutral-300 flex-shrink-0 mt-1" />}
              </motion.div>
            ))}
            {isLoading && (
              <motion.div initial={{opacity: 0}} animate={{opacity: 1}} className="flex items-start gap-3 justify-start">
                 <Bot className="w-6 h-6 text-primary flex-shrink-0 mt-1" />
                 <div className="max-w-[80%] p-3 rounded-2xl bg-white/10 text-neutral-200 rounded-bl-lg flex items-center gap-2">
                    <motion.div className="w-2 h-2 bg-neutral-400 rounded-full" animate={{y: [0, -4, 0]}} transition={{duration: 1, repeat: Infinity}}/>
                    <motion.div className="w-2 h-2 bg-neutral-400 rounded-full" animate={{y: [0, -4, 0]}} transition={{duration: 1, repeat: Infinity, delay: 0.2}}/>
                    <motion.div className="w-2 h-2 bg-neutral-400 rounded-full" animate={{y: [0, -4, 0]}} transition={{duration: 1, repeat: Infinity, delay: 0.4}}/>
                 </div>
              </motion.div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t border-white/10 flex-shrink-0">
            <div className="relative">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Ask your assistant..."
                className="w-full h-12 bg-white/5 border border-white/20 rounded-full pl-12 pr-12 text-white placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-accent"
                disabled={isLoading}
              />
              <button className="absolute left-4 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-white">
                <Paperclip size={20} />
              </button>
              <button
                onClick={handleSend}
                disabled={isLoading || !input.trim()}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-white disabled:opacity-50 transition-colors"
              >
                <Send size={20} />
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}