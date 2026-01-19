import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sun, Cloud, Wind, MapPin } from "lucide-react";

/**
 * Minimal mapping of WMO weather codes to description + emoji
 * Source: Open-Meteo / WMO code mappings (common subset)
 */
const WMO_MAP = {
  0: { text: "Clear", emoji: "☀️" },
  1: { text: "Mainly clear", emoji: "🌤️" },
  2: { text: "Partly cloudy", emoji: "⛅" },
  3: { text: "Overcast", emoji: "☁️" },
  45: { text: "Fog", emoji: "🌫️" },
  48: { text: "Depositing rime fog", emoji: "🌫️" },
  51: { text: "Light drizzle", emoji: "🌦️" },
  53: { text: "Moderate drizzle", emoji: "🌦️" },
  55: { text: "Dense drizzle", emoji: "🌧️" },
  61: { text: "Slight rain", emoji: "🌦️" },
  63: { text: "Moderate rain", emoji: "🌧️" },
  65: { text: "Heavy rain", emoji: "⛈️" },
  71: { text: "Slight snow", emoji: "🌨️" },
  73: { text: "Moderate snow", emoji: "🌨️" },
  75: { text: "Heavy snow", emoji: "❄️" },
  80: { text: "Rain showers", emoji: "🌧️" },
  95: { text: "Thunderstorm", emoji: "⛈️" },
};

function mapWmo(code) {
  return WMO_MAP[code] || { text: "Unknown", emoji: "🌈" };
}

export default function App() {
  const [query, setQuery] = useState("");
  const [place, setPlace] = useState(null); // {name, lat, lon}
  const [current, setCurrent] = useState(null); // {temp, wind, humidity, weathercode, time}
  const [daily, setDaily] = useState([]); // array of {date, max, min, code}
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Load last city from localStorage
  useEffect(() => {
    const last = localStorage.getItem("weather_last_place");
    if (last) {
      setQuery(last);
      handleSearch(last);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function geocodePlace(name) {
    const url = `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(
      name
    )}&count=5&language=en&format=json`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Geocoding failed");
    const data = await res.json();
    if (!data.results || data.results.length === 0) throw new Error("No places found");
    const p = data.results[0];
    return { name: p.name + (p.country ? ", " + p.country : ""), lat: p.latitude, lon: p.longitude };
  }

  async function fetchWeather(lat, lon) {
    // Request current_weather, hourly humidity to get current humidity, and 7-day daily forecast
    const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true&hourly=relativehumidity_2m&daily=temperature_2m_max,temperature_2m_min,weathercode&timezone=auto`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Weather API failed");
    const data = await res.json();
    // current
    const cw = data.current_weather || {};
    // find humidity for current time
    let humidity = null;
    if (data.hourly && data.hourly.time && data.hourly.relativehumidity_2m) {
      const idx = data.hourly.time.indexOf(cw.time);
      if (idx >= 0) humidity = data.hourly.relativehumidity_2m[idx];
    }
    const currentData = {
      temp: cw.temperature ?? null,
      wind: cw.windspeed ?? null,
      weathercode: cw.weathercode ?? null,
      time: cw.time ?? null,
      humidity,
    };

    // daily forecast
    const dailyList = [];
    if (data.daily && data.daily.time) {
      for (let i = 0; i < data.daily.time.length; i++) {
        dailyList.push({
          date: data.daily.time[i],
          max: data.daily.temperature_2m_max[i],
          min: data.daily.temperature_2m_min[i],
          code: data.daily.weathercode[i],
        });
      }
    }

    return { currentData, dailyList };
  }

  async function handleSearch(input = null) {
    const q = (input ?? query).trim();
    if (!q) return;
    setLoading(true);
    setError("");
    try {
      const p = await geocodePlace(q);
      setPlace(p);
      localStorage.setItem("weather_last_place", q);
      const { currentData, dailyList } = await fetchWeather(p.lat, p.lon);
      setCurrent(currentData);
      setDaily(dailyList.slice(0, 7));
    } catch (err) {
      setError(err.message || "Failed to fetch weather");
      setPlace(null);
      setCurrent(null);
      setDaily([]);
    } finally {
      setLoading(false);
    }
  }

  const containerVariants = {
    hidden: { opacity: 0, y: 8 },
    show: { opacity: 1, y: 0, transition: { staggerChildren: 0.06 } },
  };
  const itemVariants = { hidden: { opacity: 0, y: 8 }, show: { opacity: 1, y: 0 } };

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="max-w-4xl w-full glass rounded-2xl p-6 md:p-10 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex items-center gap-3">
            <MapPin className="text-cyan-300" />
            <h1 className="text-2xl font-semibold">Pro Weather Dashboard</h1>
          </div>

          <div className="flex gap-2 w-full md:w-auto">
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="Search city (e.g., London)"
              className="w-full md:w-72 px-3 py-2 rounded-lg bg-transparent border border-slate-700 focus:outline-none"
            />
            <button
              onClick={() => handleSearch()}
              className="px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-600 text-slate-900 font-medium"
            >
              {loading ? "Searching..." : "Search"}
            </button>
          </div>
        </div>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 glass rounded-xl p-6">
            <AnimatePresence>
              <motion.div
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.35 }}
              >
                {!place && !loading && (
                  <div className="text-slate-300">
                    Search a city to get started — this app uses Open-Meteo (no API key required).
                  </div>
                )}

                {error && <div className="text-rose-400">{error}</div>}

                {place && current && (
                  <div>
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-slate-300 text-sm">Current location</div>
                        <div className="text-2xl font-semibold">{place.name}</div>
                        <div className="text-sm text-slate-400 mt-1">
                          As of {new Date(current.time).toLocaleString()}
                        </div>
                      </div>

                      <div className="text-right">
                        <div className="text-5xl font-bold flex items-center gap-3 justify-end">
                          <span>{Math.round(current.temp)}°</span>
                          <span className="text-3xl">{mapWmo(current.weathercode).emoji}</span>
                        </div>
                        <div className="text-slate-300 mt-1">{mapWmo(current.weathercode).text}</div>
                      </div>
                    </div>

                    <div className="mt-6 grid grid-cols-3 gap-3">
                      <div className="p-3 rounded-lg glass flex flex-col items-start">
                        <div className="flex items-center gap-2 text-cyan-300">
                          <Sun size={16} /> Temperature
                        </div>
                        <div className="text-xl font-medium mt-2">{Math.round(current.temp)}°C</div>
                      </div>
                      <div className="p-3 rounded-lg glass flex flex-col items-start">
                        <div className="flex items-center gap-2 text-indigo-300">
                          <Wind size={16} /> Wind
                        </div>
                        <div className="text-xl font-medium mt-2">{current.wind ?? "—"} km/h</div>
                      </div>
                      <div className="p-3 rounded-lg glass flex flex-col items-start">
                        <div className="flex items-center gap-2 text-amber-300">
                          <Cloud size={16} /> Humidity
                        </div>
                        <div className="text-xl font-medium mt-2">
                          {current.humidity != null ? `${current.humidity}%` : "—"}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </motion.div>
            </AnimatePresence>
          </div>

          <div className="glass rounded-xl p-4">
            <div className="text-slate-300 font-medium">7-Day Forecast</div>

            <motion.div
              className="mt-3 grid grid-cols-2 gap-3"
              variants={containerVariants}
              initial="hidden"
              animate="show"
            >
              {daily.length === 0 && !loading && <div className="text-sm text-slate-400">No forecast yet</div>}

              {daily.map((d) => (
                <motion.div key={d.date} className="forecast-item flex items-center justify-between" variants={itemVariants}>
                  <div>
                    <div className="text-sm">{new Date(d.date).toLocaleDateString(undefined, { weekday: "short" })}</div>
                    <div className="text-xs text-slate-400">{new Date(d.date).toLocaleDateString()}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-semibold">{Math.round(d.max)}° / {Math.round(d.min)}°</div>
                    <div className="text-sm">{mapWmo(d.code).emoji} {mapWmo(d.code).text}</div>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </div>

        <div className="mt-6 text-xs text-slate-500">
          Data provided by <a className="underline" href="https://open-meteo.com/" target="_blank" rel="noreferrer">Open-Meteo</a>.
        </div>
      </div>
    </div>
  );
}
