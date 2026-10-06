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

export default function DashboardPage() {
  const router = useRouter();
  const [runner, setRunner] = useState<Runner | null>(null);
  const [stats, setStats] = useState<ActivityStats | null>(null);
  const [raceCount, setRaceCount] = useState(0);
  const [medalCount, setMedalCount] = useState(0);
  const [countryCount, setCountryCount] = useState(0);
  const [achievementCount, setAchievementCount] = useState(0);

  useEffect(() => {
    Promise.all([
      fetch(`${apiUrl}/me`, { credentials: "include" }),
      fetch(`${apiUrl}/activities/stats`, { credentials: "include" }),
      fetch(`${apiUrl}/races/count`, { credentials: "include" }),
      fetch(`${apiUrl}/medals/count`, { credentials: "include" }),
      fetch(`${apiUrl}/geography/summary?mode=training`, { credentials: "include" }),
      fetch(`${apiUrl}/insights`, { credentials: "include" }),
    ])
      .then(async ([userResponse, statsResponse, racesResponse, medalsResponse, geographyResponse, insightsResponse]) => {
        if (!userResponse.ok) throw new Error("unauthorized");
        return [await userResponse.json(), await statsResponse.json(), await racesResponse.json(), await medalsResponse.json(), await geographyResponse.json(), await insightsResponse.json()];
      })
      .then((responses) => {
        const data = responses[0] as Runner;
        const activityStats = responses[1] as ActivityStats;
        const races = responses[2] as { total: number };
        const medals = responses[3] as { total: number };
        const geography = responses[4] as { country_count: number };
        const insights = responses[5] as Insights;
        if (!data.profile.onboarding_completed) router.replace("/onboarding");
        else {
          setRunner(data);
          setStats(activityStats);
          setRaceCount(races.total);
          setMedalCount(medals.total);
          setCountryCount(geography.country_count);
          setAchievementCount(insights.unlocked_count);
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
          <a href="/perfil">Perfil</a>
        </nav>
        <button onClick={logout}>Sair</button>
      </aside>
      <section className="dashboard-main">
        <header className="dashboard-header"><div><span>OLÁ, {runner.profile.username?.toUpperCase()}</span><h1>Bem-vindo ao<br /><em>seu Runneverso.</em></h1></div><a className="avatar" href={`/u/${runner.profile.username}`} title="Ver perfil público">{runner.profile.display_name?.charAt(0).toUpperCase()}</a></header>
        <div className="dashboard-stats">{dashboardCards(stats, raceCount, medalCount, countryCount, achievementCount).map((card) => <article key={card.label}><strong>{card.value}</strong><h2>{card.label}</h2><p>{card.detail}</p></article>)}</div>
        <section className="next-step"><div><span>PRÓXIMO PASSO</span><h2>{runner.strava_connected ? (stats?.total ? "Explore seu histórico de corrida" : "Importe suas primeiras atividades") : "Conecte seu Strava"}</h2><p>Transforme seu histórico de corrida em provas, recordes e lugares conquistados.</p></div><a className="button" href={runner.strava_connected ? "/atividades" : `${apiUrl}/auth/strava/link`}>{runner.strava_connected ? "Ver atividades" : "Conectar Strava"} <b>→</b></a></section>
      </section>
    </main>
  );
}
