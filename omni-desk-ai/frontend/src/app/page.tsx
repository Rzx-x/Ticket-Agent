import TicketForm from '@/components/TicketForm';
import Link from 'next/link';
import { BarChart3 } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">OmniDesk AI</h1>
              <span className="ml-2 text-sm text-gray-500">| POWERGRID IT Support</span>
            </div>
            
            <Link 
              href="/dashboard"
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors"
            >
              <BarChart3 className="w-4 h-4" />
              IT Dashboard
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-12 pb-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Get Instant IT Support
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Describe your technical issue in English or Hindi, and our AI assistant will provide immediate help or route your request to the right team.
          </p>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="text-center p-6 bg-white rounded-lg shadow-sm">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">🤖</span>
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">AI-Powered Support</h3>
            <p className="text-gray-600 text-sm">Get instant solutions using advanced AI technology</p>
          </div>
          
          <div className="text-center p-6 bg-white rounded-lg shadow-sm">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">🌏</span>
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Multi-Language</h3>
            <p className="text-gray-600 text-sm">Support in both English and Hindi languages</p>
          </div>
          
          <div className="text-center p-6 bg-white rounded-lg shadow-sm">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">⚡</span>
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">24/7 Available</h3>
            <p className="text-gray-600 text-sm">Round-the-clock automated assistance</p>
          </div>
        </div>

        {/* Main Ticket Form */}
        <TicketForm />

        {/* Footer */}
        <div className="mt-12 text-center text-gray-500 text-sm">
          <p>Powered by Claude AI • Built for POWERGRID Corporation</p>
          <p className="mt-1">Need immediate help? Call IT Helpdesk: <span className="font-medium">1800-XXX-XXXX</span></p>
        </div>
      </div>
    </div>
  );
}