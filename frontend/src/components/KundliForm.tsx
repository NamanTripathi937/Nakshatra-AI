"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { CalendarIcon, MapPin, Clock, Sparkles } from "lucide-react"
import { format } from "date-fns"
import type { KundliInput } from "../lib/types";

export default function KundliForm({ onSubmit }: { onSubmit: (data: KundliInput) => void }) {
  const [date, setDate] = useState<Date>()
  const [formData, setFormData] = useState({
    birthdate: "",
    birthtime: "",
    birthlatitude: "",
    birthlongitude: "",
    birthtimezone: "5.5",
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData);
  }

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  return (
    <div className="flex items-center justify-center  ">
      <div className="w-full max-w-sm sm:max-w-xs md:max-w-sm lg:max-w-md">
        <div className="text-center mb-2">
          <div className="flex items-center justify-center mb-3">
            <span className="text-2xl mr-3">🌕</span>
            <h1 className="text-xl font-bold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
              Enter Your Birth Details
            </h1>
          </div>
        </div>

        <Card className="shadow-xl border border-gray-700 bg-black/90 backdrop-blur-sm pb-2">
          <CardContent className="pb-2">
            <form onSubmit={handleSubmit} className="space-y-2">
              {/* Date of Birth */}
              <div className="space-y-1">
                <Label htmlFor="birthdate" className="text-xs font-medium text-gray-300">
                  Date of Birth
                </Label>
                <div className="relative">
                  <Input
                    id="birthdate"
                    type="text"
                    placeholder="dd-mm-yy"
                    value={formData.birthdate}
                    onChange={(e) => handleInputChange("birthdate", e.target.value)}
                    className="h-9 pl-3 bg-black border-gray-600 text-gray-100 text-xs placeholder:text-gray-400 focus:border-purple-400 focus:ring-purple-400"
                    required
                  />
                </div>
              </div>

              {/* Time of Birth */}
              <div className="space-y-1">
                <Label htmlFor="birthtime" className="text-xs font-medium text-gray-300">
                  Time of Birth
                </Label>
                <div className="relative">
                  <Input
                    id="birthtime"
                    type="text"
                    placeholder="HH:MM"
                    value={formData.birthtime}
                    onChange={(e) => handleInputChange("birthtime", e.target.value)}
                    className="h-9 pl-3 bg-black border-gray-600 text-gray-100 text-xs placeholder:text-gray-400 focus:border-purple-400 focus:ring-purple-400"
                    required
                  />
                </div>
                <p className="text-xs text-gray-500">Use 24-hour format (e.g., 14:30 for 2:30 PM)</p>
              </div>

              {/* Latitude */}
              <div className="space-y-1">
                <Label htmlFor="birthlatitude" className="text-xs font-medium text-gray-300">
                  Latitude of Birth place
                </Label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-purple-600" />
                  <Input
                    id="birthlatitude"
                    type="text"
                    placeholder="Latitude"
                    value={formData.birthlatitude}
                    onChange={(e) => handleInputChange("birthlatitude", e.target.value)}
                    className="h-9 pl-9 bg-black border-gray-600 text-gray-100 text-xs placeholder:text-gray-400 focus:border-purple-400 focus:ring-purple-400"
                    required
                  />
                </div>
              </div>
              {/* Longitude */}
              <div className="space-y-1">
                <Label htmlFor="birthlongitude" className="text-xs font-medium text-gray-300">
                  Longitude of Birth place
                </Label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-purple-600" />
                  <Input
                    id="birthlongitude"
                    type="text"
                    placeholder="Longitude"
                    value={formData.birthlongitude}
                    onChange={(e) => handleInputChange("birthlongitude", e.target.value)}
                    className="h-9 pl-9 bg-black border-gray-600 text-gray-100 text-xs placeholder:text-gray-400 focus:border-purple-400 focus:ring-purple-400"
                    required
                  />
                </div>
              </div>
              {/* TimeZone */}
              <div className="space-y-1">
                <Label htmlFor="birthtimezone" className="text-xs font-medium text-gray-300">
                  Timezone of Birth place
                </Label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-purple-600" />
                  <Input
                    id="birthtimezone"
                    type="text"
                    placeholder="Time Zone (5.5 for India)"
                    value={formData.birthtimezone}
                    onChange={(e) => handleInputChange("birthtimezone", e.target.value)}
                    className="h-9 pl-9 bg-black border-gray-600 text-gray-100 text-xs placeholder:text-gray-400 focus:border-purple-400 focus:ring-purple-400"
                    required
                  />
                </div>
              </div>

              {/* Submit Button */}
              <Button
                type="submit"
                className="w-full h-8 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-medium rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 text-sm"
              >
                <Sparkles className="mr-2 h-4 w-4" />
                Get Astrological Insights
              </Button>
            </form>
          </CardContent>
        </Card>

        <div className="text-center mb-0 pb-0">
          <p className="text-xs text-gray-500 mb-0 pb-0">Your information is secure and used only for Kundali generation</p>
        </div>
      </div>
    </div>
  )
}

