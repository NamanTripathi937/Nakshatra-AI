"use client"

import type React from "react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { MapPin, Sparkles } from "lucide-react"
import PlacesAutoComplete from "./ui/placesAutoComplete"
import { Loader2 } from "lucide-react"
export default function KundaliForm({ onSubmit, loading }: { onSubmit: (data: any) => void; loading: boolean }) {
  const [formData, setFormData] = useState({
    year: "",
    month: "",
    date: "",
    hours: "",
    minutes: "",
    seconds: "",
    timezone: "Asia/Kolkata",
    latitude: "",
    longitude: "",
  })
  const [placeSelected, setPlaceSelected] = useState(false)
  const [viewPlaceSelectError, setViewPlaceSelectError] = useState(false)
  const handlePlaceSelect = (lat: number, lon: number) => {
    setPlaceSelected(true)
    setViewPlaceSelectError(false)
    setFormData((prev) => ({
      ...prev,
      latitude: lat.toString(),
      longitude: lon.toString(),
    }))
  }


  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!placeSelected) {
      setViewPlaceSelectError(true)
      return
    } else {
      const finalData = {
        year: parseInt(formData.year),
        month: parseInt(formData.month),
        date: parseInt(formData.date),
        hours: parseInt(formData.hours),
        minutes: parseInt(formData.minutes),
        seconds: parseInt(formData.seconds),
        latitude: parseFloat(formData.latitude),
        longitude: parseFloat(formData.longitude),
        timezone: "Asia/Kolkata",
        settings: {
          observation_point: "topocentric",
          ayanamsha: "lahiri",
        },
      }
      onSubmit(finalData)
    }
  }

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }
  return (
    <div className="flex items-center justify-center bg-transparent">
      <div className="w-full max-w-sm sm:max-w-xs md:max-w-sm lg:max-w-md">
        <div className="text-center mb-2">
          <div className="flex items-center justify-center mb-3">
            <span className="text-2xl mr-3">🌕</span>
            <h1 className="text-xl font-bold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
              Enter Your Birth Details
            </h1>
          </div>
        </div>

        <Card className="shadow-xl border border-gray-700 bg-black/20 backdrop-blur-md pb-2">
          <CardContent className="pb-2">
            <form onSubmit={handleSubmit} className="space-y-3">

              {/* Date of Birth */}
              <div className="space-y-1">
                <Label className="text-xs font-medium text-gray-300">Date of Birth</Label>
                <div className="flex gap-2">
                  <Input
                    type="number"
                    placeholder="YYYY"
                    value={formData.year}
                    onChange={(e) => handleInputChange("year", e.target.value)}
                    className="h-9 w-full bg-black border-gray-600 text-gray-100 text-xs placeholder:text-gray-400 focus:border-purple-400 focus:ring-purple-400"
                    required
                  />
                  <Input
                    type="number"
                    placeholder="MM"
                    value={formData.month}
                    onChange={(e) => handleInputChange("month", e.target.value)}
                    className="h-9 w-full bg-black border-gray-600 text-gray-100 text-xs placeholder:text-gray-400 focus:border-purple-400 focus:ring-purple-400"
                    required
                  />
                  <Input
                    type="number"
                    placeholder="DD"
                    value={formData.date}
                    onChange={(e) => handleInputChange("date", e.target.value)}
                    className="h-9 w-full bg-black border-gray-600 text-gray-100 text-xs placeholder:text-gray-400 focus:border-purple-400 focus:ring-purple-400"
                    required
                  />
                </div>
              </div>

              {/* Time of Birth */}
              <div className="space-y-1">
                <Label className="text-xs font-medium text-gray-300">Time of Birth</Label>
                <div className="flex gap-2">
                  <Input
                    type="number"
                    placeholder="HH"
                    value={formData.hours}
                    onChange={(e) => handleInputChange("hours", e.target.value)}
                    className="h-9 w-full bg-black border-gray-600 text-gray-100 text-xs placeholder:text-gray-400 focus:border-purple-400 focus:ring-purple-400"
                    required
                  />
                  <Input
                    type="number"
                    placeholder="Min"
                    value={formData.minutes}
                    onChange={(e) => handleInputChange("minutes", e.target.value)}
                    className="h-9 w-full bg-black border-gray-600 text-gray-100 text-xs placeholder:text-gray-400 focus:border-purple-400 focus:ring-purple-400"
                    required
                  />
                  <Input
                    type="number"
                    placeholder="SS"
                    value={formData.seconds}
                    onChange={(e) => handleInputChange("seconds", e.target.value)}
                    className="h-9 w-full bg-black border-gray-600 text-gray-100 text-xs placeholder:text-gray-400 focus:border-purple-400 focus:ring-purple-400"
                    required
                  />
                </div>
                <p className="text-xs text-gray-500">Use 24-hour format</p>
              </div>
              <PlacesAutoComplete onPlaceSelect={handlePlaceSelect} />
              {viewPlaceSelectError && <p className="text-xs text-red-500">Please select a location from the dropdown.</p>}

              {/* Submit Button */}
              <Button
                type="submit"
                disabled={loading}
                className="w-full h-8 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-medium rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 text-sm"
              >
                {loading ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" /> Get Astrological Insights
                  </>
                )}
              </Button>

            </form>
          </CardContent>
        </Card>

        <div className="text-center">
          <p className="text-xs text-gray-500">Your information is secure and used only for Kundali generation</p>
        </div>
      </div>
    </div>
  )
}
