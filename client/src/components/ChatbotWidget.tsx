import React, { useEffect, useRef, useState } from "react";
import { postData } from "../helper/apiCall";
import "../styles/chatbot.css";

type ChatRole = "user" | "assistant";

interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
}

interface ChatbotResponse {
  response: string;
  thread_id: string;
  phase_detected?: string;
  recommended_specialist?: string;
  user?: string;
}

const THREAD_STORAGE_KEY = "medhelp_chat_thread_id";
const CHAT_MESSAGES_KEY = "medhelp_chat_messages";

const createId = (): string => {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }

  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
};

const getOrCreateThreadId = (): string => {
  const existingThreadId = localStorage.getItem(THREAD_STORAGE_KEY);

  if (existingThreadId) {
    return existingThreadId;
  }

  const newThreadId = createId();
  localStorage.setItem(THREAD_STORAGE_KEY, newThreadId);
  return newThreadId;
};

const getStoredMessages = (): ChatMessage[] => {
  try {
    const raw = localStorage.getItem(CHAT_MESSAGES_KEY);
    if (!raw) return [];

    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
};

const ChatbotWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [threadId, setThreadId] = useState<string>("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState<string>("");
  const [isSending, setIsSending] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setThreadId(getOrCreateThreadId());
    setMessages(getStoredMessages());
  }, []);

  useEffect(() => {
    localStorage.setItem(CHAT_MESSAGES_KEY, JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    if (!isOpen) return;

    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [messages, isOpen, isSending]);

  const sendMessage = async (): Promise<void> => {
    const trimmed = input.trim();

    if (!trimmed || isSending) return;

    const token = localStorage.getItem("token");

    if (!token) {
      setError("Please log in to use MedHelp AI.");
      return;
    }

    const activeThreadId = threadId || getOrCreateThreadId();

    const userMessage: ChatMessage = {
      id: createId(),
      role: "user",
      content: trimmed,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setError("");
    setIsSending(true);

    try {
      const data = (await postData("/chatbot/chat", {
        message: trimmed,
        thread_id: activeThreadId,
      })) as ChatbotResponse;

      const assistantMessage: ChatMessage = {
        id: createId(),
        role: "assistant",
        content: data.response || "I could not generate a response.",
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const detail =
        err?.response?.data?.detail ||
        err?.message ||
        "Something went wrong while contacting MedHelp AI.";

      setError(detail);

      const assistantErrorMessage: ChatMessage = {
        id: createId(),
        role: "assistant",
        content:
          "Sorry, I could not process that message right now. Please try again.",
      };

      setMessages((prev) => [...prev, assistantErrorMessage]);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLTextAreaElement>
  ): void => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const startNewChat = (): void => {
    const newThreadId = createId();

    localStorage.setItem(THREAD_STORAGE_KEY, newThreadId);
    localStorage.removeItem(CHAT_MESSAGES_KEY);

    setThreadId(newThreadId);
    setMessages([]);
    setInput("");
    setError("");
  };

  const addSuggestion = (text: string): void => {
    setInput(text);
  };

  return (
    <>
      <button
        className="chatbot-toggle"
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-label="Open MedHelp AI chatbot"
      >
        {isOpen ? "×" : "AI"}
      </button>

      {isOpen && (
        <div className="chatbot-panel">
          <div className="chatbot-header">
            <div>
              <h3>MedHelp AI</h3>
              <p>Symptom guidance and doctor discovery</p>
            </div>

            <button
              className="chatbot-new-chat"
              type="button"
              onClick={startNewChat}
            >
              New
            </button>
          </div>

          <div className="chatbot-body">
            {messages.length === 0 && (
              <div className="chatbot-empty">
                <p>Hello, I’m MedHelp AI. I can help you understand which specialist may be appropriate and find available doctors.</p>

                <div className="chatbot-suggestions">
                  <button
                    type="button"
                    onClick={() =>
                      addSuggestion("I have chest pain and shortness of breath")
                    }
                  >
                    Chest pain
                  </button>

                  <button
                    type="button"
                    onClick={() =>
                      addSuggestion("I have itchy red rashes on my skin")
                    }
                  >
                    Skin rash
                  </button>

                  <button
                    type="button"
                    onClick={() =>
                      addSuggestion("Find me a dentist on Monday")
                    }
                  >
                    Find dentist
                  </button>
                </div>
              </div>
            )}

            {messages.map((message) => (
              <div
                key={message.id}
                className={`chatbot-message ${
                  message.role === "user"
                    ? "chatbot-message-user"
                    : "chatbot-message-assistant"
                }`}
              >
                <div className="chatbot-bubble">{message.content}</div>
              </div>
            ))}

            {isSending && (
              <div className="chatbot-message chatbot-message-assistant">
                <div className="chatbot-bubble chatbot-typing">
                  MedHelp AI is thinking...
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {error && <div className="chatbot-error">{error}</div>}

          <div className="chatbot-input-area">
            <textarea
              value={input}
              placeholder="Ask about symptoms or available doctors..."
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isSending}
              rows={2}
            />

            <button
              type="button"
              onClick={sendMessage}
              disabled={isSending || !input.trim()}
            >
              Send
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default ChatbotWidget;