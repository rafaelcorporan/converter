"use client"

import type { VideoFile } from "@/app/page"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { Download, Share2, Archive, Trash2, BarChart3 } from "lucide-react"
import { formatBytes, formatDuration } from "@/lib/utils"
import JSZip from "jszip"
import { useState } from "react"
import { useToast } from "@/hooks/use-toast"

interface ResultsPanelProps {
  files: VideoFile[]
}

export function ResultsPanel({ files }: ResultsPanelProps) {
  const [isDownloading, setIsDownloading] = useState(false)
  const [isSharing, setIsSharing] = useState(false)
  const { toast } = useToast()
  const totalOriginalSize = files.reduce((sum, file) => sum + file.size, 0)
  const totalConvertedSize = files.reduce((sum, file) => sum + (file.convertedSize || 0), 0)
  const totalSavings = totalOriginalSize - totalConvertedSize
  const averageReduction = totalOriginalSize > 0 ? (totalSavings / totalOriginalSize) * 100 : 0

  const handleDownloadAll = async () => {
    setIsDownloading(true)
    try {
      const zip = new JSZip()
      const convertedFiles = files.filter(file => file.convertedUrl && file.status === "completed")
      
      if (convertedFiles.length === 0) {
        toast({
          title: "No files to download",
          description: "No converted files are available for download.",
          variant: "destructive",
        })
        return
      }

      toast({
        title: "Creating ZIP file...",
        description: `Processing ${convertedFiles.length} files for download.`,
      })

      // Add each converted file to the ZIP
      for (let i = 0; i < convertedFiles.length; i++) {
        const file = convertedFiles[i]
        if (file.convertedUrl) {
          try {
            // Fetch the converted file
            const response = await fetch(file.convertedUrl)
            if (!response.ok) {
              console.error(`Failed to fetch ${file.name}: ${response.statusText}`)
              continue
            }
            
            const blob = await response.blob()
            const fileName = file.name.replace(/\.[^/.]+$/, ".webm")
            zip.file(fileName, blob)
          } catch (error) {
            console.error(`Error processing ${file.name}:`, error)
          }
        }
      }

      // Generate and download the ZIP file
      const zipBlob = await zip.generateAsync({ type: "blob" })
      const url = URL.createObjectURL(zipBlob)
      const link = document.createElement("a")
      link.href = url
      link.download = `converted-videos-${new Date().toISOString().split('T')[0]}.zip`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      
      console.log(`Downloaded ${convertedFiles.length} files as ZIP`)
      toast({
        title: "Download Complete",
        description: `Successfully downloaded ${convertedFiles.length} files as ZIP.`,
      })
    } catch (error) {
      console.error("Error creating ZIP file:", error)
      toast({
        title: "Download Failed",
        description: "Failed to create ZIP file. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsDownloading(false)
    }
  }

  const handleDownloadFile = (file: VideoFile) => {
    if (file.convertedUrl) {
      const link = document.createElement("a")
      link.href = file.convertedUrl
      link.download = file.name.replace(/\.[^/.]+$/, ".webm")
      link.click()
    }
  }

  const handleShareResults = async () => {
    setIsSharing(true)
    const convertedFiles = files.filter(file => file.convertedUrl && file.status === "completed")
    
    if (convertedFiles.length === 0) {
      toast({
        title: "No files to share",
        description: "No converted files are available for sharing.",
        variant: "destructive",
      })
      return
    }

    // Create a shareable URL with conversion data
    const shareableData = {
      timestamp: new Date().toISOString(),
      totalFiles: files.length,
      convertedFiles: convertedFiles.length,
      totalOriginalSize,
      totalConvertedSize,
      averageReduction: Math.round(averageReduction),
      files: convertedFiles.map(file => ({
        name: file.name,
        originalSize: file.size,
        convertedSize: file.convertedSize,
        convertedUrl: file.convertedUrl,
        settings: file.settings
      }))
    }
    
    // Encode the data as a URL parameter
    const encodedData = btoa(JSON.stringify(shareableData))
    const shareableUrl = `${window.location.origin}?share=${encodedData}`

    try {
      // Create a summary of the conversion results
      const summary = {
        totalFiles: files.length,
        convertedFiles: convertedFiles.length,
        totalOriginalSize: formatBytes(totalOriginalSize),
        totalConvertedSize: formatBytes(totalConvertedSize),
        averageReduction: `${Math.round(averageReduction)}%`,
        conversionDate: new Date().toLocaleDateString(),
        files: convertedFiles.map(file => ({
          name: file.name,
          originalSize: formatBytes(file.size),
          convertedSize: file.convertedSize ? formatBytes(file.convertedSize) : "N/A",
          reduction: file.convertedSize ? `${Math.round((1 - file.convertedSize / file.size) * 100)}%` : "N/A",
          settings: file.settings
        }))
      }

      // Create a shareable text
      const shareText = `🎥 Video Conversion Results

📊 Summary:
• ${summary.totalFiles} files processed
• ${summary.convertedFiles} files converted successfully
• Original size: ${summary.totalOriginalSize}
• Converted size: ${summary.totalConvertedSize}
• Average reduction: ${summary.averageReduction}

📁 Converted Files:
${summary.files.map(file => `• ${file.name} (${file.originalSize} → ${file.convertedSize}, ${file.reduction} reduction)`).join('\n')}

🔄 Conversion Settings: WebM format with ${summary.files[0]?.settings.quality || '32'} CRF quality

📅 Converted on ${summary.conversionDate}

🔗 View Results: ${shareableUrl}

#VideoConverter #WebM #Optimization`

      // Try to use Web Share API if available
      if (navigator.share) {
        await navigator.share({
          title: 'Video Conversion Results',
          text: shareText,
          url: shareableUrl
        })
        toast({
          title: "Results Shared",
          description: "Conversion results have been shared successfully.",
        })
      } else {
        // Fallback to clipboard
        await navigator.clipboard.writeText(shareText)
        toast({
          title: "Results Copied",
          description: "Conversion results have been copied to clipboard.",
        })
      }
    } catch (error) {
      console.error("Error sharing results:", error)
      toast({
        title: "Share Failed",
        description: "Failed to share results. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsSharing(false)
    }
  }

  const handleShareFile = async (file: VideoFile) => {
    if (!file.convertedUrl) {
      toast({
        title: "Cannot share file",
        description: "This file hasn't been converted yet.",
        variant: "destructive",
      })
      return
    }

    try {
      const shareText = `🎥 Converted Video: ${file.name}

📊 Conversion Details:
• Original size: ${formatBytes(file.size)}
• Converted size: ${file.convertedSize ? formatBytes(file.convertedSize) : "N/A"}
• Size reduction: ${file.convertedSize ? `${Math.round((1 - file.convertedSize / file.size) * 100)}%` : "N/A"}
• Quality (CRF): ${file.settings.quality}
• Bitrate: ${file.settings.bitrate} kbps
• Preset: ${file.settings.preset}

🔄 Converted to WebM format for optimal web compatibility

📅 Converted on ${new Date().toLocaleDateString()}

#VideoConverter #WebM #${file.name.replace(/\.[^/.]+$/, "")}`

      // Try to use Web Share API if available
      if (navigator.share) {
        await navigator.share({
          title: `Converted: ${file.name}`,
          text: shareText,
          url: file.convertedUrl
        })
        toast({
          title: "File Shared",
          description: `${file.name} has been shared successfully.`,
        })
      } else {
        // Fallback to clipboard with file URL
        const fullShareText = `${shareText}\n\n🔗 Download Link: ${file.convertedUrl}`
        await navigator.clipboard.writeText(fullShareText)
        toast({
          title: "File Info Copied",
          description: `${file.name} conversion details and download link copied to clipboard.`,
        })
      }
    } catch (error) {
      console.error("Error sharing file:", error)
      toast({
        title: "Share Failed",
        description: "Failed to share file. Please try again.",
        variant: "destructive",
      })
    }
  }

  if (files.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <BarChart3 className="h-12 w-12 text-slate-300 mb-4" />
          <h3 className="text-lg font-medium text-slate-900 mb-2">No results yet</h3>
          <p className="text-slate-500 text-center">
            Complete some video conversions to see detailed results and analytics
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Conversion Results</h2>
          <p className="text-slate-600">
            {files.length} file{files.length !== 1 ? "s" : ""} converted successfully
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <Button 
            variant="outline" 
            onClick={handleDownloadAll}
            disabled={isDownloading}
          >
            <Archive className="h-4 w-4 mr-2" />
            {isDownloading ? "Creating ZIP..." : `Download All (ZIP) - ${files.filter(f => f.convertedUrl && f.status === "completed").length} files`}
          </Button>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button onClick={handleShareResults} disabled={isSharing}>
                <Share2 className="h-4 w-4 mr-2" />
                {isSharing ? "Sharing..." : "Share Results"}
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>Share conversion results and statistics</p>
            </TooltipContent>
          </Tooltip>
        </div>
      </div>

      {/* Summary Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="text-2xl font-bold text-slate-900">{files.length}</div>
            <p className="text-sm text-slate-600">Files Converted</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="text-2xl font-bold text-slate-900">{formatBytes(totalOriginalSize)}</div>
            <p className="text-sm text-slate-600">Original Size</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="text-2xl font-bold text-slate-900">{formatBytes(totalConvertedSize)}</div>
            <p className="text-sm text-slate-600">Converted Size</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="text-2xl font-bold text-green-600">{Math.round(averageReduction)}%</div>
            <p className="text-sm text-slate-600">Average Reduction</p>
          </CardContent>
        </Card>
      </div>

      {/* Individual File Results */}
      <div className="space-y-4">
        {files.map((file) => (
          <Card key={file.id}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div>
                    <h3 className="font-medium text-slate-900">{file.name}</h3>
                    <p className="text-sm text-slate-500">Converted with {file.settings.preset} preset</p>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <Badge variant="secondary">WebM</Badge>
                  <Button variant="outline" size="sm" onClick={() => handleDownloadFile(file)}>
                    <Download className="h-4 w-4 mr-2" />
                    Download
                  </Button>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-6 gap-4 text-sm">
                <div>
                  <span className="text-slate-500">Original Size</span>
                  <p className="font-medium">{formatBytes(file.size)}</p>
                </div>
                <div>
                  <span className="text-slate-500">Converted Size</span>
                  <p className="font-medium">{file.convertedSize ? formatBytes(file.convertedSize) : "N/A"}</p>
                </div>
                <div>
                  <span className="text-slate-500">Size Reduction</span>
                  <p className="font-medium text-green-600">
                    {file.convertedSize ? `${Math.round((1 - file.convertedSize / file.size) * 100)}%` : "N/A"}
                  </p>
                </div>
                <div>
                  <span className="text-slate-500">Processing Time</span>
                  <p className="font-medium">
                    {file.startTime && file.endTime ? formatDuration((file.endTime - file.startTime) / 1000) : "N/A"}
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
              </div>

              <div className="mt-4 pt-4 border-t border-slate-200">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-slate-600">
                    Converted on {new Date().toLocaleDateString()} at {new Date().toLocaleTimeString()}
                  </div>
                  <div className="flex items-center space-x-2">
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button variant="ghost" size="sm" onClick={() => handleShareFile(file)}>
                          <Share2 className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Share this file's conversion details</p>
                      </TooltipContent>
                    </Tooltip>
                    <Button variant="ghost" size="sm">
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Optimization Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Optimization Recommendations</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h4 className="font-medium text-blue-900 mb-2">Web Deployment Tips</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Use WebM for modern browsers with MP4 fallback</li>
                <li>• Consider adaptive bitrate streaming for longer videos</li>
                <li>• Implement lazy loading for better page performance</li>
              </ul>
            </div>

            <div className="bg-green-50 p-4 rounded-lg">
              <h4 className="font-medium text-green-900 mb-2">Quality Optimization</h4>
              <ul className="text-sm text-green-800 space-y-1">
                <li>• CRF 23-28 provides good balance for most content</li>
                <li>• Use two-pass encoding for critical quality requirements</li>
                <li>• Test different presets based on content type</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
