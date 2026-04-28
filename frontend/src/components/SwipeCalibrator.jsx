import { useState, useCallback } from 'react'
import { motion, useMotionValue, useTransform, AnimatePresence } from 'framer-motion'
import { saveLike, submitFeedback } from '../api/tourismApi'

const SWIPE_THRESHOLD = 120

function SwipeCard({ dest, onSwipe, isTop }) {
    const x = useMotionValue(0)
    const rotate = useTransform(x, [-300, 0, 300], [-18, 0, 18])
    const likeOpacity = useTransform(x, [0, SWIPE_THRESHOLD], [0, 1])
    const nopeOpacity = useTransform(x, [-SWIPE_THRESHOLD, 0], [1, 0])

    const handleDragEnd = (_, info) => {
        if (info.offset.x > SWIPE_THRESHOLD) {
            onSwipe('right')
        } else if (info.offset.x < -SWIPE_THRESHOLD) {
            onSwipe('left')
        }
    }

    return (
        <motion.div
            className="absolute inset-0"
            style={{ x, rotate, zIndex: isTop ? 10 : 0 }}
            drag={isTop ? 'x' : false}
            dragConstraints={{ left: 0, right: 0 }}
            dragElastic={0.9}
            onDragEnd={handleDragEnd}
            initial={{ scale: isTop ? 1 : 0.95, opacity: isTop ? 1 : 0.7 }}
            animate={{ scale: isTop ? 1 : 0.95, opacity: isTop ? 1 : 0.7 }}
            exit={{ x: x.get() > 0 ? 400 : -400, opacity: 0, transition: { duration: 0.3 } }}
        >
            <div className="w-full h-full rounded-3xl overflow-hidden bg-white shadow-2xl border border-sage-100 relative select-none">
                {/* Destination Image Placeholder (gradient background) */}
                <div className="h-3/5 relative overflow-hidden">
                    <div
                        className="absolute inset-0"
                        style={{
                            background: `linear-gradient(135deg, 
                                hsl(${(dest.name?.charCodeAt(0) || 0) * 3}, 40%, 65%) 0%, 
                                hsl(${(dest.name?.charCodeAt(1) || 0) * 5}, 50%, 45%) 100%)`
                        }}
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent" />
                    <div className="absolute bottom-4 left-5 right-5">
                        <h3 className="text-2xl font-bold text-white drop-shadow-lg">
                            {dest.name}
                        </h3>
                        <p className="text-white/80 text-sm mt-1">{dest.country} · {dest.continent}</p>
                    </div>

                    {/* Like / Nope Indicators */}
                    {isTop && (
                        <>
                            <motion.div
                                className="absolute top-6 right-6 px-4 py-2 rounded-xl border-3 border-green-400 bg-green-400/20 backdrop-blur-sm"
                                style={{ opacity: likeOpacity }}
                            >
                                <span className="text-green-400 font-black text-xl tracking-wider">LIKE</span>
                            </motion.div>
                            <motion.div
                                className="absolute top-6 left-6 px-4 py-2 rounded-xl border-3 border-red-400 bg-red-400/20 backdrop-blur-sm"
                                style={{ opacity: nopeOpacity }}
                            >
                                <span className="text-red-400 font-black text-xl tracking-wider">NOPE</span>
                            </motion.div>
                        </>
                    )}
                </div>

                {/* Info */}
                <div className="h-2/5 p-5 flex flex-col justify-between">
                    <div>
                        <p className="text-sm text-gray-600 line-clamp-3 leading-relaxed">
                            {dest.description}
                        </p>
                    </div>
                    <div className="flex flex-wrap gap-1.5 mt-2">
                        {dest.tags?.split(',').slice(0, 4).map(tag => (
                            <span
                                key={tag}
                                className="text-xs px-2.5 py-1 rounded-full bg-sage-50 text-sage-600 border border-sage-100 font-medium"
                            >
                                {tag.trim()}
                            </span>
                        ))}
                        {dest.avg_cost_usd > 0 && (
                            <span className="text-xs px-2.5 py-1 rounded-full bg-terracotta-400/10 text-terracotta-500 border border-terracotta-400/20 font-medium">
                                ${Math.round(dest.avg_cost_usd)}
                            </span>
                        )}
                    </div>
                </div>
            </div>
        </motion.div>
    )
}

export default function SwipeCalibrator({ destinations, userId = 'demo_user', sessionId = 'demo_session' }) {
    const [currentIndex, setCurrentIndex] = useState(0)
    const [swipedCount, setSwipedCount] = useState(0)
    const [likedCount, setLikedCount] = useState(0)

    const handleSwipe = useCallback(async (direction) => {
        const dest = destinations[currentIndex]
        if (!dest) return

        setCurrentIndex(prev => prev + 1)
        setSwipedCount(prev => prev + 1)

        try {
            if (direction === 'right') {
                setLikedCount(prev => prev + 1)
                // Like + positive feedback
                await Promise.all([
                    saveLike({ user_id: userId, destination_id: String(dest.id) }),
                    submitFeedback({
                        session_id: sessionId,
                        destination_id: String(dest.id),
                        vote: 1,
                    }),
                ])
            } else {
                // Negative feedback only
                await submitFeedback({
                    session_id: sessionId,
                    destination_id: String(dest.id),
                    vote: -1,
                })
            }
        } catch (err) {
            console.error('[Swipe] Feedback error:', err)
        }
    }, [currentIndex, destinations, userId, sessionId])

    const remaining = destinations.length - currentIndex
    const progress = destinations.length > 0
        ? Math.round((swipedCount / destinations.length) * 100)
        : 0

    if (!destinations || destinations.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="text-5xl mb-4">🗺️</div>
                <p className="text-gray-500">Upload a vibe image first to get destinations to swipe!</p>
            </div>
        )
    }

    if (remaining <= 0) {
        return (
            <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex flex-col items-center justify-center py-16 text-center"
            >
                <div className="text-6xl mb-4">🎉</div>
                <h3 className="text-2xl font-bold text-gray-800 mb-2">Calibration Complete!</h3>
                <p className="text-gray-500 mb-4">
                    You liked {likedCount} out of {swipedCount} destinations
                </p>
                <div className="flex gap-6 text-sm">
                    <div className="flex flex-col items-center">
                        <span className="text-2xl font-bold text-sage-500">{likedCount}</span>
                        <span className="text-gray-400">Liked</span>
                    </div>
                    <div className="flex flex-col items-center">
                        <span className="text-2xl font-bold text-red-400">{swipedCount - likedCount}</span>
                        <span className="text-gray-400">Passed</span>
                    </div>
                </div>
                <p className="text-xs text-gray-400 mt-6 max-w-xs">
                    Your preferences have been saved. Future recommendations will prioritize destinations that match your taste.
                </p>
            </motion.div>
        )
    }

    return (
        <div className="w-full max-w-sm mx-auto">
            {/* Progress */}
            <div className="mb-4 flex items-center gap-3">
                <div className="flex-1 h-2 bg-sage-100 rounded-full overflow-hidden">
                    <motion.div
                        className="h-full bg-gradient-to-r from-sage-400 to-sage-500 rounded-full"
                        initial={{ width: 0 }}
                        animate={{ width: `${progress}%` }}
                        transition={{ type: 'spring', stiffness: 100 }}
                    />
                </div>
                <span className="text-xs text-gray-400 font-medium whitespace-nowrap">
                    {remaining} left
                </span>
            </div>

            {/* Card Stack */}
            <div className="relative w-full" style={{ aspectRatio: '3/4' }}>
                <AnimatePresence>
                    {destinations.slice(currentIndex, currentIndex + 2).reverse().map((dest, i, arr) => (
                        <SwipeCard
                            key={dest.id}
                            dest={dest}
                            isTop={i === arr.length - 1}
                            onSwipe={handleSwipe}
                        />
                    ))}
                </AnimatePresence>
            </div>

            {/* Manual Buttons */}
            <div className="flex justify-center gap-6 mt-6">
                <button
                    onClick={() => handleSwipe('left')}
                    className="w-14 h-14 rounded-full bg-white shadow-lg border border-red-100 flex items-center justify-center text-2xl hover:scale-110 hover:shadow-xl transition-all active:scale-95"
                >
                    ✕
                </button>
                <button
                    onClick={() => handleSwipe('right')}
                    className="w-14 h-14 rounded-full bg-white shadow-lg border border-green-100 flex items-center justify-center text-2xl hover:scale-110 hover:shadow-xl transition-all active:scale-95"
                >
                    ♥
                </button>
            </div>
        </div>
    )
}
