"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function OnboardingPage() {
  const router = useRouter();
  const [form, setForm] = useState({ username: "", display_name: "", real_name: "", city: "", state: "", country_code: "BR", favorite_distance: "10K" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${apiUrl}/me`, { credentials: "include" })
      .then((response) => {
        if (response.status === 401) throw new Error("unauthorized");
        return response.json();
      })
      .then((data) => {
        setForm((current) => ({ ...current, display_name: data.profile.display_name ?? "", real_name: data.profile.real_name ?? "", city: data.profile.city ?? "", state: data.profile.state ?? "" }));
        setLoading(false);
      })
      .catch(() => router.replace("/entrar"));
  }, [router]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    const response = await fetch(`${apiUrl}/me/profile`, {
      method: "PATCH",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...form, bio: null, started_running_year: null }),
    });
    if (!response.ok) {
      const data = await response.json();
      setError(data.detail ?? "Não foi possível salvar seu perfil");
      return;
    }
    router.push("/dashboard");
  }

  if (loading) return <main className="onboarding-shell"><p>Preparando seu Runneverso…</p></main>;

  return (
    <main className="onboarding-shell">
      <section className="onboarding-copy">
        <a className="brand" href="/">RUNNE<span>VERSO</span></a>
        <div><span>PASSO 1 DE 3</span><h1>Como você quer ser<br /><em>reconhecido?</em></h1><p>Você controla o que será público. Seu nome real poderá ficar oculto no perfil.</p></div>
      </section>
      <form className="onboarding-form" onSubmit={submit}>
        <label>Nome de usuário<input required minLength={3} pattern="[a-z0-9_]+" placeholder="seu_usuario" value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value.toLowerCase() })} /><small>Somente letras minúsculas, números e underline.</small></label>
        <label>Nome público<input required placeholder="Como as pessoas verão você" value={form.display_name} onChange={(event) => setForm({ ...form, display_name: event.target.value })} /></label>
        <label>Nome real <span>opcional</span><input value={form.real_name} onChange={(event) => setForm({ ...form, real_name: event.target.value })} /></label>
        <div className="form-row"><label>Cidade<input value={form.city} onChange={(event) => setForm({ ...form, city: event.target.value })} /></label><label>Estado<input value={form.state} onChange={(event) => setForm({ ...form, state: event.target.value })} /></label></div>
        <label>Distância favorita<select value={form.favorite_distance} onChange={(event) => setForm({ ...form, favorite_distance: event.target.value })}><option>5K</option><option>10K</option><option>15K</option><option>21K</option><option>42K</option><option>ULTRA</option></select></label>
        {error && <p className="form-error">{error}</p>}
        <button className="button" type="submit">Criar meu perfil <b>→</b></button>
      </form>
    </main>
  );
}
