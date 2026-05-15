import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import { FileText, Upload, FileCheck, TrendingUp, Activity } from 'lucide-react'
import { Toaster } from 'react-hot-toast'
import DocumentUpload from './pages/DocumentUpload'
import DocumentList from './pages/DocumentList'
import DraftGeneration from './pages/DraftGeneration'
import PatternInsights from './pages/PatternInsights'
import Dashboard from './pages/Dashboard'

function Navigation() {
  const location = useLocation()
  
  const isActive = (path) => location.pathname === path
  
  const navItems = [
    { path: '/', icon: Activity, label: 'Dashboard' },
    { path: '/upload', icon: Upload, label: 'Upload' },
    { path: '/documents', icon: FileText, label: 'Documents' },
    { path: '/generate', icon: FileCheck, label: 'Generate Draft' },
    { path: '/patterns', icon: TrendingUp, label: 'Patterns' },
  ]
  
  return (
    <nav className="bg-white shadow-sm border-b sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <FileText className="h-8 w-8 text-primary-600" />
              <span className="ml-2 text-xl font-bold text-gray-900">
                Legal AI
              </span>
            </div>
            <div className="hidden sm:ml-8 sm:flex sm:space-x-4">
              {navItems.map((item) => {
                const Icon = item.icon
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`inline-flex items-center px-3 py-2 border-b-2 text-sm font-medium transition-colors ${
                      isActive(item.path)
                        ? 'border-primary-500 text-primary-600'
                        : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    }`}
                  >
                    <Icon className="h-4 w-4 mr-2" />
                    {item.label}
                  </Link>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        
        <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/upload" element={<DocumentUpload />} />
            <Route path="/documents" element={<DocumentList />} />
            <Route path="/generate" element={<DraftGeneration />} />
            <Route path="/patterns" element={<PatternInsights />} />
          </Routes>
        </main>
        
        <Toaster 
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
            success: {
              duration: 3000,
              iconTheme: {
                primary: '#22c55e',
                secondary: '#fff',
              },
            },
            error: {
              duration: 4000,
              iconTheme: {
                primary: '#ef4444',
                secondary: '#fff',
              },
            },
          }}
        />
      </div>
    </Router>
  )
}

export default App
