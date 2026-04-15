/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html",
  ],

  darkMode: "class",

  theme: {
    extend: {
      // ── Agricultural color palette ────────────────────────────────────
      colors: {
        primary: {
          DEFAULT: "#2d6a4f",
          light: "#52b788",
          dark: "#1b4332",
          50:  "#f0fdf4",
          100: "#dcfce7",
          200: "#bbf7d0",
          300: "#86efac",
          400: "#4ade80",
          500: "#22c55e",
          600: "#16a34a",
          700: "#15803d",
          800: "#166534",
          900: "#14532d",
        },
        accent: {
          DEFAULT: "#74c69d",
          light: "#b7e4c7",
          dark: "#40916c",
        },
        earth: {
          50:  "#fdf8f0",
          100: "#faecd8",
          200: "#f4d5a8",
          300: "#edb96d",
          400: "#e49840",
          500: "#d97706",
          600: "#b45309",
          700: "#92400e",
          800: "#78350f",
          900: "#451a03",
        },
        surface: {
          DEFAULT: "#f8fffe",
          dark: "#1a2e25",
        },
      },

      // ── Typography ────────────────────────────────────────────────────
      fontFamily: {
        arabic: [
          "Noto Sans Arabic",
          "Segoe UI",
          "Tahoma",
          "Arial",
          "sans-serif",
        ],
        sans: [
          "Inter",
          "Segoe UI",
          "Tahoma",
          "Geneva",
          "Verdana",
          "sans-serif",
        ],
        mono: [
          "Fira Code",
          "Courier New",
          "Courier",
          "monospace",
        ],
      },

      // ── Spacing ───────────────────────────────────────────────────────
      spacing: {
        sidebar: "240px",
        "18": "4.5rem",
        "88": "22rem",
        "112": "28rem",
        "128": "32rem",
      },

      // ── Border radius ─────────────────────────────────────────────────
      borderRadius: {
        xl: "0.75rem",
        "2xl": "1rem",
        "3xl": "1.5rem",
      },

      // ── Box shadow ────────────────────────────────────────────────────
      boxShadow: {
        card: "0 1px 3px 0 rgba(0,0,0,0.06), 0 1px 2px -1px rgba(0,0,0,0.06)",
        "card-hover": "0 4px 6px -1px rgba(0,0,0,0.08), 0 2px 4px -2px rgba(0,0,0,0.06)",
        sidebar: "2px 0 8px rgba(0,0,0,0.08)",
      },

      // ── Animations ────────────────────────────────────────────────────
      keyframes: {
        fadeIn: {
          from: { opacity: 0, transform: "translateY(8px)" },
          to:   { opacity: 1, transform: "translateY(0)" },
        },
        slideInLeft: {
          from: { opacity: 0, transform: "translateX(-16px)" },
          to:   { opacity: 1, transform: "translateX(0)" },
        },
        slideInRight: {
          from: { opacity: 0, transform: "translateX(16px)" },
          to:   { opacity: 1, transform: "translateX(0)" },
        },
        progressBar: {
          "0%":   { backgroundPosition: "0% 50%" },
          "50%":  { backgroundPosition: "100% 50%" },
          "100%": { backgroundPosition: "0% 50%" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: 1 },
          "50%":      { opacity: 0.6 },
        },
      },
      animation: {
        "fade-in":       "fadeIn 0.3s ease-out both",
        "slide-in-left": "slideInLeft 0.3s ease-out both",
        "slide-in-right":"slideInRight 0.3s ease-out both",
        "progress-bar":  "progressBar 3s ease infinite",
        "pulse-soft":    "pulseSoft 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },

      // ── Backdrop ─────────────────────────────────────────────────────
      backdropBlur: {
        xs: "2px",
      },
    },
  },

  plugins: [
    // RTL support helper (uncomment if @tailwindcss/rtl is installed)
    // require('@tailwindcss/rtl'),
  ],
};
