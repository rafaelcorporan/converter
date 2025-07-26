import type { Metadata } from 'next'
import './globals.css'
import { Toaster } from '@/components/ui/toaster'
import { TooltipProvider } from '@/components/ui/tooltip'
import { AuthProvider } from '@/contexts/auth-context'

export const metadata: Metadata = {
  title: 'VideoConvert Pro - Professional Video Converter',
  description: 'Professional video conversion platform with advanced encoding options. Convert MP4 to WebM VP9 format with superior compression and quality.',
  generator: 'VideoConvert Pro',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <TooltipProvider>
            {children}
          </TooltipProvider>
          <Toaster />
        </AuthProvider>
      </body>
    </html>
  )
}
