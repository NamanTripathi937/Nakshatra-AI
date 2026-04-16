// util.ts
// Shared helpers for API configuration, styling, and birth-details formatting.

import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function getBackendUrl(): string {
  const url = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
  return url.replace(/\/+$/, "");
}

/* -------------------------
   Birth details formatter
   ------------------------- */

const MONTH_NAMES = [
  "January","February","March","April","May","June",
  "July","August","September","October","November","December"
];

function pad(n: number | string, len = 2) {
  const s = String(n ?? "");
  return s.padStart(len, "0");
}

function coordToString(coord: number, isLat = true) {
  if (typeof coord !== "number" || Number.isNaN(coord)) return "Unknown";
  const abs = Math.abs(coord);
  const dir = isLat ? (coord >= 0 ? "N" : "S") : (coord >= 0 ? "E" : "W");
  return `${abs.toFixed(4)}° ${dir}`;
}

/**
 * Formats the finalData object returned from KundaliForm.handleSubmit into a readable string.
 * Accepts objects like:
 * {
 *  year: 2001, month: 6, date: 14,
 *  hours: 8, minutes: 45, seconds: 0,
 *  latitude: 28.6139, longitude: 77.2090,
 *  timezone: "Asia/Kolkata",
 *  settings: { observation_point: "topocentric", ayanamsha: "lahiri" }
 * }
 */
export function formatBirthDetails(data: Record<string, any>) {
  if (!data || typeof data !== "object") return "Invalid birth data";

  const y = Number(data.year);
  const m = Number(data.month);
  const d = Number(data.date);
  const hh = Number(data.hours);
  const mm = Number(data.minutes);
  const ss = Number(data.seconds);

  const hasDate = Number.isInteger(y) && Number.isInteger(m) && Number.isInteger(d);
  const hasTime = !Number.isNaN(hh) && !Number.isNaN(mm) && !Number.isNaN(ss);

  const monthName = (m >= 1 && m <= 12) ? MONTH_NAMES[m - 1] : (m ? String(m) : "Unknown");
  const dateLine = hasDate ? `${pad(d)} ${monthName} ${y}` : "Unknown";
  const timeLine = hasTime ? `${pad(hh)}:${pad(mm)}:${pad(ss)} (24-hr)` : "Unknown";
  const iso = (hasDate && hasTime) ? `${y}-${pad(m)}-${pad(d)}T${pad(hh)}:${pad(mm)}:${pad(ss)}` : "";

  const lat = typeof data.latitude === "number" ? data.latitude : Number(data.latitude);
  const lon = typeof data.longitude === "number" ? data.longitude : Number(data.longitude);
  const coordsLine = (!Number.isNaN(lat) && !Number.isNaN(lon)) ? `${coordToString(lat, true)}, ${coordToString(lon, false)}` : "Unknown";

  const tz = data.timezone ?? "Unknown";

  const settings = data.settings && typeof data.settings === "object"
    ? Object.entries(data.settings).map(([k, v]) => {
        const label = k.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
        return `${label}: ${v}`;
      }).join("\n")
    : "";

  const place = (data.place && typeof data.place === "string") ? `📌 Place: ${data.place}` : null;

  const lines = [
    `📅 Date of Birth: ${dateLine}`,
    `🕒 Time of Birth: ${timeLine}`,
  ];

  if (iso) lines.push(`🧾 ISO: ${iso}`);

  if (place) lines.push(place);
  lines.push(`📍 Coordinates: ${coordsLine}`);
  lines.push(`⏰ Timezone: ${tz}`);

  if (settings) lines.push(`⚙️ Settings:\n${settings}`);

  return lines.join("\n");
}
