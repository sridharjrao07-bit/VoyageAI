import { useState, useEffect } from 'react'
import { getPerformance } from '../api/tourismApi'
import styles from './DashboardPage.module.css'

function MetricBar({ label, value, max = 1, color }) {
    const pct = Math.min((value / max) * 100, 100)
    return (
        <div className={styles.barRow}>
            <div className={styles.barLabel}>{label}</div>
            <div className={styles.barTrack}>
                <div
                    className={styles.barFill}
                    style={{ width: `${pct}%`, background: color }}
                />
            </div>
            <div className={styles.barValue} style={{ color }}>
                {value < 1 && value > 0 ? `${(value * 100).toFixed(1)}%` : value.toFixed(3)}
            </div>
        </div>
    )
}

function MetricCard({ icon, label, value, sub, color }) {
    return (
        <div className={styles.metricCard}>
            <div className={styles.metricIcon} style={{ color, background: `${color}1a` }}>{icon}</div>
            <div className={styles.metricVal} style={{ color }}>{value}</div>
            <div className={styles.metricLabel}>{label}</div>
            {sub && <div className={styles.metricSub}>{sub}</div>}
        </div>
    )
}

function ComparisonBar({ labelA, labelB, valA, valB }) {
    const max = Math.max(valA, valB, 0.01)
    return (
        <div className={styles.comparison}>
            <div className={styles.compRow}>
                <span className={styles.compLabel} style={{ color: 'var(--accent-1)' }}>{labelA}</span>
                <div className={styles.barTrack}>
                    <div className={styles.barFill} style={{ width: `${(valA / max) * 100}%`, background: 'var(--accent-1)' }} />
                </div>
                <span className={styles.compVal} style={{ color: 'var(--accent-1)' }}>{(valA * 100).toFixed(1)}%</span>
            </div>
            <div className={styles.compRow}>
                <span className={styles.compLabel} style={{ color: 'var(--text-muted)' }}>{labelB}</span>
                <div className={styles.barTrack}>
                    <div className={styles.barFill} style={{ width: `${(valB / max) * 100}%`, background: 'rgba(100,116,139,0.6)' }} />
                </div>
                <span className={styles.compVal} style={{ color: 'var(--text-muted)' }}>{(valB * 100).toFixed(1)}%</span>
            </div>
        </div>
    )
}

export default function DashboardPage() {
    const [metrics, setMetrics] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(false)

    const load = () => {
        setLoading(true)
        setError(false)
        getPerformance()
            .then(m => { setMetrics(m); setLoading(false) })
            .catch(() => { setError(true); setLoading(false) })
    }

    useEffect(() => { load() }, [])

    return (
        <div className="page-wrapper">
            <div className="section">
                <div className="section-header">
                    <span className="section-label">Performance Analytics</span>
                    <h1 className="section-title">
                        AI <span className="gradient-text">Metrics Dashboard</span>
                    </h1>
                    <p className="section-subtitle">
                        Live evaluation of Precision@10, Recall@10, MAP, and A/B test vs. popularity baseline
                    </p>
                </div>

                {loading && (
                    <div className="spinner-container">
                        <div className="spinner" />
                        <p style={{ color: 'var(--text-secondary)', marginTop: 16 }}>Computing metrics across users…</p>
                    </div>
                )}

                {error && (
                    <div className="empty-state">
                        <div className="empty-state-icon">⚠️</div>
                        <h3>Backend Not Connected</h3>
                        <p>Make sure the FastAPI backend is running on port 8000.</p>
                        <button className="btn-primary" onClick={load}>↺ Retry</button>
                    </div>
                )}

                {!loading && !error && metrics && (
                    <>
                        {/* Metric Cards */}
                        <div className={`${styles.metricsRow} stagger`}>
                            <MetricCard
                                icon="🎯"
                                label="Precision@10"
                                value={`${(metrics.precision_at_10 * 100).toFixed(1)}%`}
                                sub="Top-10 relevance"
                                color="var(--accent-1)"
                            />
                            <MetricCard
                                icon="📈"
                                label="Recall@10"
                                value={`${(metrics.recall_at_10 * 100).toFixed(1)}%`}
                                sub="Relevant items surfaced"
                                color="var(--accent-3)"
                            />
                            <MetricCard
                                icon="🏆"
                                label="MAP Score"
                                value={metrics.map_score.toFixed(3)}
                                sub="Mean Average Precision"
                                color="var(--accent-gold)"
                            />
                            <MetricCard
                                icon="⚡"
                                label="A/B Lift"
                                value={`+${metrics.ab_test?.improvement_pct?.toFixed(1)}%`}
                                sub="vs. popularity baseline"
                                color="var(--accent-green)"
                            />
                        </div>

                        {/* Charts Section */}
                        <div className={styles.chartsGrid}>
                            {/* Metric Bars */}
                            <div className={styles.chartCard}>
                                <h3 className={styles.chartTitle}>Core Retrieval Metrics</h3>
                                <p className={styles.chartSub}>Evaluated across {metrics.users_evaluated} test users at K={metrics.k}</p>
                                <div className={styles.barsContainer}>
                                    <MetricBar label="Precision@10" value={metrics.precision_at_10} color="var(--accent-1)" />
                                    <MetricBar label="Recall@10" value={metrics.recall_at_10} color="var(--accent-3)" />
                                    <MetricBar label="MAP Score" value={metrics.map_score} color="var(--accent-gold)" />
                                </div>
                            </div>

                            {/* A/B Test Comparison */}
                            <div className={styles.chartCard}>
                                <h3 className={styles.chartTitle}>A/B Test: AI vs. Baseline</h3>
                                <p className={styles.chartSub}>Precision@10 — Hybrid AI engine vs. popularity baseline</p>
                                <ComparisonBar
                                    labelA="Hybrid AI Engine"
                                    labelB="Popularity Baseline"
                                    valA={metrics.ab_test?.hybrid_precision ?? 0}
                                    valB={metrics.ab_test?.popularity_precision ?? 0}
                                />
                                <div className={styles.abSummary}>
                                    <span className={styles.abWin}>
                                        Hybrid AI wins by <b style={{ color: 'var(--accent-green)' }}>
                                            +{metrics.ab_test?.improvement_pct?.toFixed(1)}%
                                        </b> Precision
                                    </span>
                                </div>
                            </div>

                            {/* MAP Gauge (pure CSS) */}
                            <div className={`${styles.chartCard} ${styles.gaugeCard}`}>
                                <h3 className={styles.chartTitle}>MAP Score Gauge</h3>
                                <p className={styles.chartSub}>Mean Average Precision — ranking quality</p>
                                <div className={styles.gaugeWrap}>
                                    <div className={styles.gaugeBg}>
                                        <div
                                            className={styles.gaugeFill}
                                            style={{ '--gauge-pct': `${Math.round(metrics.map_score * 100)}%` }}
                                        />
                                        <div className={styles.gaugeCenter}>
                                            <b>{metrics.map_score.toFixed(3)}</b>
                                            <span>MAP</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* API Status Cards */}
                        <div className={styles.infoGrid}>
                            {[
                                { icon: '🗺️', term: 'OpenTripMap', def: 'Powers POI discovery, photos & enriched destination metadata.' },
                                { icon: '🏔️', term: 'Overpass OSM', def: 'Real hiking trails, peaks, viewpoints, and campsites near any destination.' },
                                { icon: '📚', term: 'Wikidata RAG', def: '"Why recommended" explanations grounded in verified Wikidata facts.' },
                                { icon: '🌐', term: 'GeoNames', def: 'Geographic enrichment: elevation, population, timezone, admin region.' },
                                { icon: '🌤️', term: 'OpenWeatherMap', def: 'Current weather + 5-day forecast for any destination worldwide.' },
                                { icon: '🤖', term: 'Hybrid AI Engine', def: 'Content-Based + Collaborative + Popularity, blended with XAI explanations.' },
                            ].map(({ icon, term, def }) => (
                                <div key={term} className={styles.infoCard}>
                                    <div className={styles.infoIcon}>{icon}</div>
                                    <h4>{term}</h4>
                                    <p>{def}</p>
                                </div>
                            ))}
                        </div>
                    </>
                )}
            </div>
        </div>
    )
}
