import { Link } from 'react-router-dom'
import { IconArrowRight, IconBrain, IconMapPin, IconShield, IconHeart, IconTrendingUp, IconGlobe, IconMap } from '../components/Icons'
import styles from './LandingPage.module.css'

const FEATURES = [
    { icon: <IconBrain />, title: 'Hybrid AI Engine', desc: 'Content-based + collaborative filtering combined with knowledge-based XAI explanations.' },
    { icon: <IconMapPin />, title: 'Real POI Data', desc: 'Live Points of Interest via OpenTripMap, hiking trails from Overpass/OpenStreetMap.' },
    { icon: <IconGlobe />, title: 'Wikidata RAG', desc: 'Every recommendation is grounded by real Wikidata facts — no hallucinations.' },
    { icon: <IconShield />, title: 'Hard Constraints', desc: 'Budget limits, wheelchair accessibility, and pet policies enforced automatically.' },
    { icon: <IconHeart />, title: 'Feedback Loop', desc: 'Thumbs up/down votes re-rank your recommendations in real time.' },
    { icon: <IconTrendingUp />, title: 'A/B Analytics', desc: 'Track Precision@10, Recall@10, MAP, and A/B test vs. popularity baseline.' },
]

const DESTINATIONS = [
    { name: 'Santorini', tag: 'Romance', emoji: '🌅', bg: '#ff6b6b' },
    { name: 'Patagonia', tag: 'Adventure', emoji: '🏔️', bg: '#4ecdc4' },
    { name: 'Kyoto', tag: 'Culture', emoji: '⛩️', bg: '#a29bfe' },
    { name: 'Maldives', tag: 'Luxury', emoji: '🏝️', bg: '#00b4d8' },
    { name: 'Safari Kenya', tag: 'Wildlife', emoji: '🦁', bg: '#f9a825' },
    { name: 'Cappadocia', tag: 'Unique', emoji: '🎈', bg: '#fd79a8' },
]

export default function LandingPage() {
    return (
        <div className={styles.page}>
            {/* ── Hero ── */}
            <section className={styles.hero}>
                <div className={styles.heroOrbs}>
                    <div className={styles.orb1} /><div className={styles.orb2} /><div className={styles.orb3} />
                </div>
                <div className={styles.heroContent}>
                    <div className={`${styles.heroBadge} animate-fade-up`}>
                        🤖 AI-Powered · Wikidata-Grounded · Real-Time
                    </div>
                    <h1 className={`${styles.heroTitle} animate-fade-up`} style={{ animationDelay: '0.1s' }}>
                        Discover Your<br /><span className="gradient-text">Perfect Journey</span>
                    </h1>
                    <p className={`${styles.heroSub} animate-fade-up`} style={{ animationDelay: '0.2s' }}>
                        A hybrid AI recommendation engine that goes beyond generic lists —
                        understanding your unique travel style, budget, and dreams
                        to craft hyper-personalized itineraries.
                    </p>
                    <div className={`${styles.heroCtas} animate-fade-up`} style={{ animationDelay: '0.3s' }}>
                        <Link to="/profile" className="btn-primary" style={{ fontSize: '1.05rem', padding: '16px 36px' }}>
                            Plan My Trip <IconArrowRight size={18} />
                        </Link>
                        <Link to="/explore" className="btn-secondary" style={{ fontSize: '1.05rem', padding: '16px 36px' }}>
                            Explore Destinations
                        </Link>
                    </div>
                    <div className={`${styles.heroStats} animate-fade-up`} style={{ animationDelay: '0.4s' }}>
                        <div className={styles.stat}><b>100+</b><span>Destinations</span></div>
                        <div className={styles.statDiv} />
                        <div className={styles.stat}><b>6 APIs</b><span>Real Data</span></div>
                        <div className={styles.statDiv} />
                        <div className={styles.stat}><b>Grok AI</b><span>Concierge</span></div>
                    </div>
                </div>

                <div className={styles.floatingChips}>
                    {DESTINATIONS.map((d, i) => (
                        <div key={d.name} className={styles.chip} style={{ animationDelay: `${i * 0.6}s`, '--chip-bg': d.bg }}>
                            <span className={styles.chipEmoji}>{d.emoji}</span>
                            <div>
                                <div className={styles.chipName}>{d.name}</div>
                                <div className={styles.chipTag}>{d.tag}</div>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {/* ── API Badges ── */}
            <section className={styles.apiBanner}>
                <div className={styles.apiBannerInner}>
                    <span className={styles.apiLabel}>Powered by</span>
                    {[
                        { name: 'OpenTripMap', color: '#6366f1' },
                        { name: 'Overpass OSM', color: '#10b981' },
                        { name: 'Wikidata RAG', color: '#f59e0b' },
                        { name: 'GeoNames', color: '#06b6d4' },
                        { name: 'OpenWeather', color: '#3b82f6' },
                        { name: 'Grok AI', color: '#8b5cf6' },
                    ].map(api => (
                        <span key={api.name} className={styles.apiBadge} style={{ '--api-color': api.color }}>
                            {api.name}
                        </span>
                    ))}
                </div>
            </section>

            {/* ── Features ── */}
            <section className="section">
                <div className="section-header">
                    <span className="section-label">Why Allora</span>
                    <h2 className="section-title">Built for the <span className="gradient-text">Modern Traveler</span></h2>
                    <p className="section-subtitle">
                        Production-grade AI architecture solving real problems: cold-start, data sparsity, latency, and explainability.
                    </p>
                </div>
                <div className={`${styles.featuresGrid} stagger`}>
                    {FEATURES.map(f => (
                        <div key={f.title} className={`glass-card ${styles.featureCard} animate-fade-up`}>
                            <div className={styles.featureIcon}>{f.icon}</div>
                            <h3 className={styles.featureTitle}>{f.title}</h3>
                            <p className={styles.featureDesc}>{f.desc}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* ── CTA ── */}
            <section className={styles.ctaSection}>
                <div className={styles.ctaCard}>
                    <div className={styles.ctaOrb} />
                    <h2 className={styles.ctaTitle}>Ready to experience<br />intelligent travel planning?</h2>
                    <p className={styles.ctaSub}>Set your preferences once. Our AI learns and adapts with every interaction.</p>
                    <Link to="/profile" className="btn-primary" style={{ fontSize: '1.05rem', padding: '16px 36px' }}>
                        Get Started Free <IconArrowRight size={18} />
                    </Link>
                </div>
            </section>
        </div>
    )
}
