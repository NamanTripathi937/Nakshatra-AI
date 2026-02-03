'use client';
import { Home } from "lucide-react";

export default function Header() {
  return (  
          <header className="backdrop-blur-md border-b border-gray-700 shadow-sm mb-4 bg-black/20">
            <div className="flex items-center justify-between px-6 py-4">
              {/* Home Icon */}
              <Home
                className="h-6 w-6 text-white hover:text-blue-400 cursor-pointer"
                onClick={() => (window.location.href = '/')}
              />

              {/* Title */}
              <h1 className="text-2xl font-bold bg-gradient-to-r from-white to-blue-300 bg-clip-text text-transparent">
                ✦ N A K S H A T R A ✦
              </h1>

              {/* Spacer to keep title centered */}
              <div className="w-6" />
            </div>
          </header>
  )
}