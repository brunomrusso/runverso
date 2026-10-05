# Runneverso

Sua história na corrida, reunida em um único lugar.

O Runneverso é uma comunidade para corredores organizarem provas, medalhas, recordes e os lugares onde já correram. O produto terá integração com Strava, porta-medalhas digital, mapas de provas e treinos e controles granulares de privacidade.

## Stack

- Frontend: Next.js, React e TypeScript
- Backend: Python, FastAPI e SQLAlchemy
- Banco: PostgreSQL com PostGIS
- Migrations: Alembic
- Ambiente local: Docker Compose

## Pré-requisitos

- Docker Desktop com Docker Compose
- Git

## Executar localmente

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Acesse:

- Aplicação: http://localhost:3000
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Saúde da API: http://localhost:8000/health
- Saúde do banco: http://localhost:8000/health/database

## Testes e qualidade

```powershell
docker compose exec api pytest
docker compose exec api ruff check .
docker compose exec web npm run build
```

## Estrutura

```text
apps/api     API FastAPI, modelos, migrations e testes
apps/web     Aplicação web responsiva em Next.js
storage      Uploads locais ignorados pelo Git
docs         Documentação do produto
```

## Configurar autenticação local

Copie `.env.example` para `.env` e preencha as credenciais OAuth. Sem elas, a aplicação continua funcionando e informa que os provedores estão indisponíveis.

### Google

Crie um cliente OAuth do tipo aplicação web e cadastre:

```text
Origem JavaScript: http://localhost:3000
URI de redirecionamento: http://localhost:8000/auth/google/callback
```

### Strava

Crie uma aplicação no painel de desenvolvedor do Strava e use:

```text
Authorization Callback Domain: localhost
Callback: http://localhost:8000/auth/strava/callback
```

Os tokens do Strava são criptografados antes de serem persistidos. Use valores longos, aleatórios e diferentes em `SESSION_SECRET` e `TOKEN_ENCRYPTION_SECRET`.

## Estado atual

A aplicação contém landing page responsiva, login Google/Strava, sessões persistidas por cookie seguro, onboarding, perfil, configurações de privacidade, importação paginada do Strava, confirmação de provas e porta-medalhas digital. Fotos são validadas, reprocessadas, armazenadas localmente e entregues apenas após autenticação; atividades, provas e medalhas permanecem privadas por padrão. As credenciais OAuth não são versionadas.
