import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <BrowserRouter>
            <App />
            <Toaster
                position="top-right"
                toastOptions={{
                    style: {
                        background: '#0d1526',
                        color: '#f0f4ff',
                        border: '1px solid rgba(99,102,241,0.3)',
                        borderRadius: '12px',
                        fontSize: '0.875rem',
                    },
                    success: { iconTheme: { primary: '#10b981', secondary: '#0d1526' } },
                    error: { iconTheme: { primary: '#f43f5e', secondary: '#0d1526' } },
                }}
            />
        </BrowserRouter>
    </React.StrictMode>
)
