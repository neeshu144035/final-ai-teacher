import React, { useEffect, useState, useRef, useCallback } from 'react';

const DISPLAY_DELAY_MS = 2000;

const LessonStream = ({ subtopic, onAskQuestion, resumeFlag, onResumeComplete }) => {
    const [elements, setElements] = useState([]);
    const [isFinished, setIsFinished] = useState(false);

    const socketRef     = useRef(null);
    const queueRef      = useRef([]);
    const displayingRef = useRef(false);
    const pausedRef     = useRef(false);

    const lastHaltRef    = useRef('');
    const seenImagesRef  = useRef(new Set());
    const seenVideosRef  = useRef(new Set());
    const seenWarningRef = useRef(false);

    const parseSentence = useCallback(sentence => {
        const parts = sentence.split(/(<<image:[^>]+>>|<<video:[^>]+>>)/g);
        return parts.flatMap(seg => {
            if (seg.includes("outside the syllabus")) {
                if (seenWarningRef.current) return [];
                seenWarningRef.current = true;
                return [
                    <p key="warn" style={{ color:'#a00', fontWeight:'bold', textAlign:'center' }}>
                        {seg.trim()}
                    </p>
                ];
            }
            const img = seg.match(/<<image:\s*([^\s>]+)\s*>>/i);
            if (img) {
                const name = img[1];
                if (seenImagesRef.current.has(name)) return [];
                seenImagesRef.current.add(name);
                return [
                    <div key={`img-${name}`} style={{ textAlign:'center', margin:'1em 0' }}>
                        <img
                            src={`http://localhost:8000/images/${name}`}
                            alt={name}
                            style={{ maxWidth:'100%', border:'1px solid #ccc', borderRadius:'4px' }}
                        />
                        <div style={{ fontSize:'0.9em', color:'#555', marginTop:'0.3em' }}>{name}</div>
                    </div>
                ];
            }
            const vid = seg.match(/<<video:\s*([^\s>]+)\s*>>/);
            if (vid) {
                const id = vid[1];
                if (seenVideosRef.current.has(id)) return [];
                seenVideosRef.current.add(id);
                return [
                    <div key={`vid-${id}`} style={{ margin:'1em 0' }}>
                        <iframe
                            width="560" height="315"
                            src={`https://www.youtube.com/embed/${id}`}
                            title="Lesson video"
                            frameBorder="0"
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                            allowFullScreen
                        />
                    </div>
                ];
            }
            if (seg && seg.trim()) {
                return [<p key={`txt-${Math.random().toString(36).substr(2,9)}`}>{seg}</p>];
            }
            return [];
        });
    }, []);

    const displayNext = useCallback(() => {
        if (pausedRef.current || queueRef.current.length === 0) {
            displayingRef.current = false;
            return;
        }
        displayingRef.current = true;
        const sentence = queueRef.current.shift();
        lastHaltRef.current = sentence; // record every shown sentence
        const nodes = parseSentence(sentence);
        setElements(prev => [...prev, ...nodes]);
        setTimeout(displayNext, DISPLAY_DELAY_MS);
    }, [parseSentence]);

    const startSocket = useCallback((initial = false) => {
        pausedRef.current = false;

        if (initial) {
            seenImagesRef.current.clear();
            seenVideosRef.current.clear();
            seenWarningRef.current = false;
            setElements([]);
            setIsFinished(false);
            queueRef.current = [];
            displayingRef.current = false;
            lastHaltRef.current = '';
        }

        const socket = new WebSocket('ws://localhost:8000/ws/lesson');
        socketRef.current = socket;

        socket.onopen = () => {
            const payload = initial
                ? { subtopic }
                : {
                    subtopic,
                    resumeFrom: lastHaltRef.current || '(resume point unknown)',
                };
            console.log('[LessonStream] socket.onopen — initial?', initial, 'payload=', payload);

            socket.send(JSON.stringify(payload));
        };

        socket.onmessage = ({ data }) => {
            if (data === '[DONE]') {
                setIsFinished(true);
                if (onResumeComplete) onResumeComplete();
                socket.close();
                return;
            }
            if (pausedRef.current) return;

            data
                .split('[[HALT]]')
                .map(s => s.trim())
                .filter(Boolean)
                .forEach(s => queueRef.current.push(s));

            if (!displayingRef.current) displayNext();
        };

        socket.onerror = err => console.error('WebSocket error', err);
        socket.onclose = () => { socketRef.current = null; };
    }, [subtopic, displayNext, onResumeComplete]);

    useEffect(() => {
        startSocket(true);
        return () => {
            if (socketRef.current?.readyState === WebSocket.OPEN) {
                socketRef.current.close();
            }
        };
    }, [subtopic,startSocket]);

    useEffect(() => {
        if (resumeFlag) {
            startSocket(false);
        }
    }, [resumeFlag, startSocket]);

    const handlePause = () => {
        console.log('[LessonStream] pausing at:', lastHaltRef.current);
        pausedRef.current = true;
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.close();
        }
        onAskQuestion();
    };

    return (
        <div className="lesson-stream" style={{ position: 'relative' }}>
            <button
                onClick={handlePause}
                style={{ position:'absolute', top:'1em', right:'1em', zIndex:10 }}
            >
                Ask Question
            </button>
            {elements}
            {isFinished && (
                <div style={{
                    marginTop:'2em',
                    padding:'1em',
                    borderTop:'1px solid #ccc',
                    textAlign:'center'
                }}>
                    <h2>🎉 Lesson Complete!</h2>
                    <p>Key takeaways above!</p>
                </div>
            )}
        </div>
    );
};

export default LessonStream;
