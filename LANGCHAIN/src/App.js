import React, { useState, useEffect } from 'react';
import LessonStream from './LessonStream';
import ChatWindow from './ChatWindow';

function App() {
  const [topicInput, setTopicInput] = useState("");
  const [subtopic, setSubtopic] = useState("");
  const [lessonStarted, setLessonStarted] = useState(false);
  const [questionMode, setQuestionMode] = useState(false);
  const [resumeFlag, setResumeFlag] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);

  const handleStartLesson = () => {
    const t = topicInput.trim();
    if (!t) return;
    setSubtopic(t);
    setLessonStarted(true);
    setQuestionMode(false);
    setResumeFlag(false);
    setChatHistory([]);
  };

  const handleAskQuestion = () => setQuestionMode(true);

  const handleChatSend = async (message) => {
    const updated = [...chatHistory, { role:'student', text: message }];
    setChatHistory(updated);

    const res = await fetch('http://localhost:8000/chat', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ subtopic, history: updated, question: message }),
    });

    let botText = '';
    const reader = res.body.getReader();
    const dec = new TextDecoder();
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      botText += dec.decode(value);
    }
    const trimmed = botText.trim();

    if (trimmed === '[[RESUME_LESSON]]') {
      setChatHistory([]);
      setQuestionMode(false);
      setResumeFlag(true);
      return;
    }

    setChatHistory(h => [...h, { role:'bot', text: trimmed }]);
  };

  // reset resumeFlag immediately after it's used
  useEffect(() => {
    if (resumeFlag) setResumeFlag(false);
  }, [resumeFlag]);

  return (
    <div className="App" style={{ maxWidth:800, margin:'0 auto', padding:'1rem', position:'relative' }}>
      <h1 style={{ textAlign:'center' }}>📚 AI Science Teacher</h1>

      {!lessonStarted && (
        <div style={{ display:'flex', gap:'0.5rem', marginTop:'1rem' }}>
          <input
            type="text"
            placeholder="Enter a lesson topic (e.g., Photosynthesis)"
            value={topicInput}
            onChange={e => setTopicInput(e.target.value)}
            style={{ flex:1, padding:'0.5rem', fontSize:'1rem' }}
          />
          <button
            onClick={handleStartLesson}
            disabled={!topicInput.trim()}
            style={{ padding:'0.5rem 1rem', fontSize:'1rem' }}
          >Start Lesson</button>
        </div>
      )}

      {lessonStarted && (
        <> 
          <LessonStream
            subtopic={subtopic}
            onAskQuestion={handleAskQuestion}
            resumeFlag={resumeFlag}
          />

          {questionMode && (
            <div style={{
              position:'fixed', top:0, left:0, width:'100vw', height:'100vh',
              background:'rgba(255,255,255,0.97)', zIndex:9999,
              display:'flex', flexDirection:'column'
            }}>
              <div style={{ padding:'1rem', borderBottom:'1px solid #ccc' }}>
                <button
                  onClick={() => setQuestionMode(false)}
                  style={{ padding:'0.5rem 1rem', borderRadius:'4px', border:'1px solid #ccc', background:'#fff', cursor:'pointer' }}
                >← Back to Lesson</button>
              </div>
              <div style={{ flex:1, padding:'1rem', overflowY:'auto' }}>
                <ChatWindow history={chatHistory} onSend={handleChatSend} />
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default App;
