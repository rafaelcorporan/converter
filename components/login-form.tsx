'use client'

import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { useAuth } from '@/contexts/auth-context'
import { Video, Eye, EyeOff, Cloud, Upload, Play, FileVideo, Settings, BarChart3 } from 'lucide-react'

export function LoginForm() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const { login } = useAuth()

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Set canvas size
    canvas.width = window.innerWidth
    canvas.height = window.innerHeight

    // WiFi spinners and morphing blobs
    const animatedElements: Array<{
      x: number
      y: number
      vx: number
      vy: number
      size: number
      type: 'wifi' | 'blob'
      animationTime: number
      animationSpeed: number
      color: string
      opacity: number
    }> = []

    const colors = ['#3498db', '#2563eb', '#1d4ed8', '#1e40af']
    const blobColors = [
      ['#8b5cf6', '#06b6d4', '#f59e0b', '#ec4899'], // Purple, cyan, amber, pink
      ['#3b82f6', '#10b981', '#f97316', '#ef4444'], // Blue, green, orange, red
      ['#6366f1', '#14b8a6', '#eab308', '#f43f5e']  // Indigo, teal, yellow, rose
    ]

    // Create animated elements
    for (let i = 0; i < 25; i++) {
      const isWifi = Math.random() > 0.6 // 40% WiFi, 60% blobs
      animatedElements.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 1.5,
        vy: (Math.random() - 0.5) * 1.5,
        size: Math.random() * 40 + 20,
        type: isWifi ? 'wifi' : 'blob',
        animationTime: Math.random() * Math.PI * 2,
        animationSpeed: 0.02 + Math.random() * 0.03,
        color: isWifi ? colors[Math.floor(Math.random() * colors.length)] : 'multi',
        opacity: Math.random() * 0.4 + 0.2
      })
    }

    // Video processing icons
    const videoIcons: Array<{
      x: number
      y: number
      vx: number
      vy: number
      size: number
      rotation: number
      rotationSpeed: number
      type: 'cloud' | 'upload' | 'play' | 'video' | 'settings' | 'chart'
      color: string
      opacity: number
    }> = []

    const iconTypes = ['cloud', 'upload', 'play', 'video', 'settings', 'chart'] as const

    for (let i = 0; i < 20; i++) {
      videoIcons.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 1.5,
        vy: (Math.random() - 0.5) * 1.5,
        size: Math.random() * 35 + 15,
        rotation: 0,
        rotationSpeed: (Math.random() - 0.5) * 0.01,
        type: iconTypes[Math.floor(Math.random() * iconTypes.length)],
        color: colors[Math.floor(Math.random() * colors.length)],
        opacity: Math.random() * 0.4 + 0.1
      })
    }

    function drawCloudIcon(ctx: CanvasRenderingContext2D, x: number, y: number, size: number) {
      const width = size * 1.4
      const height = size
      ctx.beginPath()
      ctx.arc(x - width/4, y, height/3, 0, Math.PI * 2)
      ctx.arc(x + width/4, y, height/4, 0, Math.PI * 2)
      ctx.arc(x, y - height/4, height/3, 0, Math.PI * 2)
      ctx.rect(x - width/2, y - height/6, width, height/3)
    }

    function drawPlayIcon(ctx: CanvasRenderingContext2D, x: number, y: number, size: number) {
      ctx.beginPath()
      ctx.moveTo(x - size/2, y - size/2)
      ctx.lineTo(x + size/2, y)
      ctx.lineTo(x - size/2, y + size/2)
      ctx.closePath()
    }

    function drawVideoIcon(ctx: CanvasRenderingContext2D, x: number, y: number, size: number) {
      const width = size * 1.2
      const height = size * 0.8
      ctx.fillRect(x - width/2, y - height/2, width, height)
      // Camera lens
      ctx.beginPath()
      ctx.arc(x - width/4, y, height/4, 0, Math.PI * 2)
      ctx.fill()
    }

    function drawUploadIcon(ctx: CanvasRenderingContext2D, x: number, y: number, size: number) {
      // Arrow up
      ctx.beginPath()
      ctx.moveTo(x, y - size/2)
      ctx.lineTo(x - size/3, y)
      ctx.lineTo(x + size/3, y)
      ctx.closePath()
      // Line
      ctx.fillRect(x - size/8, y, size/4, size/2)
    }

    function drawSettingsIcon(ctx: CanvasRenderingContext2D, x: number, y: number, size: number) {
      const radius = size/2
      ctx.beginPath()
      ctx.arc(x, y, radius, 0, Math.PI * 2)
      // Inner circle
      ctx.arc(x, y, radius/3, 0, Math.PI * 2)
    }

    function drawChartIcon(ctx: CanvasRenderingContext2D, x: number, y: number, size: number) {
      const barWidth = size/6
      ctx.fillRect(x - size/2, y, barWidth, size/3)
      ctx.fillRect(x - barWidth/2, y - size/4, barWidth, size/2)
      ctx.fillRect(x + size/2 - barWidth, y - size/2, barWidth, size)
    }

    function drawWifiSpinner(ctx: CanvasRenderingContext2D, x: number, y: number, size: number, animationTime: number, color: string) {
      ctx.strokeStyle = color
      ctx.lineWidth = size / 8
      ctx.lineCap = 'round'
      
      // Draw 3 WiFi arcs with pulsing effect
      for (let i = 0; i < 3; i++) {
        const radius = (size / 3) * (i + 1)
        const pulse = Math.sin(animationTime + i * 0.5) * 0.3 + 0.7
        
        ctx.save()
        ctx.globalAlpha = pulse
        ctx.beginPath()
        ctx.arc(x, y, radius, Math.PI * 0.8, Math.PI * 1.2)
        ctx.stroke()
        ctx.restore()
      }
      
      // Center dot
      ctx.fillStyle = color
      ctx.beginPath()
      ctx.arc(x, y, size / 10, 0, Math.PI * 2)
      ctx.fill()
    }

    function drawMorphingBlob(ctx: CanvasRenderingContext2D, x: number, y: number, size: number, animationTime: number, colorSet: string[]) {
      const numBlobs = 4
      const baseRadius = size / 3
      
      for (let i = 0; i < numBlobs; i++) {
        const angle = (animationTime + i * Math.PI / 2) * 0.8
        const offsetRadius = size / 4
        const blobX = x + Math.cos(angle) * offsetRadius
        const blobY = y + Math.sin(angle) * offsetRadius
        const blobSize = baseRadius + Math.sin(animationTime * 2 + i) * (baseRadius / 3)
        
        ctx.fillStyle = colorSet[i]
        ctx.globalAlpha = 0.7
        ctx.beginPath()
        ctx.arc(blobX, blobY, blobSize, 0, Math.PI * 2)
        ctx.fill()
      }
      ctx.globalAlpha = 1
    }

    function animate() {
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      // Gradient background
      const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height)
      gradient.addColorStop(0, '#f1f5f9')
      gradient.addColorStop(1, '#e2e8f0')
      ctx.fillStyle = gradient
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      // Update and draw animated elements (WiFi spinners and morphing blobs)
      animatedElements.forEach((element, index) => {
        element.x += element.vx
        element.y += element.vy
        element.animationTime += element.animationSpeed

        // Bounce off edges
        if (element.x < 0 || element.x > canvas.width) element.vx *= -1
        if (element.y < 0 || element.y > canvas.height) element.vy *= -1

        // Keep in bounds
        element.x = Math.max(0, Math.min(canvas.width, element.x))
        element.y = Math.max(0, Math.min(canvas.height, element.y))

        // Draw element
        ctx.save()
        ctx.globalAlpha = element.opacity

        if (element.type === 'wifi') {
          drawWifiSpinner(ctx, element.x, element.y, element.size, element.animationTime, element.color)
        } else {
          const colorSetIndex = index % blobColors.length
          drawMorphingBlob(ctx, element.x, element.y, element.size, element.animationTime, blobColors[colorSetIndex])
        }

        ctx.restore()
      })

      // Update and draw video icons
      videoIcons.forEach(icon => {
        icon.x += icon.vx
        icon.y += icon.vy
        icon.rotation += icon.rotationSpeed

        // Bounce off edges
        if (icon.x < 0 || icon.x > canvas.width) icon.vx *= -1
        if (icon.y < 0 || icon.y > canvas.height) icon.vy *= -1

        // Keep in bounds
        icon.x = Math.max(0, Math.min(canvas.width, icon.x))
        icon.y = Math.max(0, Math.min(canvas.height, icon.y))

        // Draw icon
        ctx.save()
        ctx.globalAlpha = icon.opacity
        ctx.fillStyle = icon.color
        ctx.translate(icon.x, icon.y)
        ctx.rotate(icon.rotation)

        switch (icon.type) {
          case 'cloud':
            drawCloudIcon(ctx, 0, 0, icon.size)
            break
          case 'play':
            drawPlayIcon(ctx, 0, 0, icon.size)
            break
          case 'video':
            drawVideoIcon(ctx, 0, 0, icon.size)
            break
          case 'upload':
            drawUploadIcon(ctx, 0, 0, icon.size)
            break
          case 'settings':
            drawSettingsIcon(ctx, 0, 0, icon.size)
            break
          case 'chart':
            drawChartIcon(ctx, 0, 0, icon.size)
            break
        }
        ctx.fill()
        ctx.restore()
      })

      requestAnimationFrame(animate)
    }

    animate()

    const handleResize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
    }
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      const success = login(username, password)
      if (!success) {
        setError('Invalid username or password')
      }
    } catch (err) {
      setError('An error occurred during login')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Interactive Canvas Background */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full"
        style={{ zIndex: 1 }}
      />

      {/* Login Form */}
      <div className="relative z-10 min-h-screen flex items-center justify-center p-4">
        <div className="w-80 bg-white rounded-lg shadow-sm border border-gray-200 p-8 mx-auto">
          <div className="text-center mb-8">
            <div className="flex justify-center mb-6">
              <div className="bg-blue-600 p-3 rounded-lg">
                <Video className="h-8 w-8 text-white" />
              </div>
            </div>
            <h1 className="text-lg font-medium text-gray-900 mb-2">VideoConvert Pro</h1>
            <p className="text-sm text-gray-600">Sign in to your account</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="relative">
              <Input
                id="username"
                type="text"
                placeholder="admin"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="h-12 pl-10 bg-yellow-50 border-yellow-200 focus:border-yellow-400 focus:ring-yellow-400 rounded-lg"
              />
              <div className="absolute left-3 top-1/2 transform -translate-y-1/2">
                <div className="w-4 h-4 bg-gray-400 rounded-full"></div>
              </div>
            </div>
            
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? "text" : "password"}
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="h-12 pl-10 pr-10 bg-yellow-50 border-yellow-200 focus:border-yellow-400 focus:ring-yellow-400 rounded-lg"
              />
              <div className="absolute left-3 top-1/2 transform -translate-y-1/2">
                <div className="w-4 h-4 bg-gray-400 rounded-sm"></div>
              </div>
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>

            <div className="text-xs text-gray-500 mt-4">
              Admin access for professional video conversion platform
            </div>
            
            {error && (
              <Alert variant="destructive" className="mt-4">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <Button 
              type="submit" 
              className="w-full h-12 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg mt-6"
              disabled={isLoading}
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}