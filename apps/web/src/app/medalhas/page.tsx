"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Photo = { id: string; kind: string; thumbnail_url: string; image_url: string };
type Medal = { id: string; title: string | null; story: string | null; is_favorite: boolean; visibility: string; race: { id: string; event_name: string; race_date: string; category: string; city: string | null; state: string | null }; photos: Photo[] };
type Race = { id: string; event_name: string; race_date: string; category: string; city: string | null };
const categories = ["5K", "10K", "15K", "21K", "42K", "ULTRA", "OTHER"];

export default function MedalsPage() {
  const router = useRouter();
  const [medals, setMedals] = useState<Medal[]>([]);
  const [races, setRaces] = useState<Race[]>([]);
  const [creating, setCreating] = useState(false);
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    const [medalsResponse, racesResponse] = await Promise.all([
      fetch(`${apiUrl}/medals`, { credentials: "include" }),
      fetch(`${apiUrl}/races`, { credentials: "include" }),
    ]);
    if (medalsResponse.status === 401) return router.replace("/entrar");
    setMedals((await medalsResponse.json()).items);
    setRaces((await racesResponse.json()).items);
  }, [router]);

  useEffect(() => { load(); }, [load]);

  async function createMedal(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const response = await fetch(`${apiUrl}/medals`, {
      method: "POST", credentials: "include", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ race_id: form.get("race_id"), title: form.get("title") || null, story: form.get("story") || null, visibility: "private" }),
    });
    if (!response.ok) { setMessage("Não foi possível criar a medalha."); return; }
    const medal = await response.json();
    const photo = form.get("photo") as File;
    if (photo?.size) await uploadPhoto(medal.id, photo, "front", false);
    setCreating(false); setMessage("Medalha adicionada ao seu porta-medalhas."); await load();
  }

  async function uploadPhoto(medalId: string, file: File, kind: string, reload = true) {
    const data = new FormData(); data.append("photo", file); data.append("kind", kind);
    const response = await fetch(`${apiUrl}/medals/${medalId}/photos`, { method: "POST", credentials: "include", body: data });
    if (!response.ok) { const error = await response.json(); setMessage(error.detail ?? "Erro no upload da foto."); return; }
    setMessage("Foto da medalha atualizada."); if (reload) await load();
  }

  async function toggleFavorite(medal: Medal) {
    await fetch(`${apiUrl}/medals/${medal.id}`, { method: "PATCH", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ is_favorite: !medal.is_favorite }) });
    await load();
  }

  const medalRaceIds = new Set(medals.map((medal) => medal.race.id));
  const availableRaces = races.filter((race) => !medalRaceIds.has(race.id));

  return <main className="dashboard-shell">
    <aside className="dashboard-sidebar"><a className="brand" href="/">RUNNE<span>VERSO</span></a><nav className="side-nav"><a href="/dashboard">Visão geral</a><a href="/provas">Minhas provas</a><a className="active" href="/medalhas">Porta-medalhas</a><a href="#">Mapa da corrida</a><a href="/atividades">Atividades</a></nav></aside>
    <section className="dashboard-main medals-main">
      <header className="activities-header"><div><span>SUAS CONQUISTAS</span><h1>Porta-medalhas.</h1><p>Uma galeria privada por padrão, organizada por distância.</p></div><button className="button" disabled={!availableRaces.length} onClick={() => setCreating(!creating)}>Adicionar medalha</button></header>
      {message && <div className="sync-message">{message}</div>}
      {creating && <form className="race-form" onSubmit={createMedal}><h2>Nova medalha</h2><label>Prova<select name="race_id" required><option value="">Selecione</option>{availableRaces.map((race) => <option value={race.id} key={race.id}>{race.event_name} — {race.category}</option>)}</select></label><label>Título opcional<input name="title" placeholder="Minha primeira maratona" /></label><label>História<textarea name="story" rows={3} placeholder="O que esta medalha representa para você?" /></label><label>Foto da frente<input name="photo" type="file" accept="image/jpeg,image/png,image/webp" /></label><button className="button">Guardar medalha</button></form>}
      {!medals.length && <section className="empty-state"><h2>Seu porta-medalhas está vazio</h2><p>Confirme uma prova e adicione a foto da conquista.</p><a className="button" href="/provas">Ver minhas provas</a></section>}
      {categories.map((category) => { const items = medals.filter((medal) => medal.race.category === category); if (!items.length) return null; return <section className="medal-shelf" key={category}><header><h2>{category}</h2><span>{items.length} {items.length === 1 ? "medalha" : "medalhas"}</span></header><div className="medal-grid">{items.map((medal) => { const front = medal.photos.find((photo) => photo.kind === "front") ?? medal.photos[0]; return <article key={medal.id} className={medal.is_favorite ? "favorite" : ""}><div className="medal-image">{front ? <img src={`${apiUrl}${front.thumbnail_url}`} alt={`Medalha ${medal.race.event_name}`} /> : <span>SEM FOTO</span>}<button onClick={() => toggleFavorite(medal)} aria-label="Favoritar">{medal.is_favorite ? "★" : "☆"}</button></div><div className="medal-info"><small>{new Date(`${medal.race.race_date}T12:00:00`).getFullYear()}</small><h3>{medal.title || medal.race.event_name}</h3><p>{medal.race.city || "Local não informado"}</p><label className="photo-action">Adicionar foto<input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => event.target.files?.[0] && uploadPhoto(medal.id, event.target.files[0], front ? "gallery" : "front")} /></label><span className="privacy-pill">Privada</span></div></article>})}</div></section> })}
    </section>
  </main>;
}
