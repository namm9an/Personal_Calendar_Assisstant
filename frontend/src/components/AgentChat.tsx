"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";

interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

interface AgentStep {
  step_number: number;
  message: string;
  tool_invoked: string | null;
  tool_input: any | null;
  tool_output: any | null;
  timestamp: string;
}

interface AgentResponse {
  final_intent: string;
  final_output: Record<string, any>;
  summary: string;
  steps: AgentStep[];
  timestamp: string;
}

interface AgentError {
  error: string;
  details: Record<string, any> | null;
  timestamp: string;
}

export default function AgentChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "system", content: "Hi! I'm your calendar assistant. How can I help you today?" },
  ]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [steps, setSteps] = useState<AgentStep[]>([]);
  const [provider, setProvider] = useState<"google" | "microsoft">("google");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;

    const userMessage = input.trim();
    setInput("");
    
    // Add user message to chat
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    
    // Show typing indicator
    setIsStreaming(true);
    setSteps([]);

    try {
      // Make API call to backend agent
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/agent/calendar`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ text: userMessage, provider }),
          credentials: "include",
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error("ReadableStream not supported");
      }

      // Process the stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      let finalResponse: AgentResponse | null = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        // Convert Uint8Array to string and append to buffer
        buffer += decoder.decode(value, { stream: true });

        // Process complete SSE events in buffer
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || ""; // Keep last incomplete chunk in buffer

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const jsonStr = line.slice(6); // Remove "data: " prefix
            try {
              const data = JSON.parse(jsonStr);
              
              // Check if it's a step or final response
              if (data.step_number !== undefined) {
                // It's an agent step
                setSteps((prev) => [...prev, data]);
                
                // Update message for tool invocation
                if (data.tool_invoked) {
                  setMessages((prev) => [
                    ...prev,
                    {
                      role: "assistant",
                      content: `Using tool: ${data.tool_invoked}\n${data.message}`,
                    },
                  ]);
                }
              } else if (data.final_intent !== undefined) {
                // It's the final response
                finalResponse = data;
              } else if (data.error !== undefined) {
                // It's an error
                const error = data as AgentError;
                setMessages((prev) => [
                  ...prev,
                  { role: "assistant", content: `Error: ${error.error}` },
                ]);
              }
            } catch (err) {
              console.error("Failed to parse SSE data:", err);
            }
          }
        }
      }

      // Add final response message
      if (finalResponse) {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: finalResponse?.summary || "Task completed" },
        ]);
      }
    } catch (err) {
      console.error("Error in agent chat:", err);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, I encountered an error. Please try again." },
      ]);
    } finally {
      setIsStreaming(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="h-full flex flex-col bg-gray-50 rounded-lg shadow">
      <div className="flex justify-between items-center p-4 border-b">
        <h2 className="font-semibold text-lg">Calendar Assistant</h2>
        <div>
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value as "google" | "microsoft")}
            className="p-2 border rounded text-sm"
            disabled={isStreaming}
          >
            <option value="google">Google Calendar</option>
            <option value="microsoft">Microsoft Calendar</option>
          </select>
        </div>
      </div>

      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${
              message.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[80%] px-4 py-2 rounded-lg ${
                message.role === "user"
                  ? "bg-blue-500 text-white rounded-br-none"
                  : message.role === "system"
                  ? "bg-gray-200 text-gray-800 rounded-bl-none"
                  : "bg-white border text-gray-800 rounded-bl-none"
              }`}
            >
              <pre className="whitespace-pre-wrap font-sans">{message.content}</pre>
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {isStreaming && (
          <div className="flex justify-start">
            <div className="bg-white border px-4 py-2 rounded-lg rounded-bl-none">
              <div className="flex space-x-2 items-center">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0.4s" }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="border-t p-4">
        <div className="flex">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            className="flex-1 p-2 border rounded-l-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={2}
            disabled={isStreaming}
          ></textarea>
          <button
            onClick={handleSend}
            disabled={!input.trim() || isStreaming}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-r-lg disabled:bg-blue-300 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
} 