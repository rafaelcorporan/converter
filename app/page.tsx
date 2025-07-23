"use client"

import { useState, useCallback, useEffect } from "react"
import { FileUpload } from "@/components/file-upload"
import { ConversionSettings } from "@/components/conversion-settings"
import { ConversionQueue } from "@/components/conversion-queue"
import { VideoPreview } from "@/components/video-preview"
import { ResultsPanel } from "@/components/results-panel"
import { Header } from "@/components/header"
import { Card } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useToast } from "@/hooks/use-toast"

export interface VideoFile {
  id: string
  file: File
  name: string
  size: number
  duration?: number
  status: "pending" | "processing" | "completed" | "error"
  progress: number
  originalUrl: string
  convertedUrl?: string
  startTime?: number
  endTime?: number
  originalSize: number
  convertedSize?: number
  settings: ConversionSettings
  conversionTime?: string
  conversionFps?: number
  conversionSpeed?: string
  conversionEta?: string
  errorMessage?: string
}

export interface ConversionSettings {
  preset: "web-standard" | "high-quality" | "max-compression" | "custom"
  quality: number
  bitrate: number
  resolution: "original" | "1920x1080" | "1280x720" | "854x480"
  frameRate: number
  twoPass: boolean
}

const defaultSettings: ConversionSettings = {
  preset: "web-standard",
  quality: 32,
  bitrate: 1000,
  resolution: "original",
  frameRate: 30,
  twoPass: false,
}

export default function VideoConverter() {
  const [files, setFiles] = useState<VideoFile[]>([])
  const [settings, setSettings] = useState(defaultSettings)
  const [activeTab, setActiveTab] = useState("upload")
  const { toast } = useToast()

  // Handle shared results from URL parameters
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search)
    const shareData = urlParams.get('share')
    
    if (shareData) {
      try {
        const decodedData = JSON.parse(atob(shareData))
        
        // Convert shared data to VideoFile format
        const sharedFiles: VideoFile[] = decodedData.files.map((fileData: any, index: number) => ({
          id: `shared-${index}`,
          file: new File([], fileData.name), // Placeholder file
          name: fileData.name,
          size: fileData.originalSize,
          status: "completed" as const,
          progress: 100,
          startTime: new Date(decodedData.timestamp).getTime(),
          endTime: new Date(decodedData.timestamp).getTime() + 5000, // Estimate
          originalSize: fileData.originalSize,
          convertedSize: fileData.convertedSize,
          originalUrl: fileData.convertedUrl, // Use converted URL as original for display
          convertedUrl: fileData.convertedUrl,
          settings: fileData.settings,
        }))
        
        setFiles(sharedFiles)
        setActiveTab("results")
        
        // Show notification
        toast({
          title: "Shared Results Loaded",
          description: `Loaded ${sharedFiles.length} shared conversion results.`,
        })
        
        // Clear the share parameter from URL
        const newUrl = new URL(window.location.href)
        newUrl.searchParams.delete('share')
        window.history.replaceState({}, '', newUrl.toString())
      } catch (error) {
        console.error('Failed to parse shared data:', error)
      }
    }
  }, [])

  const handleFilesAdded = useCallback(
    (newFiles: File[]) => {
      const videoFiles: VideoFile[] = newFiles.map((file) => ({
        id: Math.random().toString(36).substr(2, 9),
        file,
        name: file.name,
        size: file.size,
        status: "pending",
        progress: 0,
        startTime: undefined,
        endTime: undefined,
        originalSize: file.size,
        convertedSize: undefined,
        originalUrl: URL.createObjectURL(file),
        convertedUrl: undefined,
        settings: settings,
      }))

      setFiles((prev) => [...prev, ...videoFiles])
      if (videoFiles.length > 0) {
        setActiveTab("queue")
      }
    },
    [settings],
  )

  const handleStartConversion = useCallback(
    async (fileIds: string[]) => {
      const filesToProcess = files.filter((f) => fileIds.includes(f.id))

      for (const file of filesToProcess) {
        try {
          // Update status to processing
          setFiles((prev) =>
            prev.map((f) => (f.id === file.id ? { ...f, status: "processing", startTime: Date.now() } : f)),
          )

          // Import the VideoAPI
          const { VideoAPI } = await import("@/lib/video-api")

          // Start conversion
          const conversionResponse = await VideoAPI.convertVideo(file.file, file.settings)

          // Poll for progress
          const stopPolling = VideoAPI.pollProgress(
            conversionResponse.conversion_id,
            (progress) => {
              // Update progress with real-time data
              setFiles((prev) => prev.map((f) => (f.id === file.id ? { 
                ...f, 
                progress: progress.progress,
                conversionTime: progress.time,
                conversionFps: progress.fps,
                conversionSpeed: progress.speed,
                conversionEta: progress.eta
              } : f)))
            },
            async (result) => {
              // Conversion completed
              try {
                // Download the converted file
                const convertedBlob = await VideoAPI.downloadVideo(conversionResponse.conversion_id)
                const convertedUrl = URL.createObjectURL(convertedBlob)

                setFiles((prev) =>
                  prev.map((f) =>
                    f.id === file.id
                      ? {
                          ...f,
                          status: "completed",
                          progress: 100,
                          endTime: Date.now(),
                          convertedUrl: convertedUrl,
                          convertedSize: result.output_size || Math.floor(file.size * 0.6),
                          settings: settings,
                        }
                      : f,
                  ),
                )
              } catch (downloadError) {
                console.error("Failed to download converted file:", downloadError)
                setFiles((prev) =>
                  prev.map((f) =>
                    f.id === file.id
                      ? {
                          ...f,
                          status: "error",
                          progress: 0,
                        }
                      : f,
                  ),
                )
              }
            },
            (error) => {
              // Conversion failed
              console.error("Conversion failed:", error)
              setFiles((prev) =>
                prev.map((f) =>
                  f.id === file.id
                    ? {
                        ...f,
                        status: "error",
                        progress: 0,
                        errorMessage: typeof error === 'string' ? error : 'Conversion failed unexpectedly',
                      }
                    : f,
                ),
              )
            }
          )
        } catch (error) {
          console.error("Failed to start conversion:", error)
          setFiles((prev) =>
            prev.map((f) =>
              f.id === file.id
                ? {
                    ...f,
                    status: "error",
                    progress: 0,
                    errorMessage: error instanceof Error ? error.message : 'Failed to start conversion',
                  }
                : f,
            ),
          )
        }
      }
    },
    [files, settings],
  )

  const handleRemoveFile = useCallback((fileId: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileId))
  }, [])

  const completedFiles = files.filter((f) => f.status === "completed")

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <Header />

      <main className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-slate-900 mb-4">Professional Video Converter</h1>
            <p className="text-xl text-slate-600 max-w-2xl mx-auto">
              Convert MP4 videos to WebM (VP9) format with advanced encoding options. Optimized for web deployment with
              superior compression and quality.
            </p>
          </div>

          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="upload">Upload Files</TabsTrigger>
              <TabsTrigger value="queue">Conversion Queue</TabsTrigger>
              <TabsTrigger value="preview">Preview</TabsTrigger>
              <TabsTrigger value="results">Results</TabsTrigger>
            </TabsList>

            <TabsContent value="upload" className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                  <Card className="p-6">
                    <FileUpload onFilesAdded={handleFilesAdded} />
                  </Card>
                </div>
                <div>
                  <Card className="p-6">
                    <ConversionSettings settings={settings} onSettingsChange={setSettings} />
                  </Card>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="queue">
              <ConversionQueue
                files={files}
                onStartConversion={handleStartConversion}
                onRemoveFile={handleRemoveFile}
              />
            </TabsContent>

            <TabsContent value="preview">
              <VideoPreview files={files.filter((f) => f.status === "completed")} />
            </TabsContent>

            <TabsContent value="results">
              <ResultsPanel files={completedFiles} />
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  )
}
