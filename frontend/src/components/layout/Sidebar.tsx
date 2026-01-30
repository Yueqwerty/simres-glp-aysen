import { Link, useLocation } from "react-router-dom"
import { Home, Play, BarChart3, GitCompare, Clock, TrendingUp, Shield } from "lucide-react"

const NAV_ITEMS = [
  { name: "Dashboard", path: "/", icon: Home },
  { name: "Simulación", path: "/configurar", icon: Play },
  { name: "Monte Carlo", path: "/monte-carlo", icon: BarChart3 },
  { name: "Historial", path: "/historial", icon: Clock },
  { name: "Análisis", path: "/analisis", icon: TrendingUp },
  { name: "Validación", path: "/validacion", icon: Shield },
  { name: "Comparar", path: "/comparar", icon: GitCompare },
]

export function Sidebar() {
  const location = useLocation()

  return (
    <aside className="w-60 h-screen bg-white border-r border-neutral-200 fixed left-0 top-0 flex flex-col">
      <div className="h-16 flex items-center px-6 border-b border-neutral-200">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div>
            <h1 className="text-sm font-semibold text-neutral-900 leading-none">SIMRES-GLP</h1>
            <p className="text-[10px] text-neutral-500 leading-none mt-0.5">Aysén</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-3 py-6">
        <ul className="space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.path

            return (
              <li key={item.path}>
                <Link
                  to={item.path}
                  className={`
                    group flex items-center gap-3 px-3 py-2.5 rounded-lg text-[13px] font-medium transition-all duration-200
                    ${isActive
                      ? 'bg-neutral-100 text-neutral-900'
                      : 'text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900'
                    }
                  `}
                >
                  <Icon className={`h-[18px] w-[18px] flex-shrink-0 ${isActive ? 'text-primary-600' : 'text-neutral-400 group-hover:text-neutral-600'}`} />
                  <span>{item.name}</span>
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>

      <div className="px-6 py-4 border-t border-neutral-200">
        <p className="text-[10px] text-neutral-400 font-medium">v1.0.0</p>
      </div>
    </aside>
  )
}
