'use client';
import { useState } from "react";
import type { KundliInput } from "../lib/types";

export default function KundliForm({ onSubmit }: { onSubmit: (data: KundliInput) => void }) {
  const [form, setForm] = useState<KundliInput>({
    birthdate: "",
    birthtime: "",
    birthlatitude: "",
    birthlongitude: "",
    birthtimezone: "5.5",
  });

  const handleChange = (e: any) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  return (
    <div className="bg-white p-4 rounded-xl shadow-md max-w-md">
      <h2 className="text-xl font-semibold mb-2">Enter your birth details</h2>
      <div className="grid gap-2">
        <input name="birthdate" placeholder="Birthdate (dd-mm-yyyy)" className="input" onChange={handleChange} />
        <input name="birthtime" placeholder="Birthtime (HH:MM)" className="input" onChange={handleChange} />
        <input name="birthlatitude" placeholder="Latitude (e.g. 28.98)" className="input" onChange={handleChange} />
        <input name="birthlongitude" placeholder="Longitude (e.g. 77.7)" className="input" onChange={handleChange} />
        <input name="birthtimezone" placeholder="Timezone (e.g. 5.5)" className="input" onChange={handleChange} value={form.birthtimezone} />
        <button
          onClick={() => onSubmit(form)}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 mt-2"
        >
          Submit
        </button>
      </div>
    </div>
  );
}
