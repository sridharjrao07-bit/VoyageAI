import { useState } from 'react'
import { submitGroupPreferences } from '../../api/tourismApi'
import styles from './MemberPreferencesForm.module.css'

const TAGS = [
    { id: 'budget',      label: 'Budget',      emoji: '💰' },
    { id: 'luxury',      label: 'Luxury',      emoji: '✨' },
    { id: 'adventure',   label: 'Adventure',   emoji: '⛰️' },
    { id: 'culture',     label: 'Culture',     emoji: '🏛️' },
    { id: 'beach',       label: 'Beach',       emoji: '🌊' },
    { id: 'food',        label: 'Foodie',      emoji: '🍜' },
    { id: 'remote',      label: 'Remote',      emoji: '🏔️' },
    { id: 'urban',       label: 'Urban',       emoji: '🏙️' },
    { id: 'relaxation',  label: 'Relaxation',  emoji: '🧘' },
]

const DURATION_OPTIONS = [
    { value: 3,  label: 'Weekend',  sub: '2–3 days' },
    { value: 5,  label: 'Short',    sub: '4–6 days' },
    { value: 7,  label: 'Week',     sub: '7–9 days' },
    { value: 14, label: 'Extended', sub: '10+ days' },
]

const REGIONS = [
    '', 'Asia', 'Europe', 'North America', 'South America', 'Africa', 'Oceania', 'Middle East'
]

const MIN_BUDGET = 300
const MAX_BUDGET = 10000

export default function MemberPreferencesForm({ groupId, existingPrefs, onSaved }) {
    const [selectedTags, setSelectedTags] = useState(existingPrefs?.preference_tags || [])
    const [budgetRange, setBudgetRange] = useState([
        existingPrefs?.budget_min || 800,
        existingPrefs?.budget_max || 3000,
    ])
    const [duration, setDuration] = useState(existingPrefs?.trip_duration_days || 7)
    const [region, setRegion] = useState(existingPrefs?.region_preference || '')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [saved, setSaved] = useState(false)

    const MAX_TAGS = 3

    const toggleTag = (tagId) => {
        setSelectedTags(prev => {
            if (prev.includes(tagId)) return prev.filter(t => t !== tagId)
            if (prev.length >= MAX_TAGS) return prev // enforce max
            return [...prev, tagId]
        })
    }

    const handleBudgetMin = (e) => {
        const v = Number(e.target.value)
        setBudgetRange([Math.min(v, budgetRange[1] - 100), budgetRange[1]])
    }

    const handleBudgetMax = (e) => {
        const v = Number(e.target.value)
        setBudgetRange([budgetRange[0], Math.max(v, budgetRange[0] + 100)])
    }

    const budgetPct = (v) => ((v - MIN_BUDGET) / (MAX_BUDGET - MIN_BUDGET)) * 100

    const handleSave = async (e) => {
        e.preventDefault()
        if (selectedTags.length === 0) { setError('Please select at least one preference tag'); return }
        setError('')
        setLoading(true)
        try {
            await submitGroupPreferences(groupId, {
                preference_tags: selectedTags,
                budget_min: budgetRange[0],
                budget_max: budgetRange[1],
                trip_duration_days: duration,
                region_preference: region || null,
            })
            setSaved(true)
            onSaved?.()
            setTimeout(() => setSaved(false), 3000)
        } catch (err) {
            setError(err?.response?.data?.detail || 'Failed to save preferences')
        } finally {
            setLoading(false)
        }
    }

    return (
        <form className={styles.form} onSubmit={handleSave}>
            <div className={styles.section}>
                <div className={styles.sectionHeader}>
                    <h3>Your Travel Vibe</h3>
                    <span className={styles.badge}>{selectedTags.length}/{MAX_TAGS} selected</span>
                </div>
                <div className={styles.tagGrid}>
                    {TAGS.map(tag => {
                        const isSelected = selectedTags.includes(tag.id)
                        const isDisabled = !isSelected && selectedTags.length >= MAX_TAGS
                        return (
                            <button
                                id={`pref-tag-${tag.id}`}
                                key={tag.id}
                                type="button"
                                className={`${styles.tagBtn} ${isSelected ? styles.tagSelected : ''} ${isDisabled ? styles.tagDisabled : ''}`}
                                onClick={() => toggleTag(tag.id)}
                                disabled={isDisabled}
                            >
                                <span className={styles.tagEmoji}>{tag.emoji}</span>
                                <span className={styles.tagLabel}>{tag.label}</span>
                                {isSelected && <span className={styles.checkmark}>✓</span>}
                            </button>
                        )
                    })}
                </div>
                {selectedTags.length >= MAX_TAGS && (
                    <p className={styles.maxHint}>Max 3 tags reached. Deselect one to change.</p>
                )}
            </div>

            {/* Budget Slider */}
            <div className={styles.section}>
                <h3>Budget Range <span className={styles.budgetDisplay}>${budgetRange[0].toLocaleString()} – ${budgetRange[1].toLocaleString()}</span></h3>
                <div className={styles.sliderWrapper}>
                    <div className={styles.sliderTrack}>
                        <div
                            className={styles.sliderFill}
                            style={{
                                left: `${budgetPct(budgetRange[0])}%`,
                                width: `${budgetPct(budgetRange[1]) - budgetPct(budgetRange[0])}%`,
                            }}
                        />
                    </div>
                    <input
                        id="budget-slider-min"
                        type="range"
                        min={MIN_BUDGET} max={MAX_BUDGET} step={100}
                        value={budgetRange[0]}
                        onChange={handleBudgetMin}
                        className={styles.rangeInput}
                    />
                    <input
                        id="budget-slider-max"
                        type="range"
                        min={MIN_BUDGET} max={MAX_BUDGET} step={100}
                        value={budgetRange[1]}
                        onChange={handleBudgetMax}
                        className={styles.rangeInput}
                    />
                </div>
                <div className={styles.sliderLabels}>
                    <span>$300</span><span>$10,000</span>
                </div>
            </div>

            {/* Duration */}
            <div className={styles.section}>
                <h3>Trip Duration</h3>
                <div className={styles.durationGrid}>
                    {DURATION_OPTIONS.map(opt => (
                        <button
                            id={`duration-${opt.label.toLowerCase()}`}
                            key={opt.value}
                            type="button"
                            className={`${styles.durationBtn} ${duration === opt.value ? styles.durationSelected : ''}`}
                            onClick={() => setDuration(opt.value)}
                        >
                            <span className={styles.durLabel}>{opt.label}</span>
                            <span className={styles.durSub}>{opt.sub}</span>
                        </button>
                    ))}
                </div>
            </div>

            {/* Region */}
            <div className={styles.section}>
                <h3>Region Preference <span className={styles.optional}>(optional)</span></h3>
                <select
                    id="region-preference"
                    className={styles.regionSelect}
                    value={region}
                    onChange={e => setRegion(e.target.value)}
                >
                    <option value="">Anywhere in the world</option>
                    {REGIONS.filter(Boolean).map(r => (
                        <option key={r} value={r}>{r}</option>
                    ))}
                </select>
            </div>

            {error && <div className={styles.error}>⚠️ {error}</div>}

            <button
                id="save-preferences-btn"
                type="submit"
                className={`${styles.saveBtn} ${saved ? styles.savedBtn : ''}`}
                disabled={loading}
            >
                {loading ? <span className={styles.spinner} /> : saved ? '✅ Saved!' : '💾 Save Preferences'}
            </button>
        </form>
    )
}
