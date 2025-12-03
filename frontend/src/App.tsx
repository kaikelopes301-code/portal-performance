import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import ExecutionPage from './pages/ExecutionPage'
import PreviewPage from './pages/PreviewPage'
import SettingsPage from './pages/SettingsPage'
import HelpPage from './pages/HelpPage'
import { ToastProvider } from './components/ui/toast'

function App() {
    return (
        <ToastProvider>
            <BrowserRouter>
                <div className="min-h-screen bg-gray-50">
                    <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/execution" element={<ExecutionPage />} />
                        <Route path="/preview" element={<PreviewPage />} />
                        <Route path="/settings" element={<SettingsPage />} />
                        <Route path="/help" element={<HelpPage />} />
                    </Routes>
                </div>
            </BrowserRouter>
        </ToastProvider>
    )
}

export default App
