import React, { useState, useRef, useEffect } from 'react';

export default function ChatWindow({
    history,
    onSend,
    width = '1200px',     // default width
    fontSize = '26px'    // default font size
    }) {
    const [input, setInput] = useState("");
    const bottomRef = useRef(null);

    const handleSend = () => {
        const trimmed = input.trim();
        if (!trimmed) return;
        onSend(trimmed);
        setInput("");
    };

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [history]);

    return (
        <div
        className="chat-window"
        style={{
            display: 'flex',
            flexDirection: 'column',
            height: '70vh',
            width,               // ← set the chat box width here
            fontSize,            // ← set the base font size here
            border: '1px solid #ccc',
            borderRadius: '8px',
            padding: '1em',
            boxSizing: 'border-box'
        }}
        >
        <div
            className="messages"
            style={{
            flex: 1,
            overflowY: 'auto',
            marginBottom: '1em',
            fontSize: 'inherit'   // inherit from parent
            }}
        >
            {history.map((msg, i) => (
            <div
                key={i}
                style={{
                margin: '0.5em 0',
                textAlign: msg.role === 'student' ? 'right' : 'left',
                lineHeight: 1.4,
                fontSize: 'inherit'
                }}
            >
                <strong style={{ fontSize: 'inherit' }}>
                {msg.role === 'student' ? 'You' : 'Teacher'}:
                </strong>{" "}
                <span style={{ fontSize: 'inherit' }}>
                {msg.text}
                </span>
            </div>
            ))}
            <div ref={bottomRef} />
        </div>

        <div className="input-box" style={{ display: 'flex' }}>
            <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Type your question..."
            style={{
                flex: 1,
                padding: '0.5em',
                borderRadius: '4px',
                border: '1px solid #ccc',
                fontSize: 'inherit'   // inherit font size
            }}
            />
            <button
            onClick={handleSend}
            style={{
                marginLeft: '0.5em',
                padding: '0.5em 1em',
                borderRadius: '4px',
                fontSize: 'inherit'   // inherit font size
            }}
            >
            Send
            </button>
        </div>
        </div>
    );
    }
