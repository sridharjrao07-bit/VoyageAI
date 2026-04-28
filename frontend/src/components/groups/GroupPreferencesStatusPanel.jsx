import { useState, useEffect, useCallback } from 'react'
import { getPreferencesStatus, runGroupRecommendation } from '../../api/tourismApi'
import styles from './GroupPreferencesStatusPanel.module.css'

export default function GroupPreferencesStatusPanel({ groupId, onResults }) {
    const [status, setStatus] = useState(null)
    const [loading, setLoading] = useState(true)
    const [running, setRunning] = useState(false)
    const [error, setError] = useState('')

    const fetchStatus = useCallback(async () => {
        try {
            const data = await getPreferencesStatus(groupId)
            setStatus(data)
            setError('')
        } catch {
            setError('Could not load status')
        } finally {
            setLoading(false)
        }
    }, [groupId])

    // Poll every 15 seconds
    useEffect(() => {
        fetchStatus()
        const interval = setInterval(fetchStatus, 15000)
        return () => clearInterval(interval)
    }, [fetchStatus])

    const handleRunRecommendation = async () => {
        setRunning(true)
        setError('')
        try {
            const results = await runGroupRecommendation(groupId)
            onResults?.(results)
        } catch (err) {
            setError(err?.response?.data?.detail || 'Recommendation failed')
        } finally {
            setRunning(false)
        }
    }

    if (loading) {
        return (
            <div className={styles.panel}>
                <div className={styles.shimmerRow} />
                <div className={styles.shimmerRow} />
                <div className={styles.shimmerRow} style={{ width: '60%' }} />
            </div>
        )
    }

    if (!status) return null

    const allReady = status.all_ready
    const total = status.total_members

    return (
        <div className={styles.panel}>
            <div className={styles.header}>
                <h3 className={styles.title}>Group Readiness</h3>
                <div className={styles.progressPill}>
                    <span className={allReady ? styles.allReadyDot : styles.pendingDot} />
                    {status.submitted_count}/{total} ready
                </div>
            </div>

            {/* Progress bar */}
            <div className={styles.progressBar}>
                <div
                    className={styles.progressFill}
                    style={{ width: `${total > 0 ? (status.submitted_count / total) * 100 : 0}%` }}
                />
            </div>

            {/* Member list */}
            <div className={styles.memberList}>
                {status.submitted?.map(u => (
                    <div key={u.user_id} className={`${styles.memberRow} ${styles.submitted}`}>
                        <span className={styles.avatar}>{u.avatar_emoji}</span>
                        <span className={styles.name}>{u.display_name}</span>
                        <span className={styles.statusIcon}>✅</span>
                        <span className={styles.statusLabel}>Ready</span>
                    </div>
                ))}
                {status.pending?.map(u => (
                    <div key={u.user_id} className={`${styles.memberRow} ${styles.pending}`}>
                        <span className={styles.avatar}>{u.avatar_emoji}</span>
                        <span className={styles.name}>{u.display_name}</span>
                        <span className={styles.statusIcon}>⏳</span>
                        <span className={styles.statusLabel}>Pending</span>
                    </div>
                ))}
            </div>

            {error && <div className={styles.error}>⚠️ {error}</div>}

            <div className={styles.footer}>
                <p className={styles.pollingNote}>
                    {allReady
                        ? '🎉 Everyone\'s ready! Run the AI recommendation to find your perfect destination.'
                        : 'Waiting for all members to submit their preferences. Checking every 15s…'
                    }
                </p>
                <button
                    id="run-recommendations-btn"
                    className={styles.runBtn}
                    onClick={handleRunRecommendation}
                    disabled={!allReady || running}
                >
                    {running ? (
                        <><span className={styles.spinner} /> Finding destinations…</>
                    ) : (
                        '🔮 Run Group Recommendations'
                    )}
                </button>
            </div>
        </div>
    )
}
