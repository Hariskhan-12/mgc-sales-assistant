export interface AskResponse { answer: string }
export interface ScoreResponse { score: number; percentage: number; priority: string; error?: string }
export interface LeadPayload {
  source: string; city: string; area: string; property_type: string;
  budget_pkr_lac: number | null; bedrooms: number | null;
  first_response_minutes: number | null; agent_experience_years: number | null;
  is_overseas: number; referred_by_existing_client: number; has_financing_approved: number;
}

export async function askQuestion(question: string): Promise<AskResponse> {
  const res = await fetch("/api/ask", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question }) });
  if (!res.ok) throw new Error(`Server error: ${res.status}`);
  return res.json();
}

export async function scoreLead(lead: LeadPayload): Promise<ScoreResponse> {
  const res = await fetch("/api/score", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(lead) });
  if (!res.ok) throw new Error(`Server error: ${res.status}`);
  return res.json();
}
