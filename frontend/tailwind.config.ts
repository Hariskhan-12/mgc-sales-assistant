import type { Config } from "tailwindcss";
const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      fontFamily: { sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"] },
      animation: {
        "pulse-dot": "pulseDot 1.4s infinite ease-in-out both",
        "fade-in": "fadeIn 0.3s ease-out",
        "slide-up": "slideUp 0.3s ease-out",
        "gauge-fill": "gaugeFill 0.8s ease-out forwards",
      },
      keyframes: {
        pulseDot: { "0%,80%,100%": { transform: "scale(0.5)", opacity: "0.3" }, "40%": { transform: "scale(1)", opacity: "1" } },
        fadeIn: { from: { opacity: "0" }, to: { opacity: "1" } },
        slideUp: { from: { opacity: "0", transform: "translateY(8px)" }, to: { opacity: "1", transform: "translateY(0)" } },
        gaugeFill: { from: { strokeDashoffset: "314" } },
      },
    },
  },
  plugins: [],
};
export default config;
