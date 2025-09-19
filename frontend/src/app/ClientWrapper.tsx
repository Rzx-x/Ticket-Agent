"use client";

import { ReactNode } from 'react';
import { Providers } from './providers';
import { ThemeProvider } from './ThemeContext';

export function ClientWrapper({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider>
      <Providers>
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-primary-900 to-gray-900 text-gray-100 antialiased">
          {children}
        </div>
      </Providers>
    </ThemeProvider>
  );
}