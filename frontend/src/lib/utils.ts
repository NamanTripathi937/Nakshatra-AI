import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

//To create session ID for user
export const SESSION_KEY = "nakshatra_session_id";

export function getOrCreateSessionId(): string {
  if(typeof window === "undefined" || typeof localStorage === "undefined") {
    // Server-side rendering, return empty string or handle accordingly
    return "";
  }
  let sid = localStorage.getItem(SESSION_KEY);
  if (sid) {
    return sid; // TS now knows sid is string
  }

  // Generate new id
  sid = (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function")
    ? crypto.randomUUID()
    : "sid-" + Math.random().toString(36).slice(2, 12);

  localStorage.setItem(SESSION_KEY, sid);
  return sid;
}