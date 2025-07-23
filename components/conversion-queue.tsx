"use client"

import type { VideoFile } from "@/app/page"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Play, Trash2, Clock, CheckCircle, AlertCircle, FileVideo } from "lucide-react"
import { formatBytes, formatDuration } from "@/lib/utils"

interface ConversionQueueProps {
  files: VideoFile[]
  onStartConversion: (fileIds: string[]) => void
  onRemoveFile: (fileId: string) => void
}

export function ConversionQueue({ files, onStartConversion, onRemoveFile }: ConversionQueueProps) {
  const pendingFiles = files.filter((f) => f.status === "pending")
  const processingFiles = files.filter((f) => f.status === "processing")
  const completedFiles = files.filter((f) => f.status === "completed")
  const errorFiles = files.filter((f) => f.status === "error")

  const handleStartAll = () => {
    const pendingIds = pendingFiles.map((f) => f.id)
    if (pendingIds.length > 0) {
      onStartConversion(pendingIds)
    }
  }

  const getStatusIcon = (status: VideoFile["status"]) => {
    switch (status) {
      case "pending":
        return <Clock className="h-4 w-4 text-slate-400" />
      case "processing":
        return <div className="h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case "error":
        return <AlertCircle className="h-4 w-4 text-red-600" />
    }
  }

  const getStatusBadge = (status: VideoFile["status"]) => {
    const variants = {
      pending: "secondary",
      processing: "default",
      completed: "default",
      error: "destructive",
    } as const

    const labels = {
      pending: "Pending",
      processing: "Processing",
      completed: "Completed",
      error: "Error",
    }

    return (
      <Badge variant={variants[status]} className="capitalize">
        {labels[status]}
      </Badge>
    )
  }

  if (files.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <FileVideo className="h-12 w-12 text-slate-300 mb-4" />
          <h3 className="text-lg font-medium text-slate-900 mb-2">No files in queue</h3>
          <p className="text-slate-500 text-center">Upload some video files to get started with conversion</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Conversion Queue</h2>
          <p className="text-slate-600">
            {files.length} file{files.length !== 1 ? "s" : ""} •{pendingFiles.length} pending •{processingFiles.length}{" "}
            processing •{completedFiles.length} completed
          </p>
        </div>

        {pendingFiles.length > 0 && (
          <Button onClick={handleStartAll} className="flex items-center space-x-2">
            <Play className="h-4 w-4" />
            <span>Start All ({pendingFiles.length})</span>
          </Button>
        )}
      </div>

      <div className="space-y-4">
        {files.map((file) => (
          <Card key={file.id}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(file.status)}
                  <div>
                    <h3 className="font-medium text-slate-900">{file.name}</h3>
                    <p className="text-sm text-slate-500">
                      {formatBytes(file.size)} • {file.settings.preset} preset
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  {getStatusBadge(file.status)}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onRemoveFile(file.id)}
                    disabled={file.status === "processing"}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {file.status === "processing" && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-600">Converting...</span>
                    <span className="font-mono font-medium">{file.progress.toFixed(1)}%</span>
                  </div>
                  <Progress value={file.progress} className="w-full" />
                  
                  {/* Real-time conversion stats */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs bg-slate-50 p-3 rounded-lg">
                    <div>
                      <span className="text-slate-500 block">Time</span>
                      <span className="font-mono font-medium">{file.conversionTime || '00:00:00'}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">FPS</span>
                      <span className="font-mono font-medium">{file.conversionFps || '0'}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Speed</span>
                      <span className="font-mono font-medium">{file.conversionSpeed || '0x'}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">ETA</span>
                      <span className="font-mono font-medium">{file.conversionEta || '00:00:00'}</span>
                    </div>
                  </div>
                </div>
              )}

              {file.status === "completed" && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-slate-500">Processing Time</span>
                    <p className="font-medium">
                      {file.startTime && file.endTime ? formatDuration((file.endTime - file.startTime) / 1000) : "N/A"}
                    </p>
                  </div>
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
                </div>
              )}

              {file.status === "error" && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mt-4">
                  <div className="flex items-start space-x-3">
                    <AlertCircle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
                    <div>
                      <h4 className="font-medium text-red-800">Conversion Failed</h4>
                      <p className="text-sm text-red-600 mt-1">
                        {(file as any).errorMessage || "An error occurred during video conversion. Please try again with different settings or a different file."}
                      </p>
                      <div className="mt-3 flex space-x-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => onStartConversion([file.id])}
                          className="text-red-700 border-red-300 hover:bg-red-50"
                        >
                          <Play className="h-3 w-3 mr-1" />
                          Retry
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => onRemoveFile(file.id)}
                          className="text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="h-3 w-3 mr-1" />
                          Remove
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {file.status === "pending" && (
                <Button onClick={() => onStartConversion([file.id])} size="sm" className="mt-2">
                  <Play className="h-4 w-4 mr-2" />
                  Start Conversion
                </Button>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
