import { AuthActions } from "@/components/auth-actions";

const features = [
  { tag: "01", title: "Seu porta-medalhas", text: "Organize cada conquista por distância, prova, ano e lugar." },
  { tag: "02", title: "Seu mapa de corrida", text: "Descubra os países, estados e cidades que seus passos já alcançaram." },
  { tag: "03", title: "Sua comunidade", text: "Compartilhe provas e recordes com privacidade sob seu controle." },
];

const distances = ["5K", "10K", "15K", "21K", "42K", "ULTRA"];

export default function Home() {
  return (
    <main>
      <nav>
        <a className="brand" href="#">RUN<span>VERSO</span></a>
        <div className="nav-links">
          <a href="#recursos">Recursos</a>
          <a href="#comunidade">Comunidade</a>
          <AuthActions compact />
        </div>
      </nav>

      <section className="hero">
        <div className="eyebrow"><i /> O universo de quem corre</div>
        <h1>Sua história.<br /><em>Seu percurso.</em><br />Seu Runverso.</h1>
        <p>Provas, medalhas, recordes e todos os lugares onde a corrida já levou você — reunidos em um perfil feito para corredores.</p>
        <div className="actions">
          <AuthActions />
        </div>
        <div className="distance-strip">{distances.map((distance) => <span key={distance}>{distance}</span>)}</div>
        <div className="orbit orbit-one" /><div className="orbit orbit-two" /><div className="runner">R</div>
      </section>

      <section className="features" id="recursos">
        <div className="section-heading">
          <span>PARA CADA PASSO, UMA MEMÓRIA</span>
          <h2>Mais que números.<br />Uma vida em movimento.</h2>
        </div>
        <div className="feature-grid">
          {features.map((feature) => (
            <article key={feature.tag}>
              <small>{feature.tag}</small>
              <h3>{feature.title}</h3>
              <p>{feature.text}</p>
              <a href="#">Descobrir <span>→</span></a>
            </article>
          ))}
        </div>
      </section>

      <section className="community" id="comunidade">
        <p>DO PRIMEIRO 5K À PRÓXIMA ULTRA</p>
        <h2>Cada corredor carrega<br />um universo de histórias.</h2>
        <div className="community-action"><AuthActions /></div>
      </section>
    </main>
  );
}
