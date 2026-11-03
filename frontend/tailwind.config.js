/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        obsidian: "#0B0C10",
        gold: { DEFAULT: "#C5A059", soft: "#E6C88A" },
      },
      boxShadow: {
        glow: "0 0 24px -4px rgba(197,160,89,0.45)",
      },
    },
  },
  plugins: [],
};