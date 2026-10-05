"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Activity = {
  id: string;
  name: string;
  sport_type: string;
  distance_meters: number;
  moving_time_seconds: number;
  elevation_gain: number;
  started_at: string;
  source_visibility: string;
};
type ActivityList = { items: Activity[]; total: number; page: number; per_page: number };
type SyncStatus = { connected: boolean; status: string | null; error: string | null; last_synced_at: string | null };

function duration(seconds: number) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return hours ? `${hours}h ${minutes.toString().padStart(2, "0")}min` : `${minutes}min`;
}

export default function ActivitiesPage() {
  const router = useRouter();
  const [activities, setActivities] = useState<ActivityList | null>(null);
  const [status, setStatus] = useState<SyncStatus | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    const [activitiesResponse, statusResponse] = await Promise.all([
      fetch(`${apiUrl}/activities`, { credentials: "include" }),
      fetch(`${apiUrl}/strava/sync/status`, { credentials: "include" }),
    ]);
    if (activitiesResponse.status === 401) {
      router.replace("/entrar");
      return;
    }
    setActivities(await activitiesResponse.json());
    setStatus(await statusResponse.json());
  }, [router]);

  useEffect(() => { load(); }, [load]);

  async function sync() {
    setSyncing(true);
    setMessage("");
    const response = await fetch(`${apiUrl}/strava/sync`, {
      method: "POST",
      credentials: "include",
    });
    const data = await response.json();
    if (response.ok) {
      setMessage(`${data.imported} novas e ${data.updated} atualizadas.`);
      await load();
    } else {
      setMessage(data.detail ?? "Não foi possível sincronizar");
    }
    setSyncing(false);
  }

  return (
    <main className="dashboard-shell">
      <aside className="dashboard-sidebar">
        <a className="brand" href="/">RUNNE<span>VERSO</span></a>
        <nav className="side-nav"><a href="/dashboard">Visão geral</a><a href="/provas">Minhas provas</a><a href="/medalhas">Porta-medalhas</a><a href="/mapa">Mapa da corrida</a><a className="active" href="/atividades">Atividades</a></nav>
      </aside>
      <section className="dashboard-main activities-main">
        <header className="activities-header">
          <div><span>HISTÓRICO DE CORRIDA</span><h1>Suas atividades.</h1><p>Importadas do Strava e privadas no Runneverso por padrão.</p></div>
          {status?.connected && <button className="button" onClick={sync} disabled={syncing}>{syncing ? "Sincronizando…" : "Sincronizar Strava"}</button>}
        </header>
        {message && <div className="sync-message">{message}</div>}
        {!status?.connected && <section className="empty-state"><h2>Conecte seu Strava</h2><p>Autorize a leitura para importar seu histórico.</p><a className="button" href={`${apiUrl}/auth/strava/link`}>Conectar</a></section>}
        {status?.connected && activities?.total === 0 && <section className="empty-state"><h2>Nenhuma corrida importada</h2><p>Clique em sincronizar para buscar suas atividades de corrida.</p></section>}
        {activities && activities.total > 0 && <>
          <div className="activities-summary"><strong>{activities.total}</strong><span>corridas importadas</span>{status?.last_synced_at && <small>Última sincronização: {new Date(status.last_synced_at).toLocaleString("pt-BR")}</small>}</div>
          <div className="activity-list">{activities.items.map((activity) => <article key={activity.id}>
            <div className="activity-date"><strong>{new Date(activity.started_at).getDate().toString().padStart(2, "0")}</strong><span>{new Date(activity.started_at).toLocaleDateString("pt-BR", { month: "short" }).replace(".", "")}</span></div>
            <div className="activity-name"><small>{activity.sport_type === "TrailRun" ? "TRAIL RUN" : "CORRIDA"}</small><h2>{activity.name}</h2><p>{new Date(activity.started_at).toLocaleDateString("pt-BR", { year: "numeric", month: "long", day: "numeric" })}</p></div>
            <div className="activity-metric"><strong>{(activity.distance_meters / 1000).toFixed(2)}</strong><span>km</span></div>
            <div className="activity-metric"><strong>{duration(activity.moving_time_seconds)}</strong><span>tempo</span></div>
            <div className="activity-metric"><strong>{Math.round(activity.elevation_gain)}</strong><span>m elevação</span></div>
            <div className="privacy-pill">Privada</div>
          </article>)}</div>
        </>}
      </section>
    </main>
  );
}
