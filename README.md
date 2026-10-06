# Runneverso

**Sua história na corrida, reunida em um único lugar.**

O Runneverso é uma aplicação web/PWA em português para transformar o histórico de corrida em um “passaporte esportivo”: atividades importadas do Strava, provas confirmadas, medalhas digitais, recordes pessoais, conquistas, mapa de lugares e uma camada social entre corredores.

## Principais funcionalidades

### Conta e onboarding

- Login com Google;
- Vinculação da conta Strava a uma conta Google existente;
- Sessões persistidas por cookie seguro;
- Onboarding com username, nome de exibição e preferências básicas;
- Perfil editável com avatar processado localmente.

### Strava e atividades

- Sincronização paginada das atividades de corrida;
- Deduplicação por `external_id` do Strava;
- Atualização de atividades já importadas;
- Renovação automática de token do Strava;
- Atividades privadas por padrão;
- Estatísticas agregadas no dashboard;
- Gráficos de quilometragem semanal e distância mensal.

### Provas

- Sugestão automática de provas baseada em:
  - `workout_type` do Strava;
  - Distância;
  - Nome da atividade;
  - Quantidade de atletas;
- Classificação por confiança alta, média ou baixa;
- Confirmação manual com revisão dos dados;
- Cadastro manual de provas;
- Edição de nome, data, categoria, distância oficial, tempo, cidade e estado;
- Categorias: 5K, 10K, 15K, 21K, 42K, Ultra e outras distâncias.

### Porta-medalhas

- Medalhas vinculadas a provas confirmadas;
- Upload da foto principal;
- Galeria de fotos adicionais;
- Medalhas favoritas;
- Organização por distância;
- História da conquista;
- Privacidade por medalha.

### Passaporte geográfico

- Separação entre treinos e provas;
- Países, estados/regiões e cidades;
- Bandeiras locais;
- Mapa Leaflet com tiles do OpenStreetMap;
- Geocodificação offline no backend;
- Cache de lugares;
- Exibição apenas de centroides aproximados de cidades;
- Coordenadas e rotas originais não são enviadas ao frontend público.

### Recordes e conquistas

- Recordes pessoais calculados a partir de provas confirmadas;
- Preferência por tempo líquido;
- Pace médio por prova;
- Conquistas automáticas por provas, distâncias, medalhas, países e quilometragem.

### Comunidade

- Perfis públicos em `/u/{username}`;
- Busca por nome ou username;
- Seguir corredores;
- Solicitações pendentes quando o usuário exige aprovação;
- Aceitar, recusar e remover seguidores;
- Feed com provas e medalhas de pessoas seguidas;
- Curtidas;
- Comentários com moderação pelo autor ou dono do conteúdo;
- Notificações internas para seguidor, solicitação, aceite, curtida e comentário.

### Privacidade

Configurações separadas para:

- Perfil;
- Atividades;
- Provas e recordes;
- Medalhas;
- Fotos;
- Lugares;
- Nome real;
- Tempos;
- Aprovação de seguidores.

### PWA/mobile

- Manifesto de instalação;
- Ícone vetorial do app;
- `display: standalone`;
- Tema e cor de fundo do Runneverso;
- Layout responsivo com navegação compacta no mobile.

## Stack

- **Frontend:** Next.js, React, TypeScript, CSS
- **Backend:** Python, FastAPI, SQLAlchemy
- **Banco:** PostgreSQL/PostGIS
- **Migrations:** Alembic
- **Mapa:** Leaflet e OpenStreetMap
- **Imagens:** Pillow
- **Infraestrutura local:** Docker Compose

## Estrutura

```text
apps/api             API FastAPI, modelos, migrations e testes
apps/web             Aplicação web/PWA em Next.js
storage/uploads      Uploads locais ignorados pelo Git
docs                 Documentação do produto
```

## Pré-requisitos

- Docker Desktop com Docker Compose;
- Git.

## Configuração inicial

Copie o arquivo de ambiente:

```powershell
Copy-Item .env.example .env
```

Edite `.env` e substitua os valores de exemplo por valores seguros:

```text
SESSION_SECRET=valor-longo-e-aleatorio
TOKEN_ENCRYPTION_SECRET=outro-valor-longo-e-aleatorio
```

Para login social, preencha também:

```text
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
STRAVA_CLIENT_ID=
STRAVA_CLIENT_SECRET=
```

Sem as credenciais OAuth, a aplicação continua subindo, mas os provedores ficam indisponíveis.

## Executar localmente

```powershell
docker compose up --build
```

Acesse:

```text
Aplicação:  http://localhost:3000
API:        http://localhost:8000
Swagger:    http://localhost:8000/docs
```

Health checks:

```text
GET /health
GET /health/database
```

## Serviços Docker

| Serviço | Porta local | Descrição |
|---|---:|---|
| `web` | 3000 | Next.js em modo desenvolvimento |
| `api` | 8000 | FastAPI com reload |
| `db` | 5433 → 5432 | PostgreSQL/PostGIS |

A API executa `alembic upgrade head` automaticamente ao subir.

## Comandos úteis

### Backend

```powershell
docker compose exec api pytest -q
docker compose exec api ruff check app tests
docker compose exec api alembic upgrade head
docker compose logs -f api
```

### Frontend

```powershell
npm run build:web
# ou
npm --workspace @runverso/web run build
docker compose restart web
```

## OAuth local

### Google

Crie um cliente OAuth do tipo aplicação web e configure:

```text
Origem JavaScript:      http://localhost:3000
URI de redirecionamento: http://localhost:8000/auth/google/callback
```

### Strava

Crie uma aplicação no painel de desenvolvedor do Strava e configure:

```text
Authorization Callback Domain: localhost
Callback: http://localhost:8000/auth/strava/callback
```

Os tokens do Strava são criptografados antes de serem persistidos. Não use os mesmos valores em `SESSION_SECRET` e `TOKEN_ENCRYPTION_SECRET`.

## Rotas principais

```text
/             Landing page
/entrar       Login
/onboarding   Cadastro inicial do corredor
/dashboard    Visão geral e gráficos
/atividades   Histórico importado do Strava
/provas       Sugestões, confirmação e cadastro de provas
/medalhas     Porta-medalhas digital
/mapa         Passaporte geográfico
/conquistas   Recordes e marcos automáticos
/comunidade   Busca, seguidores, feed e notificações
/perfil       Perfil, avatar e privacidade
/u/{username} Perfil público do corredor
```

## Segurança e privacidade

- Cookies de sessão persistidos;
- Tokens OAuth criptografados;
- Conteúdo privado por padrão;
- Uploads limitados a JPEG, PNG e WebP;
- Limite de 10 MB por imagem;
- Imagens reprocessadas e otimizadas;
- Correção de orientação EXIF;
- Diretórios separados por usuário;
- Rotas e coordenadas originais não são expostas no mapa;
- Feed, curtidas e comentários respeitam permissões de visibilidade;
- `.env` é ignorado pelo Git; somente `.env.example` deve ser versionado.

## Desenvolvimento

### Testes

```powershell
docker compose exec api pytest -q
```

### Lint

```powershell
docker compose exec api ruff check app tests
```

### Build de produção do frontend

```powershell
npm --workspace @runverso/web run build
```

Em desenvolvimento no Windows, o Next.js pode alterar `apps/web/next-env.d.ts` para apontar para um diretório temporário de build. Restaure esse arquivo antes de commitar quando a mudança for apenas artefato de build.

## Repositório

```text
https://github.com/brunomrusso/runverso
```
