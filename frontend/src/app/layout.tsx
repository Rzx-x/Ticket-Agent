import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { Providers } from './providers'
import './globals.css'

const inter = Inter({ 
  subsets: ['latin'],
  variable: '--font-inter',
})

export const metadata: Metadata = {
  title: 'OmniDesk AI - Smart IT Support',
  description: 'AI-powered IT ticket management system for POWERGRID Corporation',
  keywords: ['IT Support', 'POWERGRID', 'AI Assistant', 'Ticket Management'],
  authors: [{ name: 'POWERGRID IT Team' }],
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#ffffff' },
    { media: '(prefers-color-scheme: dark)', color: '#000000' },
  ],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen bg-gradient-to-br from-gray-900 via-primary-900 to-gray-900 text-gray-100 antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}