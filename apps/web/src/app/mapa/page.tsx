"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
type Country = { country_code: string; country: string; count: number; distance_meters: number; states: string[]; cities: string[]; state_count: number; city_count: number };
type Point = { country_code: string; state: string | null; city: string | null; latitude: number; longitude: number; count: number };
type Summary = { mode: "training" | "races"; country_count: number; state_count: number; city_count: number; countries: Country[]; points: Point[] };

function flag(code: string) {
  if (!/^[A-Z]{2}$/.test(code)) return "●";
  return String.fromCodePoint(...[...code].map((letter) => 127397 + letter.charCodeAt(0)));
}

function pointPosition(point: Point) {
  return { left: `${((point.longitude + 180) / 360) * 100}%`, top: `${((90 - point.latitude) / 180) * 100}%` };
}

export default function MapPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"training" | "races">("training");
  const [summary, setSummary] = useState<Summary | null>(null);
  const [processing, setProcessing] = useState(false);
  const [message, setMessage] = useState("");

  const load = useCallback(async (selectedMode: "training" | "races") => {
    const response = await fetch(`${apiUrl}/geography/summary?mode=${selectedMode}`, { credentials: "include" });
    if (response.status === 401) return router.replace("/entrar");
    setSummary(await response.json());
  }, [router]);

  useEffect(() => { load(mode); }, [load, mode]);

  async function processLocations() {
    setProcessing(true); setMessage("");
    const response = await fetch(`${apiUrl}/geography/process`, { method: "POST", credentials: "include" });
    const data = await response.json();
    if (response.ok) { setMessage(`${data.processed} atividades localizadas sem enviar coordenadas para serviços externos.`); await load(mode); }
    else setMessage(data.detail ?? "Não foi possível processar os locais.");
    setProcessing(false);
  }

  return <main className="dashboard-shell">
    <aside className="dashboard-sidebar"><a className="brand" href="/">RUNNE<span>VERSO</span></a><nav className="side-nav"><a href="/dashboard">Visão geral</a><a href="/provas">Minhas provas</a><a href="/medalhas">Porta-medalhas</a><a className="active" href="/mapa">Mapa da corrida</a><a href="/atividades">Atividades</a></nav></aside>
    <section className="dashboard-main map-main">
      <header className="activities-header"><div><span>PASSAPORTE GEOGRÁFICO</span><h1>Por onde você correu.</h1><p>Somente cidades aproximadas são exibidas; suas rotas e coordenadas originais continuam privadas.</p></div><button className="button" onClick={processLocations} disabled={processing}>{processing ? "Processando…" : "Atualizar locais"}</button></header>
      {message && <div className="sync-message">{message}</div>}
      <div className="map-mode"><button className={mode === "training" ? "active" : ""} onClick={() => setMode("training")}>Treinos</button><button className={mode === "races" ? "active" : ""} onClick={() => setMode("races")}>Provas</button></div>
      <div className="geo-stats"><article><strong>{summary?.country_count ?? 0}</strong><span>Países</span></article><article><strong>{summary?.state_count ?? 0}</strong><span>Estados e regiões</span></article><article><strong>{summary?.city_count ?? 0}</strong><span>Cidades</span></article></div>
      <section className="world-map" aria-label="Mapa aproximado dos lugares onde você correu">
        <div className="world-grid" />
        <div className="continent americas" /><div className="continent europe" /><div className="continent africa" /><div className="continent asia" /><div className="continent oceania" />
        {summary?.points.map((point) => <button key={`${point.country_code}-${point.state}-${point.city}`} className="map-point" style={pointPosition(point)} title={`${point.city ?? point.state ?? point.country_code}: ${point.count}`}><span>{point.count}</span></button>)}
        {!summary?.points.length && <div className="map-empty">Clique em “Atualizar locais” para construir seu mapa.</div>}
      </section>
      <section className="country-passport"><h2>Bandeiras conquistadas</h2><div className="country-grid">{summary?.countries.map((country) => <article key={country.country_code}><div className="country-flag">{flag(country.country_code)}</div><div><h3>{country.country}</h3><p>{country.count} {mode === "training" ? "atividades" : "provas"} · {(country.distance_meters / 1000).toFixed(0)} km</p><small>{country.state_count} estados/regiões · {country.city_count} cidades</small></div><details><summary>Ver lugares</summary><p>{country.cities.slice(0, 30).join(" · ") || "Cidades não informadas"}</p></details></article>)}</div></section>
    </section>
  </main>;
}
