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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() === "") return;

    // Add user message
    const newUserMessage: Message = { id: Date.now().toString(), role: 'user', content: input };
    setMessages((prev) => [...prev, newUserMessage]);
    setInput('');

    // SSE Streaming Logic
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/chat/stream`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ input: newUserMessage.content }),
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
          className="fixed bottom-8 right-8 w-[400px] h-[600px] flex flex-col bg-white/70 backdrop-blur-xl border border-gray-100 rounded-3xl shadow-lg p-6 z-50"
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">AI Assistant</h2>
              <p className="text-gray-600">Ask me to schedule, reschedule, or find events</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600"></div>
            <button onClick={() => setIsOpen(false)} className="text-neutral-400 hover:text-white transition-colors">
              <X size={20} />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto mb-4 space-y-4">
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div 
                  className={`max-w-xs lg:max-w-md px-4 py-2 rounded-2xl ${message.role === 'user' ? 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white rounded-br-none' : 'bg-gray-100 text-gray-700 rounded-bl-none'}`}
                >
                  {message.content}
                </div>
                {message.role === 'assistant' && <Bot className="w-6 h-6 text-primary flex-shrink-0 mt-1" />}
                {message.role === 'user' && <User className="w-6 h-6 text-neutral-300 flex-shrink-0 mt-1" />}
              </motion.div>
            ))}
            {isLoading && (
              <motion.div initial={{opacity: 0}} animate={{opacity: 1}} className="flex items-start gap-3 justify-start">
                 <Bot className="w-6 h-6 text-primary flex-shrink-0 mt-1" />
                 <div className="max-w-xs lg:max-w-md px-4 py-2 rounded-2xl bg-gray-100 text-gray-700 rounded-bl-none flex items-center gap-2">
                    <motion.div className="w-2 h-2 bg-neutral-400 rounded-full" animate={{y: [0, -4, 0]}} transition={{duration: 1, repeat: Infinity}}/>
                    <motion.div className="w-2 h-2 bg-neutral-400 rounded-full" animate={{y: [0, -4, 0]}} transition={{duration: 1, repeat: Infinity, delay: 0.2}}/>
                    <motion.div className="w-2 h-2 bg-neutral-400 rounded-full" animate={{y: [0, -4, 0]}} transition={{duration: 1, repeat: Infinity, delay: 0.4}}/>
                 </div>
              </motion.div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form onSubmit={handleSubmit} className="flex items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSubmit(e)}
              placeholder="Type a message..."
              className="flex-1 px-4 py-3 bg-gray-100 rounded-l-2xl focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-transparent"
              disabled={isLoading}
            />
            <button 
              type="submit"
              className="px-4 py-3 bg-gradient-to-br from-indigo-500 to-purple-600 text-white rounded-r-2xl hover:from-indigo-600 hover:to-purple-700 transition-all duration-300 disabled:opacity-50"
              disabled={isLoading || !input.trim()}
            >
              Send
            </button>
            <button className="absolute left-4 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-white">
              <Paperclip size={20} />
            </button>
          </form>
        </motion.div>
      )}
    </AnimatePresence>
  );
}