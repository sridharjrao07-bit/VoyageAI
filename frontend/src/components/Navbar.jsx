import { Link, NavLink, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { IconMenu, IconX, IconGlobe, IconMessageCircle } from './Icons'
import styles from './Navbar.module.css'

const NAV_LINKS = [
    { to: '/', label: 'Home' },
    { to: '/explore', label: 'Explore' },
    { to: '/profile', label: 'Profile' },
    { to: '/recommendations', label: 'AI Picks' },
    { to: '/dashboard', label: 'Metrics' },
    { to: '/chat', label: '✨ AI Chat' },
]

export default function Navbar() {
    const [scrolled, setScrolled] = useState(false)
    const [menuOpen, setMenuOpen] = useState(false)
    const location = useLocation()

    useEffect(() => {
        const onScroll = () => setScrolled(window.scrollY > 20)
        window.addEventListener('scroll', onScroll, { passive: true })
        return () => window.removeEventListener('scroll', onScroll)
    }, [])

    useEffect(() => { setMenuOpen(false) }, [location])

    return (
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
                </div>
            )}
        </nav>
    )
}
