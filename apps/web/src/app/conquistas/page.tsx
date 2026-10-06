"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type RecordItem = { race_id: string; category: string; event_name: string; race_date: string; time_seconds: number; pace_seconds_per_km: number; city: string | null; country_code: string };
type Achievement = { code: string; title: string; description: string; unlocked: boolean; progress: number; target: number; category: string };
type Insights = { records: RecordItem[]; achievements: Achievement[]; unlocked_count: number; total_count: number };

function time(seconds: number) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  return [hours, minutes, secs].map((value) => value.toString().padStart(2, "0")).join(":");
}

function pace(seconds: number) {
  return `${Math.floor(seconds / 60)}'${(seconds % 60).toString().padStart(2, "0")}"`;
}

export default function AchievementsPage() {
  const router = useRouter();
  const [insights, setInsights] = useState<Insights | null>(null);

  useEffect(() => {
    fetch(`${apiUrl}/insights`, { credentials: "include" }).then(async (response) => {
      if (response.status === 401) return router.replace("/entrar");
      setInsights(await response.json());
    });
  }, [router]);

  return <main className="dashboard-shell">
    <aside className="dashboard-sidebar"><a className="brand" href="/">RUNNE<span>VERSO</span></a><nav className="side-nav"><a href="/dashboard">Visão geral</a><a href="/provas">Minhas provas</a><a href="/medalhas">Porta-medalhas</a><a href="/mapa">Mapa da corrida</a><a href="/atividades">Atividades</a><a className="active" href="/conquistas">Recordes</a><a href="/comunidade">Comunidade</a><a href="/perfil">Perfil</a></nav></aside>
    <section className="dashboard-main achievements-main">
      <header className="activities-header"><div><span>SEUS MARCOS</span><h1>Recordes e conquistas.</h1><p>Os melhores tempos das suas provas confirmadas e marcos automáticos do seu histórico.</p></div><a className="button" href="/provas">Revisar provas</a></header>
      <div className="geo-stats"><article><strong>{insights?.unlocked_count ?? 0}</strong><span>conquistas abertas</span></article><article><strong>{insights?.records.length ?? 0}</strong><span>recordes registrados</span></article><article><strong>{insights?.total_count ?? 0}</strong><span>metas disponíveis</span></article></div>
      {!insights?.records.length && <section className="empty-state"><h2>Nenhum recorde ainda</h2><p>Confirme provas com tempo líquido para preencher esta prateleira.</p><a className="button" href="/provas">Confirmar provas</a></section>}
      {!!insights?.records.length && <section className="record-board">{insights.records.map((record) => <article key={record.race_id}><span>{record.category}</span><strong>{time(record.time_seconds)}</strong><div><h2>{record.event_name}</h2><p>{new Date(`${record.race_date}T12:00:00`).toLocaleDateString("pt-BR")}{record.city ? ` · ${record.city}` : ""}</p></div><small>{pace(record.pace_seconds_per_km)}/km</small></article>)}</section>}
      <section className="achievement-grid">{insights?.achievements.map((achievement) => <article key={achievement.code} className={achievement.unlocked ? "unlocked" : ""}><small>{achievement.category}</small><h2>{achievement.title}</h2><p>{achievement.description}</p><div><i style={{ width: `${(achievement.progress / achievement.target) * 100}%` }} /></div><span>{achievement.progress}/{achievement.target}</span></article>)}</section>
    </section>
  </main>;
}
