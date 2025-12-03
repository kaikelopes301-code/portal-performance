import { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import { CheckCircle, AlertCircle, X, Info, AlertTriangle } from 'lucide-react'
import { cn } from '@/utils/cn'

// Tipos
type ToastType = 'success' | 'error' | 'warning' | 'info'

interface Toast {
    id: string
    type: ToastType
    title: string
    message?: string
}

interface ToastContextType {
    toasts: Toast[]
    addToast: (type: ToastType, title: string, message?: string) => void
    removeToast: (id: string) => void
    success: (title: string, message?: string) => void
    error: (title: string, message?: string) => void
    warning: (title: string, message?: string) => void
    info: (title: string, message?: string) => void
}

// Context
const ToastContext = createContext<ToastContextType | null>(null)

// Hook
export function useToast() {
    const context = useContext(ToastContext)
    if (!context) {
        throw new Error('useToast must be used within a ToastProvider')
    }
    return context
}

// Provider
export function ToastProvider({ children }: { children: ReactNode }) {
    const [toasts, setToasts] = useState<Toast[]>([])

    const addToast = useCallback((type: ToastType, title: string, message?: string) => {
        const id = Math.random().toString(36).substr(2, 9)
        setToasts(prev => [...prev, { id, type, title, message }])
        
        // Auto-remove após 5 segundos
        setTimeout(() => {
            setToasts(prev => prev.filter(t => t.id !== id))
        }, 5000)
    }, [])

    const removeToast = useCallback((id: string) => {
        setToasts(prev => prev.filter(t => t.id !== id))
    }, [])

    const success = useCallback((title: string, message?: string) => addToast('success', title, message), [addToast])
    const error = useCallback((title: string, message?: string) => addToast('error', title, message), [addToast])
    const warning = useCallback((title: string, message?: string) => addToast('warning', title, message), [addToast])
    const info = useCallback((title: string, message?: string) => addToast('info', title, message), [addToast])

    return (
        <ToastContext.Provider value={{ toasts, addToast, removeToast, success, error, warning, info }}>
            {children}
            <ToastContainer toasts={toasts} onRemove={removeToast} />
        </ToastContext.Provider>
    )
}

// Componente de Toast Container
function ToastContainer({ toasts, onRemove }: { toasts: Toast[], onRemove: (id: string) => void }) {
    if (toasts.length === 0) return null

    return (
        <div className="fixed bottom-4 right-4 z-50 space-y-2 max-w-sm">
            {toasts.map(toast => (
                <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
            ))}
        </div>
    )
}

// Componente de Toast individual
function ToastItem({ toast, onRemove }: { toast: Toast, onRemove: (id: string) => void }) {
    const icons = {
        success: CheckCircle,
        error: AlertCircle,
        warning: AlertTriangle,
        info: Info
    }
    
    // Glassmorphism styles
    const styles = {
        success: 'bg-green-500/10 border-green-500/20 text-green-700 dark:text-green-300',
        error: 'bg-red-500/10 border-red-500/20 text-red-700 dark:text-red-300',
        warning: 'bg-yellow-500/10 border-yellow-500/20 text-yellow-700 dark:text-yellow-300',
        info: 'bg-blue-500/10 border-blue-500/20 text-blue-700 dark:text-blue-300'
    }
    
    const iconColors = {
        success: 'text-green-500',
        error: 'text-red-500',
        warning: 'text-yellow-500',
        info: 'text-blue-500'
    }

    const Icon = icons[toast.type]

    return (
        <div className={cn(
            'flex items-start gap-3 p-4 rounded-xl border shadow-xl backdrop-blur-md animate-slide-in min-w-[320px]',
            styles[toast.type]
        )}>
            <div className={cn('p-2 rounded-full bg-white/20', iconColors[toast.type])}>
                <Icon className="h-5 w-5" />
            </div>
            <div className="flex-1 min-w-0 pt-1">
                <p className="font-semibold text-sm tracking-wide">{toast.title}</p>
                {toast.message && (
                    <p className="text-sm opacity-80 mt-1 leading-relaxed">{toast.message}</p>
                )}
            </div>
            <button 
                onClick={() => onRemove(toast.id)}
                className="flex-shrink-0 p-1 rounded-lg hover:bg-black/5 transition-colors opacity-60 hover:opacity-100"
            >
                <X className="h-4 w-4" />
            </button>
        </div>
    )
}
