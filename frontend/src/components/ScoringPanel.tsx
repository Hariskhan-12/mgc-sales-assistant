"use client";
import { useState } from "react";
import { scoreLead, type LeadPayload, type ScoreResponse } from "@/lib/api";
import ScoreGauge from "./ScoreGauge";

const SOURCES = ["Facebook Ads","Property Portal","Google Search","Instagram","Referral","Walk-in","WhatsApp Campaign","Expo Stall","Billboard"];
const CITIES = ["Islamabad","Rawalpindi","Lahore","Karachi","Peshawar","Faisalabad","Multan","Gujranwala","Abbottabad"];
const PTYPES = ["Apartment","Commercial Shop","Penthouse","Plot","Farmhouse","House"];

function Sel({ id, label, opts, value, onChange }: { id: string; label: string; opts: string[]; value: string; onChange: (v: string) => void }) {
  return <div><label htmlFor={id} className="block text-xs font-semibold text-slate-500 mb-1.5">{label}</label>
    <select id={id} value={value} onChange={e => onChange(e.target.value)} className="w-full px-3 py-2.5 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition">{opts.map(o => <option key={o}>{o}</option>)}</select></div>;
}
function Num({ id, label, ph, value, onChange, step }: { id: string; label: string; ph: string; value: string; onChange: (v: string) => void; step?: string }) {
  return <div><label htmlFor={id} className="block text-xs font-semibold text-slate-500 mb-1.5">{label}</label>
    <input id={id} type="number" step={step} placeholder={ph} value={value} onChange={e => onChange(e.target.value)} className="w-full px-3 py-2.5 bg-white border border-slate-200 rounded-lg text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition"/></div>;
}
function Toggle({ id, label, checked, onChange }: { id: string; label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return <label htmlFor={id} className="flex items-center gap-3 cursor-pointer">
    <div className="relative"><input id={id} type="checkbox" checked={checked} onChange={e => onChange(e.target.checked)} className="sr-only peer"/>
      <div className="w-10 h-6 bg-slate-200 rounded-full peer-checked:bg-indigo-600 transition-colors"/>
      <div className="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow-sm peer-checked:translate-x-4 transition-transform"/></div>
    <span className="text-sm text-slate-700">{label}</span></label>;
}

export default function ScoringPanel() {
  const [f, setF] = useState({ source:"Facebook Ads", city:"Islamabad", ptype:"Apartment", area:"Bahria Town", budget:"200", beds:"2", resp:"15", exp:"3.0", overseas:false, referred:false, fin:false });
  const [result, setResult] = useState<ScoreResponse|null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const u = (k: string, v: string|boolean) => setF(p => ({ ...p, [k]: v }));

  const handleScore = async () => {
    setLoading(true); setError(""); setResult(null);
    const payload: LeadPayload = {
      source: f.source, city: f.city, area: f.area||"Unknown", property_type: f.ptype,
      budget_pkr_lac: f.budget ? parseFloat(f.budget) : null, bedrooms: f.beds ? parseInt(f.beds) : null,
      first_response_minutes: f.resp ? parseFloat(f.resp) : null, agent_experience_years: f.exp ? parseFloat(f.exp) : null,
      is_overseas: f.overseas?1:0, referred_by_existing_client: f.referred?1:0, has_financing_approved: f.fin?1:0,
    };
    try {
      const data = await scoreLead(payload);
      data.error ? setError(data.error) : setResult(data);
    } catch(e: unknown) { setError(e instanceof Error ? e.message : "Failed"); }
    setLoading(false);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h2 className="text-base font-semibold text-slate-800 mb-1">Lead Details</h2>
        <p className="text-xs text-slate-500 mb-6">Enter lead information to predict conversion likelihood</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          <Sel id="source" label="Lead Source" opts={SOURCES} value={f.source} onChange={v => u("source",v)}/>
          <Sel id="city" label="City" opts={CITIES} value={f.city} onChange={v => u("city",v)}/>
          <Sel id="ptype" label="Property Type" opts={PTYPES} value={f.ptype} onChange={v => u("ptype",v)}/>
          <Num id="budget" label="Budget (PKR Lac)" ph="200" value={f.budget} onChange={v => u("budget",v)}/>
          <Num id="beds" label="Bedrooms" ph="2" value={f.beds} onChange={v => u("beds",v)}/>
          <div><label htmlFor="area" className="block text-xs font-semibold text-slate-500 mb-1.5">Area / Society</label>
            <input id="area" type="text" placeholder="Bahria Town" value={f.area} onChange={e => u("area",e.target.value)} className="w-full px-3 py-2.5 bg-white border border-slate-200 rounded-lg text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition"/></div>
          <Num id="resp" label="First Response (min)" ph="15" value={f.resp} onChange={v => u("resp",v)}/>
          <Num id="exp" label="Agent Experience (yrs)" ph="3.0" value={f.exp} onChange={v => u("exp",v)} step="0.1"/>
        </div>
        <div className="flex flex-wrap gap-6 mb-6 py-4 px-4 bg-slate-50 rounded-lg">
          <Toggle id="overseas" label="Overseas Pakistani" checked={f.overseas} onChange={v => u("overseas",v)}/>
          <Toggle id="referred" label="Referred by client" checked={f.referred} onChange={v => u("referred",v)}/>
          <Toggle id="fin" label="Financing pre-approved" checked={f.fin} onChange={v => u("fin",v)}/>
        </div>
        <button onClick={handleScore} disabled={loading} className="px-8 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white text-sm font-semibold rounded-xl transition-colors">
          {loading ? "Scoring..." : "Score This Lead"}
        </button>
      </div>
      {error && <div className="bg-rose-50 border border-rose-200 text-rose-700 px-5 py-4 rounded-xl text-sm animate-slide-up">{error}</div>}
      {result && <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 animate-slide-up"><h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">Result</h3><ScoreGauge percentage={result.percentage} priority={result.priority}/></div>}
    </div>
  );
}
