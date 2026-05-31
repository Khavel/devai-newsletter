---
title: "Cómo automaticé una newsletter de IA para developers con Claude API y GitHub Actions"
published: false
description: "Pipeline completo que recoge noticias, las cura con IA, las redacta en español y las publica sola cada semana. Open source."
tags: ai, python, automation, newsletter
cover_image: https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=1200&h=628&fit=crop&q=80
canonical_url: https://devaisemanal.com/como-automatice-newsletter-ia-developers/
---

## El problema: no existía una newsletter de AI dev tools en español con profundidad real

Hace unos meses me di cuenta de algo: consumía entre 15 y 20 fuentes distintas cada semana para estar al día con herramientas de IA para desarrollo. Blogs de Anthropic, OpenAI, GitHub, hilos de Reddit, repos trending... y todo en inglés. Cuando quería compartir algo relevante con colegas hispanohablantes, terminaba explicando las cosas desde cero.

Pensé: "debería existir una newsletter semanal que haga este filtrado por mí, en español, con contexto real para devs". Busqué y no encontré nada que me convenciera. Así que hice lo que cualquier desarrollador haría: la automaticé entera.

El resultado es [DevAI Semanal](https://devaisemanal.com), una newsletter que se genera, publica y envía completamente sola cada martes a las 9:00h (hora española). Sin intervención manual. El pipeline es open source y puedes verlo en [github.com/Khavel/devai-newsletter](https://github.com/Khavel/devai-newsletter).

Voy a explicar cómo funciona paso a paso.

---

## Arquitectura general

El pipeline tiene 5 fases secuenciales que se ejecutan en un único workflow de GitHub Actions:

```
Martes 9:00h -- GitHub Actions arranca el pipeline
      |
      v
[1] Sourcing     -- Recoge noticias de RSS, Hacker News, Reddit, GitHub Trending
      |
      v
[2] Curation     -- Claude selecciona los 5-7 mejores items de la semana
      |
      v
[3] Rewriting    -- Claude redacta cada noticia en español con contexto
      |
      v
[4] Assembly     -- Renderiza el HTML del newsletter (email-ready)
      |
      v
[5] Publishing   -- Publica en Ghost (web) + envía por MailerLite (email)
      |
      v
Telegram         -- Notificación con las URLs del resultado
```

Cada fase genera un JSON intermedio en `data/` con la fecha del día. Si el pipeline se interrumpe a mitad, al relanzarlo detecta qué archivos ya existen y salta las fases completadas. Esto es clave y lo explico más abajo.

---

## Fase 1: Sourcing -- recoger las noticias

La primera fase recorre todas las fuentes configuradas en `config.yaml` y guarda los items crudos. Las fuentes son:

- **RSS**: Anthropic, OpenAI, Google AI, GitHub, Microsoft AI, VS Code
- **Hacker News**: keywords como `claude code`, `cursor ai`, `mcp server`, `agentic`...
- **Reddit**: r/ClaudeAI, r/cursor, r/LocalLLaMA, r/ChatGPTPro
- **GitHub Trending**: topics `ai-coding`, `developer-tools`, `llm`, `mcp`

Todo está parametrizado en un YAML, no en código. Añadir una fuente nueva es editar un fichero:

```yaml
sources:
  rss:
    - url: "https://blog.anthropic.com/rss"
      name: "Anthropic"
  hackernews:
    keywords:
      - "claude code"
      - "mcp server"
    min_score: 50
  reddit:
    subreddits:
      - "ClaudeAI"
    min_upvotes: 100
```

Un detalle importante: hay un `RateLimiter` compartido que limita a 0.5 peticiones por segundo. Parece lento, pero cuando estás llamando a APIs de Reddit y Hacker News desde una GitHub Action, lo último que quieres es que te baneen la IP.

```python
_rl = RateLimiter(calls_per_second=0.5)
```

El output es un JSON con 40-80 items crudos con título, URL, fuente y fecha.

---

## Fase 2: Curation -- Claude como editor jefe

Aquí es donde la IA entra en juego. Los 40-80 items crudos se envían a Claude (actualmente `claude-sonnet-4-20250514`) con un system prompt que define los criterios editoriales:

```python
SYSTEM_PROMPT = """\
Eres el editor de una newsletter técnica sobre AI developer tools en español.
Tu audiencia son desarrolladores que usan herramientas como Claude Code, Cursor,
Copilot, Cline, y MCP servers en su día a día.

Selecciona los 6-8 más relevantes. Prioriza:
1. Lanzamientos y updates de herramientas de coding con IA
2. Comparativas y benchmarks entre herramientas
3. Nuevos MCP servers, plugins, o integraciones útiles
4. Técnicas y workflows de agentic coding aplicables hoy
5. Repos de GitHub trending que sean herramientas prácticas

Descarta: noticias de IA genérica sin impacto directo en devs,
papers académicos sin aplicación práctica, rumores sin confirmar."""
```

Claude devuelve un JSON con los items seleccionados, rankeados por relevancia, con una razón de por qué cada uno importa. Si alguna vez has intentado que un LLM actúe como filtro editorial, sabrás que el system prompt es donde se gana o se pierde la partida. Me llevó varias iteraciones afinar los criterios para que no colara noticias género "OpenAI recauda X millones" y priorizara cosas que un dev puede usar hoy.

Si te interesa cómo aplico estos flujos con Claude en otros contextos, tengo una [guía práctica sobre Claude Code](https://devaisemanal.com/guias-claude-code/) donde entro más en detalle.

---

## Fase 3: Rewriting -- redacción con personalidad

Los items curados se envían uno a uno a Claude para que los reescriba en español. Pero no es una traducción: es una reescritura completa con opinión y contexto práctico.

El prompt es bastante opinionado:

```python
ARTICLE_SYSTEM = """\
Eres un desarrollador español que escribe una newsletter técnica semanal. Tu tono es:
- Directo y sin bullshit corporativo
- Técnico pero accesible
- Opinionado -- no tienes miedo de decir si algo es bueno o malo
- NUNCA uses frases como "en el vertiginoso mundo de la IA"
- NUNCA copies texto del artículo original, reescribe completamente"""
```

Cada artículo debe tener entre 80 y 120 palabras: lo suficiente para dar contexto sin que el lector pierda interés. El resultado es un párrafo que explica qué pasó, por qué importa, y qué puede hacer el lector con esa información. Todo en formato Markdown listo para renderizar.

---

## Fase 4: Assembly -- HTML para email (que no es lo mismo que HTML para web)

Esta fue la fase que más dolores de cabeza me dio. Renderizar HTML para email no tiene nada que ver con HTML para web. No hay Flexbox, no hay Grid, y cada cliente de correo interpreta el CSS como le da la gana.

El módulo `assembly.py` toma los artículos en Markdown y los renderiza en una plantilla HTML con CSS inline (sí, todo inline -- es la única forma de que Gmail no te destroce el layout). El output es un fichero `.html` listo para inyectar en MailerLite.

Aquí hay un truco que me costó encontrar: el mismo HTML se publica en Ghost como archivo web, pero necesita ajustes. En Ghost el HTML va dentro de una `html card` de Mobiledoc, se extrae solo el contenido del `<body>`, y se inyecta CSS custom por post para ocultar el chrome de Ghost y que parezca una página independiente. Si visitas cualquier edición en [devaisemanal.com](https://devaisemanal.com) verás que las newsletters parecen páginas propias, no posts de un blog genérico.

---

## Fase 5: Publishing -- Ghost + MailerLite + Telegram

La fase final hace tres cosas:

1. **Ghost CMS**: Publica el newsletter como post en Ghost (que corre en Fly.io, región Paris). Esto crea el archivo web con URLs permanentes, SEO metadata automática (`meta_title`, `meta_description`, `custom_excerpt`), y el sistema de suscripción.

2. **MailerLite**: Crea una campaña con el HTML del email. Si `MAILERLITE_GROUP_ID` está configurado, la envía automáticamente a todos los suscriptores. Si no, la deja como borrador.

3. **Telegram**: Envía una notificación al chat configurado con los enlaces al post publicado y la campaña de email, incluyendo UTM params para tracking.

---

## Automatización: GitHub Actions como scheduler

Todo corre en un workflow de GitHub Actions programado para los martes a las 07:00 UTC (09:00 hora española):

```yaml
on:
  schedule:
    - cron: '0 7 * * 2'
  workflow_dispatch:
    inputs:
      mode:
        type: choice
        options:
          - draft
          - preview
```

El `workflow_dispatch` permite lanzar el pipeline manualmente desde la interfaz de GitHub si necesito generar una edición fuera de horario. Los secrets (API keys de Anthropic, Ghost, MailerLite, Telegram) están en GitHub Secrets, y el workflow los pasa como variables de entorno.

El timeout es de 20 minutos. En la práctica, una ejecución completa tarda entre 3 y 6 minutos dependiendo de cuántos items haya que procesar.

---

## Lecciones aprendidas

### Idempotencia por encima de todo

Cada fase guarda su output como `{fase}_{fecha}.json` en el directorio `data/`. Antes de ejecutar, comprueba si el fichero del día ya existe. Si existe, salta esa fase. Esto significa que si GitHub Actions falla a mitad (timeout, error de red, rate limit), puedo relanzar el workflow y continúa exactamente donde se quedó.

En pipelines que dependen de APIs externas, la idempotencia no es un nice-to-have: es la diferencia entre un sistema que funciona y uno que te obliga a intervenir cada semana.

### Rate limiting defensivo

Todas las llamadas externas pasan por un `RateLimiter` que controla las peticiones por segundo. Para RSS y APIs públicas uso 0.5 req/s, para Claude 1 req/s. Parece conservador, pero en meses de ejecución automática no he tenido un solo ban ni rate limit.

### HTML de email vs HTML de web

Si nunca has hecho email HTML, prepárate para sufrir. Outlook ignora `margin`, Gmail elimina etiquetas `<style>` del `<head>`, y Yahoo hace cosas que no tienen explicación racional. La solución: CSS 100% inline, tablas para layout (sí, como en 2005), y testing con Litmus o Email on Acid antes de automatizar la plantilla.

### El tono del prompt importa más de lo que crees

Invertir tiempo en el system prompt de rewriting fue lo que más impacto tuvo en la calidad. La diferencia entre "reescribe esto en español" y un prompt que define tono, longitud, estructura y prohibiciones explícitas es abismal. Si usas LLMs para generar contenido, trata el prompt como código: versiónalo, itéralo, y testea cada cambio.

Si trabajas con [MCP servers](https://devaisemanal.com/guias-mcp-servers/) y herramientas de IA para desarrollo, este tipo de integraciones son cada vez más accesibles.

---

## Resultados

El pipeline lleva meses funcionando sin intervención manual. Cada martes a las 9:00h los suscriptores de [DevAI Semanal](https://devaisemanal.com) reciben su edición con las 5-7 noticias más relevantes de la semana sobre AI dev tools, redactadas en español con contexto real.

Lo que más me sorprendió fue que el formato funciona: noticias filtradas por un LLM con criterios editoriales estrictos resultan más útiles que un dump de 20 links sin contexto. La tasa de apertura se mantiene consistentemente alta, lo cual sugiere que los lectores encuentran valor real en cada edición.

El coste por edición es mínimo: un par de llamadas a Claude API (céntimos) y la ejecución gratuita de GitHub Actions.

---

## Pruébalo tú mismo

El código completo está en [github.com/Khavel/devai-newsletter](https://github.com/Khavel/devai-newsletter). Es open source, documentado, y puedes adaptarlo a tu propio nicho. Solo necesitas una API key de Anthropic para empezar.

Si prefieres simplemente recibir el resultado final cada martes, suscríbete gratis en **[devaisemanal.com](https://devaisemanal.com)**. Sin spam, sin relleno, solo las noticias de AI dev tools que importan.

Y si tienes preguntas o sugerencias, me encuentras como [@Khavel](https://github.com/Khavel) en GitHub.

---

*Alejandro Oceja -- creador de [DevAI Semanal](https://devaisemanal.com)*
