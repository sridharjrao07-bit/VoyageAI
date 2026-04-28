import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import styles from './AuthModal.module.css'

const EMOJIS = ['🧳', '🌊', '⛰️', '🌴', '🎒', '✨', '🗺️', '🦋', '🌺', '🏔️']

export default function AuthModal({ onClose }) {
    const { login, register } = useAuth()
    const [tab, setTab] = useState('login')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [selectedEmoji, setSelectedEmoji] = useState('🧳')

    // Login form
    const [loginForm, setLoginForm] = useState({ username: '', password: '' })

    // Register form
    const [regForm, setRegForm] = useState({
        username: '', email: '', password: '', confirmPassword: '', display_name: ''
    })

    // Close on Escape
    useEffect(() => {
        const handler = (e) => e.key === 'Escape' && onClose()
        window.addEventListener('keydown', handler)
        return () => window.removeEventListener('keydown', handler)
    }, [onClose])

    const handleLogin = async (e) => {
        e.preventDefault()
        setError('')
        setLoading(true)
        try {
            await login(loginForm.username, loginForm.password)
            onClose()
        } catch (err) {
            setError(err?.response?.data?.detail || 'Invalid username or password')
        } finally {
            setLoading(false)
        }
    }

    const handleRegister = async (e) => {
        e.preventDefault()
        setError('')
        if (regForm.password !== regForm.confirmPassword) {
            setError('Passwords do not match')
            return
        }
        if (regForm.password.length < 6) {
            setError('Password must be at least 6 characters')
            return
        }
        setLoading(true)
        try {
            await register({
                username: regForm.username,
                email: regForm.email,
                password: regForm.password,
                display_name: regForm.display_name || regForm.username,
                avatar_emoji: selectedEmoji,
            })
            onClose()
        } catch (err) {
            setError(err?.response?.data?.detail || 'Registration failed')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className={styles.overlay} onClick={(e) => e.target === e.currentTarget && onClose()}>
            <div className={styles.modal}>
                {/* Header */}
                <div className={styles.header}>
                    <div className={styles.logo}>🌍 Allora</div>
                    <button className={styles.closeBtn} onClick={onClose} aria-label="Close">✕</button>
                </div>

                {/* Tabs */}
                <div className={styles.tabs}>
                    <button
                        id="auth-tab-login"
                        className={`${styles.tab} ${tab === 'login' ? styles.activeTab : ''}`}
                        onClick={() => { setTab('login'); setError('') }}
                    >
                        Sign In
                    </button>
                    <button
                        id="auth-tab-register"
                        className={`${styles.tab} ${tab === 'register' ? styles.activeTab : ''}`}
                        onClick={() => { setTab('register'); setError('') }}
                    >
                        Create Account
                    </button>
                </div>

                <div className={styles.body}>
                    {error && (
                        <div className={styles.errorBanner}>
                            <span>⚠️</span> {error}
                        </div>
                    )}

                    {/* ── Login Form ── */}
                    {tab === 'login' && (
                        <form className={styles.form} onSubmit={handleLogin}>
                            <div className={styles.field}>
                                <label htmlFor="login-username">Username or Email</label>
                                <input
                                    id="login-username"
                                    type="text"
                                    placeholder="alice_traveler"
                                    value={loginForm.username}
                                    onChange={e => setLoginForm(f => ({ ...f, username: e.target.value }))}
                                    required
                                    autoFocus
                                />
                            </div>
                            <div className={styles.field}>
                                <label htmlFor="login-password">Password</label>
                                <input
                                    id="login-password"
                                    type="password"
                                    placeholder="••••••••"
                                    value={loginForm.password}
                                    onChange={e => setLoginForm(f => ({ ...f, password: e.target.value }))}
                                    required
                                />
                            </div>
                            <button
                                id="auth-login-submit"
                                type="submit"
                                className={styles.submitBtn}
                                disabled={loading}
                            >
                                {loading ? <span className={styles.spinner} /> : '🚀 Sign In'}
                            </button>
                            <p className={styles.switchHint}>
                                Demo: <code>alice_traveler / demo1234</code>
                            </p>
                        </form>
                    )}

                    {/* ── Register Form ── */}
                    {tab === 'register' && (
                        <form className={styles.form} onSubmit={handleRegister}>
                            <div className={styles.emojiPicker}>
                                <label>Pick your travel avatar</label>
                                <div className={styles.emojiGrid}>
                                    {EMOJIS.map(e => (
                                        <button
                                            key={e}
                                            type="button"
                                            className={`${styles.emojiBtn} ${e === selectedEmoji ? styles.selectedEmoji : ''}`}
                                            onClick={() => setSelectedEmoji(e)}
                                        >
                                            {e}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div className={styles.row}>
                                <div className={styles.field}>
                                    <label htmlFor="reg-username">Username</label>
                                    <input
                                        id="reg-username"
                                        type="text"
                                        placeholder="alice_traveler"
                                        value={regForm.username}
                                        onChange={e => setRegForm(f => ({ ...f, username: e.target.value }))}
                                        required
                                    />
                                </div>
                                <div className={styles.field}>
                                    <label htmlFor="reg-name">Display Name</label>
                                    <input
                                        id="reg-name"
                                        type="text"
                                        placeholder="Alice Chen"
                                        value={regForm.display_name}
                                        onChange={e => setRegForm(f => ({ ...f, display_name: e.target.value }))}
                                    />
                                </div>
                            </div>

                            <div className={styles.field}>
                                <label htmlFor="reg-email">Email</label>
                                <input
                                    id="reg-email"
                                    type="email"
                                    placeholder="alice@example.com"
                                    value={regForm.email}
                                    onChange={e => setRegForm(f => ({ ...f, email: e.target.value }))}
                                    required
                                />
                            </div>

                            <div className={styles.row}>
                                <div className={styles.field}>
                                    <label htmlFor="reg-password">Password</label>
                                    <input
                                        id="reg-password"
                                        type="password"
                                        placeholder="Min 6 chars"
                                        value={regForm.password}
                                        onChange={e => setRegForm(f => ({ ...f, password: e.target.value }))}
                                        required
                                    />
                                </div>
                                <div className={styles.field}>
                                    <label htmlFor="reg-confirm">Confirm</label>
                                    <input
                                        id="reg-confirm"
                                        type="password"
                                        placeholder="••••••"
                                        value={regForm.confirmPassword}
                                        onChange={e => setRegForm(f => ({ ...f, confirmPassword: e.target.value }))}
                                        required
                                    />
                                </div>
                            </div>

                            <button
                                id="auth-register-submit"
                                type="submit"
                                className={styles.submitBtn}
                                disabled={loading}
                            >
                                {loading ? <span className={styles.spinner} /> : '✨ Create Account'}
                            </button>
                        </form>
                    )}
                </div>
            </div>
        </div>
    )
}
