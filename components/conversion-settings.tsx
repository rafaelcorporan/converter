"use client"

import type { ConversionSettings as Settings } from "@/app/page"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { Switch } from "@/components/ui/switch"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Info } from "lucide-react"

interface ConversionSettingsProps {
  settings: Settings
  onSettingsChange: (settings: Settings) => void
}

export function ConversionSettings({ settings, onSettingsChange }: ConversionSettingsProps) {
  const updateSetting = (key: keyof Settings, value: any) => {
    onSettingsChange({ ...settings, [key]: value })
  }

  const presetDescriptions = {
    "web-standard": "Balanced quality and file size for web deployment",
    "high-quality": "Maximum visual fidelity with larger file sizes",
    "max-compression": "Smallest file size with acceptable quality",
    custom: "Manual control over all encoding parameters",
  }

  const getQualityLabel = (crf: number) => {
    if (crf <= 15) return "Excellent"
    if (crf <= 25) return "Very Good"
    if (crf <= 35) return "Good"
    if (crf <= 45) return "Fair"
    return "Poor"
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-slate-900 mb-4">Conversion Settings</h2>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Quality Preset</CardTitle>
          <CardDescription>Choose a preset or customize settings manually</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Select value={settings.preset} onValueChange={(value: any) => updateSetting("preset", value)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="web-standard">
                <div className="flex items-center justify-between w-full">
                  <span>Web Standard</span>
                  <Badge variant="secondary">Recommended</Badge>
                </div>
              </SelectItem>
              <SelectItem value="high-quality">High Quality</SelectItem>
              <SelectItem value="max-compression">Maximum Compression</SelectItem>
              <SelectItem value="custom">Custom</SelectItem>
            </SelectContent>
          </Select>

          <div className="text-sm text-slate-600 bg-slate-50 p-3 rounded-lg flex items-start space-x-2">
            <Info className="h-4 w-4 mt-0.5 text-slate-400" />
            <span>{presetDescriptions[settings.preset]}</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Quality Control</CardTitle>
          <CardDescription>CRF (Constant Rate Factor) - Lower values = higher quality</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Quality Level</Label>
              <div className="flex items-center space-x-2">
                <Badge variant="outline">{getQualityLabel(settings.quality)}</Badge>
                <span className="text-sm font-mono">{settings.quality}</span>
              </div>
            </div>
            <Slider
              value={[settings.quality]}
              onValueChange={([value]) => updateSetting("quality", value)}
              min={0}
              max={63}
              step={1}
              disabled={settings.preset !== "custom"}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-slate-500">
              <span>Best Quality</span>
              <span>Smallest Size</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Video Parameters</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Resolution</Label>
              <Select
                value={settings.resolution}
                onValueChange={(value) => updateSetting("resolution", value)}
                disabled={settings.preset !== "custom"}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="original">Original</SelectItem>
                  <SelectItem value="1920x1080">1080p</SelectItem>
                  <SelectItem value="1280x720">720p</SelectItem>
                  <SelectItem value="854x480">480p</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Frame Rate</Label>
              <Select
                value={settings.frameRate.toString()}
                onValueChange={(value) => updateSetting("frameRate", Number.parseInt(value))}
                disabled={settings.preset !== "custom"}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="24">24 fps</SelectItem>
                  <SelectItem value="30">30 fps</SelectItem>
                  <SelectItem value="60">60 fps</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Target Bitrate (kbps)</Label>
              <span className="text-sm font-mono">{settings.bitrate}</span>
            </div>
            <Slider
              value={[settings.bitrate]}
              onValueChange={([value]) => updateSetting("bitrate", value)}
              min={500}
              max={10000}
              step={100}
              disabled={settings.preset !== "custom"}
              className="w-full"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Advanced Options</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label>Two-Pass Encoding</Label>
              <p className="text-sm text-slate-600">Slower but more accurate bitrate control</p>
            </div>
            <Switch
              checked={settings.twoPass}
              onCheckedChange={(checked) => updateSetting("twoPass", checked)}
              disabled={settings.preset !== "custom"}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
