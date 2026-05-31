# DevAI Semanal — Plan de Expansión SEO

> **Dominio:** devaisemanal.com (Ghost CMS)
> **Fecha:** 2026-05-24
> **Fuentes:** Semrush (db: es), Google Search Console, análisis SERP manual

---

## 1. Estado actual — Snapshot

### 1.1 Arquitectura técnica

| Capa | Stack |
|------|-------|
| CMS | Ghost (self-hosted o managed) |
| Publicación | Pipeline Python: sourcing → curation → rewriting → assembly → publishing |
| Email | MailerLite (campañas + auto-send) |
| Notificaciones | Telegram Bot |
| SEO Intelligence | `seo_intelligence.py` — gap analysis vía Google Search Console API (OAuth2) |
| Analytics | Google Search Console (service account + OAuth tokens) |
| Modelo IA | Claude Sonnet 4 (`claude-sonnet-4-20250514`) |

### 1.2 Flujo de publicación actual

```
RSS/HN/Reddit → sourcing.py → curation.py → rewriting.py → assembly.py → publishing.py
                                                                              ├── Ghost CMS (post publicado)
                                                                              ├── MailerLite (campaña email)
                                                                              └── Telegram (notificación)
```

**Archivos clave:**

| Archivo | Función SEO |
|---------|-------------|
| `src/publishing.py` | `_build_newsletter_seo()` genera meta_title, meta_description, custom_excerpt dinámicamente desde artículos |
| `src/seo_intelligence.py` | Gap analysis GSC — compara queries reales vs posts Ghost existentes |
| `config.yaml` | Keywords de monitoreo (claude code, cursor ai, github copilot, mcp server, vibe coding...) |
| `run_seo.py` | Entry point del pipeline SEO intelligence |
| `_list_ghost_posts.py` | Lista posts Ghost vía Admin API |
| `_check_index.py` | Verifica indexación en Google |
| `_submit_new_urls.py` | Submit URLs a Google para indexación |

### 1.3 SEO on-page actual (Ghost)

El sistema ya genera SEO dinámico por newsletter:

```python
# publishing.py — _build_newsletter_seo()
title = f"{name}: {topic_line} | {human_date}"          # ≤65 chars
description = f"Resumen semanal para desarrolladores: {topic_line}..."  # ≤155 chars
```

Campos Ghost utilizados por post:
- `title` / `meta_title`
- `meta_description`
- `custom_excerpt`
- `feature_image` (Unsplash genérica)
- `slug` → patrón `newsletter-{YYYY-MM-DD}`
- `tags` → `["Newsletter"]`
- `mobiledoc` → HTML card con contenido del email

### 1.4 Métricas Semrush (Mayo 2026)

| Métrica | Valor |
|---------|-------|
| Keywords orgánicas | 12 |
| Tráfico estimado | ~2 visitas/mes |
| Semrush Rank | 2,595,121 |
| Backlinks | No medidos |

### 1.5 Rankings actuales

| Keyword | Volumen/mes (ES) | Posición | KD |
|---------|----------------:|:--------:|---:|
| cursor ai | 8,100 | #20 | 71 |
| replit | 14,800 | #37 | 62 |
| bolt.new | 1,900 | #32 | 51 |
| mcp | 8,100 | #51 | 55 |
| codewhisperer ia | 110 | #22 | 28 |

**Diagnóstico:** El sitio rankea para 12 keywords pero NO para las de mayor intent developer. El contenido actual son newsletters semanales con slugs tipo `newsletter-2026-05-17` — Google las indexa pero no las posiciona porque no tienen estructura de contenido evergreen.

---

## 2. Keyword Research — Clusters validados

### Cluster 1: Claude Code (Prioridad máxima)

**Razón:** 9,900 vol/mes, KD 43, competencia 0.12. nocodehackers.es (2,949 keywords totales) ya rankea #3 — prueba de que un sitio pequeño puede dominar este término. DevAI NO rankea actualmente.

| Keyword | Vol/mes | KD | Intent | Tipo contenido |
|---------|--------:|---:|--------|----------------|
| claude code | 9,900 | 43 | Informational/Nav | Guía definitiva |
| claude ia | 6,600 | 38 | Navigational | Hub de producto |
| claude sonnet | 1,900 | 23 | Navigational | Comparativa modelos |
| claude code tutorial | 480 | 28 | Informational | Tutorial paso a paso |
| claude code vs cursor | 390 | 31 | Commercial | Comparativa |
| como usar claude code | 320 | 22 | Informational | Guía para principiantes |
| claude code hooks | 210 | 18 | Informational | Guía avanzada |
| claude code tips | 170 | 20 | Informational | Lista de tips |
| como hacer que claude code acepte todo automaticamente | 210 | ~5 | Informational | Tutorial específico |

**Volumen total del cluster: ~20,180/mes**

### Cluster 2: Cursor AI & Editores IA

**Razón:** Ya rankea #20 para "cursor ai". Subir de posición 20→10 es más fácil que crear ranking desde cero.

| Keyword | Vol/mes | KD | Posición actual | Tipo contenido |
|---------|--------:|---:|:-:|----------------|
| cursor ai | 8,100 | 71 | #20 | Guía completa |
| cursor ia | 2,400 | 55 | — | Redirect/sinónimo |
| cursor vs copilot | 720 | 45 | — | Comparativa |
| cursor rules | 480 | 35 | — | Guía técnica |
| mejor editor ia | 880 | 42 | — | Ranking/listicle |
| ia para programar | 720 | 38 | — | Guía panorámica |
| mejor ia para programar | 880 | 40 | — | Ranking comparativo |

**Volumen total del cluster: ~14,180/mes**

### Cluster 3: MCP (Model Context Protocol)

**Razón:** Ya rankea #51 para "mcp". Contenido técnico profundo puede subir rápido — pocos competidores en español.

| Keyword | Vol/mes | KD | Posición actual | Tipo contenido |
|---------|--------:|---:|:-:|----------------|
| mcp | 8,100 | 55 | #51 | Hub explicativo |
| mcp servers | 1,600 | 55 | — | Directorio/guía |
| mcp que es | 320 | 22 | — | Explicación conceptual |
| mcp anthropic | 260 | 30 | — | Guía oficial |
| mcp server tutorial | 170 | 25 | — | Tutorial build-your-own |
| crear mcp server | 110 | 18 | — | Tutorial paso a paso |

**Volumen total del cluster: ~10,560/mes**

### Cluster 4: Vibe Coding & Tendencias

**Razón:** Término emergente con alto volumen y KD moderado. Pocos resultados autoritativos en español.

| Keyword | Vol/mes | KD | Tipo contenido |
|---------|--------:|---:|----------------|
| vibe coding | 6,600 | 45 | Guía + opinión |
| vibe coding que es | 480 | 25 | Explicación |
| vibe coding herramientas | 210 | 30 | Listicle |
| agentes ia | 1,000 | 64 | Guía conceptual |
| agentes ia programacion | 260 | 35 | Tutorial |

**Volumen total del cluster: ~8,550/mes**

### Cluster 5: GitHub Copilot & Alternativas

| Keyword | Vol/mes | KD | Tipo contenido |
|---------|--------:|---:|----------------|
| github copilot | 12,100 | 72 | Guía completa |
| github copilot gratis | 2,900 | 45 | Tutorial activación |
| copilot vs cursor | 720 | 45 | Comparativa |
| alternativas github copilot | 480 | 38 | Listicle |
| codewhisperer ia | 110 | 28 | Review |

**Volumen total del cluster: ~16,310/mes**

### Cluster 6: Prompts & Ingeniería

| Keyword | Vol/mes | KD | Tipo contenido |
|---------|--------:|---:|----------------|
| prompts chatgpt | 1,000 | 37 | Colección/guía |
| ingenieria de prompts | 260 | 31 | Guía conceptual |
| mejores prompts programacion | 210 | 22 | Listicle curado |
| system prompt ejemplos | 170 | 20 | Colección técnica |

**Volumen total del cluster: ~1,640/mes**

### Cluster 7: Noticias IA (Brand Building)

| Keyword | Vol/mes | KD | Tipo contenido |
|---------|--------:|---:|----------------|
| noticias inteligencia artificial | 320 | 32 | Newsletter archive |
| noticias ia hoy | 260 | 28 | Feed/archivo |
| novedades ia programacion | 170 | 18 | Resumen semanal |

**Volumen total del cluster: ~750/mes**

### Resumen de oportunidad

| Cluster | Vol total/mes | Dificultad media | Prioridad |
|---------|-------------:|:-:|:-:|
| Claude Code | 20,180 | Baja-Media | 🔴 P0 |
| GitHub Copilot | 16,310 | Alta | 🟡 P2 |
| Cursor AI | 14,180 | Media | 🟠 P1 |
| MCP Protocol | 10,560 | Media | 🟠 P1 |
| Vibe Coding | 8,550 | Media | 🟡 P2 |
| Prompts | 1,640 | Baja | 🟢 P3 |
| Noticias IA | 750 | Baja | 🟢 P3 |

**Tráfico potencial total: ~72,170 búsquedas/mes** (asumiendo CTR 5-15% en posiciones 3-10)

---

## 3. Análisis competitivo SERP

### 3.1 Mapa de competidores (mercado español, nicho IA para devs)

| Sitio | Tráfico Semrush | Keywords | Tipo | Amenaza |
|-------|---------------:|--------:|------|:-------:|
| xataka.com | 1,900,000 | 280K+ | Media generalista tech | 🟡 Baja (no dev-focused) |
| genbeta.com | 50,000 | 12K+ | Media tech/software | 🟡 Media |
| hipertextual.com | 40,000 | 10K+ | Media tech | 🟡 Media |
| platzi.com | 24,000 | 8K+ | Educación online | 🟠 Media-Alta |
| **nocodehackers.es** | **22,000** | **2,949** | Blog nicho IA/nocode | 🔴 **Alta** |

### 3.2 Caso de estudio: nocodehackers.es

**Por qué importa:** Con solo 2,949 keywords, genera 22K de tráfico estimado y rankea **#3 para "claude code"** en España. Demuestra que:

1. Un sitio pequeño puede superar a Xataka/Genbeta en términos nicho
2. Contenido profundo y específico > cobertura amplia y superficial
3. Las guías evergreen superan a las noticias en SEO

**Estrategia que usa:**
- Guías largas (3,000-5,000 palabras) sobre herramientas específicas
- Estructura clara: qué es → cómo funciona → tutorial → tips → FAQ
- Actualización frecuente de posts existentes
- Foco en intent informacional con alta especificidad

### 3.3 Newsletters IA en español (competencia directa)

| Newsletter | Suscriptores | Foco | Tiene web SEO |
|------------|:-:|------|:---:|
| IA en Español | ~46,000 | General/negocios | Mínimo |
| Alejo & Adam | ~60,000 | General/negocios | No |
| Digital Brain | ~20,000 | General/productividad | No |
| **DevAI Semanal** | — | **Developers/builders** | **En desarrollo** |

**Insight clave:** NINGUNA newsletter de IA en español tiene presencia SEO seria orientada a developers. DevAI tiene un oceano azul: es la única newsletter española de IA específica para programadores y builders.

### 3.4 Content gap analysis

Keywords con alto volumen donde NO existe contenido autoritativo en español para developers:

| Keyword | Vol | Mejor resultado actual ES | Oportunidad |
|---------|----:|--------------------------|:-:|
| claude code | 9,900 | nocodehackers.es (no-dev) | 🔴 Enorme |
| mcp servers | 1,600 | Ninguno bueno | 🔴 Enorme |
| vibe coding | 6,600 | Artículos superficiales | 🔴 Enorme |
| cursor rules | 480 | Ninguno en ES | 🔴 Total |
| claude code hooks | 210 | Ninguno en ES | 🔴 Total |
| system prompt ejemplos | 170 | Ninguno para devs | 🟠 Grande |

---

## 4. Arquitectura SEO propuesta

### 4.1 Problema actual

Ghost publica cada newsletter con slug `newsletter-YYYY-MM-DD`. Este contenido:
- ❌ No tiene keyword targeting (título dinámico basado en artículos del día)
- ❌ No es evergreen — cada edición caduca
- ❌ No tiene internal linking estructurado
- ❌ No genera autoridad temática (topic clusters)
- ❌ No tiene breadcrumbs, schema markup, ni Open Graph optimizado

### 4.2 Modelo propuesto: Newsletter + Contenido Evergreen

```
devaisemanal.com/
├── / ................................ Homepage (newsletter signup + valor prop)
├── /newsletter/ .................... Archivo de newsletters (listing page)
│   └── /newsletter/newsletter-YYYY-MM-DD  ... Ediciones semanales (ya existe)
│
├── /guias/ ......................... Hub de guías (pillar page)
│   ├── /guias/claude-code/ ......... Guía definitiva Claude Code
│   ├── /guias/cursor-ai/ .......... Guía completa Cursor
│   ├── /guias/mcp-servers/ ........ Guía MCP Protocol
│   ├── /guias/vibe-coding/ ........ Qué es vibe coding
│   └── /guias/github-copilot/ ..... Guía GitHub Copilot
│
├── /comparativas/ .................. Hub de comparativas
│   ├── /comparativas/claude-code-vs-cursor/
│   ├── /comparativas/copilot-vs-cursor/
│   └── /comparativas/mejor-ia-programar/
│
├── /tutoriales/ .................... Hub de tutoriales
│   ├── /tutoriales/claude-code-tutorial/
│   ├── /tutoriales/crear-mcp-server/
│   └── /tutoriales/cursor-rules-guia/
│
└── /archivo/ ....................... Archivo por tema (tag pages)
    ├── /tag/claude-code/
    ├── /tag/cursor/
    └── /tag/mcp/
```

### 4.3 Implementación en Ghost

Ghost soporta esta estructura nativamente:

| Necesidad | Solución Ghost |
|-----------|---------------|
| Páginas evergreen | Ghost Pages (no Posts) — URL personalizable |
| Blog/guías | Ghost Posts con tag `guias` |
| Comparativas | Ghost Posts con tag `comparativas` |
| Tutoriales | Ghost Posts con tag `tutoriales` |
| Newsletters | Ghost Posts con tag `newsletter` (ya existe) |
| SEO meta | `meta_title`, `meta_description`, `og_title`, `og_description`, `canonical_url` |
| Structured data | Ghost inyecta `Article` JSON-LD automáticamente; custom con `codeinjection_head` |
| Sitemap | Ghost auto-genera `/sitemap.xml` |

### 4.4 Topic cluster model

```
                    ┌─────────────────────────┐
                    │   devaisemanal.com/      │
                    │   (Homepage + signup)    │
                    └──────────┬──────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                   │
   ┌────────▼────────┐ ┌──────▼──────┐  ┌────────▼────────┐
   │  /guias/ (hub)  │ │ /comparati- │  │ /tutoriales/    │
   │  Pillar page    │ │  vas/ (hub) │  │ (hub)           │
   └────────┬────────┘ └──────┬──────┘  └────────┬────────┘
            │                  │                   │
   ┌────────▼────────┐        │          ┌────────▼────────┐
   │ claude-code     │◄───────┼──────────│ claude-code     │
   │ cursor-ai       │        │          │ tutorial        │
   │ mcp-servers     │  ┌─────▼──────┐   │ crear-mcp      │
   │ vibe-coding     │  │ claude vs  │   │ cursor-rules   │
   │ github-copilot  │  │ cursor     │   └─────────────────┘
   └─────────────────┘  │ copilot vs │
                        │ cursor     │
                        └────────────┘
```

Cada guía/comparativa/tutorial enlaza a:
- Las newsletters relevantes donde se cubrió el tema
- Otras guías del mismo cluster
- La página hub correspondiente

---

## 5. Plan de implementación — 6 fases

### Fase 0: SEO técnico Ghost (Semana 1)

**Objetivo:** Asegurar que la infraestructura Ghost está optimizada antes de crear contenido.

#### 0.1 Auditar configuración Ghost actual

```
Verificar en Ghost Admin → Settings:
- Meta title del sitio → "DevAI — Herramientas de IA para desarrolladores, en español"
- Meta description → "Newsletter semanal sobre Claude Code, Cursor, GitHub Copilot, MCP 
  y herramientas de IA para desarrolladores. Guías, tutoriales y comparativas en español."
- Social accounts (OG defaults)
- Navigation structure (primary + secondary nav)
```

#### 0.2 Mejorar `_build_newsletter_seo()` en publishing.py

**Archivo:** `src/publishing.py`, función `_build_newsletter_seo()` (línea 69)

**Cambio:** Mejorar la generación de SEO para incluir keywords del cluster principal:

```python
def _build_newsletter_seo(config: dict, date_str: str, article_data: dict) -> dict[str, str]:
    nl_cfg = config.get("newsletter", {})
    name = nl_cfg.get("name", "DevAI")
    human_date = _format_human_date(date_str)

    items = list(article_data.get("articles", []))
    if article_data.get("repo_of_week"):
        items.append(article_data["repo_of_week"])
    topics = [_article_heading(item) for item in items]
    topics = [topic for topic in topics if topic]

    if topics:
        topic_line = ", ".join(topics[:3])
        title = _clamp(f"{name}: {topic_line} | {human_date}", 65)
        # NUEVO: description orientada a SEO con keywords del nicho
        description = _clamp(
            f"Newsletter para desarrolladores: {topic_line}. "
            "Novedades de Claude Code, Cursor, GitHub Copilot y herramientas de IA "
            "que afectan tu workflow de programación.",
            155,
        )
    else:
        title = _clamp(f"{name}: herramientas de IA para desarrolladores | {human_date}", 65)
        description = _clamp(
            "Newsletter semanal en español sobre Claude Code, Cursor, GitHub Copilot, "
            "MCP y herramientas de IA para desarrolladores.",
            155,
        )

    return {
        "title": title,
        "meta_title": title,
        "meta_description": description,
        "custom_excerpt": description,
        # NUEVO: og_title y og_description para social sharing
        "og_title": title,
        "og_description": description,
    }
```

#### 0.3 Añadir tags estructurados a newsletters

**Archivo:** `src/publishing.py`, función `_publish_ghost()` (línea 258)

**Cambio:** Asignar tags temáticos automáticamente basados en keywords detectados en el contenido:

```python
# Después de la línea 308 (tags)
# Auto-tag por contenido
AUTO_TAGS = {
    "claude code": "Claude Code",
    "cursor":      "Cursor",
    "copilot":     "GitHub Copilot",
    "mcp":         "MCP",
    "vibe coding": "Vibe Coding",
    "gemini":      "Gemini",
    "openai":      "OpenAI",
}

tags = [{"name": "Newsletter", "slug": "newsletter"}]
content_lower = html_content.lower()
for keyword, tag_name in AUTO_TAGS.items():
    if keyword in content_lower:
        tags.append({"name": tag_name, "slug": tag_name.lower().replace(" ", "-")})
```

#### 0.4 Custom `codeinjection_head` para JSON-LD mejorado

Ghost genera `Article` JSON-LD automáticamente, pero es básico. Inyectar schema enriquecido:

```python
# En _publish_ghost(), dentro del post_payload
json_ld = json.dumps({
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    "headline": title,
    "description": seo.get("meta_description", ""),
    "author": {
        "@type": "Organization",
        "name": "DevAI",
        "url": "https://devaisemanal.com"
    },
    "publisher": {
        "@type": "Organization",
        "name": "DevAI",
        "url": "https://devaisemanal.com"
    },
    "datePublished": date_str,
    "mainEntityOfPage": f"https://devaisemanal.com/newsletter-{date_str}/"
}, ensure_ascii=False)

codeinjection_head = (
    f'<script type="application/ld+json">{json_ld}</script>'
    "<style>"
    ".gh-article-header{display:none!important}"
    ".gh-article-meta{display:none!important}"
    ".gh-content.gh-canvas{padding-top:0!important}"
    ".gh-article{padding-top:0!important}"
    "</style>"
)
```

#### 0.5 Configurar navegación Ghost

```
Primary Navigation:
  Inicio       → /
  Guías        → /tag/guias/
  Comparativas → /tag/comparativas/
  Tutoriales   → /tag/tutoriales/
  Newsletter   → /tag/newsletter/

Secondary Navigation:
  Suscribirse  → /#subscribe
  Sobre DevAI  → /about/
```

**KPI Fase 0:** Todos los posts nuevos se publican con meta_title ≤65 chars, meta_description ≤155 chars, tags temáticos automáticos, JSON-LD NewsArticle.

---

### Fase 1: Contenido evergreen — Cluster Claude Code (Semanas 2-4)

**Objetivo:** Crear el content hub de Claude Code y posicionarse para el cluster de 20K búsquedas/mes.

#### 1.1 Guía pilar: "Claude Code: Guía definitiva para desarrolladores (2026)"

**URL:** `devaisemanal.com/guias/claude-code/`
**Target primary:** `claude code` (9,900 vol, KD 43)
**Target secondary:** `claude ia`, `como usar claude code`, `claude code tutorial`
**Formato:** Ghost Page (no Post) — contenido evergreen, no aparece en feed cronológico
**Longitud:** 4,000-5,000 palabras

**Estructura:**

```
H1: Claude Code: guía definitiva para desarrolladores (2026)

H2: Qué es Claude Code
  - Definición técnica (CLI agent de Anthropic)
  - Diferencia con ChatGPT/Claude web
  - Modelos disponibles (Sonnet, Opus, Haiku)

H2: Cómo instalar Claude Code
  - Requisitos previos (Node.js 18+)
  - Instalación global con npm
  - Configuración de API key
  - Primer uso: `claude` en terminal

H2: Cómo usar Claude Code — workflow completo
  - Modo interactivo vs one-shot
  - Slash commands (/init, /compact, /review)
  - Manejo de contexto (CLAUDE.md)
  - Hooks y customización

H2: Claude Code tips y trucos avanzados
  - Optimizar costes (model switching)
  - Git workflow con Claude Code
  - Multi-file editing patterns
  - Debugging con Claude Code

H2: Claude Code vs Cursor vs Copilot
  - Tabla comparativa (resumen, link a comparativa completa)

H2: Preguntas frecuentes
  - ¿Claude Code es gratis?
  - ¿Cómo hacer que Claude Code acepte todo automáticamente?
  - ¿Qué modelo usa Claude Code?
  - ¿Claude Code funciona offline?
  - ¿Es seguro dar acceso a mi código?

CTA: Suscríbete a DevAI para recibir tips semanales de Claude Code →
```

**SEO meta:**
```
meta_title: "Claude Code: Guía Definitiva para Desarrolladores (2026)"
meta_description: "Aprende a usar Claude Code desde cero. Instalación, workflow, tips avanzados, hooks y comparativa con Cursor y Copilot. Guía en español actualizada."
```

**Internal links desde esta guía:**
- → Comparativa Claude Code vs Cursor
- → Tutorial: crear tu primer MCP server
- → Newsletters que mencionan Claude Code (tag page)

#### 1.2 Artículo satélite: "Cómo hacer que Claude Code acepte todo automáticamente"

**URL:** `devaisemanal.com/tutoriales/claude-code-aceptar-automaticamente/`
**Target:** `como hacer que claude code acepte todo automaticamente` (210 vol, KD ~5)
**Formato:** Ghost Post, tags: `tutoriales`, `claude-code`
**Longitud:** 1,500-2,000 palabras

**Razón:** Keyword con intención exacta, competencia prácticamente nula en español, alto CTR esperado.

#### 1.3 Artículo satélite: "Claude Code Hooks: automatiza tu workflow de desarrollo"

**URL:** `devaisemanal.com/tutoriales/claude-code-hooks/`
**Target:** `claude code hooks` (210 vol, KD 18)
**Formato:** Ghost Post, tags: `tutoriales`, `claude-code`
**Longitud:** 2,000-2,500 palabras

#### 1.4 Artículo satélite: "Claude Sonnet vs Opus vs Haiku: cuál usar y cuándo"

**URL:** `devaisemanal.com/comparativas/claude-sonnet-opus-haiku/`
**Target:** `claude sonnet` (1,900 vol, KD 23)
**Formato:** Ghost Post, tags: `comparativas`, `claude-code`
**Longitud:** 2,000-2,500 palabras

**KPI Fase 1:** Guía pilar publicada + 3 satélites. Meta: indexación completa en 2 semanas, primeras impresiones GSC para "claude code" en 30 días.

---

### Fase 2: Cluster Cursor AI + Comparativas (Semanas 4-6)

**Objetivo:** Capitalizar el ranking #20 existente para "cursor ai" y subir a top 10.

#### 2.1 Guía pilar: "Cursor AI: guía completa del editor con inteligencia artificial"

**URL:** `devaisemanal.com/guias/cursor-ai/`
**Target:** `cursor ai` (8,100 vol, KD 71) — actualmente #20
**Formato:** Ghost Page
**Longitud:** 3,500-4,500 palabras

**Estructura:**
```
H1: Cursor AI: guía completa del editor con IA para programadores

H2: Qué es Cursor (y por qué reemplaza a VS Code)
H2: Cursor AI: instalación y primeros pasos
H2: Cursor Rules: configura tu IA personalizada
H2: Features clave: Tab, Composer, Chat, Agent
H2: Cursor AI gratis vs Pro vs Business
H2: Tips avanzados para Cursor
H2: Cursor vs Copilot vs Claude Code
H2: FAQ
```

#### 2.2 Comparativa: "Claude Code vs Cursor: cuál elegir en 2026"

**URL:** `devaisemanal.com/comparativas/claude-code-vs-cursor/`
**Target:** `claude code vs cursor` (390 vol, KD 31)
**Formato:** Ghost Post, tags: `comparativas`, `claude-code`, `cursor`
**Longitud:** 2,500-3,000 palabras

**Estructura con tabla comparativa SEO-friendly:**
```
| Característica | Claude Code | Cursor |
|---------------|:-----------:|:------:|
| Interfaz | Terminal CLI | IDE completo |
| Modelo base | Claude (Sonnet/Opus) | Multi (GPT-4, Claude, etc.) |
| Precio | Por uso API | $20/mes Pro |
| Multi-file editing | ✅ Nativo | ✅ Composer |
| ...
```

#### 2.3 Guía: "Cursor Rules: la guía definitiva para configurar tu IA"

**URL:** `devaisemanal.com/tutoriales/cursor-rules-guia/`
**Target:** `cursor rules` (480 vol, KD 35)
**Longitud:** 2,000-2,500 palabras

#### 2.4 Listicle: "Mejor IA para programar en 2026: ranking completo"

**URL:** `devaisemanal.com/comparativas/mejor-ia-programar/`
**Targets:** `mejor ia para programar` (880 vol), `ia para programar` (720 vol)
**Longitud:** 3,000-3,500 palabras

**KPI Fase 2:** Posición "cursor ai" sube de #20 a #10-15. Guía pilar + 3 satélites publicados. Primeras impresiones para "cursor rules", "mejor ia para programar".

---

### Fase 3: Cluster MCP (Semanas 6-8)

**Objetivo:** Dominar el espacio MCP en español — prácticamente sin competencia.

#### 3.1 Guía pilar: "MCP (Model Context Protocol): guía completa para desarrolladores"

**URL:** `devaisemanal.com/guias/mcp-servers/`
**Target:** `mcp` (8,100 vol, KD 55), `mcp servers` (1,600 vol, KD 55)
**Formato:** Ghost Page
**Longitud:** 4,000-5,000 palabras

**Nota:** El keyword "mcp" es ambiguo (también puede referirse a otros significados). La guía debe establecer contexto IA rápidamente para capturar el tráfico correcto.

```
H1: MCP (Model Context Protocol): guía completa para desarrolladores

H2: Qué es MCP y por qué importa
  - Model Context Protocol explicado para developers
  - Analogía: "USB-C para herramientas de IA"
  - Quién lo creó (Anthropic) y quién lo adopta

H2: Arquitectura MCP: servidores, clientes, transporte
H2: Cómo usar MCP servers con Claude Code
H2: Cómo crear tu propio MCP server (tutorial)
H2: Los mejores MCP servers en 2026
H2: MCP vs function calling vs plugins
H2: FAQ: qué es MCP, cómo funciona, es gratis
```

#### 3.2 Tutorial: "Cómo crear un MCP server desde cero"

**URL:** `devaisemanal.com/tutoriales/crear-mcp-server/`
**Target:** `crear mcp server` (110 vol, KD 18), `mcp server tutorial` (170 vol, KD 25)
**Longitud:** 3,000-3,500 palabras con code blocks

#### 3.3 Explicación: "MCP: qué es el Model Context Protocol y cómo cambia la IA"

**URL:** `devaisemanal.com/guias/mcp-que-es/`
**Target:** `mcp que es` (320 vol, KD 22)
**Longitud:** 1,500-2,000 palabras

**KPI Fase 3:** 3 posts MCP publicados. Meta: rankear top 20 para "mcp servers" en 60 días. Posición "mcp" sube de #51 a #30.

---

### Fase 4: Cluster Vibe Coding + Prompts (Semanas 8-10)

#### 4.1 Guía: "Vibe Coding: qué es y cómo programar con IA en 2026"

**URL:** `devaisemanal.com/guias/vibe-coding/`
**Target:** `vibe coding` (6,600 vol, KD 45)
**Longitud:** 3,000-3,500 palabras

#### 4.2 Guía: "Ingeniería de Prompts para desarrolladores: guía práctica"

**URL:** `devaisemanal.com/guias/ingenieria-de-prompts/`
**Target:** `ingenieria de prompts` (260 vol, KD 31), `prompts chatgpt` (1,000 vol, KD 37)
**Longitud:** 3,000-3,500 palabras

#### 4.3 Listicle: "Los mejores prompts para programar con IA en 2026"

**URL:** `devaisemanal.com/tutoriales/mejores-prompts-programacion/`
**Target:** `mejores prompts programacion` (210 vol, KD 22)
**Longitud:** 2,500-3,000 palabras con ejemplos copy-paste

**KPI Fase 4:** 3 posts publicados. Primeras impresiones GSC para "vibe coding" en 30 días.

---

### Fase 5: Contenido programático + Internal linking (Semanas 10-12)

#### 5.1 Script de auto-linking en newsletters

**Concepto:** Cuando el pipeline publica una newsletter que menciona "Claude Code", el sistema automáticamente convierte la primera mención en un link a `/guias/claude-code/`.

**Archivo nuevo:** `src/internal_linking.py`

```python
"""Auto-inject internal links from newsletters to evergreen guides."""

import re
from typing import dict

# Map keywords to their canonical guide URLs
INTERNAL_LINKS: dict[str, str] = {
    "Claude Code":     "/guias/claude-code/",
    "Cursor":          "/guias/cursor-ai/",
    "MCP":             "/guias/mcp-servers/",
    "GitHub Copilot":  "/guias/github-copilot/",
    "vibe coding":     "/guias/vibe-coding/",
}

def inject_internal_links(html: str, base_url: str = "https://devaisemanal.com") -> str:
    """Replace first occurrence of each keyword with a link to the guide.
    
    Only replaces text NOT already inside an <a> tag.
    """
    for keyword, path in INTERNAL_LINKS.items():
        # Skip if keyword is already linked
        pattern = re.compile(
            rf'(?<!<a[^>]*>)(?<!/)\b({re.escape(keyword)})\b(?![^<]*</a>)',
            re.IGNORECASE,
        )
        url = f"{base_url}{path}"
        html = pattern.sub(
            rf'<a href="{url}" title="Guía de {keyword}">\1</a>',
            html,
            count=1,  # Only first occurrence
        )
    return html
```

**Integración en `publishing.py`:**
```python
# En _publish_ghost(), antes de crear el mobiledoc
from .internal_linking import inject_internal_links
email_body = inject_internal_links(email_body)
```

#### 5.2 Archivo de newsletter con buscador

**URL:** `devaisemanal.com/archivo/`
**Tipo:** Ghost Page con listado dinámico de todas las ediciones
**SEO value:** Genera internal links a TODAS las newsletters, mejora crawlability

#### 5.3 Página "Sobre DevAI"

**URL:** `devaisemanal.com/about/`
**Tipo:** Ghost Page
**Propósito:** E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness)

```
H1: Sobre DevAI

Quiénes somos, por qué creamos la newsletter, credenciales del equipo.
Links a perfiles LinkedIn/GitHub.
Mención de herramientas que usamos (build credibility).
```

**KPI Fase 5:** Internal linking automático activo. Página about publicada. Archivo de newsletters navegable.

---

### Fase 6: Growth loop — Newsletter ↔ SEO (Continuo)

#### 6.1 Optimizar `seo_intelligence.py` para content calendar

**Concepto actual:** `seo_intelligence.py` hace gap analysis (queries GSC vs posts Ghost).

**Mejora propuesta:** Que el gap analysis también sugiera qué guías evergreen actualizar o crear basado en queries emergentes.

```python
# Pseudo-código para run_seo.py mejorado
def suggest_content_actions(gsc_queries, existing_guides):
    """
    Para cada query GSC con impresiones altas pero sin guía evergreen:
    - Si vol > 500 y no hay guía → CREAR nueva guía
    - Si ya hay guía pero posición > 15 → ACTUALIZAR guía existente
    - Si posición 5-15 → LINK desde próxima newsletter
    """
    pass
```

#### 6.2 Flywheel newsletter → SEO → newsletter

```
Newsletter semanal
    ↓ menciona Claude Code
    ↓ auto-link a /guias/claude-code/
    ↓ genera backlinks internos
    ↓
Guía evergreen sube en Google
    ↓ tráfico orgánico llega
    ↓ CTA: suscríbete a DevAI
    ↓ nuevo suscriptor
    ↓
Más suscriptores → más shares → más backlinks
    ↓
Newsletter tiene más autoridad
    ↓ (repite)
```

#### 6.3 Feature images únicas por guía

Reemplazar la imagen Unsplash genérica (`_NEWSLETTER_FEATURE_IMAGE`) con imágenes específicas por guía:

- OG image con logo de la herramienta + "Guía DevAI"
- Tamaño 1200x628px (estándar OG)
- Cada guía con su propia imagen para CTR en SERPs

**KPI Fase 6:** GSC muestra crecimiento mes a mes en impresiones y clics. Ratio newsletter→guía (clicks internos) > 5%. Al menos 2 guías actualizadas/mes basado en datos GSC.

---

## 6. Publicación de contenido — Métodos

### 6.1 Ghost Admin API (para contenido programático)

El pipeline ya tiene integración Ghost Admin API funcional en `publishing.py`. Se puede reutilizar para publicar guías:

```python
# Ejemplo: publicar guía como Ghost Page
def publish_guide(title, slug, html_content, meta_title, meta_description, tags):
    """Publish an evergreen guide as a Ghost Page."""
    mobiledoc = json.dumps({
        "version": "0.3.1",
        "atoms": [],
        "cards": [["html", {"html": html_content}]],
        "markups": [],
        "sections": [[10, 0]],
    })
    
    post_payload = {
        "pages": [{  # "pages" en lugar de "posts" para Ghost Pages
            "title": title,
            "slug": slug,
            "status": "published",
            "mobiledoc": mobiledoc,
            "meta_title": meta_title,
            "meta_description": meta_description,
            "tags": [{"name": t} for t in tags],
        }]
    }
    
    token = _ghost_jwt(admin_api_key)
    # POST a /ghost/api/admin/pages/ (no /posts/)
    resp = client.post(f"{ghost_url}/ghost/api/admin/pages/", ...)
```

### 6.2 Ghost Admin UI (para contenido editorial)

Para guías largas que necesitan revisión humana, usar el editor Ghost directamente:
1. Abrir Ghost Admin (`devaisemanal.com/ghost/`)
2. Crear nueva Page (no Post)
3. Escribir contenido con el editor
4. Configurar SEO meta en Settings panel
5. Publicar

### 6.3 Script helper para bulk publishing

**Archivo nuevo:** `publish_guides.py`

```python
"""Publish pre-written guides to Ghost CMS."""
import json
from pathlib import Path
from src.publishing import _ghost_jwt, _rl

GUIDES_DIR = Path("guides/")  # Directorio con guías en formato JSON

def publish_all_guides():
    for guide_file in GUIDES_DIR.glob("*.json"):
        guide = json.loads(guide_file.read_text())
        # publish_guide(guide["title"], guide["slug"], ...)
        print(f"Published: {guide['slug']}")
```

---

## 7. Priorización y timeline

| Semana | Fase | Entregable | Impacto esperado |
|:------:|:----:|-----------|-----------------|
| 1 | F0 | SEO técnico Ghost + mejoras publishing.py | Base técnica |
| 2-3 | F1 | Guía Claude Code + 3 satélites | 20K vol cluster |
| 4-5 | F2 | Guía Cursor + comparativas | 14K vol cluster + mejorar #20 actual |
| 6-7 | F3 | Guía MCP + tutoriales | 10K vol cluster |
| 8-9 | F4 | Vibe Coding + Prompts | 10K vol cluster |
| 10-11 | F5 | Internal linking + archivo | Multiplicador SEO |
| 12+ | F6 | Growth loop continuo | Compound growth |

### Quick wins (hacer AHORA)

1. **Mejorar `_build_newsletter_seo()`** — 30 min de código, impacto inmediato en todos los posts futuros
2. **Auto-tagging en `_publish_ghost()`** — 20 min, estructura todos los posts por tema
3. **Publicar guía Claude Code** — es el 80/20, un solo post puede traer miles de visitas/mes
4. **Configurar navegación Ghost** — 5 min en Ghost Admin, mejora UX y crawlability

### Apuesta principal

**Claude Code es EL keyword para DevAI Semanal:**
- 9,900 búsquedas/mes en España
- KD 43 (alcanzable para sitios nicho)
- nocodehackers.es ya demostró que un sitio pequeño puede rankear #3
- DevAI tiene más autoridad temática (newsletter semanal que cubre Claude Code cada semana)
- Competencia 0.12 — espacio abierto
- Perfectamente alineado con el posicionamiento del newsletter

Si DevAI rankea top 5 para "claude code", eso solo puede generar **500-1,500 visitas/mes** a la guía, cada una con CTA de suscripción. Con conversión del 3-5%, eso son **15-75 nuevos suscriptores/mes** solo de SEO orgánico.

---

## 8. KPIs y medición

### Métricas SEO (medir en GSC + Semrush)

| KPI | Baseline (May 2026) | Target 3 meses | Target 6 meses |
|-----|:---:|:---:|:---:|
| Keywords orgánicas | 12 | 80+ | 200+ |
| Tráfico orgánico/mes | ~2 | 500+ | 2,000+ |
| Posición "claude code" | No rankea | Top 20 | Top 10 |
| Posición "cursor ai" | #20 | #12 | #8 |
| Posición "mcp" | #51 | #30 | #15 |
| Impresiones GSC/mes | ~200 | 5,000+ | 20,000+ |
| CTR medio GSC | ~1% | 3%+ | 5%+ |
| Páginas indexadas | ~20 | 35+ | 50+ |

### Métricas de negocio

| KPI | Baseline | Target 3 meses | Target 6 meses |
|-----|:---:|:---:|:---:|
| Suscriptores newsletter (via SEO) | 0 | 50+ | 200+ |
| Conversion rate guía→suscriptor | — | 3%+ | 5%+ |
| Pageviews guías/mes | 0 | 1,000+ | 5,000+ |
| Internal link clicks (newsletter→guía) | 0 | 100+/mes | 500+/mes |

### Herramientas de medición

| Herramienta | Qué mide | Ya configurada |
|-------------|----------|:-:|
| Google Search Console | Impresiones, clics, posiciones, CTR | ✅ Sí (`seo_intelligence.py`) |
| Semrush | Keywords, tráfico estimado, backlinks | ✅ Sí (via MCP) |
| Ghost Analytics | Pageviews, member signups | ✅ Built-in |
| MailerLite | Open rate, click rate, subscribers | ✅ Sí |

---

## 9. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|:-:|:-:|-----------|
| Ghost no permite URL structure `/guias/slug/` | Media | Alto | Usar tags como proxy (`/tag/guias/`) o subdirectorios Ghost routes |
| Contenido IA detectado como low-quality | Baja | Alto | Todas las guías requieren edición humana + experiencia real |
| nocodehackers.es publica guía Claude Code mejorada | Alta | Medio | Publicar primero, actualizar frecuentemente, diferenciarse con perspectiva developer |
| Google penaliza thin content de newsletters | Baja | Alto | Newsletters ya tienen contenido sustancial; guías evergreen son el foco |
| API costs de Claude para generar guías | Baja | Bajo | Presupuesto ~$5-10 por guía larga |

---

## Resumen ejecutivo

**DevAI Semanal tiene un posicionamiento único:** es la única newsletter española de IA exclusivamente para desarrolladores. Pero su tráfico orgánico es casi cero porque todo el contenido son newsletters semanales sin keyword targeting.

**La estrategia es simple:**
1. Mantener las newsletters semanales como motor de contenido fresco
2. Crear **guías evergreen** optimizadas para los keywords de mayor volumen
3. Conectar ambos con **internal linking automático**
4. Usar el **flywheel** newsletter↔SEO para crecimiento compuesto

**El primer paso es publicar UNA guía sobre Claude Code.** Eso solo puede capturar miles de visitas/mes de un keyword que hoy nadie domina en español para developers.

Tráfico potencial total de todos los clusters: **~72,000 búsquedas/mes**. Con posicionamiento top 10 en los principales, el target realista a 6 meses es **2,000+ visitas orgánicas/mes** — desde una base actual de 2 visitas/mes.
