import type { VideoFile } from "@/app/page"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Play, Download, Eye, Pause, Square } from "lucide-react"
import { formatBytes } from "@/lib/utils"
import { useState, useRef } from "react"

interface VideoPreviewProps {
  files: VideoFile[]
}

export function VideoPreview({ files }: VideoPreviewProps) {
  const [playingFile, setPlayingFile] = useState<string | null>(null)
  const [isComparisonMode, setIsComparisonMode] = useState<string | null>(null)
  const videoRefs = useRef<{ [key: string]: HTMLVideoElement | null }>({})

  if (files.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <Eye className="h-12 w-12 text-slate-300 mb-4" />
          <h3 className="text-lg font-medium text-slate-900 mb-2">No converted files</h3>
          <p className="text-slate-500 text-center">Complete some conversions to preview the results here</p>
        </CardContent>
      </Card>
    )
  }

  const handlePlayComparison = (fileId: string) => {
    setIsComparisonMode(fileId)
    setPlayingFile(fileId)
    
    // Start both videos simultaneously
    const originalVideo = videoRefs.current[`${fileId}-original`]
    const convertedVideo = videoRefs.current[`${fileId}-converted`]
    
    if (originalVideo && convertedVideo) {
      originalVideo.currentTime = 0
      convertedVideo.currentTime = 0
      originalVideo.play()
      convertedVideo.play()
    }
  }

  const handleStopComparison = (fileId: string) => {
    setIsComparisonMode(null)
    setPlayingFile(null)
    
    // Stop both videos
    const originalVideo = videoRefs.current[`${fileId}-original`]
    const convertedVideo = videoRefs.current[`${fileId}-converted`]
    
    if (originalVideo && convertedVideo) {
      originalVideo.pause()
      convertedVideo.pause()
      originalVideo.currentTime = 0
      convertedVideo.currentTime = 0
    }
  }

  const handleDownloadWebM = async (file: VideoFile) => {
    if (!file.convertedUrl) {
      console.error("No converted file available for download")
      return
    }

    try {
      // Create a temporary link element to trigger download
      const link = document.createElement('a')
      link.href = file.convertedUrl
      link.download = `${file.name.replace(/\.[^/.]+$/, "")}.webm`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    } catch (error) {
      console.error("Failed to download file:", error)
    }
  }

  const handleVideoEnded = (fileId: string) => {
    setPlayingFile(null)
    setIsComparisonMode(null)
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-slate-900 mb-2">Video Preview</h2>
        <p className="text-slate-600">Compare original and converted videos side by side</p>
      </div>

      <div className="grid gap-6">
        {files.map((file) => (
          <Card key={file.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">{file.name}</CardTitle>
                <div className="flex items-center space-x-2">
                  <Badge variant="outline">WebM</Badge>
                  <Badge variant="secondary">
                    {file.convertedSize && file.size
                      ? `${Math.round((1 - file.convertedSize / file.size) * 100)}% smaller`
                      : "Converted"}
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Original Video */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium text-slate-900">Original (MP4)</h4>
                    <span className="text-sm text-slate-500">{formatBytes(file.size)}</span>
                  </div>
                  <div className="aspect-video bg-slate-100 rounded-lg overflow-hidden">
                    {file.originalUrl ? (
                                             <video
                         ref={(el) => {
                           videoRefs.current[`${file.id}-original`] = el
                         }}
                         src={file.originalUrl}
                         className="w-full h-full object-cover"
                         onEnded={() => handleVideoEnded(file.id)}
                         muted={isComparisonMode === file.id}
                       />
                    ) : (
                      <div className="flex items-center justify-center h-full">
                        <div className="text-center">
                          <Play className="h-12 w-12 text-slate-400 mx-auto mb-2" />
                          <p className="text-sm text-slate-500">Original Video Preview</p>
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-slate-500">Format</span>
                      <p className="font-medium">MP4 (H.264)</p>
                    </div>
                    <div>
                      <span className="text-slate-500">Quality</span>
                      <p className="font-medium">Original</p>
                    </div>
                  </div>
                </div>

                {/* Converted Video */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium text-slate-900">Converted (WebM)</h4>
                    <span className="text-sm text-slate-500">
                      {file.convertedSize ? formatBytes(file.convertedSize) : "N/A"}
                    </span>
                  </div>
                  <div className="aspect-video bg-slate-100 rounded-lg overflow-hidden">
                    {file.convertedUrl ? (
                                             <video
                         ref={(el) => {
                           videoRefs.current[`${file.id}-converted`] = el
                         }}
                         src={file.convertedUrl}
                         className="w-full h-full object-cover"
                         onEnded={() => handleVideoEnded(file.id)}
                         muted={isComparisonMode === file.id}
                       />
                    ) : (
                      <div className="flex items-center justify-center h-full">
                        <div className="text-center">
                          <Play className="h-12 w-12 text-slate-400 mx-auto mb-2" />
                          <p className="text-sm text-slate-500">WebM Preview</p>
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-slate-500">Format</span>
                      <p className="font-medium">WebM (VP9)</p>
                    </div>
                    <div>
                      <span className="text-slate-500">Preset</span>
                      <p className="font-medium capitalize">{file.settings.preset.replace("-", " ")}</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Comparison Stats */}
              <div className="bg-slate-50 p-4 rounded-lg">
                <h5 className="font-medium text-slate-900 mb-3">Conversion Summary</h5>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-slate-500">Size Reduction</span>
                    <p className="font-medium text-green-600">
                      {file.convertedSize && file.size
                        ? `${Math.round((1 - file.convertedSize / file.size) * 100)}%`
                        : "N/A"}
                    </p>
                  </div>
                  <div>
                    <span className="text-slate-500">Quality (CRF)</span>
                    <p className="font-medium">{file.settings.quality}</p>
                  </div>
                  <div>
                    <span className="text-slate-500">Bitrate</span>
                    <p className="font-medium">{file.settings.bitrate} kbps</p>
                  </div>
                  <div>
                    <span className="text-slate-500">Two-Pass</span>
                    <p className="font-medium">{file.settings.twoPass ? "Yes" : "No"}</p>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                {isComparisonMode === file.id ? (
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => handleStopComparison(file.id)}
                  >
                    <Square className="h-4 w-4 mr-2" />
                    Stop Comparison
                  </Button>
                ) : (
                  <Button 
                    size="sm"
                    onClick={() => handlePlayComparison(file.id)}
                    disabled={!file.convertedUrl}
                  >
                    <Play className="h-4 w-4 mr-2" />
                    Play Comparison
                  </Button>
                )}
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => handleDownloadWebM(file)}
                  disabled={!file.convertedUrl}
                >
                  <Download className="h-4 w-4 mr-2" />
                  Download WebM
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
