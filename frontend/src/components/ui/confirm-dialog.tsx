import { useState } from 'react'
import { AlertTriangle } from 'lucide-react'
import { Button } from './button'

interface ConfirmDialogProps {
    open: boolean
    onClose: () => void
    onConfirm: () => void
    title: string
    message: string
    confirmText?: string
    cancelText?: string
    variant?: 'danger' | 'warning' | 'default'
    loading?: boolean
}

export function ConfirmDialog({
    open,
    onClose,
    onConfirm,
    title,
    message,
    confirmText = 'Confirmar',
    cancelText = 'Cancelar',
    variant = 'default',
    loading = false
}: ConfirmDialogProps) {
    if (!open) return null

    const variantStyles = {
        danger: {
            icon: 'bg-red-100 text-red-600',
            button: 'bg-red-600 hover:bg-red-700 text-white'
        },
        warning: {
            icon: 'bg-yellow-100 text-yellow-600',
            button: 'bg-yellow-600 hover:bg-yellow-700 text-white'
        },
        default: {
            icon: 'bg-blue-100 text-blue-600',
            button: 'bg-blue-600 hover:bg-blue-700 text-white'
        }
    }

    const styles = variantStyles[variant]

    return (
        <div className="fixed inset-0 z-50 overflow-y-auto">
            {/* Backdrop */}
            <div 
                className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
                onClick={onClose}
            />
            
            {/* Dialog */}
            <div className="flex min-h-full items-center justify-center p-4">
                <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6 transform transition-all">
                    <div className="flex items-start gap-4">
                        <div className={`p-2 rounded-full ${styles.icon}`}>
                            <AlertTriangle className="h-6 w-6" />
                        </div>
                        <div className="flex-1">
                            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
                            <p className="mt-2 text-sm text-gray-600">{message}</p>
                        </div>
                    </div>
                    
                    <div className="mt-6 flex justify-end gap-3">
                        <Button 
                            variant="outline" 
                            onClick={onClose}
                            disabled={loading}
                        >
                            {cancelText}
                        </Button>
                        <Button 
                            className={styles.button}
                            onClick={onConfirm}
                            disabled={loading}
                        >
                            {loading ? 'Processando...' : confirmText}
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    )
}

// Hook para uso simplificado
interface UseConfirmOptions {
    title: string
    message: string
    confirmText?: string
    variant?: 'danger' | 'warning' | 'default'
}

export function useConfirm() {
    const [state, setState] = useState<{
        open: boolean
        options: UseConfirmOptions | null
        resolve: ((value: boolean) => void) | null
    }>({
        open: false,
        options: null,
        resolve: null
    })

    const confirm = (options: UseConfirmOptions): Promise<boolean> => {
        return new Promise(resolve => {
            setState({ open: true, options, resolve })
        })
    }

    const handleClose = () => {
        state.resolve?.(false)
        setState({ open: false, options: null, resolve: null })
    }

    const handleConfirm = () => {
        state.resolve?.(true)
        setState({ open: false, options: null, resolve: null })
    }

    const ConfirmDialogComponent = () => state.options ? (
        <ConfirmDialog
            open={state.open}
            onClose={handleClose}
            onConfirm={handleConfirm}
            title={state.options.title}
            message={state.options.message}
            confirmText={state.options.confirmText}
            variant={state.options.variant}
        />
    ) : null

    return { confirm, ConfirmDialog: ConfirmDialogComponent }
}
