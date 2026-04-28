import { useState } from 'react'
import styles from './RecommendationResultsPanel.module.css'

const COUNTRY_FLAGS = {
    Indonesia: '🇮🇩', Portugal: '🇵🇹', Japan: '🇯🇵', Mexico: '🇲🇽',
    Thailand: '🇹🇭', Spain: '🇪🇸', 'New Zealand': '🇳🇿', Morocco: '🇲🇦',
    Greece: '🇬🇷', Colombia: '🇨🇴', Iceland: '🇮🇸', Vietnam: '🇻🇳',
    UAE: '🇦🇪', Nepal: '🇳🇵', 'South Africa': '🇿🇦', Georgia: '🇬🇪',
    Peru: '🇵🇪', Maldives: '🇲🇻', Croatia: '🇭🇷', 'Sri Lanka': '🇱🇰',
}

function ScoreBar({ score, tier }) {
    const pct = Math.round(score * 100)
    const colorClass = tier === 'green' ? styles.barGreen : tier === 'amber' ? styles.barAmber : styles.barRed
    return (
        <div className={styles.scoreBarWrapper}>
            <div className={styles.scoreBarBg}>
                <div
                    className={`${styles.scoreBarFill} ${colorClass}`}
                    style={{ width: `${pct}%` }}
                />
            </div>
            <span className={`${styles.scoreBarPct} ${colorClass}`}>{pct}%</span>
        </div>
    )
}

function DestinationCard({ dest, rank, isExpanded, onClick }) {
    const flag = COUNTRY_FLAGS[dest.country] || '🌍'
    const isBest = rank === 1
    const isSolo = dest.fairness_score === null || dest.fairness_score === undefined
    const fairnessPct = isSolo ? null : Math.round(dest.fairness_score * 100)
    const avgPct = Math.round((dest.average_score ?? 0) * 100)
    const maximinPct = isSolo ? null : Math.round((dest.maximin_score ?? 0) * 100)
    const tags = Array.isArray(dest.activity_tags)
        ? dest.activity_tags
        : (dest.tags || '').split(',').map(t => t.trim()).filter(Boolean)

    return (
        <div
            className={`${styles.card} ${isBest ? styles.bestCard : ''} ${isExpanded ? styles.expandedCard : ''}`}
            onClick={onClick}
            role="button"
            tabIndex={0}
            onKeyDown={e => e.key === 'Enter' && onClick()}
        >
            {/* Rank + Best badge */}
            <div className={styles.cardHead}>
                <div className={styles.rankBadge}>#{rank}</div>
                {isBest && <div className={styles.bestBadge}>🏆 Best Compromise</div>}
                <div className={styles.expandHint}>{isExpanded ? '▲' : '▼'}</div>
            </div>

            {/* Destination title */}
            <div className={styles.destTitle}>
                <span className={styles.flag}>{flag}</span>
                <div>
                    <h3 className={styles.destName}>{dest.name}</h3>
                    <p className={styles.destCountry}>{dest.country}</p>
                </div>
            </div>

            {/* Score badges */}
            <div className={styles.scoreBadges}>
                <div className={styles.scoreBadge}>
                    <span className={styles.scoreLabel}>Fairness</span>
                    {isSolo ? (
                        <span
                            className={styles.soloTrip}
                            title="Fairness score requires 2+ members"
                        >
                            🧳 Solo Trip
                        </span>
                    ) : (
                        <span className={`${styles.scoreValue} ${styles.fairnessScore}`}>{fairnessPct}%</span>
                    )}
                </div>
                <div className={styles.scoreBadge}>
                    <span className={styles.scoreLabel}>Average</span>
                    <span className={`${styles.scoreValue} ${styles.avgScore}`}>{avgPct}%</span>
                </div>
                {!isSolo && (
                    <div className={styles.scoreBadge}>
                        <span className={styles.scoreLabel}>Min</span>
                        <span className={`${styles.scoreValue} ${styles.minScore}`}>{maximinPct}%</span>
                    </div>
                )}
            </div>

            {/* Tags */}
            <div className={styles.tagRow}>
                {tags.slice(0, 5).map(t => (
                    <span key={t} className={styles.tag}>{t}</span>
                ))}
            </div>

            {/* Budget */}
            <div className={styles.budgetRow}>
                {(dest.budget_range?.min > 0 || dest.budget_range?.max > 0) ? (
                    <>💵 ${dest.budget_range.min > 0 ? dest.budget_range.min.toLocaleString() : '?'} – ${dest.budget_range.max > 0 ? dest.budget_range.max.toLocaleString() : '?'} / person</>
                ) : (
                    <span className={styles.budgetUnknown}>💵 Budget not specified</span>
                )}
            </div>

            {/* Expanded: per-member bars */}
            {isExpanded && dest.member_scores?.length > 0 && (
                <div className={styles.memberBreakdown}>
                    <p className={styles.breakdownTitle}>Per-Member Satisfaction</p>
                    {dest.member_scores.map(m => (
                        <div key={m.user_id} className={styles.memberBar}>
                            <span className={styles.memberName}>{m.display_name}</span>
                            <ScoreBar score={m.score} tier={m.tier} />
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

export default function RecommendationResultsPanel({ results }) {
    const [expandedIdx, setExpandedIdx] = useState(0)

    if (!results) return null

    const { destinations = [], conflicts_detected = [] } = results

    if (destinations.length === 0) {
        return (
            <div className={styles.empty}>
                <span className={styles.emptyIcon}>🌐</span>
                <h3>No destinations matched</h3>
                <p>Try adjusting member preferences and running again.</p>
            </div>
        )
    }

    return (
        <div className={styles.panel}>
            {/* Conflict banner */}
            {conflicts_detected.length > 0 && (
                <div className={styles.conflictBanner}>
                    <div className={styles.conflictIcon}>⚡</div>
                    <div className={styles.conflictContent}>
                        <p className={styles.conflictTitle}>
                            {conflicts_detected.length} preference conflict{conflicts_detected.length > 1 ? 's' : ''} detected — here's how the top pick bridges the gap:
                        </p>
                        {conflicts_detected.map((c, i) => (
                            <div key={i} className={styles.conflictItem}>
                                <span className={styles.conflictLabel}>{c.label}</span>
                                {c.resolution_note && (
                                    <p className={styles.conflictNote}>"{c.resolution_note}"</p>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Results header */}
            <div className={styles.resultsHeader}>
                <h2 className={styles.resultsTitle}>
                    🎯 Top {destinations.length} Destinations for Your Group
                </h2>
                <p className={styles.resultsSubtitle}>
                    Ranked by fairness score — optimised so no one is left behind
                </p>
            </div>

            {/* Cards */}
            <div className={styles.cardList}>
                {destinations.map((dest, i) => (
                    <DestinationCard
                        key={dest.destination_id}
                        dest={dest}
                        rank={i + 1}
                        isExpanded={expandedIdx === i}
                        onClick={() => setExpandedIdx(expandedIdx === i ? -1 : i)}
                    />
                ))}
            </div>
        </div>
    )
}
