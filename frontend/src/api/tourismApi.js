import axios from 'axios'

/**
 * API Base URL Strategy:
 *
 * Development (npm run dev):
 *   VITE_API_URL is unset → falls back to '' (empty string)
 *   Vite proxy handles routing:
 *     /auth/*  → http://127.0.0.1:8001/auth/*  (direct passthrough)
 *     /api/*   → http://127.0.0.1:8001/*       (strips /api prefix)
 *
 * Production (Vercel):
 *   VITE_API_URL = 'https://<username>-allora-backend.hf.space'
 *   All requests go directly to the HF Spaces backend (no proxy needed).
 *
 *   api calls:    /destinations → VITE_API_URL/destinations  ✓
 *   auth calls:   /auth/me      → VITE_API_URL/auth/me       ✓
 */

// Resolve backend base URL from env (set in Vercel dashboard or .env.production)
const BACKEND_URL = import.meta.env.VITE_API_URL || ''

// Primary axios instance — for all /destinations, /recommend, /groups etc.
// Dev: uses /api proxy (Vite strips the prefix → backend /destinations)
// Prod: uses VITE_API_URL directly (no prefix stripping needed)
const api = axios.create({
    baseURL: BACKEND_URL ? `${BACKEND_URL}` : '/api',
    timeout: 60000,
    headers: { 'Content-Type': 'application/json' },
})

// Long-timeout instance for batch photo fetches
const apiLong = axios.create({
    baseURL: BACKEND_URL ? `${BACKEND_URL}` : '/api',
    timeout: 120000,
    headers: { 'Content-Type': 'application/json' },
})

// Auth instance — /auth/* routes
// Dev: '' base, /auth/* goes through Vite proxy
// Prod: VITE_API_URL base, /auth/* goes directly to HF Spaces backend
const authApi = axios.create({
    baseURL: BACKEND_URL ? `${BACKEND_URL}` : '',
    timeout: 30000,
    headers: { 'Content-Type': 'application/json' },
})

// Keep Authorization header in sync on authApi too
api.interceptors.request.use(config => {
    const token = localStorage.getItem('allora_token')
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
})
authApi.interceptors.request.use(config => {
    const token = localStorage.getItem('allora_token')
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
})

// ── Destinations ──────────────────────────────
export const getDestinations = (params = {}) => {
    const instance = params.include_photos ? apiLong : api
    return instance.get('/destinations', { params }).then(r => r.data)
}

export const getDestination = (id, includePois = false) =>
    api.get(`/destinations/${id}`, { params: { include_pois: includePois } }).then(r => r.data)

// ── Recommendations ───────────────────────────
export const getRecommendations = (payload) =>
    api.post('/recommend', payload).then(r => r.data)

// ── Feedback ──────────────────────────────────
export const submitFeedback = (payload) =>
    api.post('/feedback', payload).then(r => r.data)

// ── Feedback Loop (RL) — Likes / Bucket List ──
export const saveLike = (payload) =>
    api.post('/likes', payload).then(r => r.data)

export const getUserLikes = (userId) =>
    api.get(`/likes/${userId}`).then(r => r.data)

// ── Semantic Search ───────────────────────────
export const semanticSearch = (q, topN = 10) =>
    api.get('/search', { params: { q, top_n: topN } }).then(r => r.data)

// ── Performance Metrics ───────────────────────
export const getPerformance = () =>
    api.get('/performance').then(r => r.data)

// ── Users ─────────────────────────────────────
export const getUsers = () =>
    api.get('/users').then(r => r.data)

export const getUser = (userId) =>
    api.get(`/users/${userId}`).then(r => r.data)

// ── Outdoor Features (Overpass) ───────────────
export const getOutdoorFeatures = (destId) =>
    api.get(`/destinations/${destId}/outdoor`).then(r => r.data)

// ── Weather (OpenWeatherMap) ──────────────────
export const getWeather = (destId) =>
    api.get(`/destinations/${destId}/weather`).then(r => r.data)

// ── Trekking Routes (OpenRouteService) ────────
export const getTrekkingRoute = (params) =>
    api.get('/trekking-route', { params }).then(r => r.data)

// ── Chat (Grok AI) ────────────────────────────
export const sendChatMessage = (payload) =>
    api.post('/chat', payload).then(r => r.data)

// ── Visual (CLIP) Search ──────────────────────
export const visualSearch = (file, topN = 10) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/search/visual?top_n=${topN}`, formData, {
        timeout: 30000,
        headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data)
}

// ────────────────────────────────────────────────────────────────
// Auth Endpoints  (proxy: /auth/* → backend /auth/*)
// ────────────────────────────────────────────────────────────────

export const authLogin = (username, password) =>
    authApi.post('/auth/login', { username, password }).then(r => r.data)

export const authRegister = (payload) =>
    authApi.post('/auth/register', payload).then(r => r.data)

export const authMe = () =>
    authApi.get('/auth/me').then(r => r.data)

/** Search users by username/name for group invites */
export const searchUsers = (q = '') =>
    authApi.get('/auth/users', { params: { q } }).then(r => r.data)

// ────────────────────────────────────────────────────────────────
// Group Consensus Trip Recommendation Endpoints
// (proxy: /api/groups → backend /groups via /api strip)
// ────────────────────────────────────────────────────────────────

/** List all groups the current user belongs to */
export const getMyGroups = () =>
    api.get('/groups').then(r => r.data)

/** Get a group's full details + member list */
export const getGroupDetails = (groupId) =>
    api.get(`/groups/${groupId}`).then(r => r.data)

/** Create a new trip group */
export const createGroup = (payload) =>
    api.post('/groups', payload).then(r => r.data)

/** Add a member to a group (owner only) */
export const addGroupMember = (groupId, userId) =>
    api.post(`/groups/${groupId}/members`, { user_id: userId }).then(r => r.data)

/** Remove a member from a group */
export const removeGroupMember = (groupId, userId) =>
    api.delete(`/groups/${groupId}/members/${userId}`).then(r => r.data)

/** Submit / update the current user's preferences for a group */
export const submitGroupPreferences = (groupId, payload) =>
    api.put(`/groups/${groupId}/preferences`, payload).then(r => r.data)

/** Get preference submission status for all group members */
export const getPreferencesStatus = (groupId) =>
    api.get(`/groups/${groupId}/preferences/status`).then(r => r.data)

/** Trigger a fairness-aware recommendation run */
export const runGroupRecommendation = (groupId) =>
    api.post(`/groups/${groupId}/recommend`).then(r => r.data)

/** Fetch a previously saved recommendation run */
export const getRecommendationRun = (groupId, runId) =>
    api.get(`/groups/${groupId}/recommendations/${runId}`).then(r => r.data)

export default api
