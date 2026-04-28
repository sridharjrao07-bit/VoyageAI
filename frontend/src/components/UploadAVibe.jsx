import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { visualSearch } from '../api/tourismApi'

export default function UploadAVibe({ onResultsReady }) {
    const [preview, setPreview] = useState(null)
    const [isDragging, setIsDragging] = useState(false)
    const [loading, setLoading] = useState(false)
    const [results, setResults] = useState(null)
    const [error, setError] = useState(null)

    const handleFile = useCallback(async (file) => {
        if (!file || !file.type.startsWith('image/')) return
        setPreview(URL.createObjectURL(file))
        setError(null)
        setLoading(true)
        try {
            const data = await visualSearch(file, 10)
            setResults(data.results)
            if (onResultsReady) onResultsReady(data.results)
        } catch (err) {
            setError('Visual search failed. Please try another image.')
            console.error(err)
        } finally {
            setLoading(false)
        }
    }, [onResultsReady])

    const onDrop = useCallback((e) => {
        e.preventDefault()
        setIsDragging(false)
        const file = e.dataTransfer.files[0]
        handleFile(file)
    }, [handleFile])

    const onDragOver = (e) => { e.preventDefault(); setIsDragging(true) }
    const onDragLeave = () => setIsDragging(false)

    const onFileSelect = (e) => {
        const file = e.target.files[0]
        handleFile(file)
    }

    const reset = () => {
        setPreview(null)
        setResults(null)
        setError(null)
    }

    return (
        <div className="w-full max-w-2xl mx-auto">
            {/* Drop Zone */}
            <motion.div
                onDrop={onDrop}
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                className={`
                    relative rounded-3xl border-2 border-dashed transition-all duration-300 cursor-pointer
                    ${isDragging
                        ? 'border-sage-400 bg-sage-50/80 scale-[1.02]'
                        : 'border-sage-200 bg-white/60 hover:border-sage-300 hover:bg-white/80'}
                    ${preview ? 'p-4' : 'p-12'}
                `}
                whileHover={{ y: -2 }}
                onClick={() => !preview && document.getElementById('vibe-upload-input').click()}
            >
                <input
                    id="vibe-upload-input"
                    type="file"
                    accept="image/*"
                    onChange={onFileSelect}
                    className="hidden"
                />

                <AnimatePresence mode="wait">
                    {!preview ? (
                        <motion.div
                            key="placeholder"
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="flex flex-col items-center gap-4 text-center"
                        >
                            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-sage-400 to-sage-500 flex items-center justify-center shadow-lg">
                                <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.41a2.25 2.25 0 013.182 0l2.909 2.91m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
                                </svg>
                            </div>
                            <div>
                                <p className="text-lg font-semibold text-gray-700">Upload a Vibe</p>
                                <p className="text-sm text-gray-500 mt-1">
                                    Drag & drop an image, or click to browse
                                </p>
                                <p className="text-xs text-gray-400 mt-2">
                                    JPEG, PNG, WebP — we'll find destinations that match the mood
                                </p>
                            </div>
                        </motion.div>
                    ) : (
                        <motion.div
                            key="preview"
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            className="relative"
                        >
                            <img
                                src={preview}
                                alt="Uploaded vibe"
                                className="w-full h-64 object-cover rounded-2xl shadow-md"
                            />
                            <button
                                onClick={(e) => { e.stopPropagation(); reset() }}
                                className="absolute top-3 right-3 w-8 h-8 rounded-full bg-black/50 text-white flex items-center justify-center hover:bg-black/70 transition-colors text-sm"
                            >
                                ✕
                            </button>
                            {loading && (
                                <div className="absolute inset-0 bg-white/60 backdrop-blur-sm rounded-2xl flex items-center justify-center">
                                    <div className="flex flex-col items-center gap-3">
                                        <div className="w-10 h-10 border-3 border-sage-200 border-t-sage-500 rounded-full animate-spin" />
                                        <p className="text-sm font-medium text-sage-600">Reading your vibe…</p>
                                    </div>
                                </div>
                            )}
                        </motion.div>
                    )}
                </AnimatePresence>
            </motion.div>

            {/* Error */}
            {error && (
                <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-center text-red-500 text-sm mt-4"
                >
                    {error}
                </motion.p>
            )}

            {/* Results Grid */}
            {results && results.length > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="mt-8"
                >
                    <h3 className="text-lg font-bold text-gray-800 mb-4">
                        ✨ Destinations matching your vibe
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {results.map((dest, i) => (
                            <motion.div
                                key={dest.id}
                                initial={{ opacity: 0, y: 12 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.1 * i }}
                                className="bg-white/70 backdrop-blur-sm rounded-2xl p-4 border border-sage-100 hover:border-sage-300 hover:shadow-lg transition-all group"
                            >
                                <div className="flex justify-between items-start mb-2">
                                    <div>
                                        <h4 className="font-bold text-gray-800 group-hover:text-sage-500 transition-colors">
                                            {dest.name}
                                        </h4>
                                        <p className="text-xs text-gray-500">{dest.country} · {dest.continent}</p>
                                    </div>
                                    <span className="text-xs font-semibold px-2 py-1 rounded-full bg-sage-50 text-sage-600">
                                        {Math.round(dest.visual_similarity * 100)}% match
                                    </span>
                                </div>
                                <p className="text-sm text-gray-600 line-clamp-2 mb-2">
                                    {dest.description}
                                </p>
                                <div className="flex flex-wrap gap-1">
                                    {dest.tags?.split(',').slice(0, 3).map(tag => (
                                        <span key={tag} className="text-xs px-2 py-0.5 rounded-full bg-sage-50 text-sage-500 border border-sage-100">
                                            {tag.trim()}
                                        </span>
                                    ))}
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </motion.div>
            )}
        </div>
    )
}
