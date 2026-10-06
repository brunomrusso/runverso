"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Runner = { username: string; display_name: string | null; city: string | null; state: string | null; country_code: string; follower_count: number; viewer_follow_status: string | null };
type Followers = { followers: Runner[]; pending: Runner[]; following: Runner[] };

export default function CommunityPage() {
  const router = useRouter();
  const [items, setItems] = useState<Runner[]>([]);
  const [followers, setFollowers] = useState<Followers | null>(null);
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState("");

  const loadFollowers = useCallback(async () => {
    const response = await fetch(`${apiUrl}/me/followers`, { credentials: "include" });
    if (response.status === 401) return router.replace("/entrar");
    setFollowers(await response.json());
  }, [router]);

  useEffect(() => { loadFollowers(); }, [loadFollowers]);

  async function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const response = await fetch(`${apiUrl}/community/runners?q=${encodeURIComponent(query)}`, { credentials: "include" });
    if (response.status === 401) return router.replace("/entrar");
    setItems((await response.json()).items);
  }

  async function follow(username: string) {
    const response = await fetch(`${apiUrl}/users/${username}/follow`, { method: "POST", credentials: "include" });
    setMessage(response.ok ? "Solicitação registrada." : "Não foi possível seguir este corredor.");
    await loadFollowers();
    if (query.length >= 2) {
      const results = await fetch(`${apiUrl}/community/runners?q=${encodeURIComponent(query)}`, { credentials: "include" });
      setItems((await results.json()).items);
    }
  }

  async function answer(username: string, accept: boolean) {
    const response = await fetch(`${apiUrl}/me/followers/${username}${accept ? "/accept" : ""}`, {
      method: accept ? "POST" : "DELETE",
      credentials: "include",
    });
    setMessage(response.ok ? (accept ? "Seguidor aprovado." : "Relação removida.") : "Não foi possível atualizar.");
    await loadFollowers();
  }

  const runnerCard = (runner: Runner, actions?: React.ReactNode) => <article key={runner.username} className="runner-card"><a className="runner-avatar small" href={`/u/${runner.username}`}>{runner.display_name?.charAt(0).toUpperCase()}</a><div><a href={`/u/${runner.username}`}><h2>{runner.display_name}</h2></a><p>@{runner.username}{runner.city ? ` · ${runner.city}${runner.state ? `, ${runner.state}` : ""}` : ""}</p><small>{runner.follower_count} seguidores</small></div>{actions}</article>;

  return <main className="dashboard-shell">
    <aside className="dashboard-sidebar"><a className="brand" href="/">RUNNE<span>VERSO</span></a><nav className="side-nav"><a href="/dashboard">Visão geral</a><a href="/provas">Minhas provas</a><a href="/medalhas">Porta-medalhas</a><a href="/mapa">Mapa da corrida</a><a href="/atividades">Atividades</a><a href="/conquistas">Recordes</a><a className="active" href="/comunidade">Comunidade</a><a href="/perfil">Perfil</a></nav></aside>
    <section className="dashboard-main achievements-main">
      <header className="activities-header"><div><span>COMUNIDADE</span><h1>Encontre corredores.</h1><p>Busque perfis públicos, aprove solicitações e gerencie seus seguidores.</p></div></header>
      {message && <div className="sync-message">{message}</div>}
      <form className="runner-search" onSubmit={search}><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar por nome ou @usuário" /><button className="button">Buscar</button></form>
      {!!items.length && <section className="community-section"><h2>Resultados</h2>{items.map((runner) => runnerCard(runner, <button className="button" onClick={() => follow(runner.username)}>{runner.viewer_follow_status === "pending" ? "Pendente" : runner.viewer_follow_status === "accepted" ? "Seguindo" : "Seguir"}</button>))}</section>}
      <section className="community-grid">
        <div className="community-section"><h2>Solicitações <b>{followers?.pending.length ?? 0}</b></h2>{followers?.pending.map((runner) => runnerCard(runner, <div className="request-actions"><button className="button" onClick={() => answer(runner.username, true)}>Aceitar</button><button onClick={() => answer(runner.username, false)}>Recusar</button></div>))}{!followers?.pending.length && <p className="public-note">Nenhuma solicitação pendente.</p>}</div>
        <div className="community-section"><h2>Seguidores <b>{followers?.followers.length ?? 0}</b></h2>{followers?.followers.map((runner) => runnerCard(runner, <button className="link-button" onClick={() => answer(runner.username, false)}>Remover</button>))}{!followers?.followers.length && <p className="public-note">Você ainda não possui seguidores.</p>}</div>
        <div className="community-section"><h2>Seguindo <b>{followers?.following.length ?? 0}</b></h2>{followers?.following.map((runner) => runnerCard(runner))}{!followers?.following.length && <p className="public-note">Você ainda não segue ninguém.</p>}</div>
      </section>
    </section>
  </main>;
}
