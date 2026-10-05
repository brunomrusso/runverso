"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Suggestion = { id: string; name: string; started_at: string; distance_meters: number; moving_time_seconds: number; workout_type: number | null; suggested_category: string | null; confidence: string; score: number; reasons: string[] };
type Race = { id: string; event_name: string; race_date: string; category: string; official_distance_meters: number; net_time_seconds: number | null; city: string | null; state: string | null; visibility: string };

function duration(seconds: number | null) {
  if (!seconds) return "—";
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  return [hours, minutes, secs].map((value) => value.toString().padStart(2, "0")).join(":");
}

function parseDuration(value: string) {
  const parts = value.split(":").map(Number);
  if (parts.some(Number.isNaN)) return null;
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  return null;
}

export default function RacesPage() {
  const router = useRouter();
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [races, setRaces] = useState<Race[]>([]);
  const [tab, setTab] = useState<"races" | "suggestions">("suggestions");
  const [manual, setManual] = useState(false);
  const [editing, setEditing] = useState<Suggestion | null>(null);
  const [editingRace, setEditingRace] = useState<Race | null>(null);
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    const [suggestionsResponse, racesResponse] = await Promise.all([
      fetch(`${apiUrl}/race-suggestions`, { credentials: "include" }),
      fetch(`${apiUrl}/races`, { credentials: "include" }),
    ]);
    if (suggestionsResponse.status === 401) return router.replace("/entrar");
    setSuggestions(await suggestionsResponse.json());
    setRaces((await racesResponse.json()).items);
  }, [router]);

  useEffect(() => { load(); }, [load]);

  async function confirm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editing) return;
    const form = new FormData(event.currentTarget);
    const response = await fetch(`${apiUrl}/race-suggestions/${editing.id}/confirm`, {
      method: "POST", credentials: "include", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        event_name: form.get("event_name"), category: form.get("category"),
        net_time_seconds: parseDuration(String(form.get("net_time"))), city: form.get("city") || null,
        state: form.get("state") || null, visibility: "private", country_code: "BR",
      }),
    });
    setMessage(response.ok ? "Prova confirmada e mantida privada." : "Não foi possível confirmar.");
    if (response.ok) setEditing(null);
    await load();
  }

  async function reject(id: string) {
    await fetch(`${apiUrl}/race-suggestions/${id}/reject`, { method: "POST", credentials: "include" });
    setSuggestions((items) => items.filter((item) => item.id !== id));
  }

  async function createManual(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const category = String(form.get("category"));
    const distances: Record<string, number> = { "5K": 5000, "10K": 10000, "15K": 15000, "21K": 21097.5, "42K": 42195, ULTRA: 50000 };
    const response = await fetch(`${apiUrl}/races`, {
      method: "POST", credentials: "include", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        event_name: form.get("event_name"), race_date: form.get("race_date"), category,
        official_distance_meters: category === "OTHER" ? Number(form.get("distance_km")) * 1000 : distances[category],
        net_time_seconds: parseDuration(String(form.get("net_time"))), city: form.get("city") || null,
        state: form.get("state") || null, country_code: "BR", visibility: "private",
      }),
    });
    if (response.ok) {
      setManual(false); setTab("races"); setMessage("Prova cadastrada."); await load();
    } else setMessage("Revise os dados da prova.");
  }

  async function updateRace(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editingRace) return;
    const form = new FormData(event.currentTarget);
    const response = await fetch(`${apiUrl}/races/${editingRace.id}`, {
      method: "PATCH", credentials: "include", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        event_name: form.get("event_name"), category: form.get("category"),
        official_distance_meters: Number(form.get("distance_km")) * 1000,
        net_time_seconds: parseDuration(String(form.get("net_time"))), city: form.get("city") || null,
        state: form.get("state") || null,
      }),
    });
    if (response.ok) {
      setEditingRace(null); setMessage("Prova atualizada. O porta-medalhas foi reagrupado."); await load();
    } else setMessage("Não foi possível atualizar a prova.");
  }

  return <main className="dashboard-shell">
    <aside className="dashboard-sidebar"><a className="brand" href="/">RUNNE<span>VERSO</span></a><nav className="side-nav"><a href="/dashboard">Visão geral</a><a className="active" href="/provas">Minhas provas</a><a href="/medalhas">Porta-medalhas</a><a href="#">Mapa da corrida</a><a href="/atividades">Atividades</a></nav></aside>
    <section className="dashboard-main races-main">
      <header className="activities-header"><div><span>PASSAPORTE DE CORRIDAS</span><h1>Minhas provas.</h1><p>Confirme sugestões do Strava ou registre uma prova manualmente.</p></div><button className="button" onClick={() => setManual(!manual)}>Cadastrar prova</button></header>
      {message && <div className="sync-message">{message}</div>}
      {manual && <form className="race-form" onSubmit={createManual}><h2>Nova prova</h2><label>Nome da prova<input name="event_name" required /></label><div className="form-row"><label>Data<input name="race_date" type="date" required /></label><label>Categoria<select name="category"><option>5K</option><option>10K</option><option>15K</option><option>21K</option><option>42K</option><option>ULTRA</option><option>OTHER</option></select></label></div><label>Distância em km <small>preencha somente para “OTHER”</small><input name="distance_km" type="number" step="0.01" /></label><label>Tempo líquido <small>HH:MM:SS</small><input name="net_time" placeholder="00:50:00" /></label><div className="form-row"><label>Cidade<input name="city" /></label><label>Estado<input name="state" /></label></div><button className="button" type="submit">Salvar prova</button></form>}
      {editing && <form className="race-form confirm-form" onSubmit={confirm}><h2>Confirmar prova</h2><p>Revise os dados antes de transformar a atividade em prova.</p><label>Nome oficial<input name="event_name" defaultValue={editing.name} required /></label><div className="form-row"><label>Categoria<select name="category" defaultValue={editing.suggested_category ?? "OTHER"}><option>5K</option><option>10K</option><option>15K</option><option>21K</option><option>42K</option><option>ULTRA</option><option>OTHER</option></select></label><label>Tempo líquido <small>HH:MM:SS</small><input name="net_time" defaultValue={duration(editing.moving_time_seconds)} /></label></div><div className="form-row"><label>Cidade<input name="city" /></label><label>Estado<input name="state" /></label></div><div className="confirm-actions"><button className="button" type="submit">Confirmar como prova</button><button type="button" onClick={() => setEditing(null)}>Cancelar</button></div></form>}
      {editingRace && <form className="race-form confirm-form" onSubmit={updateRace}><h2>Editar prova confirmada</h2><p>Corrija a categoria e a distância oficial quando o GPS registrar metros extras.</p><label>Nome oficial<input name="event_name" defaultValue={editingRace.event_name} required /></label><div className="form-row"><label>Categoria<select name="category" defaultValue={editingRace.category}><option>5K</option><option>10K</option><option>15K</option><option>21K</option><option>42K</option><option>ULTRA</option><option>OTHER</option></select></label><label>Distância oficial (km)<input name="distance_km" type="number" step="0.001" defaultValue={editingRace.official_distance_meters / 1000} required /></label></div><label>Tempo líquido <small>HH:MM:SS</small><input name="net_time" defaultValue={duration(editingRace.net_time_seconds)} /></label><div className="form-row"><label>Cidade<input name="city" defaultValue={editingRace.city ?? ""} /></label><label>Estado<input name="state" defaultValue={editingRace.state ?? ""} /></label></div><div className="confirm-actions"><button className="button" type="submit">Salvar alterações</button><button type="button" onClick={() => setEditingRace(null)}>Cancelar</button></div></form>}
      <div className="race-tabs"><button className={tab === "suggestions" ? "active" : ""} onClick={() => setTab("suggestions")}>Sugestões <b>{suggestions.length}</b></button><button className={tab === "races" ? "active" : ""} onClick={() => setTab("races")}>Confirmadas <b>{races.length}</b></button></div>
      {tab === "suggestions" && <div className="suggestion-list">{suggestions.length === 0 ? <section className="empty-state"><h2>Nenhuma sugestão pendente</h2></section> : suggestions.map((item) => <article key={item.id}><div className={`confidence ${item.confidence}`}>{item.confidence === "high" ? "ALTA" : item.confidence === "medium" ? "MÉDIA" : "BAIXA"}</div><div className="suggestion-title"><small>{item.suggested_category ?? "OUTRA DISTÂNCIA"}</small><h2>{item.name}</h2><p>{new Date(item.started_at).toLocaleDateString("pt-BR")} · {(item.distance_meters / 1000).toFixed(2)} km · {duration(item.moving_time_seconds)}</p><ul>{item.reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul></div><div className="suggestion-actions"><button className="button" onClick={() => { setEditing(item); window.scrollTo({ top: 0, behavior: "smooth" }); }}>Revisar e confirmar</button><button onClick={() => reject(item.id)}>Não é prova</button></div></article>)}</div>}
      {tab === "races" && <div className="race-list">{races.length === 0 ? <section className="empty-state"><h2>Nenhuma prova confirmada</h2></section> : races.map((race) => <article key={race.id}><div className="race-category">{race.category}</div><div><h2>{race.event_name}</h2><p>{new Date(`${race.race_date}T12:00:00`).toLocaleDateString("pt-BR", { day: "2-digit", month: "long", year: "numeric" })}{race.city ? ` · ${race.city}${race.state ? `, ${race.state}` : ""}` : ""}</p></div><strong>{duration(race.net_time_seconds)}</strong><div className="race-row-actions"><span className="privacy-pill">Privada</span><button onClick={() => { setEditingRace(race); window.scrollTo({ top: 0, behavior: "smooth" }); }}>Editar</button></div></article>)}</div>}
    </section>
  </main>;
}
