import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { IconThumbsUp, IconThumbsDown, IconRefreshCw, IconMapPin, IconDollarSign, IconInfo } from '../components/Icons'
import toast from 'react-hot-toast'
import { getRecommendations, submitFeedback, saveLike, getUserLikes } from '../api/tourismApi'
import styles from './RecommendationsPage.module.css'

function StarRating({ rating }) {
    return (
        <span className="stars">
            {[1, 2, 3, 4, 5].map(i => (
                <span key={i} style={{ opacity: i <= Math.round(rating) ? 1 : 0.25 }}>★</span>
            ))}
            <span style={{ marginLeft: 4, fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{rating}</span>
        </span>
    )
}

function SkeletonCard() {
    return (
        <div className={styles.skCard}>
            <div className={`skeleton ${styles.skImg}`} />
            <div className={styles.skBody}>
                <div className="skeleton" style={{ height: 22, width: '60%', marginBottom: 8 }} />
                <div className="skeleton" style={{ height: 14, width: '40%', marginBottom: 16 }} />
                <div className="skeleton" style={{ height: 60 }} />
                <div className="skeleton" style={{ height: 14, width: '80%', marginTop: 12 }} />
            </div>
        </div>
    )
}

function DestCard({ dest, rank, userVote, onVote, isLiked, onLike, surprise, currency }) {
    const [imgErr, setImgErr] = useState(false)
    const [xaiOpen, setXaiOpen] = useState(false)
    const fallback = 'https://images.unsplash.com/photo-1488085061387-422e29b40080?w=800'

    return (
        <motion.div
            className={styles.card}
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: rank * 0.08, ease: "easeOut" }}
        >
            <div className={styles.rankBadge}>#{rank}</div>

            {/* Hidden Gem badge (Surprise mode) */}
            {(surprise || dest.is_surprise) && (
                <div className={styles.surpriseBadge}>💎 Hidden Gem</div>
            )}

            <div className={styles.imgWrap}>
                <img src={imgErr ? fallback : (dest.photo_url || fallback)} alt={dest.name} className={styles.img} onError={() => setImgErr(true)} />
                <div className={styles.imgOverlay} />
                <div className={styles.imgMeta}>
                    <span className={styles.country}><IconMapPin size={12} /> {dest.country}</span>
                    <StarRating rating={dest.avg_rating} />
                </div>
                {String(dest.accessibility).toLowerCase() === 'true' && (
                    <div className={styles.a11yBadge} title="Wheelchair accessible">♿</div>
                )}
                {/* Like / Bucket List heart */}
                <button
                    className={`${styles.heartBtn} ${isLiked ? styles.heartActive : ''}`}
                    onClick={() => onLike()}
                    title={isLiked ? 'Remove from Bucket List' : 'Save to Bucket List'}
                >
                    {isLiked ? '❤️' : '🤍'}
                </button>

                {/* XAI Overlay */}
                {xaiOpen && (
                    <div className={styles.xaiOverlay}>
                        <button className={styles.xaiClose} onClick={() => setXaiOpen(false)}>✕</button>
                        <div className={styles.xaiBody}>{dest.xai_snippet}</div>
                    </div>
                )}
            </div>

            <div className={styles.body}>
                {/* Weather Pivot banner */}
                {dest.pivot_applied && (
                    <div className={styles.pivotBanner}>
                        🔄 <strong>Pivoted</strong> — {dest.pivot_reason || 'Swapped due to severe weather alert.'}
                    </div>
                )}

                <div className={styles.titleRow}>
                    <h3 className={styles.name}>{dest.name}</h3>
                    <span className={styles.cost}>
                        {currency === 'INR' ? '₹' : <IconDollarSign size={14} />}
                        {currency === 'INR' ? (dest.avg_cost_usd * 90).toLocaleString() : dest.avg_cost_usd?.toLocaleString()}
                    </span>
                </div>
                <div className={styles.tags}>
                    {String(dest.tags || '').split(',').slice(0, 4).map(t => (
                        <span key={t} className="tag-chip">{t.trim()}</span>
                    ))}
                </div>
                <p className={styles.desc}>{dest.description}</p>
                <button className={styles.xaiToggle} onClick={() => setXaiOpen(o => !o)}>
                    ✨ Why recommended? <span style={{ marginLeft: 'auto' }}>{xaiOpen ? '▲' : '▼'}</span>
                </button>
                <div className={styles.feedbackRow}>
                    <span className={styles.feedbackLabel}>Was this helpful?</span>
                    <button className={`${styles.voteBtn} ${userVote === 1 ? styles.votedUp : ''}`} onClick={() => onVote(1)} title="Thumbs up">
                        <IconThumbsUp size={15} />
                    </button>
                    <button className={`${styles.voteBtn} ${userVote === -1 ? styles.votedDown : ''}`} onClick={() => onVote(-1)} title="Thumbs down">
                        <IconThumbsDown size={15} />
                    </button>
                    <div className={styles.scoreBar}><div className={styles.scoreFill} style={{ width: `${Math.round(dest.score * 100)}%` }} /></div>
                    <span className={styles.scoreLabel}>{Math.round(dest.score * 100)}%</span>
                </div>
            </div>
        </motion.div>
    )
}

export default function RecommendationsPage() {
    const navigate = useNavigate()
    const [profile, setProfile] = useState(null)
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)
    const [sessionId, setSessionId] = useState(null)
    const [votes, setVotes] = useState({})
    const [likedIds, setLikedIds] = useState(new Set())
    const [likedCategories, setLikedCategories] = useState([])
    const [surpriseMode, setSurpriseMode] = useState(false)

    // Load liked state from backend on mount
    const loadLikes = useCallback((userId) => {
        getUserLikes(userId)
            .then(res => {
                setLikedIds(new Set(res.liked_destination_ids || []))
                setLikedCategories(res.liked_categories || [])
            })
            .catch(() => {/* silently ignore */ })
    }, [])

    useEffect(() => {
        const stored = sessionStorage.getItem('travelProfile')
        if (!stored) { navigate('/profile'); return }
        const p = JSON.parse(stored)
        setProfile(p)
        loadLikes(p.user_id || 'new_user')
        fetchRecs(p, null, false)
    }, [])

    const fetchRecs = (p, sid, isSurprise = false) => {
        setLoading(true)
        const payload = {
            user_id: p.user_id || 'new_user',
            tags: p.tags || [],
            budget_usd: p.budget_usd || 0,
            accessibility_required: p.accessibility_required || false,
            top_n: p.top_n || 8,
            travel_style: p.travel_style || null,
            origin: p.origin || 'DEL',
            include_flights: Object.hasOwn(p, 'include_flights') ? p.include_flights : true,
            currency_preference: p.currency_preference || 'INR',
            session_id: sid,
            include_photos: true,
            surprise_mode: isSurprise,
            liked_categories: likedCategories,
        }
        console.log('[Allora] 📤 /recommend request payload:', payload)
        getRecommendations(payload)
            .then(result => {
                console.log('[Allora] 📥 /recommend raw response:', result)
                console.log('[Allora] 🗺️  recommendations array:', result.recommendations)
                result.recommendations?.forEach((rec, i) =>
                    console.log(`[Allora]   #${i + 1} ${rec.name}:`, rec)
                )
                setData(result)
                setSessionId(result.session_id)
                setLoading(false)
            })
            .catch((err) => {
                console.error('[Allora] ❌ /recommend error:', err?.response?.data || err.message)
                toast.error('Could not connect to AI engine. Is the backend running?')
                setLoading(false)
            })
    }

    const handleVote = (destId, vote) => {
        if (!sessionId || votes[destId] === vote) return
        setVotes(v => ({ ...v, [destId]: vote }))
        submitFeedback({ session_id: sessionId, destination_id: destId, vote })
            .then(() => {
                toast.success(vote === 1 ? '👍 Loved it! Re-ranking…' : '👎 Got it! Filtering…')
                fetchRecs(profile, sessionId, surpriseMode)
            })
            .catch(() => toast.error('Feedback failed'))
    }

    const handleLike = (dest) => {
        const userId = profile?.user_id || 'new_user'
        const destId = String(dest.id)
        const alreadyLiked = likedIds.has(destId)

        // Optimistic update
        setLikedIds(prev => {
            const next = new Set(prev)
            if (alreadyLiked) next.delete(destId)
            else next.add(destId)
            return next
        })

        saveLike({ user_id: userId, destination_id: destId })
            .then(res => {
                if (res.liked) {
                    toast.success(`❤️ Saved "${dest.name}" to your Bucket List!`)
                    // Update liked categories so next fetch is better
                    if (res.categories_saved) {
                        setLikedCategories(prev => [...prev, ...res.categories_saved])
                    }
                } else {
                    toast(`💔 Removed "${dest.name}" from Bucket List`, { icon: '🗑' })
                }
            })
            .catch(() => {
                // Revert on failure
                setLikedIds(prev => {
                    const next = new Set(prev)
                    if (alreadyLiked) next.add(destId)
                    else next.delete(destId)
                    return next
                })
                toast.error('Could not save like')
            })
    }

    const handleRefresh = () => {
        setVotes({})
        setSurpriseMode(false)
        fetchRecs(profile, null, false)
        toast('Refreshing…', { icon: '🔄' })
    }

    const handleSurprise = () => {
        setSurpriseMode(true)
        setVotes({})
        fetchRecs(profile, null, true)
        toast('🎲 Finding hidden gems just for you…', { duration: 3000 })
    }

    if (!profile) return null

    return (
        <div className="page-wrapper">
            <div className="section">
                <div className={styles.header}>
                    <div>
                        <span className="section-label">AI Recommendations</span>
                        <h1 className="section-title" style={{ textAlign: 'left', marginBottom: 8 }}>
                            Your <span className="gradient-text">Perfect Trips</span>
                        </h1>
                        {data?.is_cold_start && (
                            <div className={styles.coldStartBadge}><IconInfo size={14} /> Cold-start — showing content-based + popularity recommendations</div>
                        )}
                    </div>
                    <div className={styles.headerActions}>
                        <div className={styles.profileSummary}>
                            {profile.tags?.slice(0, 3).map(t => <span key={t} className="tag-chip">{t}</span>)}
                            {profile.tags?.length > 3 && <span className="tag-chip">+{profile.tags.length - 3}</span>}
                            <span className={styles.budget}>
                                ≤ {profile.currency_preference === 'INR' ? '₹' : '$'}{profile.currency_preference === 'INR' ? (profile.budget_usd * 90).toLocaleString() : profile.budget_usd?.toLocaleString()}
                            </span>
                        </div>
                        <button className="btn-secondary" onClick={handleRefresh}><IconRefreshCw size={15} /> Refresh</button>
                        <button
                            className={`btn-primary ${surpriseMode ? styles.surpriseActive : ''}`}
                            onClick={handleSurprise}
                            title="Ignore preferences — find the most unexpected hidden gems"
                            style={{ background: surpriseMode ? 'linear-gradient(135deg, #f59e0b, #ef4444)' : '' }}
                        >
                            🎲 Surprise Me
                        </button>
                    </div>
                </div>

                {/* Surprise Mode Banner */}
                {surpriseMode && !loading && (
                    <div className={styles.surpriseBanner}>
                        <span>🌟</span>
                        <div>
                            <strong>Hidden Gem Mode Active</strong>
                            <p>The AI is ignoring your usual preferences and surfacing the most unique, off-the-beaten-path destinations — places most travel guides will never tell you about.</p>
                        </div>
                        <button className="btn-ghost" onClick={handleRefresh}>Exit</button>
                    </div>
                )}

                {/* RL Bias indicator */}
                {likedCategories.length > 0 && !surpriseMode && (
                    <div className={styles.rlBanner}>
                        ❤️ <strong>Personalised</strong> — AI is favouring your liked categories:&nbsp;
                        {[...new Set(likedCategories)].slice(0, 4).map(c => (
                            <span key={c} className="tag-chip" style={{ fontSize: '0.72rem' }}>{c}</span>
                        ))}
                    </div>
                )}

                {loading ? (
                    <div className="cards-grid stagger">
                        {Array.from({ length: profile.top_n || 8 }).map((_, i) => <SkeletonCard key={i} />)}
                    </div>
                ) : data?.recommendations?.length === 0 ? (
                    <div className="empty-state">
                        <div className="empty-state-icon">🗺️</div>
                        <h3>No destinations found</h3>
                        <p>Try relaxing your budget or accessibility filters.</p>
                        <button className="btn-primary" onClick={() => navigate('/profile')}>Adjust Profile</button>
                    </div>
                ) : (
                    <div className="cards-grid stagger">
                        {data?.recommendations?.map((dest, idx) => (
                            <DestCard
                                key={dest.id}
                                dest={dest}
                                rank={idx + 1}
                                userVote={votes[dest.id]}
                                onVote={(v) => handleVote(dest.id, v)}
                                isLiked={likedIds.has(String(dest.id))}
                                onLike={() => handleLike(dest)}
                                surprise={surpriseMode}
                                currency={profile?.currency_preference || 'INR'}
                            />
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}
