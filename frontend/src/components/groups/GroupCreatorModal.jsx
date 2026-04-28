import { useState, useEffect } from 'react'
import { searchUsers, createGroup } from '../../api/tourismApi'
import styles from './GroupCreatorModal.module.css'

export default function GroupCreatorModal({ onClose, onCreated }) {
    const [name, setName] = useState('')
    const [query, setQuery] = useState('')
    const [searchResults, setSearchResults] = useState([])
    const [selectedMembers, setSelectedMembers] = useState([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [searching, setSearching] = useState(false)

    // Debounced user search
    useEffect(() => {
        if (!query.trim()) { setSearchResults([]); return }
        const t = setTimeout(async () => {
            setSearching(true)
            try {
                const res = await searchUsers(query)
                const filtered = res.filter(u => !selectedMembers.find(m => m.id === u.id))
                setSearchResults(filtered)
            } catch {
                setSearchResults([])
            } finally {
                setSearching(false)
            }
        }, 300)
        return () => clearTimeout(t)
    }, [query, selectedMembers])

    // Escape to close
    useEffect(() => {
        const h = (e) => e.key === 'Escape' && onClose()
        window.addEventListener('keydown', h)
        return () => window.removeEventListener('keydown', h)
    }, [onClose])

    const addMember = (user) => {
        if (selectedMembers.find(m => m.id === user.id)) return
        setSelectedMembers(prev => [...prev, user])
        setQuery('')
        setSearchResults([])
    }

    const removeMember = (userId) => {
        setSelectedMembers(prev => prev.filter(m => m.id !== userId))
    }

    const handleCreate = async (e) => {
        e.preventDefault()
        if (!name.trim()) { setError('Group name is required'); return }
        setError('')
        setLoading(true)
        try {
            const res = await createGroup({
                name: name.trim(),
                invited_user_ids: selectedMembers.map(m => m.id),
            })
            onCreated?.(res)
            onClose()
        } catch (err) {
            setError(err?.response?.data?.detail || 'Failed to create group')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className={styles.overlay} onClick={e => e.target === e.currentTarget && onClose()}>
            <div className={styles.modal}>
                <div className={styles.header}>
                    <div>
                        <h2 className={styles.title}>✈️ New Trip Group</h2>
                        <p className={styles.subtitle}>Invite your travel crew and plan together</p>
                    </div>
                    <button className={styles.closeBtn} onClick={onClose}>✕</button>
                </div>

                <form className={styles.form} onSubmit={handleCreate}>
                    {/* Group name */}
                    <div className={styles.field}>
                        <label htmlFor="group-name-input">Group Name</label>
                        <input
                            id="group-name-input"
                            type="text"
                            placeholder='e.g. "Bali 2025 🌴"'
                            value={name}
                            onChange={e => setName(e.target.value)}
                            autoFocus
                            required
                        />
                    </div>

                    {/* Member search */}
                    <div className={styles.field}>
                        <label htmlFor="member-search-input">Invite Members</label>
                        <div className={styles.searchWrapper}>
                            <input
                                id="member-search-input"
                                type="text"
                                placeholder="Search by username or name…"
                                value={query}
                                onChange={e => setQuery(e.target.value)}
                                autoComplete="off"
                            />
                            {searching && <span className={styles.searchSpinner} />}
                        </div>

                        {searchResults.length > 0 && (
                            <div className={styles.dropdown}>
                                {searchResults.map(u => (
                                    <button
                                        key={u.id}
                                        type="button"
                                        className={styles.dropdownItem}
                                        onClick={() => addMember(u)}
                                    >
                                        <span className={styles.dropAvatar}>{u.avatar_emoji}</span>
                                        <span className={styles.dropName}>{u.display_name}</span>
                                        <span className={styles.dropUsername}>@{u.username}</span>
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Selected members */}
                    {selectedMembers.length > 0 && (
                        <div className={styles.memberGrid}>
                            {selectedMembers.map(u => (
                                <div key={u.id} className={styles.memberChip}>
                                    <span className={styles.chipAvatar}>{u.avatar_emoji}</span>
                                    <span className={styles.chipName}>{u.display_name}</span>
                                    <button
                                        type="button"
                                        className={styles.chipRemove}
                                        onClick={() => removeMember(u.id)}
                                        aria-label={`Remove ${u.display_name}`}
                                    >
                                        ×
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}

                    {error && <div className={styles.error}>⚠️ {error}</div>}

                    <div className={styles.actions}>
                        <button type="button" className={styles.cancelBtn} onClick={onClose}>
                            Cancel
                        </button>
                        <button
                            id="create-group-submit"
                            type="submit"
                            className={styles.createBtn}
                            disabled={loading}
                        >
                            {loading ? <span className={styles.spinner} /> : '🚀 Create Group'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}
