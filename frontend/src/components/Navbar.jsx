import { Link, NavLink, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { IconMenu, IconX, IconGlobe } from './Icons'
import { useAuth } from '../contexts/AuthContext'
import AuthModal from './AuthModal'
import styles from './Navbar.module.css'

const NAV_LINKS = [
    { to: '/', label: 'Home' },
    { to: '/explore', label: 'Explore' },
    { to: '/vibe', label: '🎯 Vibe' },
    { to: '/groups', label: '👥 Groups' },
    { to: '/profile', label: 'Profile' },
    { to: '/recommendations', label: 'AI Picks' },
    { to: '/dashboard', label: 'Metrics' },
    { to: '/chat', label: '✨ AI Chat' },
]

export default function Navbar() {
    const [scrolled, setScrolled] = useState(false)
    const [menuOpen, setMenuOpen] = useState(false)
    const [showAuthModal, setShowAuthModal] = useState(false)
    const location = useLocation()
    const { user, logout } = useAuth()

    useEffect(() => {
        const onScroll = () => setScrolled(window.scrollY > 20)
        window.addEventListener('scroll', onScroll, { passive: true })
        return () => window.removeEventListener('scroll', onScroll)
    }, [])

    useEffect(() => { setMenuOpen(false) }, [location])

    return (
        <>
            {showAuthModal && <AuthModal onClose={() => setShowAuthModal(false)} />}

            <nav className={`${styles.nav} ${scrolled ? styles.scrolled : ''}`}>
                <div className={styles.inner}>
                    <Link to="/" className={styles.logo}>
                        <IconGlobe size={22} className={styles.logoIcon} />
                        <span>Allora</span>
                        <span className={styles.logoTag}>AI Tourism</span>
                    </Link>

                    {/* Desktop Links */}
                    <div className={styles.links}>
                        {NAV_LINKS.map(l => (
                            <NavLink
                                key={l.to}
                                to={l.to}
                                end={l.to === '/'}
                                className={({ isActive }) => `${styles.link} ${isActive ? styles.active : ''}`}
                            >
                                {l.label}
                            </NavLink>
                        ))}
                    </div>

                    {/* Auth area */}
                    <div className={styles.authArea}>
                        {user ? (
                            <div className={styles.userMenu}>
                                <span className={styles.userAvatar} title={user.display_name}>
                                    {user.avatar_emoji}
                                </span>
                                <button
                                    id="navbar-logout-btn"
                                    className={styles.logoutBtn}
                                    onClick={logout}
                                >
                                    Sign Out
                                </button>
                            </div>
                        ) : (
                            <button
                                id="navbar-login-btn"
                                className={styles.loginBtn}
                                onClick={() => setShowAuthModal(true)}
                            >
                                Sign In
                            </button>
                        )}
                    </div>

                    {/* Mobile burger */}
                    <button
                        className={styles.burger}
                        onClick={() => setMenuOpen(o => !o)}
                        aria-label="Toggle menu"
                    >
                        {menuOpen ? <IconX size={22} /> : <IconMenu size={22} />}
                    </button>
                </div>

                {/* Mobile drawer */}
                {menuOpen && (
                    <div className={styles.drawer}>
                        {NAV_LINKS.map(l => (
                            <NavLink
                                key={l.to}
                                to={l.to}
                                end={l.to === '/'}
                                className={({ isActive }) => `${styles.drawerLink} ${isActive ? styles.active : ''}`}
                            >
                                {l.label}
                            </NavLink>
                        ))}
                        <div className={styles.drawerAuth}>
                            {user ? (
                                <button className={styles.logoutBtn} onClick={logout}>
                                    {user.avatar_emoji} Sign Out
                                </button>
                            ) : (
                                <button className={styles.loginBtn} onClick={() => { setShowAuthModal(true); setMenuOpen(false) }}>
                                    Sign In
                                </button>
                            )}
                        </div>
                    </div>
                )}
            </nav>
        </>
    )
}
