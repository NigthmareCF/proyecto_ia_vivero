import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#13261a",
        moss: "#3e6b48",
        sand: "#f3ecd8",
        clay: "#bc6c25",
        alert: "#a8201a"
      },
      fontFamily: {
        display: ["Georgia", "serif"],
        body: ["Segoe UI", "sans-serif"]
      }
    }
  },
  plugins: []
} satisfies Config;
