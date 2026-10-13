"use client";
import { useState } from "react";
import ChatPanel from "@/components/ChatPanel";
import ScoringPanel from "@/components/ScoringPanel";

type Tab = "assistant" | "scoring";

export default function Home() {
  const [tab, setTab] = useState<Tab>("assistant");
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-gradient-to-r from-slate-900 to-slate-800 text-white">
        <div className="max-w-5xl mx-auto px-6 py-5 flex items-center justify-between">
          <div><h1 className="text-xl font-bold tracking-tight">MGC Sales Assistant</h1><p className="text-slate-400 text-sm mt-0.5">Aurora Heights &middot; GT Road, Islamabad</p></div>
          <div className="hidden sm:flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 text-xs font-medium text-slate-300"><span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"/>Internal Sales Tool</div>
        </div>
      </header>
      <nav className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 flex">
          {(["assistant","scoring"] as Tab[]).map(t => (
            <button key={t} onClick={() => setTab(t)} className={`px-5 py-3.5 text-sm font-semibold border-b-2 transition-colors ${tab===t ? "text-indigo-600 border-indigo-600" : "text-slate-500 border-transparent hover:text-slate-700"}`}>
              {t === "assistant" ? "Document Assistant" : "Lead Scoring"}
            </button>
          ))}
        </div>
      </nav>
      <main className="flex-1 max-w-5xl mx-auto w-full px-6 py-6">
        {tab === "assistant" ? <ChatPanel/> : <ScoringPanel/>}
      </main>
    </div>
  );
}
