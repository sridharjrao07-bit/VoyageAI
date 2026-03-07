import { useState, useEffect, useCallback } from 'react'
import { IconSearch, IconFilter, IconMapPin, IconDollarSign } from '../components/Icons'
import { getDestinations, getDestination, semanticSearch } from '../api/tourismApi'
import styles from './ExplorePage.module.css'

const CONTINENTS = ['All', 'Asia', 'Europe', 'Africa', 'South America', 'North America', 'Oceania', 'Caribbean', 'Central America']
const CLIMATES = ['All', 'tropical', 'mediterranean', 'temperate', 'cold', 'arid', 'highland', 'subarctic', 'subtropical']
const FALLBACK = 'https://images.unsplash.com/photo-1488085061387-422e29b40080?w=600'

/** Detect if a query should use vector / semantic search instead of keyword matching */
const isNaturalLanguage = (q) => {
    if (!q || q.trim().length < 3) return false
    const trimmed = q.trim()
    // 4+ words OR starts with common NL patterns
    const wordCount = trimmed.split(/\s+/).length
    const nlPhrases = ['a place', 'somewhere', 'like a', 'that feels', 'that looks', 'hidden', 'secret', 'remote', 'peaceful']
    return wordCount >= 4 || nlPhrases.some(ph => trimmed.toLowerCase().startsWith(ph))
}

function DestCard({ dest, semanticScore }) {
    const [imgErr, setImgErr] = useState(false)
    const [photoUrl, setPhotoUrl] = useState(dest.photo_url || null)

    // IntersectionObserver: only fetch photo when card scrolls into view
    useEffect(() => {
        if (photoUrl) return
        const el = document.getElementById(`ec-${dest.id}`)
        if (!el) return
        const obs = new IntersectionObserver(
            ([entry]) => {
                if (!entry.isIntersecting) return
                obs.disconnect()
                getDestination(String(dest.id), false)
                    .then(d => { if (d.photo_url) setPhotoUrl(d.photo_url) })
                    .catch(() => { })
            },
            { rootMargin: '150px' }
        )
        obs.observe(el)
        return () => obs.disconnect()
    }, [dest.id])
    return (
        <div id={`ec-${dest.id}`} className={`${styles.card} animate-fade-up`}>
            {semanticScore !== undefined && (
                <div className={styles.semanticBadge} title="Semantic similarity score">
                    🧠 {Math.round(semanticScore * 100)}% match
                </div>
            )}
            <div className={styles.imgWrap}>
                <img src={imgErr ? FALLBACK : (photoUrl || FALLBACK)} alt={dest.name} className={styles.img} onError={() => setImgErr(true)} />
                <div className={styles.overlay} />
                <div className={styles.imgBottom}>
                    <span className={styles.continent}>{dest.continent}</span>
                    <span className={styles.cost}><IconDollarSign size={13} />{dest.avg_cost_usd?.toLocaleString()}</span>
                </div>
            </div>
            <div className={styles.body}>
                <div className={styles.titleRow}>
                    <h3 className={styles.name}>{dest.name}</h3>
                    <span className={styles.rating}>★ {dest.avg_rating}</span>
                </div>
                <div className={styles.location}><IconMapPin size={12} /> {dest.country}</div>
                <p className={styles.desc}>{dest.description}</p>
                <div className={styles.tags}>
                    {String(dest.tags || '').split(',').slice(0, 4).map(t => (
                        <span key={t} className="tag-chip">{t.trim()}</span>
                    ))}
                </div>
                <div className={styles.meta}>
                    <span className={styles.season}>🗓 {dest.best_season}</span>
                    <span className={styles.climate}>{dest.climate}</span>
                    {String(dest.accessibility).toLowerCase() === 'true' && <span className={styles.a11y}>♿ Accessible</span>}
                </div>
            </div>
        </div>
    )
}

export default function ExplorePage() {
    const [allDests, setAllDests] = useState([])
    const [filtered, setFiltered] = useState([])
    const [loading, setLoading] = useState(true)
    const [search, setSearch] = useState('')
    const [continent, setContinent] = useState('All')
    const [climate, setClimate] = useState('All')
    const [maxCost, setMaxCost] = useState(6000)
    const [showFilters, setShowFilters] = useState(false)
    const [semanticMode, setSemanticMode] = useState(false)
    const [semanticLoading, setSemanticLoading] = useState(false)
    const [semanticResults, setSemanticResults] = useState(null) // null = not in semantic mode

    useEffect(() => {
        // Load WITHOUT photos — instant response. Photos load lazily per card.
        getDestinations({ include_photos: false })
            .then(d => { setAllDests(d.destinations || []); setFiltered(d.destinations || []); setLoading(false) })
            .catch(() => setLoading(false))
    }, [])

    const applyFilters = useCallback(() => {
        // If we're in semantic mode, don't override with keyword filter
        if (semanticResults !== null) return

        let result = allDests
        if (search) {
            const q = search.toLowerCase()
            result = result.filter(d =>
                d.name?.toLowerCase().includes(q) ||
                d.country?.toLowerCase().includes(q) ||
                String(d.tags).toLowerCase().includes(q) ||
                d.description?.toLowerCase().includes(q)
            )
        }
        if (continent !== 'All') result = result.filter(d => d.continent === continent)
        if (climate !== 'All') result = result.filter(d => d.climate === climate)
        result = result.filter(d => (d.avg_cost_usd || 0) <= maxCost)
        setFiltered(result)
        setSemanticMode(false)
    }, [allDests, search, continent, climate, maxCost, semanticResults])

    useEffect(() => { applyFilters() }, [applyFilters])

    // Debounce semantic search: trigger after user stops typing for 600ms
    useEffect(() => {
        if (!isNaturalLanguage(search)) {
            // Switch back to keyword mode
            setSemanticResults(null)
            return
        }
        setSemanticMode(true)
        setSemanticLoading(true)
        const timer = setTimeout(() => {
            semanticSearch(search, 20)
                .then(res => {
                    setSemanticResults(res.results || [])
                    setFiltered(res.results || [])
                    setSemanticLoading(false)
                })
                .catch(() => {
                    setSemanticResults(null)
                    setSemanticMode(false)
                    setSemanticLoading(false)
                })
        }, 600)
        return () => clearTimeout(timer)
    }, [search])

    const clearFilters = () => {
        setSearch('')
        setContinent('All')
        setClimate('All')
        setMaxCost(6000)
        setSemanticResults(null)
        setSemanticMode(false)
    }
    const hasFilters = continent !== 'All' || climate !== 'All' || search || maxCost < 6000
    const displayList = semanticResults !== null ? semanticResults : filtered

    return (
        <div className="page-wrapper">
            <div className="section">
                <div className="section-header">
                    <span className="section-label">Destination Catalog</span>
                    <h1 className="section-title">Explore <span className="gradient-text">100 Destinations</span></h1>
                    <p className="section-subtitle">Browse the full catalog powered by OpenTripMap. Filter by continent, climate, or budget. Type a full sentence for AI-powered semantic search.</p>
                </div>

                {/* Search & Filter Bar */}
                <div className={styles.filterBar}>
                    <div className={styles.searchWrap}>
                        <IconSearch size={16} className={styles.searchIcon} />
                        <input
                            type="text"
                            className={styles.searchInput}
                            placeholder="Search or describe a vibe — e.g. 'a place that feels like a Studio Ghibli movie'…"
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                        />
                        {/* Search mode indicator */}
                        {search.length > 0 && (
                            <span className={`${styles.searchModeBadge} ${semanticMode ? styles.semanticActive : ''}`}>
                                {semanticMode ? '🧠 Semantic' : '📋 Keyword'}
                            </span>
                        )}
                    </div>
                    <button className={`${styles.filterToggle} ${showFilters ? styles.filterActive : ''}`} onClick={() => setShowFilters(f => !f)}>
                        <IconFilter size={15} /> Filters
                        {hasFilters && <span className={styles.filterDot} />}
                    </button>
                </div>

                {/* Filters Panel */}
                {showFilters && (
                    <div className={`${styles.filtersPanel} animate-fade-up`}>
                        <div className={styles.filterGroup}>
                            <label>Continent</label>
                            <div className={styles.filterChips}>
                                {CONTINENTS.map(c => <button key={c} className={`${styles.filterChip} ${continent === c ? styles.chipActive : ''}`} onClick={() => setContinent(c)}>{c}</button>)}
                            </div>
                        </div>
                        <div className={styles.filterGroup}>
                            <label>Climate</label>
                            <div className={styles.filterChips}>
                                {CLIMATES.map(c => <button key={c} className={`${styles.filterChip} ${climate === c ? styles.chipActive : ''}`} onClick={() => setClimate(c)}>{c}</button>)}
                            </div>
                        </div>
                        <div className={styles.filterGroup}>
                            <label>Max Budget: <b style={{ color: 'var(--text-primary)' }}>${maxCost.toLocaleString()}</b></label>
                            <input type="range" min={200} max={6000} step={100} value={maxCost} className={styles.slider} onChange={e => setMaxCost(+e.target.value)} />
                        </div>
                    </div>
                )}

                {/* Semantic mode info bar */}
                {semanticMode && !semanticLoading && (
                    <div className={styles.semanticInfoBar}>
                        🧠 <strong>Semantic Vector Search</strong> — showing destinations closest in meaning to your description, not just keyword matches.
                        <button className="btn-ghost" style={{ marginLeft: 'auto' }} onClick={clearFilters}>Return to Browse</button>
                    </div>
                )}

                {/* Result Count */}
                {!loading && !semanticLoading && (
                    <div className={styles.resultCount}>
                        Showing <b>{displayList.length}</b> {semanticMode ? 'semantic' : 'of ' + allDests.length} destinations
                        {hasFilters && <button className="btn-ghost" onClick={clearFilters}>Clear filters ✕</button>}
                    </div>
                )}

                {/* Grid */}
                {loading || semanticLoading ? (
                    <div className="cards-grid stagger">
                        {Array.from({ length: 12 }).map((_, i) => (
                            <div key={i} className={styles.skCard}>
                                <div className={`skeleton ${styles.skImg}`} />
                                <div style={{ padding: 16 }}>
                                    <div className="skeleton" style={{ height: 18, width: '55%', marginBottom: 8 }} />
                                    <div className="skeleton" style={{ height: 12, width: '35%', marginBottom: 12 }} />
                                    <div className="skeleton" style={{ height: 48 }} />
                                </div>
                            </div>
                        ))}
                    </div>
                ) : displayList.length === 0 ? (
                    <div className="empty-state">
                        <div className="empty-state-icon">🌍</div>
                        <h3>No destinations match</h3>
                        <p>Try broadening your filters or searching something different.</p>
                    </div>
                ) : (
                    <div className="cards-grid stagger">
                        {displayList.map(dest => (
                            <DestCard
                                key={dest.id}
                                dest={dest}
                                semanticScore={semanticMode ? dest.semantic_score : undefined}
                            />
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}
