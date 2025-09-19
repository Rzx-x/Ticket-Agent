import { Inter } from 'next/font/google'
import { ClientWrapper } from './ClientWrapper'
import { ErrorBoundaryWrapper } from '@/components/ErrorBoundary'
import './globals.css'
export { metadata } from './metadata'

const inter = Inter({ 
  subsets: ['latin'],
  variable: '--font-inter',
})

function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body>
        <ErrorBoundaryWrapper>
          <ClientWrapper>
            {children}
          </ClientWrapper>
        </ErrorBoundaryWrapper>
      </body>
    </html>
  )
}

export default RootLayout