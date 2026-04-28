import { useState, useNavigate } from 'react'
import { useNavigate as useNav } from 'react-router-dom'
import { IconArrowRight, IconUser, IconDollarSign, IconHeart, IconInfo } from '../components/Icons'
import toast from 'react-hot-toast'
import styles from './ProfilePage.module.css'

const TAGS = [
    'adventure', 'beach', 'mountain', 'trekking', 'culture', 'food',
    'luxury', 'budget', 'wildlife', 'diving', 'history', 'temples',
    'skiing', 'wellness', 'nature', 'romance', 'desert', 'island',
    'northern_lights', 'safari', 'photography', 'art', 'wine', 'hiking',
    'backpacker', 'eco_tourism', 'spiritual', 'urban', 'scenic', 'unique',
]

const STYLES = [
    { id: 'adventurer', label: '🏔️ Adventurer', desc: 'Thrill-seeking & outdoor' },
    { id: 'cultural', label: '🏛️ Cultural', desc: 'History, art & local life' },
    { id: 'luxury', label: '💎 Luxury', desc: 'Premium & indulgent stays' },
    { id: 'backpacker', label: '🎒 Backpacker', desc: 'Budget-friendly & social' },
    { id: 'eco_traveler', label: '🌿 Eco Traveler', desc: 'Nature & sustainability' },
    { id: 'romantic', label: '💑 Romantic', desc: 'Couples & intimate escapes' },
    { id: 'explorer', label: '🔭 Explorer', desc: 'Off-the-beaten-path' },
]

const EXISTING_USERS = [
    { id: 'U001', name: "Arjun Sharma — Adventurer" },
    { id: 'U002', name: "Priya Nair — Luxury" },
    { id: 'U005', name: "Liam O'Brien — Eco Traveler" },
    { id: 'U006', name: "Yuki Tanaka — Cultural" },
    { id: 'U010', name: "Marie Dubois — Romantic" },
    { id: 'U050', name: "Aaron Mitchell — Explorer" },
]

export default function ProfilePage() {
    const navigate = useNav()
    const [step, setStep] = useState(1)
    const [form, setForm] = useState({
        user_id: 'new_user',
        useExisting: false,
        travel_style: '',
        tags: [],
        budget_usd: 2000,
        accessibility_required: false,
        top_n: 8,
        origin: 'DEL',
        include_flights: true,
        currency_preference: 'INR',
    })

    const toggleTag = (tag) =>
        setForm(f => ({
            ...f,
            tags: f.tags.includes(tag) ? f.tags.filter(t => t !== tag) : [...f.tags, tag],
        }))

    const handleSubmit = () => {
        if (!form.travel_style) { toast.error('Please select a travel style'); return }
        if (form.tags.length < 2) { toast.error('Pick at least 2 interest tags'); return }
        sessionStorage.setItem('travelProfile', JSON.stringify(form))
        toast.success('Profile saved! Finding your perfect trips…')
        navigate('/recommendations')
    }

    return (
        <div className="page-wrapper">
            <div className={styles.wrapper}>
                {/* Progress */}
                <div className={styles.progress}>
                    {[1, 2, 3].map(s => (
                        <div key={s} className={styles.progressStep}>
                            <div className={`${styles.dot} ${step >= s ? styles.dotActive : ''} ${step > s ? styles.dotDone : ''}`}>
                                {step > s ? '✓' : s}
                            </div>
                            <span className={styles.stepLabel}>{s === 1 ? 'Profile' : s === 2 ? 'Interests' : 'Budget'}</span>
                        </div>
                    ))}
                </div>

                {/* STEP 1 */}
                {step === 1 && (
                    <div className={`${styles.card} animate-fade-up`}>
                        <div className={styles.cardHeader}>
                            <IconUser size={28} className={styles.cardIcon} />
                            <div><h2>Who are you?</h2><p>Choose an existing traveler or start fresh</p></div>
                        </div>
                        <div className={styles.field}>
                            <label>Traveler Mode</label>
                            <div className={styles.segmented}>
                                <button className={!form.useExisting ? styles.segActive : ''} onClick={() => setForm(f => ({ ...f, useExisting: false, user_id: 'new_user' }))}>New User (Cold-Start)</button>
                                <button className={form.useExisting ? styles.segActive : ''} onClick={() => setForm(f => ({ ...f, useExisting: true }))}>Existing User</button>
                            </div>
                        </div>
                        {form.useExisting && (
                            <div className={styles.field}>
                                <label>Select Profile</label>
                                <select className={styles.select} value={form.user_id} onChange={e => setForm(f => ({ ...f, user_id: e.target.value }))}>
                                    {EXISTING_USERS.map(u => <option key={u.id} value={u.id}>{u.name}</option>)}
                                </select>
                            </div>
                        )}
                        <div className={styles.field}>
                            <label>Travel Style</label>
                            <div className={styles.styleGrid}>
                                {STYLES.map(s => (
                                    <button key={s.id} className={`${styles.styleCard} ${form.travel_style === s.id ? styles.styleActive : ''}`} onClick={() => setForm(f => ({ ...f, travel_style: s.id }))}>
                                        <span className={styles.styleLabel}>{s.label}</span>
                                        <span className={styles.styleDesc}>{s.desc}</span>
                                    </button>
                                ))}
                            </div>
                        </div>
                        <button className="btn-primary" style={{ width: '100%', justifyContent: 'center' }} onClick={() => setStep(2)}>
                            Next: Select Interests <IconArrowRight size={18} />
                        </button>
                    </div>
                )}

                {/* STEP 2 */}
                {step === 2 && (
                    <div className={`${styles.card} animate-fade-up`}>
                        <div className={styles.cardHeader}>
                            <IconHeart size={28} className={styles.cardIcon} />
                            <div><h2>What do you love?</h2><p>Pick at least 2 interests that excite you</p></div>
                        </div>
                        <div className={styles.tagsGrid}>
                            {TAGS.map(tag => (
                                <button key={tag} className={`${styles.tagBtn} ${form.tags.includes(tag) ? styles.tagActive : ''}`} onClick={() => toggleTag(tag)}>
                                    {tag}
                                </button>
                            ))}
                        </div>
                        <p className={styles.hint}><IconInfo size={14} /> {form.tags.length} selected — more tags = better recommendations</p>
                        <div className={styles.navBtns}>
                            <button className="btn-secondary" onClick={() => setStep(1)}>← Back</button>
                            <button className="btn-primary" onClick={() => setStep(3)}>Next: Budget <IconArrowRight size={18} /></button>
                        </div>
                    </div>
                )}

                {/* STEP 3 */}
                {step === 3 && (
                    <div className={`${styles.card} animate-fade-up`}>
                        <div className={styles.cardHeader}>
                            <IconDollarSign size={28} className={styles.cardIcon} />
                            <div><h2>Budget & Accessibility</h2><p>Set your trip budget and any accessibility needs</p></div>
                        </div>
                        <div className={styles.field}>
                            <label>Max Budget per Trip
                                <b className={styles.budgetVal}>
                                    {form.currency_preference === 'INR' ? '₹' : '$'}{(form.currency_preference === 'INR' ? form.budget_usd * 90 : form.budget_usd).toLocaleString()}
                                </b>
                            </label>
                            <input
                                type="range"
                                min={200}
                                max={6000}
                                step={100}
                                value={form.budget_usd}
                                className={styles.slider}
                                onChange={e => setForm(f => ({ ...f, budget_usd: +e.target.value }))}
                            />
                            <div className={styles.sliderLabels}>
                                <span>{form.currency_preference === 'INR' ? '₹18,000' : '$200'}</span>
                                <span>{form.currency_preference === 'INR' ? '₹540,000+' : '$6,000+'}</span>
                            </div>
                        </div>
                        <div className={styles.field}>
                            <label>Number of Recommendations: <b className={styles.budgetVal}>{form.top_n}</b></label>
                            <input type="range" min={3} max={15} step={1} value={form.top_n} className={styles.slider} onChange={e => setForm(f => ({ ...f, top_n: +e.target.value }))} />
                        </div>
                        <div className={styles.toggleRow}>
                            <div>
                                <span style={{ fontSize: '1.3rem' }}>♿</span>
                                <div><b>Wheelchair Accessible Only</b><p>Filter to only show fully accessible destinations</p></div>
                            </div>
                            <button className={`${styles.toggle} ${form.accessibility_required ? styles.toggleOn : ''}`} onClick={() => setForm(f => ({ ...f, accessibility_required: !f.accessibility_required }))}>
                                <span className={styles.toggleThumb} />
                            </button>
                        </div>
                        <div className={styles.toggleRow}>
                            <div>
                                <span style={{ fontSize: '1.3rem' }}>✈️</span>
                                <div><b>Include Flight Prices</b><p>Add live AviationStack estimates to the total cost</p></div>
                            </div>
                            <button className={`${styles.toggle} ${form.include_flights ? styles.toggleOn : ''}`} onClick={() => setForm(f => ({ ...f, include_flights: !f.include_flights }))}>
                                <span className={styles.toggleThumb} />
                            </button>
                        </div>
                        <div className={styles.field} style={{ display: 'flex', gap: '1rem' }}>
                            <div style={{ flex: 1 }}>
                                <label>Origin Airport (IATA)</label>
                                <input
                                    type="text"
                                    value={form.origin}
                                    className={styles.select}
                                    style={{ width: '100%', padding: '0.8rem', background: 'var(--bg-main)', border: '1px solid var(--border)', borderRadius: '8px', color: 'var(--text-main)', textTransform: 'uppercase' }}
                                    onChange={e => setForm(f => ({ ...f, origin: e.target.value.toUpperCase().slice(0, 3) }))}
                                />
                            </div>
                            <div style={{ flex: 1 }}>
                                <label>Currency</label>
                                <select
                                    className={styles.select}
                                    value={form.currency_preference}
                                    style={{ width: '100%', padding: '0.8rem', background: 'var(--bg-main)', border: '1px solid var(--border)', borderRadius: '8px', color: 'var(--text-main)' }}
                                    onChange={e => {
                                        const newCurr = e.target.value;
                                        setForm(f => ({
                                            ...f,
                                            currency_preference: newCurr
                                        }))
                                    }}
                                >
                                    <option value="INR">₹ (INR)</option>
                                    <option value="USD">$ (USD)</option>
                                </select>
                            </div>
                        </div>
                        <div className={styles.navBtns}>
                            <button className="btn-secondary" onClick={() => setStep(2)}>← Back</button>
                            <button className="btn-primary" onClick={handleSubmit}>Find My Destinations 🚀</button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
