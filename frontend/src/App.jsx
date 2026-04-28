import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import LandingPage from './pages/LandingPage'
import ProfilePage from './pages/ProfilePage'
import RecommendationsPage from './pages/RecommendationsPage'
import DashboardPage from './pages/DashboardPage'
import ExplorePage from './pages/ExplorePage'
import ChatPage from './pages/ChatPage'
import VibeSearchPage from './pages/VibeSearchPage'
import GroupsPage from './pages/GroupsPage'
import { AuthProvider } from './contexts/AuthContext'

export default function App() {
    return (
        <AuthProvider>
            <Navbar />
            <Routes>
                <Route path="/" element={<LandingPage />} />
                <Route path="/profile" element={<ProfilePage />} />
                <Route path="/recommendations" element={<RecommendationsPage />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/explore" element={<ExplorePage />} />
                <Route path="/chat" element={<ChatPage />} />
                <Route path="/vibe" element={<VibeSearchPage />} />
                <Route path="/groups" element={<GroupsPage />} />
            </Routes>
        </AuthProvider>
    )
}
