import { Video, Settings, BarChart3 } from "lucide-react"
import { Button } from "@/components/ui/button"

export function Header() {
  return (
    <header className="bg-white border-b border-slate-200 shadow-sm">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-3">
            <div className="bg-blue-600 p-2 rounded-lg">
              <Video className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">VideoConvert Pro</h1>
              <p className="text-sm text-slate-500">MP4 to WebM Converter</p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <Button variant="ghost" size="sm">
              <BarChart3 className="h-4 w-4 mr-2" />
              Analytics
            </Button>
            <Button variant="ghost" size="sm">
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </Button>
            <Button>Sign In</Button>
          </div>
        </div>
      </div>
    </header>
  )
}
