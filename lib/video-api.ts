import type { ConversionSettings } from "@/app/page"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'

export interface ConversionResponse {
  conversion_id: string
  message: string
}

export interface ProgressResponse {
  conversion_id: string
  progress: number
  status: 'processing' | 'completed' | 'error' | 'unknown'
  error?: string
  compression_ratio?: number
  input_size?: number
  output_size?: number
  time?: string
  fps?: number
  speed?: string
  eta?: string
}

export class VideoAPI {
  private static async makeRequest<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`
    
    try {
      const response = await fetch(url, {
        headers: {
          ...options?.headers,
        },
        ...options,
      })

      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`
        try {
          const errorData = await response.json()
          if (errorData.error) {
            errorMessage = errorData.error
          }
        } catch {
          // If we can't parse error response, use status text
        }
        throw new Error(errorMessage)
      }

      return await response.json()
    } catch (error) {
      console.error(`API request failed: ${error}`)
      
      // Provide more user-friendly error messages
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error('Cannot connect to video conversion server. Please ensure the backend is running.')
      }
      
      throw error
    }
  }

  static async convertVideo(file: File, settings: ConversionSettings): Promise<ConversionResponse> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('settings', JSON.stringify({
      quality: settings.quality,
      bitrate: settings.bitrate,
      twoPass: settings.twoPass,
      resolution: settings.resolution,
      frameRate: settings.frameRate,
      preset: settings.preset
    }))

    return this.makeRequest<ConversionResponse>('/api/convert', {
      method: 'POST',
      body: formData,
    })
  }

  static async getProgress(conversionId: string): Promise<ProgressResponse> {
    return this.makeRequest<ProgressResponse>(`/api/progress/${conversionId}`, {
      headers: {
        'Content-Type': 'application/json',
      }
    })
  }

  static async downloadVideo(conversionId: string): Promise<Blob> {
    const url = `${API_BASE_URL}/api/download/${conversionId}`
    
    try {
      const response = await fetch(url)
      
      if (!response.ok) {
        let errorMessage = `Download failed! HTTP ${response.status}`
        try {
          const errorData = await response.json()
          if (errorData.error) {
            errorMessage = errorData.error
          }
        } catch {
          // If we can't parse error response, use status text
        }
        throw new Error(errorMessage)
      }

      return await response.blob()
    } catch (error) {
      console.error(`Download failed: ${error}`)
      
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error('Cannot connect to video conversion server. Please ensure the backend is running.')
      }
      
      throw error
    }
  }

  static pollProgress(
    conversionId: string,
    onProgress: (progress: ProgressResponse) => void,
    onComplete: (result: ProgressResponse) => void,
    onError: (error: string) => void,
    pollInterval: number = 1000
  ): () => void {
    let isPolling = true
    let pollTimeout: NodeJS.Timeout

    const poll = async () => {
      if (!isPolling) return

      try {
        const progress = await this.getProgress(conversionId)
        
        // Call progress callback
        onProgress(progress)

        // Check if conversion is complete
        if (progress.status === 'completed') {
          onComplete(progress)
          return
        }

        // Check if conversion failed
        if (progress.status === 'error') {
          onError(progress.error || 'Conversion failed')
          return
        }

        // Continue polling
        pollTimeout = setTimeout(poll, pollInterval)
      } catch (error) {
        console.error('Progress polling error:', error)
        onError('Failed to get progress')
      }
    }

    // Start polling
    poll()

    // Return function to stop polling
    return () => {
      isPolling = false
      if (pollTimeout) {
        clearTimeout(pollTimeout)
      }
    }
  }
} 