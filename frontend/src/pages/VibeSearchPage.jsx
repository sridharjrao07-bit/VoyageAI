import { useState } from 'react'
import { motion } from 'framer-motion'
import UploadAVibe from '../components/UploadAVibe'
import SwipeCalibrator from '../components/SwipeCalibrator'

const TABS = [
    { id: 'upload', label: 'Upload a Vibe', icon: '📸' },
    { id: 'swipe', label: 'Swipe to Calibrate', icon: '👆' },
]

export default function VibeSearchPage() {
    const [activeTab, setActiveTab] = useState('upload')
    const [vibeResults, setVibeResults] = useState([])

    const handleResultsReady = (results) => {
        setVibeResults(results)
    }

    return (
        <div className="page-wrapper">
            <div className="section">
                {/* Header */}
                <div className="text-center mb-12">
                    <motion.span
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="inline-block text-xs font-bold tracking-[0.15em] uppercase text-sage-500 mb-3"
                    >
                        AI Visual Search
                    </motion.span>
                    <motion.h1
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="font-serif text-4xl md:text-5xl font-extrabold text-gray-800 mb-4"
                    >
                        Find Your <span className="gradient-text">Vibe</span>
                    </motion.h1>
                    <motion.p
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="text-gray-500 max-w-lg mx-auto"
                    >
                        Upload a photo that captures the travel experience you're looking for. Our CLIP AI will find destinations that match the mood and aesthetic.
                    </motion.p>
                </div>

                {/* Tab Switcher */}
                <div className="flex justify-center mb-10">
                    <div className="inline-flex bg-white/70 backdrop-blur-sm rounded-2xl p-1.5 border border-sage-100 shadow-sm">
                        {TABS.map(tab => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`
                                    relative px-6 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200
                                    ${activeTab === tab.id
                                        ? 'text-white'
                                        : 'text-gray-500 hover:text-gray-700'}
                                `}
                            >
                                {activeTab === tab.id && (
                                    <motion.div
                                        layoutId="activeVibeTab"
                                        className="absolute inset-0 bg-gradient-to-r from-sage-400 to-sage-500 rounded-xl shadow-md"
                                        transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                                    />
                                )}
                                <span className="relative z-10 flex items-center gap-2">
                                    {tab.icon} {tab.label}
                                    {tab.id === 'swipe' && vibeResults.length > 0 && (
                                        <span className={`
                                            w-5 h-5 rounded-full text-xs flex items-center justify-center font-bold
                                            ${activeTab === tab.id
                                                ? 'bg-white/30 text-white'
                                                : 'bg-sage-100 text-sage-600'}
                                        `}>
                                            {vibeResults.length}
                                        </span>
                                    )}
                                </span>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Tab Content */}
                <motion.div
                    key={activeTab}
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                >
                    {activeTab === 'upload' && (
                        <UploadAVibe onResultsReady={handleResultsReady} />
                    )}
                    {activeTab === 'swipe' && (
                        <SwipeCalibrator destinations={vibeResults} />
                    )}
                </motion.div>
            </div>
        </div>
    )
}
