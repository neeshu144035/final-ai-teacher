import React, { useState } from 'react';

const QuestionBox = ({ onSend, onCancel }) => {
    const [question, setQuestion] = useState("");

    const handleSend = () => {
        if (!question.trim()) return;
        onSend(question);
        setQuestion("");
    };

    return (
        <div className="question-box">
        <h3>Ask your question</h3>
        <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Type your question..."
            onKeyDown={(e) => {
            if (e.key === "Enter") handleSend();
            }}
        />
        <button onClick={handleSend}>Submit</button>
        <button onClick={onCancel}>Cancel</button>
        </div>
    );
    };

    export default QuestionBox;
