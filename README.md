# DevAI Newsletter — Pipeline automático

Newsletter semanal de herramientas de IA para desarrolladores, en español. Se genera, publica y envía **completamente solo** cada martes a las 9:00h (España) sin intervención manual.

**Web:** [devaisemanal.com](https://devaisemanal.com)

---

## Cómo funciona

```
Martes 9:00h — GitHub Actions arranca el pipeline
      │
      ▼
[1] Sourcing     — Recoge noticias de RSS, Hacker News, Reddit, GitHub Trending
      │
      ▼
[2] Curation     — Claude selecciona los 5-7 mejores items de la semana
      │
      ▼
[3] Rewriting    — Claude redacta cada noticia en español con contexto
      │
      ▼
[4] Assembly     — Renderiza el HTML del newsletter (email-ready)
      │
      ▼
[5] Publishing   — Publica en Ghost (web) + envía por MailerLite (email)
      │
      ▼
Telegram         — Notificación con las URLs del resultado
```

Cada fase es **idempotente**: si el pipeline se interrumpe, reanudar no repite el trabajo ya hecho (los JSON intermedios se cachean por fecha en `data/`).

---

## Stack

| Componente | Rol |
|---|---|
| **GitHub Actions** | Scheduler — cron martes 07:00 UTC |
| **Claude API** (Anthropic) | Curation + rewriting del contenido |
| **Ghost 5** en Fly.io | CMS — archivo web en devaisemanal.com |
| **MailerLite** | Plataforma de email — envío automático a suscriptores |
| **Resend** | SMTP transaccional de Ghost (confirmaciones, etc.) |
| **Namecheap** | DNS de devaisemanal.com |
| **Telegram Bot** | Notificaciones al terminar |

---

## Fuentes de noticias

Configuradas en `config.yaml`:

- **RSS**: Anthropic, OpenAI, Google AI, GitHub, Microsoft AI, VS Code
- **Hacker News**: keywords como `claude code`, `cursor ai`, `github copilot`, `mcp server`…
- **Reddit**: r/ClaudeAI, r/cursor, r/LocalLLaMA, r/ChatGPTPro
- **GitHub Trending**: topics `ai-coding`, `developer-tools`, `llm`, `mcp`

---

## Estructura del proyecto

```
devai-newsletter/
├── run.py                  # Entry point — python run.py [--draft|--preview]
├── config.yaml             # Fuentes, modelo Claude, nombre del newsletter
├── requirements.txt
├── .env.example            # Plantilla de variables de entorno
│
├── src/
│   ├── sourcing.py         # Fase 1 — recoge noticias
│   ├── curation.py         # Fase 2 — Claude selecciona
│   ├── rewriting.py        # Fase 3 — Claude redacta
│   ├── assembly.py         # Fase 4 — renderiza HTML/TXT
│   ├── publishing.py       # Fase 5 — publica en Ghost + MailerLite
│   └── utils.py            # Rate limiter, logging
│
├── templates/              # Plantillas HTML del newsletter
├── data/                   # Cache intermedio por fecha (gitignored)
├── output/                 # HTML/TXT generados (gitignored)
├── logs/                   # Logs de ejecución (gitignored)
│
└── .github/
    └── workflows/
        └── newsletter.yml  # GitHub Actions — cron martes 07:00 UTC
```

---

## Configuración

### 1. Clonar y dependencias

```bash
git clone https://github.com/Khavel/devai-newsletter.git
cd devai-newsletter
pip install -r requirements.txt
```

### 2. Variables de entorno

```bash
cp .env.example .env
# Rellenar los valores en .env
```

| Variable | Obligatoria | Descripción |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ | API key de Claude — [console.anthropic.com](https://console.anthropic.com/settings/keys) |
| `GHOST_URL` | ✅ | URL del sitio Ghost (ej. `https://devaisemanal.com`) |
| `GHOST_ADMIN_API_KEY` | ✅ | Ghost Admin → Settings → Integrations → Custom integration |
| `MAILERLITE_API_KEY` | Para email | [dashboard.mailerlite.com/integrations/api](https://dashboard.mailerlite.com/integrations/api) |
| `MAILERLITE_SENDER_EMAIL` | Para email | Email verificado en MailerLite → Senders |
| `MAILERLITE_SENDER_NAME` | Para email | Nombre del remitente (ej. `DevAI`) |
| `MAILERLITE_GROUP_ID` | Para auto-envío | ID numérico del grupo de suscriptores — si se omite, crea draft |
| `TELEGRAM_BOT_TOKEN` | Opcional | Token del bot de Telegram ([@BotFather](https://t.me/BotFather)) |
| `TELEGRAM_CHAT_ID` | Opcional | Chat ID donde enviar notificaciones |

> **Auto-envío de email:** Si `MAILERLITE_GROUP_ID` está configurado, el pipeline crea la campaña **y la envía automáticamente**. Sin ese valor, crea un borrador en MailerLite que hay que enviar a mano.

### 3. Obtener el MAILERLITE_GROUP_ID

1. Ir a [MailerLite → Subscribers → Groups](https://dashboard.mailerlite.com/subscribers/groups)
2. Clic en "View group" sobre el grupo deseado
3. Copiar el ID numérico de la URL: `...groups/[ESTE_ES_EL_ID]`

---

## Uso local

```bash
# Vista previa — genera el newsletter y lo abre en el navegador
python run.py

# Publicar — sube a Ghost y envía por MailerLite
python run.py --draft
```

El pipeline es idempotente: si ya existen los ficheros intermedios del día (`data/raw_items_YYYY-MM-DD.json`, etc.), las fases ya completadas se saltan automáticamente.

---

## Automatización (GitHub Actions)

El workflow `.github/workflows/newsletter.yml` corre cada **martes a las 07:00 UTC** (09:00 CEST).

### Secrets necesarios en GitHub

```bash
gh secret set ANTHROPIC_API_KEY
gh secret set GHOST_URL
gh secret set GHOST_ADMIN_API_KEY
gh secret set MAILERLITE_API_KEY
gh secret set MAILERLITE_SENDER_EMAIL
gh secret set MAILERLITE_SENDER_NAME
gh secret set MAILERLITE_GROUP_ID
gh secret set TELEGRAM_BOT_TOKEN
gh secret set TELEGRAM_CHAT_ID
```

### Ejecutar manualmente

GitHub → Actions → "DevAI Newsletter Pipeline" → "Run workflow" → seleccionar modo `draft`.

---

## Infraestructura web (Ghost en Fly.io)

Ghost 5 corre en Fly.io (región París, `cdg`) con SQLite y volumen persistente.

```toml
# fly.toml
app            = "devaisemanal"
primary_region = "cdg"

[build]
  image = "ghost:5-alpine"

[env]
  url = "https://devaisemanal.com"
  mail__options__host = "smtp.resend.com"
  mail__options__port = "465"
  mail__options__auth__user = "resend"

[[mounts]]
  source = "ghost_content"
  destination = "/var/lib/ghost/content"
```

El email transaccional de Ghost (confirmaciones de suscripción, etc.) va por **Resend** con dominio verificado `devaisemanal.com`.

### Secretos en Fly.io

```bash
fly secrets set url=https://devaisemanal.com
fly secrets set mail__options__auth__pass=re_...  # Resend API key
fly secrets set GHOST_ADMIN_API_KEY=...
```

---

## Decisiones técnicas

### ¿Por qué 1x/semana?

Datos de beehiiv (15.600M emails, 2024): las newsletters semanales tienen la mayor tasa de apertura y el menor churn. Los envíos diarios generan un 40% más de bajas. El formato de 5-7 noticias con análisis en español no escala a 2x/semana sin degradar la calidad.

**Umbral para revisar:** +5.000 suscriptores activos con >40% de open rate.

### ¿Por qué martes?

Captura los lanzamientos y anuncios del lunes (el día más activo en el ecosistema de IA), y tiene mejores tasas de apertura que el fin de semana.

### Ghost + MailerLite vs. plataforma única

Ghost gestiona el archivo web público (SEO, lectores ocasionales) y MailerLite gestiona la lista de suscriptores y el envío de email. Separar ambas responsabilidades permite cambiar cualquiera de las dos sin afectar a la otra.

### HTML del newsletter en Ghost

El HTML del email (diseñado para clientes de correo) se inyecta en Ghost como un HTML card de mobiledoc. Para que se renderice correctamente en la web:
- Se extrae solo el contenido del `<body>` (evita el problema de documento anidado)
- Se inyecta CSS por post (`codeinjection_head`) para ocultar el chrome de Ghost y eliminar padding superior
- Se aplica el tag `newsletter` para identificar este tipo de posts

---

## Añadir nuevas fuentes

Editar `config.yaml`:

```yaml
sources:
  rss:
    - url: "https://mi-nuevo-blog.com/feed"
      name: "Mi Blog"
  hackernews:
    keywords:
      - "nuevo keyword"
  reddit:
    subreddits:
      - "nuevo_subreddit"
```

No hace falta tocar código — `sourcing.py` lee la configuración dinámicamente.
