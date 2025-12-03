import { render, RenderOptions } from '@testing-library/react'
import { ReactElement, ReactNode } from 'react'
import { BrowserRouter } from 'react-router-dom'
import { ToastProvider } from '@/components/ui/toast'

// Wrapper com todos os providers necessários
function AllProviders({ children }: { children: ReactNode }) {
    return (
        <BrowserRouter>
            <ToastProvider>
                {children}
            </ToastProvider>
        </BrowserRouter>
    )
}

// Render customizado com providers
const customRender = (
    ui: ReactElement,
    options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllProviders, ...options })

// Re-exporta tudo do testing-library
export * from '@testing-library/react'
export { customRender as render }
