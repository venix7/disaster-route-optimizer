import { useEffect, useRef, useState } from "react";
import { chatWithAssistant } from "../services/api";


const INITIAL_MESSAGE = {
  role: "assistant",
  content:
    "Ask me to explain the displayed route, compare shelters, check the flood, or run the existing routing tools for your selected map locations.",
};


function AssistantChat({ context, onAction }) {
  const [messages, setMessages] = useState([INITIAL_MESSAGE]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async (messageText) => {
    const cleanMessage = messageText.trim();

    if (!cleanMessage || loading) {
      return;
    }

    const history = messages
      .slice(1)
      .slice(-12)
      .map(({ role, content }) => ({
        role,
        content: content.slice(0, 4000),
      }));

    setMessages((currentMessages) => [
      ...currentMessages,
      { role: "user", content: cleanMessage },
    ]);
    setInput("");
    setLoading(true);

    try {
      const result = await chatWithAssistant(cleanMessage, context, history);

      for (const action of result.actions || []) {
        onAction?.(action);
      }

      setMessages((currentMessages) => [
        ...currentMessages,
        {
          role: "assistant",
          content: result.reply,
          toolsUsed: result.tools_used || [],
        },
      ]);
    } catch (error) {
      const detail = error.response?.data?.detail;

      setMessages((currentMessages) => [
        ...currentMessages,
        {
          role: "assistant",
          content:
            detail ||
            "I could not reach the assistant service. The map controls and deterministic routing tools are still available.",
          isError: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    sendMessage(input);
  };

  const suggestions = [
    "Why was this route selected?",
    "How is the flood affecting roads?",
    "Which shelter should I use?",
  ];

  return (
    <section className="assistant-panel" aria-labelledby="assistant-title">
      <div className="assistant-header">
        <div className="assistant-title-group">
          <div className="assistant-icon">✦</div>
          <div>
            <p className="card-label">GROQ + DETERMINISTIC TOOLS</p>
            <h2 id="assistant-title">Evacuation Assistant</h2>
          </div>
        </div>

        <span className="assistant-context-status">
          {context.route
            ? "ROUTE CONTEXT READY"
            : context.start_location
              ? "LOCATION CONTEXT READY"
              : "SELECT MAP LOCATION"}
        </span>
      </div>

      <div className="assistant-layout">
        <div className="assistant-suggestions" aria-label="Suggested questions">
          <p>Suggested questions</p>

          {suggestions.map((suggestion) => (
            <button
              type="button"
              className="suggestion-button"
              key={suggestion}
              onClick={() => sendMessage(suggestion)}
              disabled={loading}
            >
              {suggestion}
            </button>
          ))}

          <div className="assistant-safety-note">
            Routes and hazard counts come from the backend algorithms. Groq only chooses tools and explains their results.
          </div>
        </div>

        <div className="assistant-chat">
          <div className="assistant-messages" aria-live="polite">
            {messages.map((message, index) => (
              <div
                className={`assistant-message ${message.role} ${message.isError ? "message-error" : ""}`}
                key={`${message.role}-${index}`}
              >
                <span className="message-role">
                  {message.role === "user" ? "YOU" : "ASSISTANT"}
                </span>
                <p>{message.content}</p>

                {message.toolsUsed?.length > 0 && (
                  <span className="tool-trace">
                    VERIFIED VIA {message.toolsUsed.join(", ")}
                  </span>
                )}
              </div>
            ))}

            {loading && (
              <div className="assistant-message assistant assistant-thinking">
                <span className="message-role">ASSISTANT</span>
                <p>Checking the live evacuation tools…</p>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          <form className="assistant-form" onSubmit={handleSubmit}>
            <label htmlFor="assistant-input" className="visually-hidden">
              Ask the evacuation assistant
            </label>
            <textarea
              id="assistant-input"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  sendMessage(input);
                }
              }}
              placeholder="Ask about the current route, shelter, or flood…"
              rows="2"
              maxLength="2000"
              disabled={loading}
            />
            <button type="submit" disabled={loading || !input.trim()}>
              {loading ? "Checking…" : "Ask Assistant"}
            </button>
          </form>
        </div>
      </div>
    </section>
  );
}


export default AssistantChat;
