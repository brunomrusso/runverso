"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Runner = {
  email: string;
  profile: {
    display_name: string | null;
    username: string | null;
    favorite_distance: string | null;
    onboarding_completed: boolean;
  };
  strava_connected: boolean;
};
type ActivityStats = { total: number; total_distance_meters: number };
type Insights = { unlocked_count: number };
type DistancePoint = { label: string; distance_km: number; count: number };
type ActivityTrends = { weekly: DistancePoint[]; monthly: DistancePoint[] };

function dashboardCards(stats: ActivityStats | null, raceCount: number, medalCount: number, countryCount: number, achievementCount: number) {
  return [
    { value: String(stats?.total ?? 0), label: "Atividades", detail: "Corridas importadas do Strava" },
    { value: String(raceCount), label: "Provas", detail: "Provas confirmadas" },
    { value: String(medalCount), label: "Medalhas", detail: "Conquistas no porta-medalhas" },
    { value: String(countryCount), label: "Países", detail: "Lugares onde você correu" },
    { value: String(achievementCount), label: "Conquistas", detail: "Marcos desbloqueados" },
    { value: ((stats?.total_distance_meters ?? 0) / 1000).toFixed(0), label: "Quilômetros", detail: "Distância total importada" },
  ];
}

function BarChart({ points }: { points: DistancePoint[] }) {
  const max = Math.max(...points.map((point) => point.distance_km), 1);
  return <div className="chart-bars">{points.map((point) => <div className="chart-bar" key={point.label} title={`${point.distance_km} km`}><b>{point.distance_km.toFixed(0)}</b><i style={{ height: `${Math.max(8, (point.distance_km / max) * 82)}%` }} /><small>{new Date(`${point.label}T00:00:00`).toLocaleDateString("pt-BR", { month: "short" }).replace(".", "")}</small></div>)}</div>;
}

function LineChart({ points }: { points: DistancePoint[] }) {
  const width = 560;
  const height = 190;
  const max = Math.max(...points.map((point) => point.distance_km), 1);
  const step = points.length > 1 ? (width - 44) / (points.length - 1) : width;
  const position = (point: DistancePoint, index: number) => ({
    x: 22 + index * step,
    y: 18 + (1 - point.distance_km / max) * (height - 62),
  });
  const coordinates = points.map((point, index) => {
    const pointPosition = position(point, index);
    return `${pointPosition.x},${pointPosition.y}`;
  }).join(" ");
  return <svg className="chart-line" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none"><polyline points={`22,${height - 28} ${coordinates} ${width - 22},${height - 28}`} /><polyline className="stroke" points={coordinates} />{points.map((point, index) => { const pointPosition = position(point, index); return <g key={point.label}><text className="chart-value" x={pointPosition.x} y={pointPosition.y - 10} textAnchor="middle">{point.distance_km.toFixed(0)}</text><circle cx={pointPosition.x} cy={pointPosition.y} r="5"><title>{point.distance_km} km</title></circle><text className="chart-axis" x={pointPosition.x} y={height - 8} textAnchor="middle">{new Date(`${point.label}T00:00:00`).toLocaleDateString("pt-BR", { month: "short" }).replace(".", "")}</text></g>; })}</svg>;
}

export default function DashboardPage() {
  const router = useRouter();
  const [runner, setRunner] = useState<Runner | null>(null);
  const [stats, setStats] = useState<ActivityStats | null>(null);
  const [raceCount, setRaceCount] = useState(0);
  const [medalCount, setMedalCount] = useState(0);
  const [countryCount, setCountryCount] = useState(0);
  const [achievementCount, setAchievementCount] = useState(0);
  const [trends, setTrends] = useState<ActivityTrends>({ weekly: [], monthly: [] });

  useEffect(() => {
    Promise.all([
      fetch(`${apiUrl}/me`, { credentials: "include" }),
      fetch(`${apiUrl}/activities/stats`, { credentials: "include" }),
      fetch(`${apiUrl}/races/count`, { credentials: "include" }),
      fetch(`${apiUrl}/medals/count`, { credentials: "include" }),
      fetch(`${apiUrl}/geography/summary?mode=training`, { credentials: "include" }),
      fetch(`${apiUrl}/insights`, { credentials: "include" }),
      fetch(`${apiUrl}/activities/trends`, { credentials: "include" }),
    ])
      .then(async ([userResponse, statsResponse, racesResponse, medalsResponse, geographyResponse, insightsResponse, trendsResponse]) => {
        if (!userResponse.ok) throw new Error("unauthorized");
        return [await userResponse.json(), await statsResponse.json(), await racesResponse.json(), await medalsResponse.json(), await geographyResponse.json(), await insightsResponse.json(), await trendsResponse.json()];
      })
      .then((responses) => {
        const data = responses[0] as Runner;
        const activityStats = responses[1] as ActivityStats;
        const races = responses[2] as { total: number };
        const medals = responses[3] as { total: number };
        const geography = responses[4] as { country_count: number };
        const insights = responses[5] as Insights;
        const activityTrends = responses[6] as ActivityTrends;
        if (!data.profile.onboarding_completed) router.replace("/onboarding");
        else {
          setRunner(data);
          setStats(activityStats);
          setRaceCount(races.total);
          setMedalCount(medals.total);
          setCountryCount(geography.country_count);
          setAchievementCount(insights.unlocked_count);
          setTrends(activityTrends);
        }
      })
      .catch(() => router.replace("/entrar"));
  }, [router]);

  async function logout() {
    await fetch(`${apiUrl}/auth/logout`, { method: "POST", credentials: "include" });
    router.replace("/");
  }

  if (!runner) return <main className="dashboard-loading">Carregando seu Runneverso…</main>;

  return (
    <main className="dashboard-shell">
      <aside className="dashboard-sidebar">
        <a className="brand" href="/">RUNNE<span>VERSO</span></a>
        <nav className="side-nav">
          <a className="active" href="/dashboard">Visão geral</a>
          <a href="/provas">Minhas provas</a>
          <a href="/medalhas">Porta-medalhas</a>
          <a href="/mapa">Mapa da corrida</a>
          <a href="/atividades">Atividades</a>
          <a href="/conquistas">Recordes</a>
          <a href="/comunidade">Comunidade</a>
          <a href="/perfil">Perfil</a>
        </nav>
        <button onClick={logout}>Sair</button>
      </aside>
      <section className="dashboard-main">
        <header className="dashboard-header"><div><span>OLÁ, {runner.profile.username?.toUpperCase()}</span><h1>Bem-vindo ao<br /><em>seu Runneverso.</em></h1></div><a className="avatar" href={`/u/${runner.profile.username}`} title="Ver perfil público">{runner.profile.display_name?.charAt(0).toUpperCase()}</a></header>
        <div className="dashboard-stats">{dashboardCards(stats, raceCount, medalCount, countryCount, achievementCount).map((card) => <article key={card.label}><strong>{card.value}</strong><h2>{card.label}</h2><p>{card.detail}</p></article>)}</div>
        <section className="dashboard-charts"><article><header><div><span>CONSISTÊNCIA</span><h2>Quilômetros por semana</h2></div><strong>{trends.weekly.reduce((total, point) => total + point.distance_km, 0).toFixed(0)} km</strong></header><BarChart points={trends.weekly} /></article><article><header><div><span>TENDÊNCIA</span><h2>Distância mensal</h2></div><strong>{trends.monthly.reduce((total, point) => total + point.count, 0)} corridas</strong></header><LineChart points={trends.monthly} /></article></section>
        <section className="next-step"><div><span>PRÓXIMO PASSO</span><h2>{runner.strava_connected ? (stats?.total ? "Explore seu histórico de corrida" : "Importe suas primeiras atividades") : "Conecte seu Strava"}</h2><p>Transforme seu histórico de corrida em provas, recordes e lugares conquistados.</p></div><a className="button" href={runner.strava_connected ? "/atividades" : `${apiUrl}/auth/strava/link`}>{runner.strava_connected ? "Ver atividades" : "Conectar Strava"} <b>→</b></a></section>
      </section>
    </main>
  );
}
