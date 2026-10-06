"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type PublicProfile = {
  profile: {
    username: string | null;
    display_name: string | null;
    bio: string | null;
    avatar_url: string | null;
    city: string | null;
    state: string | null;
    country_code: string;
    started_running_year: number | null;
    favorite_distance: string | null;
  };
  race_count: number | null;
  medal_count: number | null;
  country_count: number | null;
  records: { race_id: string; category: string; event_name: string; race_date: string; time_seconds: number; pace_seconds_per_km: number }[] | null;
  medals: { id: string; title: string | null; race_name: string; race_category: string; race_date: string; is_favorite: boolean }[] | null;
  follower_count: number;
  following_count: number;
  viewer_follow_status: string | null;
  is_own_profile: boolean;
};

function duration(seconds: number) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  return [hours, minutes, secs].map((value) => value.toString().padStart(2, "0")).join(":");
}

export default function PublicRunnerPage() {
  const { username } = useParams<{ username: string }>();
  const [runner, setRunner] = useState<PublicProfile | null>(null);
  const [notFound, setNotFound] = useState(false);

  const load = useCallback(async () => {
    const response = await fetch(`${apiUrl}/community/${username}`, { credentials: "include" });
    if (!response.ok) {
      setNotFound(true);
      return;
    }
    setRunner(await response.json());
  }, [username]);

  useEffect(() => { load(); }, [load]);

  async function follow() {
    const method = runner?.viewer_follow_status ? "DELETE" : "POST";
    const response = await fetch(`${apiUrl}/users/${username}/follow`, {
      method,
      credentials: "include",
    });
    if (response.status === 401) {
      window.location.href = "/entrar";
      return;
    }
    await load();
  }

  if (notFound) return <main className="public-runner"><a className="brand" href="/">RUNNE<span>VERSO</span></a><section className="empty-state"><h1>Perfil não encontrado</h1><p>Este corredor não existe ou manteve o perfil privado.</p><a className="button" href="/">Voltar ao início</a></section></main>;
  if (!runner) return <main className="dashboard-loading">Carregando perfil…</main>;

  const profile = runner.profile;
  const location = [profile.city, profile.state].filter(Boolean).join(", ");

  return <main className="public-runner">
    <nav><a className="brand" href="/">RUNNE<span>VERSO</span></a><a className="button button-small" href="/entrar">Entrar</a></nav>
    <section className="runner-hero">
      <div className="runner-avatar">{profile.avatar_url ? <img src={profile.avatar_url} alt="" /> : profile.display_name?.charAt(0).toUpperCase()}</div>
      <div><span>@{profile.username}</span><h1>{profile.display_name}</h1><p>{profile.bio || "Sua história na corrida, reunida em um único lugar."}</p><small>{location}{profile.started_running_year ? ` · corre desde ${profile.started_running_year}` : ""}{profile.favorite_distance ? ` · distância favorita ${profile.favorite_distance}` : ""}</small></div>
      {!runner.is_own_profile && <button className="button" onClick={follow}>{runner.viewer_follow_status === "pending" ? "Solicitação enviada" : runner.viewer_follow_status === "accepted" ? "Seguindo" : "Seguir corredor"}</button>}
    </section>
    <section className="geo-stats"><article><strong>{runner.follower_count}</strong><span>seguidores</span></article><article><strong>{runner.following_count}</strong><span>seguindo</span></article><article><strong>{runner.race_count ?? "—"}</strong><span>provas</span></article></section>
    {(runner.records || runner.medals || runner.country_count !== null) && <section className="public-sections">
      {runner.records && <div><h2>Recordes</h2><div className="public-list">{runner.records.map((record) => <article key={record.race_id}><b>{record.category}</b><div><strong>{duration(record.time_seconds)}</strong><span>{record.event_name}</span></div></article>)}</div></div>}
      {runner.medals && <div><h2>Medalhas públicas</h2><div className="public-list">{runner.medals.map((medal) => <article key={medal.id}><b>{medal.race_category}</b><div><strong>{medal.title || medal.race_name}</strong><span>{new Date(`${medal.race_date}T12:00:00`).toLocaleDateString("pt-BR")}</span></div></article>)}</div></div>}
      {runner.country_count !== null && <div><h2>Passaporte</h2><p className="public-note">{runner.country_count} {runner.country_count === 1 ? "país conquistado" : "países conquistados"}</p></div>}
    </section>}
  </main>;
}
