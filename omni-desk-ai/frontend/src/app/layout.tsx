import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'OmniDesk AI - Smart IT Support',
  description: 'AI-powered IT ticket management system for POWERGRID Corporation',
  keywords: ['IT Support', 'POWERGRID', 'AI Assistant', 'Ticket Management'],
  authors: [{ name: 'POWERGRID IT Team' }],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
}