"use client"

import { useCallback, useState } from "react"
import { useDropzone } from "react-dropzone"
import { Upload, FileVideo, AlertCircle } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"

interface FileUploadProps {
  onFilesAdded: (files: File[]) => void
}

export function FileUpload({ onFilesAdded }: FileUploadProps) {
  const [error, setError] = useState<string | null>(null)

  const onDrop = useCallback(
    (acceptedFiles: File[], rejectedFiles: any[]) => {
      setError(null)

      if (rejectedFiles.length > 0) {
        const reasons = rejectedFiles.map(file => {
          if (file.errors?.some((e: any) => e.code === 'file-too-large')) {
            return `${file.file.name}: File too large (max 500MB)`
          }
          if (file.errors?.some((e: any) => e.code === 'file-invalid-type')) {
            return `${file.file.name}: Unsupported file type`
          }
          return `${file.file.name}: Unknown error`
        }).join(', ')
        
        setError(`Files rejected: ${reasons}`)
        return
      }

      if (acceptedFiles.length > 0) {
        onFilesAdded(acceptedFiles)
      }
    },
    [onFilesAdded],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "video/mp4": [".mp4"],
      "video/quicktime": [".mov"],
      "video/x-msvideo": [".avi"],
      "video/x-matroska": [".mkv"],
      "video/x-ms-wmv": [".wmv"],
      "video/x-flv": [".flv"],
      "video/webm": [".webm"],
      "video/3gpp": [".3gp"],
    },
    maxSize: 500 * 1024 * 1024, // 500MB
    multiple: true,
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-900">Upload Video Files</h2>
        <div className="text-sm text-slate-500">Max size: 500MB per file</div>
      </div>

      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
          ${isDragActive ? "border-blue-400 bg-blue-50" : "border-slate-300 hover:border-slate-400"}
        `}
      >
        <input {...getInputProps()} />

        <div className="space-y-4">
          <div className="mx-auto w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center">
            {isDragActive ? (
              <Upload className="h-8 w-8 text-blue-600" />
            ) : (
              <FileVideo className="h-8 w-8 text-slate-400" />
            )}
          </div>

          <div>
            <p className="text-lg font-medium text-slate-900">
              {isDragActive ? "Drop files here" : "Drag & drop video files"}
            </p>
            <p className="text-slate-500 mt-1">
              or <span className="text-blue-600 font-medium">browse files</span>
            </p>
          </div>

          <div className="text-sm text-slate-400">Supports MP4, MOV, AVI, MKV, WMV, FLV, WebM formats</div>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        <div className="bg-slate-50 p-4 rounded-lg">
          <h3 className="font-medium text-slate-900 mb-2">Supported Formats</h3>
          <ul className="text-slate-600 space-y-1">
            <li>• MP4 (H.264/H.265)</li>
            <li>• MOV (QuickTime)</li>
            <li>• AVI, MKV, WMV</li>
            <li>• FLV, WebM, 3GP</li>
          </ul>
        </div>

        <div className="bg-slate-50 p-4 rounded-lg">
          <h3 className="font-medium text-slate-900 mb-2">Output Format</h3>
          <ul className="text-slate-600 space-y-1">
            <li>• WebM (VP9 codec)</li>
            <li>• Opus audio codec</li>
            <li>• Optimized for web</li>
          </ul>
        </div>

        <div className="bg-slate-50 p-4 rounded-lg">
          <h3 className="font-medium text-slate-900 mb-2">Features</h3>
          <ul className="text-slate-600 space-y-1">
            <li>• Batch processing</li>
            <li>• Quality presets</li>
            <li>• Advanced options</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
