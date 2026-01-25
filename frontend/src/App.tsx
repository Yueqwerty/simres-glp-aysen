import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { Sidebar } from "./components/layout/Sidebar"
import Dashboard from "./pages/Dashboard"
import Configuration from "./pages/Configuration"
import Results from "./pages/Results"
import MonteCarlo from "./pages/MonteCarlo"
import Compare from "./pages/Compare"
import History from "./pages/History"
import Analysis from "./pages/Analysis"
import Validation from "./pages/Validation"
import "./index.css"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutos
      retry: 1,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="flex min-h-screen bg-slate-50">
          <Sidebar />
          <div className="flex-1 ml-60">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/configurar" element={<Configuration />} />
              <Route path="/resultados/:simulacionId" element={<Results />} />
              <Route path="/monte-carlo" element={<MonteCarlo />} />
              <Route path="/comparar/:ids" element={<Compare />} />
              <Route path="/historial" element={<History />} />
              <Route path="/analisis" element={<Analysis />} />
              <Route path="/validacion" element={<Validation />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
