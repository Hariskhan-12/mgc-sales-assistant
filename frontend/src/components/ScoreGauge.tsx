"use client";
interface Props { percentage: number; priority: string }

const COLORS = {
  high:   { stroke: "#10b981", text: "#059669", bg: "bg-emerald-50", badge: "text-emerald-700", ring: "ring-emerald-200" },
  medium: { stroke: "#f59e0b", text: "#d97706", bg: "bg-amber-50",   badge: "text-amber-700",   ring: "ring-amber-200"   },
  low:    { stroke: "#f43f5e", text: "#e11d48", bg: "bg-rose-50",    badge: "text-rose-700",    ring: "ring-rose-200"    },
};

export default function ScoreGauge({ percentage, priority }: Props) {
  const tier = percentage >= 15 ? "high" : percentage >= 8 ? "medium" : "low";
  const c = COLORS[tier];
  const dashoffset = 314 - (314 * Math.min(percentage, 100)) / 100;
  return (
    <div className="flex items-center gap-8 animate-fade-in">
      <div className="relative w-32 h-32 flex-shrink-0">
        <svg viewBox="0 0 120 120" className="w-32 h-32 -rotate-90">
          <circle cx="60" cy="60" r="50" fill="none" className="stroke-slate-200" strokeWidth="8" />
          <circle cx="60" cy="60" r="50" fill="none" stroke={c.stroke} className="animate-gauge-fill" strokeWidth="8" strokeLinecap="round" strokeDasharray="314" style={{ strokeDashoffset: dashoffset }} />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-extrabold" style={{ color: c.text }}>{percentage}%</span>
          <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">conversion</span>
        </div>
      </div>
      <div className="flex-1 space-y-3">
        <span className={`inline-block px-4 py-1.5 rounded-lg text-sm font-bold ring-1 ${c.bg} ${c.badge} ${c.ring}`}>{priority}</span>
        <p className="text-sm text-slate-500">
          {percentage >= 15 ? "High likelihood. Contact immediately." : percentage >= 8 ? "Moderate signals. Follow up within 24h." : "Low signals. Add to nurture queue."}
        </p>
      </div>
    </div>
  );
}
