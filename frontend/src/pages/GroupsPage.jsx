import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../contexts/AuthContext'
import AuthModal from '../components/AuthModal'
import GroupCreatorModal from '../components/groups/GroupCreatorModal'
import MemberPreferencesForm from '../components/groups/MemberPreferencesForm'
import GroupPreferencesStatusPanel from '../components/groups/GroupPreferencesStatusPanel'
import RecommendationResultsPanel from '../components/groups/RecommendationResultsPanel'
import { getMyGroups, getGroupDetails } from '../api/tourismApi'
import styles from './GroupsPage.module.css'

export default function GroupsPage() {
    const { user, isLoading: authLoading } = useAuth()
    const [showAuthModal, setShowAuthModal] = useState(false)
    const [showCreateModal, setShowCreateModal] = useState(false)
    const [groups, setGroups] = useState([])
    const [selectedGroupId, setSelectedGroupId] = useState(null)
    const [selectedGroup, setSelectedGroup] = useState(null)
    const [groupLoading, setGroupLoading] = useState(false)
    const [results, setResults] = useState(null)
    const [tab, setTab] = useState('preferences') // 'preferences' | 'status' | 'results'

    const loadGroups = useCallback(async () => {
        if (!user) return
        try {
            const data = await getMyGroups()
            setGroups(data.groups || [])
        } catch {
            setGroups([])
        }
    }, [user])

    const loadGroupDetails = useCallback(async (groupId) => {
        setGroupLoading(true)
        try {
            const data = await getGroupDetails(groupId)
            setSelectedGroup(data)
        } catch {
            setSelectedGroup(null)
        } finally {
            setGroupLoading(false)
        }
    }, [])

    useEffect(() => { if (user) loadGroups() }, [user, loadGroups])
    useEffect(() => {
        if (selectedGroupId) {
            setResults(null)
            setTab('preferences')
            loadGroupDetails(selectedGroupId)
        }
    }, [selectedGroupId, loadGroupDetails])

    // If not logged in, show auth prompt
    if (authLoading) {
        return (
            <div className={styles.loadingScreen}>
                <div className={styles.spinner} />
                <p>Loading…</p>
            </div>
        )
    }

    if (!user) {
        return (
            <div className={styles.authPrompt}>
                {showAuthModal && <AuthModal onClose={() => setShowAuthModal(false)} />}
                <div className={styles.authCard}>
                    <div className={styles.authIcon}>✈️</div>
                    <h1 className={styles.authTitle}>Plan Together</h1>
                    <p className={styles.authDesc}>
                        Create trip groups with friends, submit individual preferences, and discover destinations that make <em>everyone</em> happy — powered by fairness-aware AI.
                    </p>
                    <button
                        id="auth-prompt-login-btn"
                        className={styles.primaryBtn}
                        onClick={() => setShowAuthModal(true)}
                    >
                        🚀 Sign In to Get Started
                    </button>
                </div>
            </div>
        )
    }

    return (
        <div className={styles.page}>
            {/* Modals */}
            {showCreateModal && (
                <GroupCreatorModal
                    onClose={() => setShowCreateModal(false)}
                    onCreated={() => { loadGroups(); setShowCreateModal(false) }}
                />
            )}

            {/* Sidebar */}
            <aside className={styles.sidebar}>
                <div className={styles.sidebarHeader}>
                    <div className={styles.userInfo}>
                        <span className={styles.userAvatar}>{user.avatar_emoji}</span>
                        <div>
                            <p className={styles.userName}>{user.display_name}</p>
                            <p className={styles.userHandle}>@{user.username}</p>
                        </div>
                    </div>
                    <button
                        id="new-group-btn"
                        className={styles.newGroupBtn}
                        onClick={() => setShowCreateModal(true)}
                    >
                        + New Group
                    </button>
                </div>

                <div className={styles.groupList}>
                    {groups.length === 0 && (
                        <div className={styles.emptyGroups}>
                            <p>No groups yet.</p>
                            <p>Create one to start planning!</p>
                        </div>
                    )}
                    {groups.map(g => (
                        <button
                            key={g.id}
                            id={`group-item-${g.id}`}
                            className={`${styles.groupItem} ${selectedGroupId === g.id ? styles.activeGroup : ''}`}
                            onClick={() => setSelectedGroupId(g.id)}
                        >
                            <div className={styles.groupItemName}>{g.name}</div>
                            <div className={styles.groupItemMeta}>
                                <span>{g.member_count} members</span>
                                <span className={`${styles.statusDot} ${g.preferences_submitted ? styles.readyDot : styles.waitingDot}`} />
                                <span className={styles.statusBadge}>{g.status}</span>
                            </div>
                        </button>
                    ))}
                </div>
            </aside>

            {/* Main content */}
            <main className={styles.main}>
                {!selectedGroupId ? (
                    <div className={styles.welcomeState}>
                        <div className={styles.welcomeIcon}>🗺️</div>
                        <h2>Select a group to start planning</h2>
                        <p>Or create a new trip group and invite your travel crew.</p>
                        <button
                            className={styles.primaryBtn}
                            onClick={() => setShowCreateModal(true)}
                        >
                            ✈️ Create a Trip Group
                        </button>
                    </div>
                ) : groupLoading ? (
                    <div className={styles.loading}>
                        <div className={styles.spinner} />
                        <p>Loading group…</p>
                    </div>
                ) : selectedGroup ? (
                    <div className={styles.groupContent}>
                        {/* Group header */}
                        <div className={styles.groupHeader}>
                            <div>
                                <h1 className={styles.groupName}>{selectedGroup.name}</h1>
                                <p className={styles.groupMeta}>
                                    {selectedGroup.members?.length} members
                                    · Created by {selectedGroup.members?.find(m => m.user_id === selectedGroup.created_by)?.display_name || 'owner'}
                                </p>
                            </div>
                            <div className={styles.memberAvatars}>
                                {selectedGroup.members?.slice(0, 5).map(m => (
                                    <span key={m.user_id} className={styles.memberAvatar} title={m.display_name}>
                                        {m.avatar_emoji}
                                    </span>
                                ))}
                            </div>
                        </div>

                        {/* Tabs */}
                        <div className={styles.tabs}>
                            {[
                                { id: 'preferences', label: '✏️ My Preferences' },
                                { id: 'status', label: '👥 Group Status' },
                                { id: 'results', label: '🎯 Results', disabled: !results },
                            ].map(t => (
                                <button
                                    id={`tab-${t.id}`}
                                    key={t.id}
                                    className={`${styles.tab} ${tab === t.id ? styles.activeTab : ''} ${t.disabled ? styles.disabledTab : ''}`}
                                    onClick={() => !t.disabled && setTab(t.id)}
                                    disabled={t.disabled}
                                >
                                    {t.label}
                                </button>
                            ))}
                        </div>

                        {/* Tab content */}
                        <div className={styles.tabContent}>
                            {tab === 'preferences' && (
                                <MemberPreferencesForm
                                    groupId={selectedGroupId}
                                    onSaved={() => setTab('status')}
                                />
                            )}
                            {tab === 'status' && (
                                <GroupPreferencesStatusPanel
                                    groupId={selectedGroupId}
                                    onResults={(res) => {
                                        setResults(res)
                                        setTab('results')
                                    }}
                                />
                            )}
                            {tab === 'results' && results && (
                                <RecommendationResultsPanel results={results} />
                            )}
                        </div>
                    </div>
                ) : null}
            </main>
        </div>
    )
}
