import axios from 'axios'

// In production (Vercel), call Render backend directly to avoid Vercel's 30s rewrite timeout.
// In local dev, Vite proxy handles /api -> localhost:8000.
const BACKEND_URL = import.meta.env.PROD
    ? 'https://voyageai-production.up.railway.app'
    : '/api'

const api = axios.create({
    baseURL: BACKEND_URL,
    timeout: 60000,
    headers: { 'Content-Type': 'application/json' },
})

// Long-timeout instance for endpoints that batch many external API calls (e.g. 100 photo enrichments)
const apiLong = axios.create({
    baseURL: BACKEND_URL,
    timeout: 120000,
    headers: { 'Content-Type': 'application/json' },
})

// ── Destinations ──────────────────────────────
export const getDestinations = (params = {}) => {
    // Use long timeout when fetching photos (batches 100 external API calls)
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

export default api
