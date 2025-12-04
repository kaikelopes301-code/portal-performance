import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import ExecutionPage from './pages/ExecutionPage'
import PreviewPage from './pages/PreviewPage'
import SettingsPage from './pages/SettingsPage'
import HelpPage from './pages/HelpPage'
import LoginPage from './pages/LoginPage'
import { ToastProvider } from './components/ui/toast'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'

// Componente para redirecionar usuários já logados
function PublicRoute({ children }: { children: React.ReactNode }) {
    const { isAuthenticated, isLoading } = useAuth()
    
    if (isLoading) {
        return null
    }
    
    if (isAuthenticated) {
        return <Navigate to="/" replace />
    }
    
    return <>{children}</>
}

function AppRoutes() {
    return (
        <Routes>
            {/* Rota pública - Login */}
            <Route 
                path="/login" 
                element={
                    <PublicRoute>
                        <LoginPage />
                    </PublicRoute>
                } 
            />
            
            {/* Rotas protegidas */}
            <Route 
                path="/" 
                element={
                    <ProtectedRoute>
                        <div className="min-h-screen bg-gray-50">
                            <Dashboard />
                        </div>
                    </ProtectedRoute>
                } 
            />
            <Route 
                path="/execution" 
                element={
                    <ProtectedRoute>
                        <div className="min-h-screen bg-gray-50">
                            <ExecutionPage />
                        </div>
                    </ProtectedRoute>
                } 
            />
            <Route 
                path="/preview" 
                element={
                    <ProtectedRoute>
                        <div className="min-h-screen bg-gray-50">
                            <PreviewPage />
                        </div>
                    </ProtectedRoute>
                } 
            />
            <Route 
                path="/settings" 
                element={
                    <ProtectedRoute>
                        <div className="min-h-screen bg-gray-50">
                            <SettingsPage />
                        </div>
                    </ProtectedRoute>
                } 
            />
            <Route 
                path="/help" 
                element={
                    <ProtectedRoute>
                        <div className="min-h-screen bg-gray-50">
                            <HelpPage />
                        </div>
                    </ProtectedRoute>
                } 
            />
            
            {/* Redireciona rotas desconhecidas para login */}
            <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
    )
}

function App() {
    return (
        <AuthProvider>
            <ToastProvider>
                <BrowserRouter>
                    <AppRoutes />
                </BrowserRouter>
            </ToastProvider>
        </AuthProvider>
    )
}

export default App
