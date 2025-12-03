import { LayoutDashboard, Settings, Send, Eye, HelpCircle, Menu, X } from "lucide-react"
import { Link, useLocation } from "react-router-dom"
import { cn } from "@/utils/cn"
import { useState, useEffect } from "react"

const navigation = [
    { name: "Dashboard", href: "/", icon: LayoutDashboard },
    { name: "Execução", href: "/execution", icon: Send },
    { name: "Preview", href: "/preview", icon: Eye },
    { name: "Configurações", href: "/settings", icon: Settings },
    { name: "Ajuda", href: "/help", icon: HelpCircle },
]

export default function Layout({ children }: { children: React.ReactNode }) {
    const location = useLocation()
    const [scrolled, setScrolled] = useState(false)
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

    useEffect(() => {
        const handleScroll = () => {
            setScrolled(window.scrollY > 20)
        }
        window.addEventListener('scroll', handleScroll)
        return () => window.removeEventListener('scroll', handleScroll)
    }, [])

    return (
        <div className="min-h-screen flex flex-col relative overflow-x-hidden">
            {/* Ambient Background */}
            <div className="fixed inset-0 z-[-1] pointer-events-none bg-[radial-gradient(circle_at_50%_-20%,#e0f2fe_0%,#f8fafc_100%)] dark:bg-[radial-gradient(circle_at_50%_-20%,#1e293b_0%,#020617_100%)] transition-colors duration-700">
                <div className="absolute inset-0 opacity-30 bg-[radial-gradient(currentColor_1px,transparent_1px)] [background-size:32px_32px] text-slate-400 [mask-image:radial-gradient(circle_at_center,black_40%,transparent_80%)]"></div>
                <div className="absolute top-[-10%] left-[-10%] w-[50vw] h-[50vw] rounded-full bg-[#2F4F71] opacity-15 blur-[100px] animate-float"></div>
                <div className="absolute bottom-[10%] right-[-10%] w-[40vw] h-[40vw] rounded-full bg-[#3b82f6] opacity-10 blur-[100px] animate-float" style={{ animationDelay: '-5s' }}></div>
            </div>

            {/* Navbar */}
            <nav className={cn(
                "fixed top-0 left-0 w-full z-50 transition-all duration-500 px-8 py-5 flex justify-center items-center",
                scrolled && "bg-white/65 dark:bg-slate-900/60 backdrop-blur-xl border-b border-white/80 dark:border-white/10 py-3"
            )}>
                <div className="w-full max-w-[1280px] flex justify-between items-center relative">
                    {/* Logo */}
                    <Link to="/" className="flex items-center gap-3 group hover:opacity-90 transition-opacity">
                        <img 
                            src="/logo-atlas.png" 
                            alt="Atlas Inovações" 
                            className="h-10 w-auto object-contain group-hover:scale-105 transition-transform duration-300"
                        />
                    </Link>

                    {/* Desktop Navigation */}
                    <div className="hidden md:flex items-center gap-1 bg-white/40 dark:bg-slate-800/40 backdrop-blur-md px-2 py-1.5 rounded-full border border-white/50 dark:border-white/10 shadow-sm">
                        {navigation.map((item) => {
                            const isActive = location.pathname === item.href
                            return (
                                <Link
                                    key={item.name}
                                    to={item.href}
                                    className={cn(
                                        "flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all duration-300",
                                        isActive 
                                            ? "bg-white dark:bg-slate-700 text-[#3b82f6] shadow-sm" 
                                            : "text-gray-600 dark:text-gray-300 hover:text-[#2F4F71] dark:hover:text-white hover:bg-white/50 dark:hover:bg-slate-700/50"
                                    )}
                                >
                                    <item.icon className={cn("h-4 w-4", isActive && "text-[#3b82f6]")} />
                                    {item.name}
                                </Link>
                            )
                        })}
                    </div>

                    {/* Right Actions */}
                    <div className="flex items-center gap-4">
                        {/* Mobile Menu Button */}
                        <button 
                            className="md:hidden p-2 text-gray-600"
                            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                        >
                            {mobileMenuOpen ? <X /> : <Menu />}
                        </button>
                    </div>
                </div>
            </nav>

            {/* Mobile Menu Overlay */}
            {mobileMenuOpen && (
                <div className="fixed inset-0 z-40 bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl pt-24 px-6 md:hidden animate-fade-in-up">
                    <div className="flex flex-col gap-4">
                        {navigation.map((item) => (
                            <Link
                                key={item.name}
                                to={item.href}
                                onClick={() => setMobileMenuOpen(false)}
                                className={cn(
                                    "flex items-center gap-4 p-4 rounded-xl text-lg font-medium transition-colors",
                                    location.pathname === item.href
                                        ? "bg-blue-50 dark:bg-blue-900/20 text-[#3b82f6]"
                                        : "text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-800/50"
                                )}
                            >
                                <item.icon className="h-6 w-6" />
                                {item.name}
                            </Link>
                        ))}
                    </div>
                </div>
            )}

            {/* Main Content */}
            <main className="flex-1 pt-32 pb-20 px-6 md:px-8 relative z-10 max-w-[1280px] mx-auto w-full">
                {children}
            </main>

            {/* Footer Compacto e Transparente */}
            <footer className="relative z-10 mt-auto border-t border-white/10 bg-white/5 backdrop-blur-sm">
                <div className="max-w-[1280px] mx-auto px-6 py-8">
                    <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                        
                        {/* Logo */}
                        <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-white/10 rounded-lg flex items-center justify-center backdrop-blur-md border border-white/20">
                                <span className="text-white font-bold text-lg">A</span>
                            </div>
                            <span className="text-white/90 font-semibold tracking-wide">Atlas Inovações</span>
                        </div>

                        {/* Social Links */}
                        <div className="flex items-center gap-6">
                            <a 
                                href="https://www.instagram.com/atlasinovacoes/" 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-white/60 hover:text-white transition-colors font-medium text-sm tracking-wider hover:scale-105 transform duration-200"
                            >
                                INSTAGRAM
                            </a>
                            <a 
                                href="https://www.linkedin.com/company/atlas-inovacoes-e-tecnologia/" 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-white/60 hover:text-white transition-colors font-medium text-sm tracking-wider hover:scale-105 transform duration-200"
                            >
                                LINKEDIN
                            </a>
                        </div>

                        {/* Credits */}
                        <div className="flex flex-col items-center md:items-end gap-1 text-xs text-white/40">
                            <span>Atlas Inovações 2025 ©</span>
                            <span className="flex items-center gap-1">
                                Desenvolvida por <span className="text-white/60 font-medium">Dados</span>
                            </span>
                        </div>
                    </div>
                </div>
            </footer>
        </div>
    )
}
