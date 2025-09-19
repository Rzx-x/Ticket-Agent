import Dashboard from '@/components/Dashboard';
import Link from 'next/link';
import { Home, Brain, Zap, Activity } from 'lucide-react';

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Navigation */}
      <nav className="backdrop-blur-xl bg-white/5 border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl">
                <Activity className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">OmniDesk AI</h1>
                <span className="text-xs text-purple-300 font-medium">Command Center</span>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="hidden md:flex items-center gap-6">
                <div className="flex items-center gap-2 text-green-400">
                  <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium">System Online</span>
                </div>
                
                <div className="flex items-center gap-2 text-blue-400">
                  <Brain className="w-4 h-4" />
                  <span className="text-sm">AI Active</span>
                </div>
                
                <div className="flex items-center gap-2 text-yellow-400">
                  <Zap className="w-4 h-4" />
                  <span className="text-sm">Real-time</span>
                </div>
              </div>
              
              <Link 
                href="/"
                className="group flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white font-semibold rounded-xl transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-xl"
              >
                <Home className="w-5 h-5" />
                <span>Support Portal</span>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Dashboard Content */}
      <Dashboard />
    </div>
  );
}