/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Scientific instrument palette: deep blue surfaces, amber findings,
        // green confidence. Not decoration — amber means "the answer",
        // green means "passes the gate".
        lab: {
          bg: "#0A0F1E",
          panel: "#111832",
          surface: "#16215C",
          line: "#26327B",
          text: "#E8ECF8",
          muted: "#9AA3C7",
          amber: "#D97706",
          emerald: "#10B981",
          danger: "#F87171",
        },
      },
      fontFamily: {
        // Fira pair: Sans sets sentences, Code sets every chemical identifier.
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      maxWidth: {
        bench: "80rem",
      },
    },
  },
  plugins: [],
};
