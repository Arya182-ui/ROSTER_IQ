/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        panel: "rgba(15, 23, 42, 0.78)",
        border: "rgba(148, 163, 184, 0.18)",
        accent: {
          400: "#2dd4bf",
          500: "#14b8a6",
          600: "#0f766e"
        }
      },
      boxShadow: {
        panel: "0 22px 60px rgba(15, 23, 42, 0.35)"
      },
      fontFamily: {
        sans: ["IBM Plex Sans", "Segoe UI", "sans-serif"],
        display: ["Space Grotesk", "IBM Plex Sans", "sans-serif"]
      }
    }
  },
  plugins: []
};
