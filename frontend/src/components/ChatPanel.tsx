"use client";
import { useState, useRef, useEffect } from "react";
import { askQuestion } from "@/lib/api";

interface Message { role: "user" | "assistant"; content: string }

const EXAMPLES = [
  { label: "Base price 2-bed Block B", q: "What is the base price of a 2-bed in Block B?" },
  { label: "Margalla corner floor 15", q: "What is the total for a Margalla-facing corner unit on floor 15, 2-bed Block B?" },
  { label: "Overseas 50% upfront", q: "An overseas Pakistani buyer pays 50% upfront on a 3-Bed Executive — what is the price after discounts, and what is due at booking?" },
  { label: "Transfer fee", q: "What is the transfer fee?" },
  { label: "Rental yield", q: "What is the rental yield on a 1-bed?" },
  { label: "Anchor tenant", q: "Who is the anchor tenant?" },
];

function fmt(text: string): string {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/\[Source: (.+?)\]/g, '<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-indigo-50 text-indigo-700 ring-1 ring-indigo-200">$1</span>')
    .replace(/\n/g, "<br/>");
}

export default function ChatPanel() {
  const [msgs, setMsgs] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottom = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { bottom.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs, loading]);

  const send = async (q?: string) => {
    const question = (q || input).trim();
    if (!question || loading) return;
    setInput(""); setMsgs(p => [...p, { role: "user", content: question }]); setLoading(true);
    try {
      const data = await askQuestion(question);
      setMsgs(p => [...p, { role: "assistant", content: data.answer }]);
    } catch (e: unknown) {
      setMsgs(p => [...p, { role: "assistant", content: `Error: ${e instanceof Error ? e.message : "Unknown"}\n\nCheck that LLM_API_KEY is set in .env` }]);
    }
    setLoading(false); inputRef.current?.focus();
  };

  return (
    <div className="flex flex-col h-[calc(100vh-10rem)] bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      <div className="flex-1 overflow-y-auto p-5 space-y-4 bg-slate-50/50">
        {msgs.length === 0 && !loading && (
          <div className="flex flex-col items-center justify-center h-full text-center py-16 animate-fade-in">
            <h3 className="text-lg font-semibold text-slate-800 mb-1">Ask about MGC Aurora Heights</h3>
            <p className="text-sm text-slate-500 max-w-md">Answers grounded in the project brochure, price list, and booking policy. Every answer cites its source.</p>
          </div>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={`flex animate-slide-up ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className="max-w-[80%]">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">
                {m.role === "user" ? "You" : "MGC Assistant"}
              </span>
              <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${m.role === "user" ? "bg-indigo-600 text-white rounded-br-md" : "bg-white border border-slate-200 text-slate-700 rounded-bl-md shadow-sm"}`}
                dangerouslySetInnerHTML={{ __html: m.role === "assistant" ? fmt(m.content) : m.content.replace(/</g, "&lt;") }} />
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start animate-fade-in">
            <div><span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">MGC Assistant</span>
              <div className="px-4 py-3 bg-white border border-slate-200 rounded-2xl rounded-bl-md shadow-sm">
                <div className="flex gap-1.5 h-5"><span className="w-2 h-2 bg-slate-400 rounded-full animate-pulse-dot"/><span className="w-2 h-2 bg-slate-400 rounded-full animate-pulse-dot [animation-delay:0.2s]"/><span className="w-2 h-2 bg-slate-400 rounded-full animate-pulse-dot [animation-delay:0.4s]"/></div>
              </div>
            </div>
          </div>
        )}
        <div ref={bottom}/>
      </div>
      {msgs.length === 0 && (
        <div className="px-5 py-3 border-t border-slate-100 bg-white">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-2">Try these</p>
          <div className="flex flex-wrap gap-2">
            {EXAMPLES.map(e => <button key={e.label} onClick={() => send(e.q)} className="px-3 py-1.5 text-xs font-medium text-slate-600 bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 rounded-full border border-slate-200 hover:border-indigo-200 transition-colors">{e.label}</button>)}
          </div>
        </div>
      )}
      <div className="px-5 py-4 border-t border-slate-200 bg-white flex gap-3">
        <input ref={inputRef} value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && send()}
          placeholder="Ask about pricing, payment plans, booking..." disabled={loading}
          className="flex-1 px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition"/>
        <button onClick={() => send()} disabled={loading || !input.trim()} className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white text-sm font-semibold rounded-xl transition-colors">Send</button>
      </div>
    </div>
  );
}
