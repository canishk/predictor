/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        pitch: {
          900: "#0f172a",
          800: "#1e293b",
          700: "#334155",
        },
        accent: {
          DEFAULT: "#10b981",
          muted: "#059669",
        },
      },
    },
  },
  plugins: [],
};
