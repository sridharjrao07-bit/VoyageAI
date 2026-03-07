import { useState, useRef, useEffect } from 'react'
import { IconSend, IconBot, IconX, IconUser } from '../components/Icons'
import styles from './ChatPage.module.css'

const QUICK_PROMPTS = [
    "Plan a 7-day adventure trip to Patagonia under $3000",
    "Best romantic destinations in Europe for spring?",
    "I love diving and beaches — where should I go?",
    "What's the best time to visit Kyoto for the cherry blossoms?",
    "Suggest an eco-friendly trip with wildlife experiences",
    "Compare Bali and Thailand for a 2-week solo trip",
]

const WELCOME = {
    role: 'assistant',
    content: `Namaste! 🌏 I'm **Allora**, your AI travel concierge powered by **Grok AI**.

I can help you:
- 🗺️ Plan personalized itineraries for any destination
- 💰 Find trips that fit your budget exactly
- 🏔️ Discover off-the-beaten-path adventures
- 🌤️ Get the best travel seasons and practical tips
- 🤿 Match your interests (diving, trekking, culture, wellness…)

**What kind of trip are you dreaming of?**`,
    ts: Date.now(),
}

function MessageBubble({ msg }) {
    const isUser = msg.role === 'user'
    // Simple markdown-lite: bold, bullet points
    const format = (text) => {
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .split('\n')
            .map((line, i) => {
                if (line.startsWith('- ') || line.startsWith('• ')) {
                    return `<li key="${i}">${line.slice(2)}</li>`
                }
                return line ? `<p>${line}</p>` : '<br/>'
            })
            .join('')
            .replace(/<li>.*?<\/li>/gs, (m) => `<ul>${m}</ul>`)
    }

    return (
        <div className={`${styles.bubble} ${isUser ? styles.bubbleUser : styles.bubbleBot}`}>
            {!isUser && (
                <div className={styles.avatar}>
                    <IconBot size={16} />
                </div>
            )}
            <div className={styles.bubbleContent}>
                {isUser ? (
                    <p>{msg.content}</p>
                ) : (
                    <div dangerouslySetInnerHTML={{ __html: format(msg.content) }} />
                )}
                {msg.error && <p className={styles.errorNote}>⚠️ {msg.error}</p>}
            </div>
            {isUser && (
                <div className={`${styles.avatar} ${styles.avatarUser}`}>
                    <IconUser size={16} />
                </div>
            )}
        </div>
    )
}

export default function ChatPage() {
    const [messages, setMessages] = useState([WELCOME])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const bottomRef = useRef(null)
    const inputRef = useRef(null)

    // Get stored user profile for context
    const profile = (() => {
        try { return JSON.parse(sessionStorage.getItem('travelProfile') || 'null') } catch { return null }
    })()

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages, loading])

    const sendMessage = async (text) => {
        const userMsg = text || input.trim()
        if (!userMsg || loading) return

        setInput('')
        const newMessages = [...messages, { role: 'user', content: userMsg, ts: Date.now() }]
        setMessages(newMessages)
        setLoading(true)

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    messages: newMessages.slice(1).map(m => ({ role: m.role, content: m.content })), // skip welcome
                    user_profile: profile,
                }),
            })

            if (!response.ok) throw new Error(`HTTP ${response.status}`)

            const data = await response.json()
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: data.reply || data.content || 'Sorry, I couldn\'t generate a response.',
                ts: Date.now(),
                error: data.error,
            }])
        } catch (err) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'I seem to be having connection issues. Please make sure the backend is running and try again.',
                ts: Date.now(),
                error: err.message,
            }])
        } finally {
            setLoading(false)
            inputRef.current?.focus()
        }
    }

    const handleKey = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
    }

    const clearChat = () => setMessages([WELCOME])

    return (
        <div className={styles.page}>
            {/* Header */}
            <div className={styles.header}>
                <div className={styles.headerLeft}>
                    <div className={styles.botAvatar}>
                        <IconBot size={22} />
                    </div>
                    <div>
                        <h1 className={styles.headerTitle}>Allora AI Concierge</h1>
                        <div className={styles.headerStatus}>
                            <span className={styles.statusDot} />
                            <span>Powered by Grok AI · Travel Specialist</span>
                        </div>
                    </div>
                </div>
                <button className={styles.clearBtn} onClick={clearChat} title="Clear conversation">
                    <IconX size={16} /> Clear
                </button>
            </div>

            {/* Quick Prompts */}
            {messages.length === 1 && (
                <div className={styles.quickPrompts}>
                    {QUICK_PROMPTS.map(p => (
                        <button key={p} className={styles.quickBtn} onClick={() => sendMessage(p)}>
                            {p}
                        </button>
                    ))}
                </div>
            )}

            {/* Messages */}
            <div className={styles.messages}>
                {messages.map((msg, i) => <MessageBubble key={i} msg={msg} />)}
                {loading && (
                    <div className={`${styles.bubble} ${styles.bubbleBot}`}>
                        <div className={styles.avatar}><IconBot size={16} /></div>
                        <div className={styles.typingDots}>
                            <span /><span /><span />
                        </div>
                    </div>
                )}
                <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div className={styles.inputBar}>
                <div className={styles.inputWrap}>
                    <textarea
                        ref={inputRef}
                        className={styles.textarea}
                        placeholder="Ask about destinations, itineraries, budget tips…"
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyDown={handleKey}
                        rows={1}
                        disabled={loading}
                    />
                    <button
                        className={styles.sendBtn}
                        onClick={() => sendMessage()}
                        disabled={!input.trim() || loading}
                        title="Send (Enter)"
                    >
                        <IconSend size={18} />
                    </button>
                </div>
                <p className={styles.inputHint}>Press Enter to send · Shift+Enter for new line · Powered by xAI Grok</p>
            </div>
        </div>
    )
}
