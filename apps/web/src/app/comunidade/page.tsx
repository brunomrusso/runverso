"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Runner = { username: string; display_name: string | null; avatar_url: string | null; city: string | null; state: string | null; country_code: string; follower_count: number; viewer_follow_status: string | null };
type Followers = { followers: Runner[]; pending: Runner[]; following: Runner[] };
type FeedItem = { id: string; target_type: string; target_id: string; kind: string; username: string; display_name: string | null; title: string; subtitle: string | null; happened_at: string; like_count: number; viewer_liked: boolean };
type Notification = { id: string; kind: string; message: string; actor_username: string | null; actor_display_name: string | null; is_read: boolean; created_at: string };

export default function CommunityPage() {
  const router = useRouter();
  const [items, setItems] = useState<Runner[]>([]);
  const [followers, setFollowers] = useState<Followers | null>(null);
  const [feed, setFeed] = useState<FeedItem[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState("");

  const loadFollowers = useCallback(async () => {
    const [response, feedResponse, notificationResponse] = await Promise.all([
      fetch(`${apiUrl}/me/followers`, { credentials: "include" }),
      fetch(`${apiUrl}/feed`, { credentials: "include" }),
      fetch(`${apiUrl}/notifications`, { credentials: "include" }),
    ]);
    if (response.status === 401) return router.replace("/entrar");
    setFollowers(await response.json());
    setFeed((await feedResponse.json()).items);
    setNotifications((await notificationResponse.json()).items);
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

  async function toggleLike(item: FeedItem) {
    const response = await fetch(`${apiUrl}/feed/${item.target_type}/${item.target_id}/like`, { method: "POST", credentials: "include" });
    if (!response.ok) return;
    const result = await response.json();
    setFeed((current) => current.map((entry) => entry.id === item.id && entry.kind === item.kind ? { ...entry, viewer_liked: result.liked, like_count: result.like_count } : entry));
  }

  async function markRead() {
    const response = await fetch(`${apiUrl}/notifications/read`, { method: "POST", credentials: "include" });
    if (response.ok) setNotifications((current) => current.map((item) => ({ ...item, is_read: true })));
  }

  const runnerCard = (runner: Runner, actions?: React.ReactNode) => <article key={runner.username} className="runner-card"><a className="runner-avatar small" href={`/u/${runner.username}`}>{runner.avatar_url ? <img src={`${apiUrl}${runner.avatar_url}`} alt="" /> : runner.display_name?.charAt(0).toUpperCase()}</a><div><a href={`/u/${runner.username}`}><h2>{runner.display_name}</h2></a><p>@{runner.username}{runner.city ? ` · ${runner.city}${runner.state ? `, ${runner.state}` : ""}` : ""}</p><small>{runner.follower_count} seguidores</small></div>{actions}</article>;

  return <main className="dashboard-shell">
    <aside className="dashboard-sidebar"><a className="brand" href="/">RUNNE<span>VERSO</span></a><nav className="side-nav"><a href="/dashboard">Visão geral</a><a href="/provas">Minhas provas</a><a href="/medalhas">Porta-medalhas</a><a href="/mapa">Mapa da corrida</a><a href="/atividades">Atividades</a><a href="/conquistas">Recordes</a><a className="active" href="/comunidade">Comunidade</a><a href="/perfil">Perfil</a></nav></aside>
    <section className="dashboard-main achievements-main">
      <header className="activities-header"><div><span>COMUNIDADE</span><h1>Encontre corredores.</h1><p>Busque perfis públicos, aprove solicitações e gerencie seus seguidores.</p></div></header>
      {message && <div className="sync-message">{message}</div>}
      <form className="runner-search" onSubmit={search}><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar por nome ou @usuário" /><button className="button">Buscar</button></form>
      {!!items.length && <section className="community-section"><h2>Resultados</h2>{items.map((runner) => runnerCard(runner, <button className="button" onClick={() => follow(runner.username)}>{runner.viewer_follow_status === "pending" ? "Pendente" : runner.viewer_follow_status === "accepted" ? "Seguindo" : "Seguir"}</button>))}</section>}
      <section className="community-section"><h2>Notificações <b>{notifications.filter((item) => !item.is_read).length}</b></h2>{notifications.map((item) => <article className={item.is_read ? "notification-item" : "notification-item unread"} key={item.id}><strong>{item.actor_display_name ?? item.actor_username ?? "Runneverso"}</strong><p>{item.message}</p><small>{new Date(item.created_at).toLocaleDateString("pt-BR")}</small></article>)}{!notifications.length && <p className="public-note">Nenhuma notificação por enquanto.</p>}{!!notifications.length && <button className="link-button" onClick={markRead}>Marcar todas como lidas</button>}</section>
      <section className="community-section feed-section"><h2>Feed de quem você segue</h2>{feed.map((item) => <article className="feed-item" key={`${item.kind}-${item.id}`}><span>{item.kind === "medal" ? "MEDALHA" : "PROVA"}</span><div><a href={`/u/${item.username}`}><strong>{item.display_name}</strong></a><h3>{item.title}</h3><p>{item.subtitle}</p></div><div className="feed-actions"><small>{new Date(item.happened_at).toLocaleDateString("pt-BR")}</small><button className={item.viewer_liked ? "like-button liked" : "like-button"} onClick={() => toggleLike(item)}>Curtir · {item.like_count}</button></div></article>)}{!feed.length && <p className="public-note">Siga corredores para ver provas e medalhas compartilhadas aqui.</p>}</section>
      <section className="community-grid">
        <div className="community-section"><h2>Solicitações <b>{followers?.pending.length ?? 0}</b></h2>{followers?.pending.map((runner) => runnerCard(runner, <div className="request-actions"><button className="button" onClick={() => answer(runner.username, true)}>Aceitar</button><button onClick={() => answer(runner.username, false)}>Recusar</button></div>))}{!followers?.pending.length && <p className="public-note">Nenhuma solicitação pendente.</p>}</div>
        <div className="community-section"><h2>Seguidores <b>{followers?.followers.length ?? 0}</b></h2>{followers?.followers.map((runner) => runnerCard(runner, <button className="link-button" onClick={() => answer(runner.username, false)}>Remover</button>))}{!followers?.followers.length && <p className="public-note">Você ainda não possui seguidores.</p>}</div>
        <div className="community-section"><h2>Seguindo <b>{followers?.following.length ?? 0}</b></h2>{followers?.following.map((runner) => runnerCard(runner))}{!followers?.following.length && <p className="public-note">Você ainda não segue ninguém.</p>}</div>
      </section>
    </section>
  </main>;
}
