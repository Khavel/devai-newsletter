"""Publish evergreen SEO articles derived from newsletter research."""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import time
from html import escape
from pathlib import Path

import httpx
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
GHOST_URL = "https://devaisemanal.com"

CTA_HTML = """<div style="background:#f0f9ff;border:2px solid #0ea5e9;border-radius:12px;padding:32px;margin:40px 0;text-align:center;font-family:system-ui,sans-serif;">
  <p style="font-size:20px;font-weight:700;margin:0 0 8px;color:#0c4a6e;">Recibe una lectura semanal de herramientas IA para devs</p>
  <p style="font-size:15px;color:#374151;margin:0 0 24px;line-height:1.6;">Cada martes: Claude Code, Cursor, Copilot, MCP, agentes y herramientas nuevas. En español y sin ruido.</p>
  <a href="https://devaisemanal.com/#/portal/signup" style="display:inline-block;background:#0ea5e9;color:#fff;font-weight:600;padding:13px 32px;border-radius:8px;text-decoration:none;font-size:16px;">Suscribirme gratis</a>
</div>"""


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def ghost_jwt(admin_api_key: str) -> str:
    key_id, secret = admin_api_key.split(":", 1)
    header = {"alg": "HS256", "typ": "JWT", "kid": key_id}
    now = int(time.time())
    payload = {"iat": now, "exp": now + 5 * 60, "aud": "/admin/"}
    body = f"{_b64url(json.dumps(header, separators=(',', ':')).encode())}.{_b64url(json.dumps(payload, separators=(',', ':')).encode())}"
    sig = hmac.new(bytes.fromhex(secret), body.encode(), hashlib.sha256).digest()
    return f"{body}.{_b64url(sig)}"


def headers(admin_api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Ghost {ghost_jwt(admin_api_key)}",
        "Content-Type": "application/json",
        "Accept-Version": "v5.0",
    }


def text_node(text: str) -> dict:
    return {
        "type": "text",
        "version": 1,
        "text": text,
        "format": 0,
        "style": "",
        "detail": 0,
        "mode": "normal",
    }


def paragraph(text: str) -> dict:
    return {
        "type": "paragraph",
        "version": 1,
        "format": "",
        "indent": 0,
        "direction": "ltr",
        "children": [text_node(text)],
    }


def heading(text: str, tag: str = "h2") -> dict:
    return {
        "type": "heading",
        "version": 1,
        "tag": tag,
        "format": "",
        "indent": 0,
        "direction": "ltr",
        "children": [text_node(text)],
    }


def bullet_list(items: list[str]) -> dict:
    return {
        "type": "list",
        "version": 1,
        "listType": "bullet",
        "start": 1,
        "tag": "ul",
        "format": "",
        "indent": 0,
        "direction": "ltr",
        "children": [
            {
                "type": "listitem",
                "version": 1,
                "value": i + 1,
                "checked": False,
                "format": "",
                "indent": 0,
                "direction": "ltr",
                "children": [text_node(item)],
            }
            for i, item in enumerate(items)
        ],
    }


def html_card(html: str) -> dict:
    return {"type": "html", "version": 1, "html": html}


def build_lexical(nodes: list[dict]) -> str:
    return json.dumps(
        {
            "root": {
                "children": nodes,
                "direction": "ltr",
                "format": "",
                "indent": 0,
                "type": "root",
                "version": 1,
            }
        },
        ensure_ascii=False,
    )


def sources_card(sources: list[tuple[str, str]]) -> dict:
    links = "".join(
        f'<li><a href="{url}" rel="nofollow noopener" target="_blank">{label}</a></li>'
        for label, url in sources
    )
    return html_card(
        f"""<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:20px;margin:32px 0;font-family:system-ui,sans-serif;">
  <p style="font-size:13px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:.04em;margin:0 0 12px;">Fuentes y referencias</p>
  <ul style="margin:0;padding-left:20px;color:#334155;line-height:1.7;font-size:14px;">{links}</ul>
</div>"""
    )


def related_card(items: list[tuple[str, str]]) -> dict:
    links = "".join(
        f'<a href="https://devaisemanal.com{url}" style="display:block;padding:12px 16px;background:#fff;border:1px solid #e2e8f0;border-radius:8px;text-decoration:none;color:#1e293b;font-weight:500;font-size:14px;margin-bottom:8px;">{title}</a>'
        for title, url in items
    )
    return html_card(
        f"""<div style="margin:40px 0;font-family:system-ui,sans-serif;">
  <p style="font-size:13px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:.04em;margin:0 0 12px;">También te puede interesar</p>
  {links}
</div>"""
    )


ARTICLES = [
    {
        "title": "GitHub Copilot: qué cambia con los AI Credits y el pago por uso",
        "slug": "github-copilot-ai-credits-pago-por-uso",
        "meta_description": "Guía para entender los AI Credits de GitHub Copilot, las premium requests y cómo controlar el coste de usar IA para programar.",
        "excerpt": "GitHub Copilot se mueve hacia un modelo más ligado al consumo. Esta guía explica qué mirar para evitar sorpresas de coste.",
        "sources": [
            ("Planes y precios de GitHub Copilot", "https://github.com/features/copilot/plans"),
            ("Modelos y pricing de Copilot", "https://docs.github.com/copilot/reference/copilot-billing/models-and-pricing"),
            ("Changelog de Copilot consumptive billing", "https://github.blog/changelog/2025-06-18-update-to-github-copilot-consumptive-billing-experience"),
        ],
        "related": [
            ("GitHub Copilot: guía completa para desarrolladores", "/github-copilot-guia-completa/"),
            ("Cursor AI: qué es y cómo usarlo", "/cursor-ai-que-es-guia-completa/"),
        ],
        "sections": [
            ("Por qué importa", [
                "Copilot empezó como una suscripción fácil de entender: pagabas una cuota y usabas autocompletado, chat y ayuda contextual. El problema es que las funciones más potentes ya no se parecen a un simple autocomplete. Agent mode, code review, modelos premium y tareas multiarchivo tienen costes de inferencia mucho más altos.",
                "Por eso GitHub está empujando el producto hacia unidades de consumo: premium requests o AI Credits, según el plan y el momento de facturación. Para un desarrollador individual puede parecer un detalle menor. Para un equipo con decenas de usuarios, cambia cómo se presupuestan las herramientas de IA.",
            ]),
            ("Qué son los AI Credits", [
                "Los AI Credits son la forma de expresar cuánto uso de modelos y funciones avanzadas estás consumiendo. No todo gasta igual: una sugerencia inline pequeña no tiene el mismo coste que pedir a un agente que revise un pull request completo, razone sobre varios archivos y proponga cambios.",
                "La lectura práctica es sencilla: Copilot deja de ser solo una herramienta de productividad y empieza a comportarse como infraestructura de IA. Si el equipo no mide el uso, el coste queda escondido hasta que llega la factura.",
            ]),
            ("Funciones que conviene vigilar", [
                "Code review automático en pull requests, porque puede ejecutarse muchas veces al día sin que parezca una interacción manual.",
                "Agent mode y tareas multiarchivo, porque suelen consumir más contexto y más salida del modelo.",
                "Modelos premium, porque pueden tener multiplicadores o unidades de consumo superiores al modelo base.",
                "Uso en repositorios grandes, donde cada petición puede arrastrar más contexto del necesario.",
            ]),
            ("Cómo controlar el coste", [
                "Define cuándo se permite usar Copilot para code review y cuándo basta con revisión humana normal.",
                "Mide cuántos pull requests se abren por semana y cuántas veces se invoca revisión automática.",
                "Crea una política simple para modelos premium: cuándo aportan valor y cuándo son overkill.",
                "Revisa el dashboard de facturación después de cada cambio de plan, no al final del trimestre.",
            ]),
            ("Conclusión", [
                "Copilot sigue siendo útil, pero ya no conviene tratarlo como una tarifa plana infinita. La ventaja competitiva no está en apagarlo, sino en usarlo donde realmente reduce tiempo: revisiones repetitivas, navegación por código desconocido, explicación de cambios y tareas donde el contexto del repositorio aporta valor.",
            ]),
        ],
    },
    {
        "title": "Copilot Code Review consumirá minutos de GitHub Actions: qué cambia en junio de 2026",
        "slug": "copilot-code-review-minutos-github-actions",
        "meta_description": "Desde junio de 2026, Copilot Code Review consumirá minutos de GitHub Actions. Qué significa y cómo preparar tus repos.",
        "excerpt": "Copilot Code Review añade una segunda dimensión de coste: además del uso de IA, también entran los minutos de Actions.",
        "sources": [
            ("GitHub Docs: Copilot code review", "https://docs.github.com/copilot/code-review"),
            ("GitHub Changelog: code review y Actions minutes", "https://github.blog/changelog/2026-04-27-github-copilot-code-review-will-start-consuming-github-actions-minutes-on-june-1-2026"),
        ],
        "related": [
            ("GitHub Copilot: AI Credits y pago por uso", "/github-copilot-ai-credits-pago-por-uso/"),
            ("GitHub Copilot: guía completa para desarrolladores", "/github-copilot-guia-completa/"),
        ],
        "sections": [
            ("El cambio clave", [
                "A partir del 1 de junio de 2026, las ejecuciones de Copilot Code Review pasan a consumir minutos de GitHub Actions en runners hospedados por GitHub. Esto importa porque la revisión automática deja de ser solo una función de Copilot: también toca el presupuesto de CI.",
                "En equipos pequeños puede pasar desapercibido durante unas semanas. En organizaciones con muchos pull requests, bots, ramas de dependabot y revisiones automáticas, puede convertirse en un coste recurrente.",
            ]),
            ("Dónde aparece el coste", [
                "El coste aparece cuando usas Copilot para revisar cambios en pull requests y esa revisión se ejecuta sobre infraestructura de GitHub Actions. Si además tu plan usa AI Credits o premium requests, estás combinando dos contadores: consumo de IA y minutos de ejecución.",
            ]),
            ("Qué repos deberían revisarlo primero", [
                "Repos con muchos pull requests pequeños, porque el overhead de revisar automáticamente cada cambio puede ser alto.",
                "Repos con dependabot o Renovate abriendo PRs de forma frecuente.",
                "Monorepos, porque cada revisión puede tocar más contexto y más archivos.",
                "Equipos que ya van justos de minutos de Actions antes de activar Copilot Code Review.",
            ]),
            ("Política recomendada", [
                "No actives revisión automática en todos los repos por defecto.",
                "Empieza con repos críticos donde el valor de una segunda lectura compense el coste.",
                "Excluye cambios triviales: documentación, lockfiles o bumps automáticos de bajo riesgo.",
                "Mide durante dos semanas y compara PRs revisados, minutos consumidos y bugs detectados.",
            ]),
            ("Conclusión", [
                "Copilot Code Review puede aportar valor, pero no debería configurarse como un interruptor global. La mejor configuración es selectiva: activar donde reduce riesgo real y dejar fuera lo que solo añade coste operacional.",
            ]),
        ],
    },
    {
        "title": "GitHub Copilot y privacidad: cómo evitar que tus datos se usen para entrenar IA",
        "slug": "github-copilot-datos-entrenamiento-privacidad",
        "meta_description": "Qué datos puede usar GitHub Copilot para mejorar modelos, qué usuarios están afectados y cómo revisar la configuración de privacidad.",
        "excerpt": "La privacidad de Copilot depende del tipo de cuenta y de la configuración. Esta guía resume qué revisar antes de usarlo con código sensible.",
        "sources": [
            ("GitHub Copilot: producto oficial", "https://github.com/features/copilot"),
            ("Configuración de Copilot", "https://github.com/settings/copilot/features"),
        ],
        "related": [
            ("GitHub Copilot: guía completa para desarrolladores", "/github-copilot-guia-completa/"),
            ("Cursor AI: qué es y cómo usarlo", "/cursor-ai-que-es-guia-completa/"),
        ],
        "sections": [
            ("La pregunta que importa", [
                "Cuando usas una herramienta de IA para programar, no solo envías prompts. También puede viajar contexto del archivo abierto, fragmentos de código, nombres de funciones, comentarios, estructura del repositorio y la respuesta que aceptas o rechazas.",
                "La pregunta no es si Copilot funciona bien. La pregunta es qué datos salen de tu entorno, bajo qué plan, con qué controles y si pueden usarse para mejorar modelos.",
            ]),
            ("Quién debería preocuparse más", [
                "Freelancers que trabajan con código de clientes sin una política explícita de IA.",
                "Startups que usan repos privados con lógica de negocio sensible.",
                "Equipos que mezclan cuentas personales y repos profesionales.",
                "Desarrolladores que trabajan con secretos, datos regulados o propiedad intelectual no publicada.",
            ]),
            ("Qué revisar en tu cuenta", [
                "Entra en la configuración de Copilot y revisa las opciones de privacidad y entrenamiento.",
                "Distingue entre cuenta individual, organización y empresa: las políticas no siempre son iguales.",
                "Comprueba si tu organización fuerza una política central o si cada usuario puede decidir.",
                "Documenta la decisión para que el equipo no dependa de memoria o capturas antiguas.",
            ]),
            ("Buenas prácticas", [
                "No abras secretos ni claves en el editor mientras usas asistentes de IA.",
                "Usa reglas de organización para repos con código sensible.",
                "Evalúa alternativas self-hosted o modelos locales para proyectos con restricciones fuertes.",
                "Incluye el uso de IA en el onboarding técnico y en la política de seguridad.",
            ]),
            ("Conclusión", [
                "Copilot puede ser perfectamente razonable en muchos equipos, pero no debería usarse en piloto automático. La privacidad se gestiona con configuración, política y hábitos de desarrollo, no con confianza genérica en el proveedor.",
            ]),
        ],
    },
    {
        "title": "Serena MCP: búsqueda semántica de código para agentes de IA",
        "slug": "serena-mcp-busqueda-semantica-codigo",
        "meta_description": "Qué es Serena MCP, cómo ayuda a agentes de IA a entender código y cuándo conviene usar búsqueda semántica frente a grep.",
        "excerpt": "Serena conecta agentes de IA con una vista semántica del código: símbolos, referencias y edición más precisa que leer archivos enteros.",
        "sources": [
            ("Repositorio oficial de Serena", "https://github.com/oraios/serena"),
            ("MCP Registry: Serena", "https://github.com/mcp/oraios/serena"),
        ],
        "related": [
            ("Claude Code: guía completa para desarrolladores", "/claude-code-que-es-guia-completa/"),
            ("Cursor AI: qué es y cómo usarlo", "/cursor-ai-que-es-guia-completa/"),
        ],
        "sections": [
            ("Qué problema resuelve", [
                "Los agentes de IA suelen trabajar mal cuando solo tienen dos herramientas: leer archivos enteros o buscar texto con grep. En proyectos pequeños puede bastar. En repos grandes, esa estrategia desperdicia tokens y hace que el modelo pierda relaciones importantes.",
                "Serena intenta resolver ese hueco: dar a los agentes una capa parecida a un IDE, con conocimiento de símbolos, referencias, estructura del proyecto y operaciones de edición más precisas.",
            ]),
            ("Qué aporta frente a grep", [
                "Grep encuentra cadenas. Serena encuentra entidades de código. Esa diferencia importa cuando preguntas por una función, una clase, las referencias a un método o el lugar correcto para insertar un cambio.",
                "Para un humano, el IDE ya cumple ese papel. Para un agente, una herramienta MCP como Serena convierte esa inteligencia del IDE en una API que el modelo puede usar.",
            ]),
            ("Casos de uso", [
                "Code review asistido por IA en repos medianos o grandes.",
                "Refactors donde importa encontrar referencias reales y no coincidencias textuales.",
                "Onboarding de agentes en proyectos con arquitectura compleja.",
                "Reducción de tokens al evitar leer archivos enteros sin necesidad.",
            ]),
            ("Cuándo no hace falta", [
                "Si el proyecto tiene dos o tres archivos, Serena probablemente añade más complejidad que valor. También conviene evitarlo si el lenguaje no tiene buen soporte de servidor de lenguaje en tu entorno.",
                "La regla práctica: si ya te molesta que el agente se pierda entre archivos, Serena puede ayudar. Si todavía no tienes ese problema, no empieces por ahí.",
            ]),
            ("Conclusión", [
                "Serena es interesante porque no intenta ser otro chat de código. Es infraestructura para que los agentes trabajen mejor: menos lectura inútil, más navegación semántica y ediciones más controladas.",
            ]),
        ],
    },
    {
        "title": "RTK: proxy CLI para reducir tokens en agentes de IA",
        "slug": "rtk-proxy-cli-reducir-tokens-ia",
        "meta_description": "RTK es un proxy CLI en Rust que reduce el contexto enviado a modelos de IA. Qué hace, cuándo usarlo y límites reales.",
        "excerpt": "Los agentes de coding queman tokens con salidas enormes de terminal. RTK propone filtrar y comprimir ese ruido antes de enviarlo al modelo.",
        "sources": [
            ("Repositorio oficial de RTK", "https://github.com/rtk-ai/rtk"),
            ("Documentación de RTK", "https://www.rtk-ai.app/docs/"),
        ],
        "related": [
            ("Serena MCP: búsqueda semántica de código", "/serena-mcp-busqueda-semantica-codigo/"),
            ("Claude Code: guía completa para desarrolladores", "/claude-code-que-es-guia-completa/"),
        ],
        "sections": [
            ("El problema de los tokens invisibles", [
                "Cuando un agente ejecuta comandos como tests, logs, git diff o listados largos, gran parte de la salida no aporta valor. Aun así, termina dentro del contexto del modelo y se cobra como tokens.",
                "RTK, Rust Token Killer, ataca ese punto concreto: actuar como proxy CLI para filtrar, resumir o compactar salidas comunes antes de que lleguen al asistente.",
            ]),
            ("Qué tipo de ahorro promete", [
                "El proyecto se presenta como una forma de reducir consumo de tokens entre un 60% y un 90% en comandos habituales. La cifra exacta depende mucho del workflow: no es lo mismo comprimir logs repetitivos que resumir una traza pequeña.",
                "La idea fuerte no es la cifra, sino el patrón: si el agente no necesita ver todo, no deberías pagar por mandarle todo.",
            ]),
            ("Dónde encaja", [
                "Sesiones largas con Claude Code, Codex CLI u otros agentes que ejecutan muchos comandos.",
                "Repos con tests ruidosos o logs extensos.",
                "Equipos que pagan API por token y quieren controlar gasto.",
                "Pipelines donde los agentes repiten comandos parecidos muchas veces.",
            ]),
            ("Riesgos y límites", [
                "Filtrar demasiado puede ocultar justo la línea que explica el bug.",
                "Hay que probarlo con tus comandos reales antes de meterlo en un flujo crítico.",
                "No sustituye a buenas prácticas: tests claros, logs estructurados y prompts concretos siguen importando.",
            ]),
            ("Conclusión", [
                "RTK apunta a una tendencia clara: optimizar el contexto será tan importante como elegir modelo. A medida que los agentes ejecutan más trabajo real, controlar qué información entra al modelo se vuelve una parte central del coste.",
            ]),
        ],
    },
    {
        "title": "Zed Parallel Agents: cómo trabajar con varios agentes de IA en el editor",
        "slug": "zed-parallel-agents-editor-ia",
        "meta_description": "Zed permite ejecutar varios agentes de IA en paralelo dentro del editor. Cómo funciona y para qué workflows tiene sentido.",
        "excerpt": "Los agentes paralelos de Zed cambian el modelo de trabajo: varias tareas de IA avanzan a la vez, con contextos separados.",
        "sources": [
            ("Zed Blog: Introducing Parallel Agents", "https://zed.dev/blog/parallel-agents"),
            ("Documentación de Zed Parallel Agents", "https://zed.dev/docs/ai/parallel-agents"),
        ],
        "related": [
            ("Cursor AI: qué es y cómo usarlo", "/cursor-ai-que-es-guia-completa/"),
            ("Windsurf IDE: editor de código con IA", "/windsurf-ide-editor-ia/"),
        ],
        "sections": [
            ("Qué propone Zed", [
                "La mayoría de editores con IA funcionan con un agente principal: le das una tarea, esperas y revisas. Zed está empujando una idea distinta: ejecutar varios agentes en paralelo dentro del mismo editor, cada uno con su propio hilo y contexto.",
                "Esto encaja con una forma de trabajo más cercana a coordinar tareas que a conversar con un asistente único.",
            ]),
            ("Ejemplos prácticos", [
                "Un agente escribe tests mientras otro refactoriza una función concreta.",
                "Un agente investiga un bug y otro prepara documentación del cambio.",
                "Un agente migra un componente y otro revisa impacto en estilos o accesibilidad.",
                "Un agente explora una alternativa sin bloquear la implementación principal.",
            ]),
            ("Ventajas", [
                "Reduce espera cuando las tareas son independientes.",
                "Mantiene contextos separados, lo que evita mezclar conversaciones incompatibles.",
                "Se parece más a coordinar trabajo técnico real: dividir, revisar e integrar.",
            ]),
            ("Riesgos", [
                "Más paralelismo no significa mejor resultado. Si dos agentes tocan los mismos archivos, puedes acabar integrando conflictos o decisiones contradictorias.",
                "La clave está en dividir trabajo por límites claros: módulos, archivos, tests o preguntas de investigación separadas.",
            ]),
            ("Conclusión", [
                "Parallel Agents es una señal de hacia dónde van los IDEs con IA: menos asistente único y más orquestación de pequeñas tareas. Para desarrolladores senior puede ser potente; para principiantes, puede añadir demasiada superficie de revisión.",
            ]),
        ],
    },
    {
        "title": "VS Code y Co-authored-by Copilot: qué pasó y cómo revisar tus commits",
        "slug": "vs-code-copilot-coauthored-by-commits",
        "meta_description": "VS Code llegó a atribuir commits a Copilot en ciertos casos. Qué revisar en tu configuración y cómo mantener limpio el historial Git.",
        "excerpt": "La atribución automática de commits a IA abre una pregunta práctica: cómo mantener un historial Git claro cuando usas asistentes de código.",
        "sources": [
            ("Análisis del cambio en VS Code y Copilot", "https://www.techradar.com/pro/that-is-unacceptable-in-a-professional-development-workflow-microsoft-acts-after-vs-code-gives-copilot-credit-for-work-a-human-developer-did"),
            ("GitHub Copilot", "https://github.com/features/copilot"),
        ],
        "related": [
            ("GitHub Copilot: guía completa para desarrolladores", "/github-copilot-guia-completa/"),
            ("GitHub Copilot y privacidad", "/github-copilot-datos-entrenamiento-privacidad/"),
        ],
        "sections": [
            ("Por qué molestó a tantos desarrolladores", [
                "El historial Git no es decoración. Es una fuente de responsabilidad técnica: quién cambió qué, cuándo y por qué. Por eso cualquier atribución automática relacionada con IA debe ser precisa y explícita.",
                "El caso de VS Code y Copilot abrió una discusión incómoda: si una herramienta añade metadatos de coautoría sin que el usuario lo espere, puede ensuciar el historial y crear señales falsas sobre cómo se produjo el código.",
            ]),
            ("Qué revisar", [
                "Comprueba la configuración de Copilot y VS Code relacionada con commits, chat y atribución de cambios.",
                "Revisa los commits recientes antes de hacer push si usas extensiones de IA.",
                "Asegura que tu equipo tiene una política clara: cuándo se declara ayuda de IA y cuándo no.",
            ]),
            ("Buenas prácticas para equipos", [
                "No dependas de configuración por defecto para un tema de auditoría.",
                "Incluye una comprobación en hooks o CI si la coautoría automática es un problema para tu organización.",
                "Separa la discusión ética de la práctica: puedes usar IA y, aun así, exigir metadata Git limpia.",
            ]),
            ("Conclusión", [
                "La IA en el editor no debería alterar el contrato básico de Git. Si un asistente participa de forma relevante, declararlo puede tener sentido. Si no participa, añadirlo como coautor es ruido.",
            ]),
        ],
    },
]


ARTICLES = [
    {
        "title": "GitHub Copilot y AI Credits: guía práctica para no perder el control del gasto",
        "slug": "github-copilot-ai-credits-pago-por-uso",
        "meta_description": "Guía práctica sobre AI Credits, premium requests y uso de GitHub Copilot sin sorpresas de coste en equipos de desarrollo.",
        "excerpt": "Copilot ya no es solo autocompletado. Entre chat, agentes, revisiones y modelos premium, conviene tratarlo como una herramienta de productividad con presupuesto propio.",
        "sources": [
            ("GitHub Copilot Plans", "https://github.com/features/copilot/plans"),
            ("GitHub Docs: Copilot billing", "https://docs.github.com/en/copilot/concepts/billing"),
            ("GitHub Docs: models and pricing", "https://docs.github.com/copilot/reference/copilot-billing/models-and-pricing"),
        ],
        "related": [
            ("Copilot Code Review y minutos de Actions", "/copilot-code-review-minutos-github-actions/"),
            ("GitHub Copilot: guía completa", "/github-copilot-guia-completa/"),
            ("GitHub Copilot y privacidad", "/github-copilot-datos-entrenamiento-privacidad/"),
        ],
        "sections": [
            ("La versión corta", [
                "GitHub Copilot está dejando de ser una tarifa plana mentalmente simple. Las funciones básicas siguen pareciendo las de siempre: escribir código, completar líneas, resolver dudas en el editor. Pero las funciones nuevas, sobre todo las que usan agentes, modelos premium o revisiones amplias, tienen un coste computacional mucho más variable.",
                "La consecuencia práctica es que ya no basta con preguntar cuánto cuesta Copilot al mes. La pregunta útil es: qué usa tu equipo, con qué modelos, cuántas veces al día y bajo qué límites. Si no tienes esa respuesta, no tienes un presupuesto: tienes fe.",
            ]),
            ("Qué es realmente un AI Credit", [
                "Un AI Credit es una unidad de consumo para funciones de Copilot que no encajan bien en el viejo modelo de requests iguales. Una pregunta corta al chat, una sesión de agent mode sobre varios archivos y una revisión de pull request no cuestan lo mismo para el proveedor. El nuevo sistema intenta reflejar esa diferencia.",
                "Eso no significa que cada interacción vaya a arruinarte. Significa que el coste empieza a depender del comportamiento del equipo. Si un desarrollador usa Copilot como autocomplete y consulta ocasional, el patrón será estable. Si otro usa agentes para reescribir módulos completos, analizar PRs grandes y probar modelos premium, el consumo puede variar mucho.",
            ]),
            ("Lo que más puede mover la factura", [
                "Agent mode: suele arrastrar más contexto, hace más pasos y genera más salida.",
                "Modelos premium: normalmente aportan mejor razonamiento, pero consumen más presupuesto que modelos base.",
                "Code review: parece una acción pequeña, pero puede leer diffs grandes y ejecutarse muchas veces.",
                "Repositorios grandes: más archivos, más contexto potencial y más riesgo de pedirle al modelo información que no necesita.",
                "Uso automático: lo peligroso no es una petición manual, sino una integración que dispara trabajo sin que nadie mire el contador.",
            ]),
            ("Un ejemplo de política sensata", [
                "Imagina un equipo de 12 desarrolladores. La tentación es activar Copilot en todo: autocomplete, chat, review, agentes y modelos top. Es cómodo, pero difícil de gobernar. Una política más sana empieza separando tres niveles.",
                "Nivel 1: uso libre para completions, chat normal y explicación de código. Nivel 2: uso recomendado pero medido para agent mode, refactors multiarchivo y code review manual. Nivel 3: uso restringido para modelos premium, revisiones automáticas en repos grandes y tareas que se ejecutan muchas veces al día.",
                "Esto no reduce productividad; reduce ruido. El objetivo no es que la gente pida permiso para todo, sino que el equipo sepa qué tipo de trabajo consume más y dónde merece la pena pagarlo.",
            ]),
            ("Cómo auditar tu uso en una tarde", [
                "Haz una lista de repos donde Copilot está activo.",
                "Separa uso individual de uso automatizado en pull requests, Actions o agentes.",
                "Identifica quién usa modelos premium y para qué tareas.",
                "Mira los últimos 20 PRs: cuántos habrían necesitado review de IA y cuántos eran triviales.",
                "Define un presupuesto mensual inicial y revísalo después de dos ciclos de desarrollo.",
            ]),
            ("Errores comunes", [
                "El primer error es tratar Copilot como si siguiera siendo solo autocomplete. Ya no lo es. El segundo es apagar funciones avanzadas por miedo antes de medir si ahorran tiempo real. El tercero es dejar que cada usuario elija modelo y modo sin criterios compartidos.",
                "La buena gestión está en el medio: deja que Copilot trabaje donde aporta palanca, pero pon límites a las tareas repetidas y caras. Si un agente ahorra dos horas en un refactor delicado, probablemente compensa. Si revisa veinte PRs automáticos de dependencias, quizá solo está quemando presupuesto.",
            ]),
            ("Mi recomendación", [
                "Para freelancers: empieza con el plan que cubra tu uso normal y revisa el consumo semanalmente durante el primer mes.",
                "Para startups: activa límites por organización desde el principio, aunque sean generosos.",
                "Para equipos medianos: documenta cuándo se permite agent mode, cuándo code review y cuándo modelos premium.",
                "Para consultoras: separa proyectos de cliente. No mezcles consumo ni contexto de repos con políticas distintas.",
            ]),
            ("Conclusión", [
                "Copilot puede seguir siendo rentable, pero hay que cambiar la forma de mirarlo. Ya no es una extensión barata que completa líneas; es una capa de IA integrada en el ciclo de desarrollo. Las herramientas de ese tipo necesitan métricas, límites y criterios. Lo contrario es descubrir el coste cuando ya no puedes explicar de dónde salió.",
            ]),
        ],
    },
    {
        "title": "Copilot Code Review y GitHub Actions: cómo prepararte para el coste de junio de 2026",
        "slug": "copilot-code-review-minutos-github-actions",
        "meta_description": "Copilot Code Review consumirá minutos de GitHub Actions desde junio de 2026. Guía para decidir dónde activarlo y cómo medir coste.",
        "excerpt": "Copilot Code Review puede ser útil, pero desde junio de 2026 también entra en la conversación de coste operativo de CI.",
        "sources": [
            ("GitHub Docs: Copilot code review", "https://docs.github.com/copilot/code-review"),
            ("GitHub Docs: automatic code review", "https://docs.github.com/en/copilot/how-tos/copilot-on-github/set-up-copilot/configure-automatic-review"),
            ("GitHub Changelog: Actions minutes", "https://github.blog/changelog/2026-04-27-github-copilot-code-review-will-start-consuming-github-actions-minutes-on-june-1-2026"),
        ],
        "related": [
            ("GitHub Copilot y AI Credits", "/github-copilot-ai-credits-pago-por-uso/"),
            ("GitHub Copilot: guía completa", "/github-copilot-guia-completa/"),
            ("VS Code y Co-authored-by Copilot", "/vs-code-copilot-coauthored-by-commits/"),
        ],
        "sections": [
            ("Qué cambia exactamente", [
                "A partir del 1 de junio de 2026, GitHub indica que las ejecuciones de Copilot Code Review consumirán minutos de GitHub Actions. Este detalle cambia la naturaleza de la función: ya no es únicamente una revisión de IA dentro de Copilot, también se convierte en trabajo que compite con tu presupuesto de CI.",
                "No todos los equipos lo notarán igual. Un repositorio pequeño con pocos pull requests quizá vea un impacto mínimo. Un monorepo con decenas de PRs diarios, dependabot, tests pesados y revisiones automáticas puede notar el cambio rápido.",
            ]),
            ("Por qué esta función puede ser valiosa", [
                "Copilot Code Review puede detectar errores obvios, inconsistencias, edge cases olvidados y cambios que merecen una segunda mirada. No sustituye a un revisor humano, pero sí puede actuar como una capa de pre-review, especialmente en equipos donde los PRs llegan con poca explicación.",
                "El valor aparece cuando reduce trabajo repetitivo: comentarios sobre validaciones ausentes, null checks, rutas no cubiertas, cambios de API o convenciones de repositorio. El problema aparece cuando se ejecuta en todo, sin distinguir entre cambios triviales y cambios que realmente necesitan análisis.",
            ]),
            ("Dónde lo activaría primero", [
                "Repos de producto donde un bug cuesta dinero o soporte.",
                "Servicios con lógica de negocio compleja y PRs difíciles de revisar manualmente.",
                "Repos donde los reviewers humanos están saturados y los PRs esperan demasiado.",
                "Cambios de seguridad, autenticación, pagos, permisos o migraciones de datos.",
            ]),
            ("Dónde lo evitaría", [
                "Actualizaciones automáticas de dependencias de bajo riesgo.",
                "Cambios de documentación, copy o contenido estático.",
                "Repos experimentales donde el coste de equivocarse es bajo.",
                "PRs muy pequeños que un humano revisa en menos de dos minutos.",
            ]),
            ("Una política simple para equipos", [
                "Empieza con revisión manual bajo demanda, no automática global.",
                "Crea una etiqueta como `copilot-review` para activar la revisión solo cuando el PR lo merece.",
                "Excluye rutas que no aportan valor: lockfiles, snapshots, assets generados, documentación y fixtures.",
                "Revisa semanalmente cuántos comentarios de Copilot terminaron en cambios reales.",
                "Si después de dos semanas la mayoría de comentarios se ignoran, la configuración está demasiado abierta.",
            ]),
            ("Métrica que sí importa", [
                "No midas solo cuántos issues encontró Copilot. Mide cuántos comentarios generaron cambios aceptados. Esa diferencia separa señal de ruido.",
                "Una buena revisión automática debería ahorrar tiempo al reviewer humano. Si añade cinco comentarios genéricos y obliga a explicarle al autor por qué no aplican, está haciendo lo contrario.",
            ]),
            ("Checklist antes del 1 de junio", [
                "Identifica repos con Copilot Code Review activado.",
                "Comprueba si está en modo automático o bajo demanda.",
                "Calcula PRs semanales por repositorio.",
                "Revisa consumo actual de GitHub Actions para saber si tienes margen.",
                "Define exclusiones de archivos antes de que empiece la facturación con minutos.",
            ]),
            ("Conclusión", [
                "Copilot Code Review no es malo por consumir minutos. Lo malo sería usarlo sin criterio. La función tiene sentido cuando revisa cambios donde una segunda lectura aporta valor. Para todo lo demás, puede convertirse en otro job más que se ejecuta porque nadie se acordó de apagarlo.",
            ]),
        ],
    },
    {
        "title": "GitHub Copilot y privacidad: guía para usar IA sin regalar contexto sensible",
        "slug": "github-copilot-datos-entrenamiento-privacidad",
        "meta_description": "Guía práctica de privacidad para GitHub Copilot: qué revisar, cómo hacer opt-out y cómo definir una política de uso de IA en equipos.",
        "excerpt": "Usar Copilot con código sensible no es solo una decisión técnica. También es una decisión de datos, contratos y hábitos de equipo.",
        "sources": [
            ("GitHub Copilot Plans", "https://github.com/features/copilot/plans"),
            ("GitHub Copilot settings", "https://github.com/settings/copilot/features"),
            ("GitHub Copilot Trust Center", "https://github.com/features/copilot/trust"),
        ],
        "related": [
            ("GitHub Copilot: guía completa", "/github-copilot-guia-completa/"),
            ("GitHub Copilot y AI Credits", "/github-copilot-ai-credits-pago-por-uso/"),
            ("VS Code y Co-authored-by Copilot", "/vs-code-copilot-coauthored-by-commits/"),
            ("Tabnine: privacidad y autocompletado", "/tabnine-autocompletado-codigo-ia/"),
        ],
        "sections": [
            ("La parte incómoda", [
                "Copilot funciona porque ve contexto. Esa es su ventaja y también su riesgo. Cuando le pides ayuda dentro del editor, el sistema puede necesitar fragmentos del archivo, nombres de funciones, comentarios, imports, errores y a veces contexto del repositorio. Sin contexto, la ayuda sería mucho peor.",
                "El problema no es que exista transferencia de datos. El problema es que muchos equipos no saben qué se envía, qué configuración aplica a cada cuenta y qué restricciones contractuales tienen con clientes o datos internos.",
            ]),
            ("Qué tipo de datos debes mapear", [
                "Código fuente propietario.",
                "Nombres de clientes, endpoints internos o rutas privadas.",
                "Comentarios con decisiones de negocio.",
                "Errores, logs o trazas que pueden contener datos personales.",
                "Secretos accidentales: tokens, claves, URLs firmadas o credenciales de desarrollo.",
            ]),
            ("La diferencia entre persona y organización", [
                "Un error habitual es pensar que la configuración de una cuenta personal representa la política de una empresa. No necesariamente. GitHub distingue planes individuales, organizaciones y entornos enterprise. La política de entrenamiento, retención y administración puede variar según el tipo de cuenta.",
                "Si trabajas como freelance, esto importa todavía más. Puede que uses tu cuenta personal para proyectos de varios clientes. En ese caso, la configuración de privacidad no es un detalle de preferencias: es parte de cómo cumples acuerdos de confidencialidad.",
            ]),
            ("Qué revisar hoy", [
                "Entra en la configuración de Copilot y revisa las opciones relacionadas con uso de datos para entrenamiento.",
                "Comprueba si tu organización fuerza políticas centralizadas o si cada usuario decide.",
                "Separa repos personales, proyectos de cliente y repos internos de empresa.",
                "Haz una prueba sencilla: pregunta al equipo qué datos cree que Copilot puede ver. Si las respuestas son distintas, falta política.",
            ]),
            ("Política mínima para un equipo pequeño", [
                "No pegar secretos, credenciales ni datos personales en prompts.",
                "No usar Copilot en repos de cliente si el contrato no lo permite explícitamente.",
                "Usar cuentas de organización para trabajo profesional, no cuentas personales sin control.",
                "Definir qué proveedores de IA están permitidos y para qué tipos de código.",
                "Documentar el opt-out o la configuración elegida con fecha, no en una conversación perdida de Slack.",
            ]),
            ("Cómo reducir riesgo sin apagarlo todo", [
                "Puedes permitir Copilot para boilerplate, tests, documentación interna y exploración de APIs, pero restringirlo en módulos con secretos, lógica regulada o propiedad intelectual especialmente sensible.",
                "También puedes combinar herramientas. Copilot para trabajo general, modelos locales para repos delicados y revisión humana obligatoria para cambios que tocan seguridad o datos personales. No hay una única respuesta correcta; hay niveles de exposición.",
            ]),
            ("Señales de mala implementación", [
                "Nadie sabe si el entrenamiento está activado o desactivado.",
                "Cada desarrollador usa su propia cuenta con configuración distinta.",
                "Se aceptan sugerencias de IA sin revisión en código crítico.",
                "El equipo tiene política de seguridad, pero no menciona asistentes de código.",
                "Los prompts se tratan como si no fueran datos del proyecto.",
            ]),
            ("Conclusión", [
                "La privacidad en Copilot no se resuelve con miedo ni con confianza ciega. Se resuelve con inventario, configuración, límites y hábitos. Si tu equipo sabe qué puede usar, dónde y bajo qué cuenta, Copilot puede ser una herramienta razonable. Si nadie lo sabe, el riesgo no está en la IA: está en la falta de gobierno.",
            ]),
        ],
    },
    {
        "title": "Serena MCP: el puente entre agentes de IA y código que entienden de verdad",
        "slug": "serena-mcp-busqueda-semantica-codigo",
        "meta_description": "Análisis práctico de Serena MCP: búsqueda semántica, símbolos, referencias y cuándo usarlo con Claude Code, Codex o agentes de IA.",
        "excerpt": "Serena no intenta ser otro chatbot. Su valor está en dar a los agentes una forma más parecida a un IDE para navegar y editar código.",
        "sources": [
            ("Serena GitHub", "https://github.com/oraios/serena"),
            ("MCP Registry: Serena", "https://github.com/mcp/oraios/serena"),
            ("Model Context Protocol", "https://modelcontextprotocol.io/"),
        ],
        "related": [
            ("Claude Code: guía completa", "/claude-code-que-es-guia-completa/"),
            ("RTK: proxy CLI para reducir tokens", "/rtk-proxy-cli-reducir-tokens-ia/"),
            ("Cursor AI: guía completa", "/cursor-ai-que-es-guia-completa/"),
        ],
        "sections": [
            ("El problema real no es que el modelo sea tonto", [
                "Muchos fallos de los agentes de código no vienen de que el modelo no sepa programar. Vienen de que mira el proyecto como si estuviera leyendo texto plano por una rendija. Abre un archivo entero, busca palabras, intenta inferir referencias y a veces cambia una coincidencia que no era la correcta.",
                "Un desarrollador humano no trabaja así. Usa el IDE: saltar a definición, buscar referencias, ver símbolos, entender tipos, navegar dependencias. Serena intenta darle ese tipo de herramientas a un agente vía MCP.",
            ]),
            ("Qué aporta Serena", [
                "Serena se presenta como un toolkit MCP para coding con recuperación y edición semántica. La idea es que un agente pueda pedir información de código a nivel de símbolo y relación, no solo como texto.",
                "Esto cambia la calidad del trabajo en tareas donde importa saber qué función se está tocando, qué referencias existen y dónde conviene insertar o modificar código. No elimina la revisión humana, pero reduce una clase de errores muy común: cirugía textual frágil.",
            ]),
            ("Ejemplo mental", [
                "Imagina que pides: cambia cómo se calcula el precio final en el checkout. Un agente sin herramientas semánticas puede buscar `price`, abrir varios archivos y decidir por proximidad textual. Un agente con herramientas tipo Serena puede localizar funciones, referencias y módulos relacionados antes de editar.",
                "La diferencia no es estética. En un repo real, hay `price`, `basePrice`, `displayPrice`, `discountedPrice`, tests, fixtures y componentes UI. El riesgo de tocar lo incorrecto sube rápido.",
            ]),
            ("Dónde lo usaría", [
                "Repos medianos o grandes donde grep ya se queda corto.",
                "Refactors donde necesitas encontrar referencias reales.",
                "Agentes que hacen cambios sobre varios archivos.",
                "Code review automatizado que debe razonar sobre símbolos, no solo sobre diffs.",
                "Proyectos donde quieres reducir tokens evitando lecturas completas innecesarias.",
            ]),
            ("Dónde no lo usaría todavía", [
                "Proyectos pequeños donde todo cabe en pocos archivos.",
                "Spikes rápidos donde la sobrecarga de configurar herramientas no compensa.",
                "Lenguajes o entornos donde el soporte LSP sea pobre.",
                "Equipos que todavía no tienen tests ni flujo de revisión: Serena no sustituye disciplina básica.",
            ]),
            ("Cómo evaluarlo sin hype", [
                "Escoge una tarea real que ya haya dado problemas a un agente.",
                "Ejecuta la misma tarea con y sin Serena.",
                "Mide archivos leídos, tokens aproximados, número de ediciones y correcciones humanas necesarias.",
                "No te quedes con si el agente “parece más listo”. Mira si cambia menos código irrelevante.",
            ]),
            ("Mi lectura", [
                "Serena es interesante porque apunta a una capa que todos los agentes de código van a necesitar: herramientas de comprensión de proyecto. El futuro no será un LLM leyendo repos enteros una y otra vez; será un LLM pidiendo al entorno justo la información que necesita.",
                "Eso se parece menos a magia y más a ingeniería de herramientas. Precisamente por eso merece atención.",
            ]),
        ],
    },
    {
        "title": "RTK: cómo reducir tokens en agentes de IA sin quedarte ciego al depurar",
        "slug": "rtk-proxy-cli-reducir-tokens-ia",
        "meta_description": "RTK, Rust Token Killer, reduce el ruido que llega a modelos de IA. Guía práctica para usarlo sin ocultar errores importantes.",
        "excerpt": "RTK ataca un problema muy concreto: los agentes de coding mandan demasiada salida de terminal al modelo y eso cuesta dinero.",
        "sources": [
            ("RTK documentation", "https://www.rtk-ai.app/docs/"),
            ("RTK GitHub", "https://github.com/rtk-ai/rtk"),
        ],
        "related": [
            ("Serena MCP: búsqueda semántica", "/serena-mcp-busqueda-semantica-codigo/"),
            ("Claude Code: guía completa", "/claude-code-que-es-guia-completa/"),
            ("GitHub Copilot y AI Credits", "/github-copilot-ai-credits-pago-por-uso/"),
        ],
        "sections": [
            ("El coste oculto de los agentes", [
                "Cuando usas un agente de código, no pagas solo por el prompt bonito que escribes. Pagas por el contexto que entra y la respuesta que sale. Si el agente ejecuta tests, imprime logs enormes, lee diffs completos o lista directorios gigantes, una parte importante del coste está en texto que nadie necesitaba leer entero.",
                "RTK, Rust Token Killer, parte de una premisa sencilla: antes de mandar salida de terminal a un LLM, conviene limpiar ruido, compactar información repetida y conservar lo que realmente ayuda a decidir el siguiente paso.",
            ]),
            ("Qué tipo de ruido recorta", [
                "Trazas largas donde solo importan las primeras y últimas líneas.",
                "Logs repetidos de frameworks que no explican el fallo.",
                "Salidas de comandos con cientos de archivos irrelevantes.",
                "Diffs donde el agente necesita contexto localizado, no todo el patch.",
                "Mensajes de instalación o build que repiten warnings conocidos.",
            ]),
            ("El riesgo de pasarse filtrando", [
                "Reducir tokens no puede ser más importante que entender el bug. Si una herramienta compacta demasiado, puede ocultar justo la línea que explica el fallo. Por eso RTK y cualquier capa parecida deben evaluarse con comandos reales, no solo con demos donde el resultado queda bonito.",
                "La pregunta correcta no es cuánto reduce. Es qué conserva. Un resumen útil mantiene exit code, comando ejecutado, error principal, archivo afectado, línea relevante y contexto suficiente para decidir.",
            ]),
            ("Workflow recomendado", [
                "Empieza con comandos ruidosos pero no críticos: logs de desarrollo, listados largos o salidas de tests conocidas.",
                "Compara una sesión normal con una sesión usando RTK.",
                "Mide si el agente pide menos contexto adicional después del resumen.",
                "Mantén una vía para ver la salida completa cuando el bug sea ambiguo.",
                "No lo metas primero en producción o CI crítico; úsalo antes en sesiones interactivas.",
            ]),
            ("Dónde puede ahorrar de verdad", [
                "Equipos que usan agentes todos los días y pagan por API.",
                "Repos con suites de test grandes y salidas verbosas.",
                "Workflows de code review donde el agente lee demasiados diffs.",
                "Sesiones largas de depuración donde el modelo acumula contexto sin limpiar.",
            ]),
            ("RTK frente a Serena", [
                "RTK y Serena atacan problemas distintos. Serena ayuda a encontrar y editar código de forma semántica. RTK ayuda a reducir el coste de la información que sale de comandos. Uno mejora navegación; el otro higiene de contexto.",
                "Combinados tienen sentido: Serena evita leer archivos enteros cuando no hace falta, RTK evita mandar salidas de terminal enormes cuando bastan señales compactas.",
            ]),
            ("Conclusión", [
                "El futuro de los agentes no será solo modelos más grandes. También será mejor gestión del contexto. RTK apunta a esa capa: menos ruido, menos tokens, menos coste. Pero como toda optimización, hay que aplicarla con criterio. Si el resumen impide ver el fallo, no estás ahorrando; estás comprando deuda técnica.",
            ]),
        ],
    },
    {
        "title": "Zed Parallel Agents: cómo usar varios agentes sin convertir tu repo en un caos",
        "slug": "zed-parallel-agents-editor-ia",
        "meta_description": "Zed Parallel Agents permite ejecutar varios agentes de IA en paralelo. Guía práctica para dividir tareas, evitar conflictos y revisar resultados.",
        "excerpt": "Los agentes paralelos de Zed son potentes si divides bien el trabajo. Si no, solo multiplican cambios que luego tienes que deshacer.",
        "sources": [
            ("Zed: Introducing Parallel Agents", "https://zed.dev/blog/parallel-agents"),
            ("Zed docs: Parallel Agents", "https://zed.dev/docs/ai/parallel-agents"),
            ("Zed Parallel Agents", "https://zed.dev/parallel-agents"),
        ],
        "related": [
            ("Cursor AI: guía completa", "/cursor-ai-que-es-guia-completa/"),
            ("Windsurf IDE: editor con IA", "/windsurf-ide-editor-ia/"),
            ("Serena MCP: búsqueda semántica", "/serena-mcp-busqueda-semantica-codigo/"),
        ],
        "sections": [
            ("La idea es buena, pero peligrosa", [
                "Zed Parallel Agents permite ejecutar varios hilos de agente al mismo tiempo, cada uno con su contexto y conversación. La promesa es atractiva: mientras un agente escribe tests, otro investiga un bug y otro prepara una refactorización.",
                "Pero el paralelismo no arregla mala planificación. Si tres agentes tocan los mismos archivos o persiguen objetivos incompatibles, no tienes productividad: tienes una cola de merge conflicts y decisiones incoherentes.",
            ]),
            ("Cómo dividir tareas", [
                "La división buena es por frontera clara. Un agente puede encargarse de tests, otro de documentación, otro de investigar una API. La división mala es pedir a varios agentes que “mejoren el mismo módulo” a la vez.",
                "Antes de lanzar agentes en paralelo, escribe una frase de contrato para cada uno: qué puede tocar, qué no puede tocar y qué debe entregar. Si no puedes escribir ese contrato, la tarea no está lista para paralelizarse.",
            ]),
            ("Ejemplos que sí tienen sentido", [
                "Agente A: reproduce el bug y localiza causa probable sin editar archivos.",
                "Agente B: añade tests en un directorio concreto.",
                "Agente C: actualiza documentación de uso después de que el cambio esté claro.",
                "Agente D: explora una alternativa en worktree separado.",
            ]),
            ("Ejemplos que evitaría", [
                "Dos agentes refactorizando el mismo componente.",
                "Un agente cambiando API pública mientras otro actualiza consumidores sin contrato previo.",
                "Varios agentes ejecutando formateadores o cambios globales.",
                "Agentes generando arquitectura nueva sin que una persona haya decidido el diseño.",
            ]),
            ("Revisión humana: el cuello de botella correcto", [
                "El objetivo de Parallel Agents no debería ser saltarse la revisión humana. Debería mover el cuello de botella hacia donde aporta valor: revisar decisiones, integrar resultados y descartar trabajo flojo.",
                "Un buen flujo termina con commits pequeños y legibles. Si el resultado es un diff enorme que mezcla tests, estilos, refactor y cambios de comportamiento, el paralelismo se comió la trazabilidad.",
            ]),
            ("Regla práctica", [
                "Usa paralelismo para tareas independientes, investigación y trabajo auxiliar. Usa un único agente, o trabajo manual, para cambios de arquitectura, APIs centrales y migraciones delicadas.",
                "Si quieres ir más lejos, combina Parallel Agents con worktrees. Aislar cambios reduce conflictos y permite comparar alternativas sin contaminar la rama principal.",
            ]),
            ("Conclusión", [
                "Zed acierta al tratar los agentes como unidades de trabajo, no como un único chat mágico. La clave está en que el desarrollador actúe como coordinador técnico. Quien divide mal, revisa el doble. Quien divide bien, convierte espera pasiva en avance paralelo.",
            ]),
        ],
    },
    {
        "title": "VS Code, Copilot y Co-authored-by: cómo proteger la trazabilidad de tus commits",
        "slug": "vs-code-copilot-coauthored-by-commits",
        "meta_description": "Qué pasó con Co-authored-by Copilot en VS Code, por qué importa para auditoría y cómo revisar la atribución de commits con IA.",
        "excerpt": "La atribución automática de IA en commits no es un detalle cosmético. Afecta confianza, auditoría y responsabilidad técnica.",
        "sources": [
            ("VS Code issue #314311", "https://github.com/microsoft/vscode/issues/314311"),
            ("TechRadar: VS Code and Copilot attribution", "https://www.techradar.com/pro/that-is-unacceptable-in-a-professional-development-workflow-microsoft-acts-after-vs-code-gives-copilot-credit-for-work-a-human-developer-did"),
            ("GitHub Copilot", "https://github.com/features/copilot"),
        ],
        "related": [
            ("GitHub Copilot y privacidad", "/github-copilot-datos-entrenamiento-privacidad/"),
            ("GitHub Copilot: guía completa", "/github-copilot-guia-completa/"),
            ("Zed Parallel Agents", "/zed-parallel-agents-editor-ia/"),
        ],
        "sections": [
            ("Por qué este tema levantó tanta reacción", [
                "El historial Git no es una caja de comentarios. Es una herramienta de auditoría. Cuando un commit dice `Co-authored-by`, está haciendo una afirmación sobre quién participó en ese cambio. Si esa afirmación se añade automáticamente o de forma demasiado amplia, el historial pierde precisión.",
                "El caso de VS Code y Copilot generó rechazo porque algunos desarrolladores vieron atribución a Copilot en commits donde no esperaban esa marca. Microsoft abrió discusión pública en el issue correspondiente y la configuración cambió hacia un comportamiento más explícito.",
            ]),
            ("Qué problema hay con atribuir a la IA", [
                "No es que declarar ayuda de IA sea malo. En algunos equipos puede ser deseable. El problema es usar una etiqueta de coautoría humana para expresar algo ambiguo: tal vez Copilot sugirió una línea, tal vez generó un bloque entero, tal vez no participó en ese commit concreto.",
                "Mezclar esos casos bajo la misma marca complica auditorías, contratos con clientes y políticas internas donde el uso de IA tiene restricciones.",
            ]),
            ("Qué revisar en tu entorno", [
                "Revisa la configuración de VS Code relacionada con AI co-authoring.",
                "Haz un commit de prueba desde la UI de Git de VS Code y mira el mensaje antes de confirmar.",
                "Comprueba si tu equipo usa extensiones que modifican mensajes de commit.",
                "Define si la atribución de IA será obligatoria, opcional o prohibida en repos concretos.",
            ]),
            ("Política razonable", [
                "Si la IA genera una parte sustancial del cambio, documentarlo puede ser útil.",
                "Si la IA solo sugiere completions triviales, coautoría completa probablemente exagera su papel.",
                "Si un cliente prohíbe IA, no basta con apagar chat: hay que revisar extensiones, settings y metadatos.",
                "Si se usa coautoría, debe ser explícita y revisable antes de hacer commit.",
            ]),
            ("Alternativas más precisas", [
                "Una línea de commit puede decir demasiado poco. Para cambios importantes asistidos por IA, puede ser mejor explicarlo en la descripción del PR: qué se generó, qué revisó una persona y qué pruebas se ejecutaron.",
                "Otra opción es usar convenciones internas: etiquetas en PRs, checklist de uso de IA o secciones de auditoría. Lo importante es separar asistencia de responsabilidad. El responsable del cambio sigue siendo quien lo revisa y lo integra.",
            ]),
            ("Checklist rápido", [
                "Antes de hacer push, revisa el commit message completo.",
                "Busca `Co-authored-by` en commits recientes si usaste VS Code Git UI.",
                "Añade una regla de pre-commit si tu organización no permite esa atribución.",
                "Documenta settings recomendados en el README interno del equipo.",
                "No mezcles discusión política con higiene técnica: el historial debe ser exacto.",
            ]),
            ("Conclusión", [
                "La IA puede ayudar a programar, pero no debería escribir metadata de autoría sin claridad. La trazabilidad de Git es demasiado importante para tratarla como un experimento de producto. Si usas asistentes de código, revisa no solo el diff: revisa también lo que tus herramientas dicen sobre cómo se produjo ese diff.",
            ]),
        ],
    },
    {
        "title": "Real-time chunking: cómo trocear datos vivos para RAG sin perder contexto",
        "slug": "real-time-chunking-rag-streaming",
        "meta_description": "Guía técnica de real-time chunking para RAG: ventanas temporales, embeddings incrementales, contexto, latencia, grafos temporales y evaluación.",
        "excerpt": "El chunking en tiempo real no consiste en partir texto más rápido. Consiste en convertir flujos incompletos en memoria consultable sin romper orden, causa ni contexto.",
        "sources": [
            ("Physical Intelligence: Real-Time Action Chunking with Large Models", "https://www.pi.website/research/real_time_chunking"),
            ("Training-Time Action Conditioning for Efficient Real-Time Chunking", "https://arxiv.org/abs/2512.05964"),
            ("StreamingRAG: Real-time Contextual Retrieval and Generation Framework", "https://arxiv.org/abs/2501.14101"),
            ("Late Chunking: Contextual Chunk Embeddings Using Long-Context Embedding Models", "https://arxiv.org/abs/2409.04701"),
            ("Anthropic: Contextual Retrieval", "https://www.anthropic.com/research/contextual-retrieval"),
            ("Is Semantic Chunking Worth the Computational Cost?", "https://huggingface.co/papers/2410.13070"),
            ("How Does Chunking Affect Retrieval-Augmented Code Completion?", "https://arxiv.org/abs/2605.04763"),
        ],
        "related": [
            ("Serena MCP: búsqueda semántica", "/serena-mcp-busqueda-semantica-codigo/"),
            ("RTK: proxy CLI para reducir tokens", "/rtk-proxy-cli-reducir-tokens-ia/"),
            ("Claude Code: guía completa", "/claude-code-que-es-guia-completa/"),
        ],
        "sections": [
            ("La idea en una frase", [
                "Real-time chunking es una familia de técnicas para dividir una secuencia viva en unidades ejecutables o recuperables mientras el mundo sigue avanzando. En IA aplicada aparece en dos contextos distintos: sistemas RAG que trocean datos en streaming y modelos de robótica que generan chunks de acciones para actuar sin pausas.",
                "La diferencia parece pequeña, pero cambia todo el diseño. En un RAG clásico puedes limpiar documentos, partirlos, embeberlos y revisarlos antes de publicarlos. En un sistema en tiempo real, el chunker está en el camino crítico: si tarda demasiado, la respuesta llega tarde; si corta mal, el modelo recupera evidencia incompleta; si actualiza mal, conserva versiones obsoletas como si siguieran siendo verdad.",
            ]),
            ("Dos significados que conviene no mezclar", [
                "En RAG, un chunk suele ser una unidad de información: texto, evento, ventana temporal o resumen que luego se recupera para responder. En robótica, un chunk puede ser una secuencia de acciones motoras: posiciones, velocidades, comandos de control o trayectorias que el robot ejecuta durante una fracción de segundo o varios segundos.",
                "La conexión conceptual es fuerte: ambos problemas intentan amortiguar la latencia. Un RAG no puede esperar a reprocesar todo el corpus cada vez que entra un evento. Un robot no puede quedarse quieto mientras un modelo grande piensa la siguiente acción. En ambos casos, el sistema necesita trabajar con chunks parciales, consistentes y actualizables.",
                "La diferencia crítica está en el coste del error. Un chunk de texto mal cortado produce una respuesta pobre. Un chunk de acciones incompatible puede producir una trayectoria brusca, acelerar de forma insegura o fallar una manipulación física.",
            ]),
            ("RTC en robótica: pensar mientras se mueve", [
                "Physical Intelligence presentó Real-Time Action Chunking como una estrategia para vision-language-action models. Estos modelos pueden generar secuencias de acciones, pero son pesados y tienen latencia. Si el robot espera a que termine cada inferencia antes de moverse, aparecen pausas. Si cambia ingenuamente de un chunk de acciones a otro mientras está en movimiento, puede haber discontinuidades peligrosas.",
                "La idea central de RTC es ejecutar parte del chunk anterior mientras el modelo calcula el siguiente. Cuando el nuevo chunk llega, no puede ignorar lo ya comprometido: algunos timesteps ya ocurrieron y otros se solapan con acciones pendientes. RTC formula ese empalme como un problema de inpainting: congela el prefijo de acciones que ya están determinadas y rellena el resto de forma compatible con la trayectoria actual.",
                "Ese detalle es importante porque muestra que real-time chunking no es solo batch size. Es consistencia entre chunks bajo latencia. En el artículo de Physical Intelligence, RTC permite ejecución en tiempo real con modelos VLA sin cambios de entrenamiento, y reportan robustez incluso con retrasos artificiales superiores a 300 ms en tareas de precisión como encender una cerilla o conectar un cable Ethernet.",
            ]),
            ("Inference-time RTC vs training-time RTC", [
                "El paper posterior, Training-Time Action Conditioning for Efficient Real-Time Chunking, plantea una mejora: en vez de resolver la consistencia mediante inpainting durante la inferencia, simula retrasos durante el entrenamiento y condiciona directamente el modelo en prefijos de acciones ya comprometidas.",
                "La motivación es sencilla. El RTC por inpainting funciona, pero añade sobrecarga computacional en inferencia. Si el modelo aprende durante entrenamiento que parte del chunk ya está fijado, puede producir el resto de la secuencia sin pagar ese coste extra en runtime. Según el resumen del paper, este enfoque mantiene rendimiento y velocidad en tareas reales como box building y espresso making con el VLA pi_0.6, siendo más barato computacionalmente.",
                "La lección general para sistemas de IA en tiempo real es clara: puedes resolver latencia en runtime con algoritmos de reconciliación, o puedes enseñar al modelo durante entrenamiento a vivir con acciones, eventos o contexto ya comprometido. La segunda opción suele ser más eficiente, pero exige controlar mejor los datos de entrenamiento.",
            ]),
            ("Por qué el chunking normal no basta", [
                "El chunking tradicional presupone que el material ya existe. Normalmente eliges un tamaño, un solapamiento y un criterio de corte: párrafos, títulos, tokens, funciones de código o bloques Markdown. Después indexas y recuperas. Ese flujo es razonable para documentación, wikis, PDFs o repositorios que cambian de forma controlada.",
                "Los datos vivos tienen otra forma. Una frase puede llegar antes de su explicación. Un error de log puede aparecer 200 líneas antes de la causa. Una llamada de soporte puede empezar con una queja genérica y terminar revelando versión, plataforma y workaround. Un partido en directo cambia de probabilidad después de una lesión, una roja o una sustitución. Si el chunk se cerró demasiado pronto, la memoria queda partida justo donde necesitabas continuidad.",
            ]),
            ("La unidad correcta no siempre es texto", [
                "En real-time chunking, el chunk ideal no es necesariamente un bloque de 800 tokens. Puede ser un evento enriquecido, una ventana temporal, una transición de estado, una secuencia de logs, una jugada, una intervención de un usuario o una hipótesis provisional que luego se confirma o se corrige.",
                "Por eso conviene pensar en chunks como objetos, no como strings. Un chunk debería tener texto, pero también metadatos: fuente, timestamp de evento, timestamp de ingestión, sesión, entidad principal, tipo de señal, estado de confianza, versión, relación con chunks anteriores y política de expiración. Sin esa estructura, el vector store se convierte en una bolsa de frases parecidas sin memoria temporal.",
            ]),
            ("Arquitectura de referencia", [
                "Una arquitectura práctica empieza con ingestión. Aquí entran webhooks, colas, Kafka, sockets, transcripciones parciales, logs, eventos de producto o APIs externas. Cada entrada necesita un identificador de fuente y un reloj fiable. El timestamp no es decoración: es parte de la verdad que luego recuperará el modelo.",
                "Después viene el buffer. El sistema acumula una ventana pequeña antes de decidir. Puede ser una ventana de tiempo, una ventana de tokens, una ventana por número de eventos o una ventana cerrada por señal externa. El objetivo es evitar chunks raquíticos que digan algo como 'falló otra vez' sin conservar qué falló, dónde y después de qué acción.",
                "La tercera capa es segmentación. Aquí se decide si el buffer se cierra, se extiende, se fusiona con un chunk anterior o genera un chunk provisional. La cuarta capa es enriquecimiento: entidades, resumen local, etiquetas, enlaces a contexto padre y señales de recencia. La quinta capa es indexación incremental, normalmente híbrida: vectorial para similitud semántica, lexical para términos exactos y a veces grafo temporal para relaciones de estado.",
            ]),
            ("Estrategias de segmentación", [
                "Ventana temporal fija. Corta cada N segundos. Es simple, predecible y útil en audio, vídeo, sensores o telemetría. Su debilidad es que puede cortar en mitad de una idea.",
                "Ventana por tokens con overlap. Acumula hasta un límite y arrastra parte del contexto anterior. Es robusta y barata, pero duplica información y no entiende cambios de tema.",
                "Segmentación por eventos. Cierra chunks cuando ocurre algo significativo: error nuevo, cambio de pantalla, commit, gol, sustitución, alerta, decisión o intención detectada.",
                "Segmentación semántica incremental. Usa embeddings, clasificadores o LLMs pequeños para detectar cambios de tema. Puede mejorar legibilidad, pero añade coste y debe evaluarse porque no siempre supera a estrategias simples.",
                "Chunking jerárquico. Guarda chunks pequeños para precisión y chunks padre para contexto. Es útil cuando una respuesta necesita tanto el detalle como el episodio completo.",
            ]),
            ("Contextual retrieval aplicado a streaming", [
                "Anthropic propuso contextual retrieval como una forma de añadir a cada chunk una explicación breve antes de embeberlo e indexarlo. En documentos estáticos, eso ayuda a que un fragmento no pierda su lugar dentro del documento. En streaming, el patrón es todavía más importante porque muchos fragmentos nacen incompletos.",
                "Un chunk crudo puede decir: 'el botón falla después de confirmar'. Un chunk contextualizado debería decir: 'En una sesión de soporte sobre checkout Android, el usuario indica que el botón de confirmar pago falla después de actualizar a la versión 5.12'. Esa frase extra mejora la recuperación vectorial y también BM25, porque introduce términos que el usuario probablemente usará al preguntar.",
            ]),
            ("Late chunking y contexto largo", [
                "Late chunking plantea otra idea: procesar un contexto amplio con un modelo de embeddings de contexto largo y partir después la representación. En vez de cortar primero y embeber fragmentos aislados, intenta que cada embedding de chunk arrastre información global del documento o secuencia.",
                "En tiempo real estricto puede ser caro, pero en near-real-time es útil. Por ejemplo, una reunión puede procesarse por bloques de cinco minutos con late chunking, mientras se mantiene una memoria rápida por ventanas de 20 segundos. La capa rápida responde ahora; la capa tardía reindexa mejor cuando hay suficiente contexto.",
            ]),
            ("El problema de los chunks provisionales", [
                "Muchos sistemas fallan porque tratan el primer chunk como definitivo. En streaming, lo normal es lo contrario: el primer chunk suele ser provisional. Puede faltar la causa, la resolución o el dato que cambia la interpretación.",
                "Una solución práctica es usar estados. Un chunk puede nacer como `provisional`, pasar a `confirmado`, quedar `obsoleto` o ser `corregido_por` otro chunk. En recuperación, esos estados deben afectar al ranking. Si el usuario pregunta por el estado actual, un chunk corregido no debería competir en igualdad con uno confirmado hace 30 segundos.",
            ]),
            ("Indexación incremental", [
                "No todos los cambios merecen reembeddings inmediatos. En sistemas de alto volumen, conviene separar hot index y cold index. El hot index recibe chunks recientes, quizá con embeddings baratos o incluso solo búsqueda lexical temporal. El cold index consolida, resume y reembebe cuando hay más contexto.",
                "Otra técnica es mantener ids estables. Si un chunk provisional se actualiza, no siempre quieres crear un documento nuevo; a veces quieres reemplazar su representación y conservar trazabilidad. La decisión depende de auditoría. En soporte o salud quizá necesitas historial completo. En una app de productividad quizá basta con versión actual y log de cambios.",
            ]),
            ("Ranking temporal", [
                "La similitud semántica no basta. En tiempo real necesitas señales de recencia, estado y secuencia. Un chunk de ayer puede parecer semánticamente perfecto y estar completamente obsoleto. Un chunk de hace diez segundos puede ser menos parecido, pero contener la actualización que cambia la respuesta.",
                "Un ranking razonable combina similitud vectorial, match lexical, recencia, autoridad de fuente, estado del chunk, relación con la entidad preguntada y distancia temporal respecto al evento objetivo. Para preguntas de 'qué pasó', conviene recuperar secuencias; para preguntas de 'qué está pasando ahora', conviene priorizar estado vigente.",
            ]),
            ("Evaluación: cómo saber si funciona", [
                "No evalúes chunks mirando si parecen bonitos. Evalúa si recuperan la evidencia correcta. Crea un conjunto de preguntas reales con respuesta esperada y referencias a eventos concretos. Mide recall de evidencia, precisión de contexto, latencia de disponibilidad, tasa de chunks obsoletos recuperados y coste por minuto procesado.",
                "También mide daño por corte. Una métrica útil es contar cuántas respuestas fallidas recuperaron un chunk sobre el tema correcto pero sin la frase que contenía la respuesta. Ese patrón indica que el problema no es el embedding, sino la frontera del chunk.",
            ]),
            ("Errores de implementación", [
                "Cortar por tokens sin guardar estructura temporal.",
                "No distinguir evento original de timestamp de indexación.",
                "Reembeder todo ante cualquier cambio pequeño.",
                "Resumir demasiado pronto y perder detalles verificables.",
                "No conservar raw events para auditoría y reprocesado.",
                "Usar solo búsqueda vectorial y perder IDs, códigos de error o nombres exactos.",
                "No marcar chunks obsoletos cuando llega información correctiva.",
            ]),
            ("Diseño recomendado para empezar", [
                "Empieza simple: ventanas por tiempo o tokens, metadatos buenos, búsqueda híbrida y evaluación con preguntas reales. Añade chunking semántico solo cuando veas fallos causados por fronteras pobres, no porque suene más sofisticado.",
                "Para producción, separa tres caminos. Camino rápido: indexa chunks recientes con baja latencia. Camino de consolidación: fusiona, contextualiza y reembebe cuando llega más información. Camino de auditoría: conserva eventos originales y relaciones entre versiones. Esa separación evita que la necesidad de responder rápido destruya la calidad de la memoria a medio plazo.",
            ]),
            ("Conclusión", [
                "Real-time chunking es una pieza de infraestructura para agentes que viven conectados al mundo. Su trabajo no es partir texto: es preservar significado bajo presión de tiempo. Cuando funciona, el modelo responde con información reciente y trazable. Cuando falla, el sistema parece inteligente pero contesta con fragmentos incompletos, duplicados o caducados.",
                "La pregunta práctica no es 'cuántos tokens debe tener un chunk'. La pregunta es: cuál es la unidad mínima de evidencia que mi sistema puede recuperar sin mentir sobre cuándo ocurrió, de dónde salió y si todavía sigue siendo válida.",
            ]),
        ],
    },
    {
        "title": "IA en apuestas deportivas: modelos predictivos, cuotas y riesgos reales",
        "slug": "ia-apuestas-deportivas-modelos-riesgos",
        "meta_description": "Análisis técnico de IA en apuestas deportivas: modelos predictivos, calibración, cuotas, edge, trading, fraude, juego responsable y regulación.",
        "excerpt": "La IA puede mejorar análisis, pricing y detección de riesgo en apuestas deportivas. Lo que no puede hacer es eliminar el margen de la casa ni convertir incertidumbre en certeza.",
        "sources": [
            ("Machine learning for sports betting: accuracy or calibration?", "https://www.sciencedirect.com/science/article/pii/S266682702400015X"),
            ("NCAA: harassment related to sports betting", "https://www.ncaa.org/news/2025/11/18/media-center-ncaa-study-finds-over-one-third-of-di-mens-basketball-student-athletes-harassed-by-bettors"),
            ("NCAA: sports betting impact on college basketball", "https://ncaaorg.sidearmsports.com/news/2026/3/25/media-center-division-i-student-athletes-express-concerns-about-sports-bettings-impact-on-college-basketball.aspx"),
            ("American Gaming Association: Responsible Marketing Code", "https://www.americangaming.org/marketing-code/"),
            ("Michigan Gaming Control Board: illegal sportsbook cease-and-desist", "https://www.michigan.gov/mgcb/news/2025/04/28/mgcb-issues-cease-and-desist-orders-to-sportsbetting-and-betonline"),
            ("NBAPropLab: NBA player props analysis", "https://nbaproplab.com/"),
            ("FutPicks: football picks and predictions", "https://futpicks.com/"),
        ],
        "related": [
            ("Real-time chunking para RAG", "/real-time-chunking-rag-streaming/"),
            ("RTK: proxy CLI para reducir tokens", "/rtk-proxy-cli-reducir-tokens-ia/"),
            ("Serena MCP: búsqueda semántica", "/serena-mcp-busqueda-semantica-codigo/"),
        ],
        "sections": [
            ("La tesis incómoda", [
                "La IA en apuestas deportivas tiene usos serios: pricing, trading, gestión de riesgo, detección de fraude, análisis de lesiones, simulación de escenarios y protección de usuarios vulnerables. También tiene un lado mucho menos serio: productos que venden picks como si un modelo pudiera imprimir dinero.",
                "La frontera entre ambos mundos es técnica. Un sistema responsable habla de probabilidades, calibración, límites, incertidumbre y trazabilidad. Un sistema oportunista habla de aciertos, rachas, confianza absoluta y 'apuestas seguras'. En deporte no hay apuestas seguras; hay precios, riesgo y varianza.",
            ]),
            ("Cómo se modela una apuesta", [
                "Una apuesta no empieza con 'quién gana'. Empieza con una probabilidad y una cuota. Si una cuota decimal es 2.00, su probabilidad implícita bruta es 50%. Si la cuota es 1.80, la probabilidad implícita es 55,6%. Pero esa cifra incluye margen de la casa cuando miras el mercado completo.",
                "El trabajo del modelo es estimar una probabilidad propia y compararla con la probabilidad implícita ajustada. Si el modelo estima 60% y el mercado, sin margen, paga como si fuera 52%, existe edge teórico. Si estima 54%, quizá no hay ventaja suficiente para cubrir error, comisiones, límites y varianza.",
            ]),
            ("Accuracy no es suficiente", [
                "En apuestas, un modelo puede acertar muchos favoritos y aun así perder dinero. La métrica crítica no es solo accuracy, sino calibración. Cuando el modelo dice 60%, eventos similares deberían ocurrir alrededor del 60% de las veces. Si ocurren el 52%, el modelo está sobreconfiado aunque acierte a menudo.",
                "También importan log loss, Brier score, calibration curves, expected value por segmento, closing line value y rendimiento fuera de muestra. Un modelo que gana en backtest pero pierde contra la closing line probablemente no está descubriendo información nueva; solo está sobreajustado al histórico.",
            ]),
            ("Datos que sí importan", [
                "El dataset mínimo depende del deporte, pero suele incluir forma de equipo, fuerza del rival, localía, descanso, viajes, lesiones, alineaciones, minutos esperados, estilo, ritmo, clima, árbitro, congestión de calendario y cuotas históricas.",
                "En deportes de baja anotación, como fútbol, variables de calidad de ocasión suelen ser más útiles que resultado bruto. En baloncesto, posesiones, ritmo, eficiencia, usage y disponibilidad de jugadores pesan mucho. En tenis, superficie, fatiga, historial de servicio/resto y estado físico pueden cambiar el precio. El modelo debe respetar la estructura del deporte; una red genérica sobre resultados rara vez basta.",
            ]),
            ("Ejemplos de producto donde se ve el problema", [
                "En mercados de player props, una herramienta como NBAPropLab encaja porque el reto no es solo predecir si un jugador supera una línea. Hay que comparar minutos esperados, uso, matchup, ritmo, bajas de compañeros, cuota implícita y tamaño de stake. Ese tipo de producto obliga a separar predicción deportiva de decisión de apuesta.",
                "En fútbol, un producto como FutPicks ilustra otro patrón: convertir modelos estadísticos en picks legibles para usuario final. Ahí el valor no está en decir 'gana el local', sino en explicar qué probabilidad estima el sistema, qué mercado se está evaluando y qué histórico respalda la recomendación.",
            ]),
            ("Pipeline técnico", [
                "Primero ingesta: resultados, box scores, tracking, lesiones, noticias, calendario y cuotas. Segundo normalización: resolver nombres de equipos, jugadores, competiciones, casas y mercados. Tercero feature store: calcular variables reproducibles con timestamps correctos para evitar leakage.",
                "Cuarto entrenamiento: modelos probabilísticos, gradient boosting, Poisson, Elo dinámico, bayesianos jerárquicos, redes temporales o ensembles. Quinto calibración: isotonic regression, Platt scaling, temperature scaling o calibración por buckets. Sexto comparación con mercado: convertir cuotas en probabilidades, quitar margen y estimar edge. Séptimo control: límites de stake, exposición correlacionada y auditoría.",
            ]),
            ("El leakage es el enemigo", [
                "Muchos backtests de apuestas son falsamente buenos porque usan información que no estaba disponible en el momento de apostar. Una alineación confirmada, una cuota de cierre o una estadística corregida después del partido no pueden aparecer en una predicción simulada de la mañana anterior.",
                "La regla de oro es guardar `available_at` para cada dato. No basta con saber cuándo ocurrió un partido; hay que saber cuándo el sistema conoció cada noticia, cuota, lesión o cambio de mercado. Sin esa disciplina temporal, el modelo aprende del futuro.",
            ]),
            ("Mercados prepartido e in-play", [
                "Prepartido permite más tiempo para cálculo, limpieza y explicación. In-play exige latencia baja, feeds fiables y modelos que actualicen probabilidades con eventos: goles, tarjetas, faltas, posesiones, lesiones, sustituciones o cambios tácticos.",
                "Aquí aparecen arquitecturas cercanas al real-time chunking: eventos vivos, estado actualizado, ranking temporal y corrección de información. Un modelo in-play que procesa tarde una roja o duplica una lesión puede producir precios peligrosos. La velocidad no sirve si el estado del partido está mal representado.",
            ]),
            ("LLMs: interfaz, no oráculo", [
                "Los modelos generativos son útiles para resumir noticias, explicar movimientos de cuota, convertir informes médicos en variables candidatas, generar reportes y ayudar a un analista a entender por qué el modelo cambió una probabilidad.",
                "No deberían ser el motor final de pricing sin una capa cuantitativa medible. Un LLM puede sonar convincente y estar desactualizado, ignorar la cuota, inventar causalidad o no calibrar incertidumbre. En apuestas, una predicción sin precio es incompleta. Decir 'me gusta el favorito' no significa nada si la cuota ya descuenta esa superioridad.",
            ]),
            ("Gestión de banca y stake", [
                "Aunque exista edge, el stake decide supervivencia. Kelly Criterion y variantes fraccionarias intentan ajustar tamaño de apuesta al valor esperado y probabilidad estimada. En producción, casi siempre se usan versiones conservadoras porque las probabilidades del modelo tienen error.",
                "Un sistema serio limita exposición por deporte, liga, mercado, jugador, evento y correlación. Apostar over de puntos de un jugador, victoria de su equipo y over total del partido puede parecer tres edges independientes y ser una sola tesis apalancada. La IA puede ayudar a detectar esa correlación antes de que la cartera dependa de un mismo supuesto.",
            ]),
            ("Detección de fraude e integridad", [
                "Los operadores y ligas pueden usar IA para detectar patrones anómalos: movimientos de cuota no explicados, volumen extraño en mercados pequeños, cuentas relacionadas, apuestas coordinadas, uso de información privilegiada o props vulnerables.",
                "La preocupación no es abstracta. La expansión de mercados granulares aumenta presión sobre atletas y oficiales. La NCAA ha publicado datos sobre acoso relacionado con apuestas y ha pedido limitar determinados prop bets universitarios. Cuanto más individual y granular es un mercado, más fácil es que una persona concreta reciba presión o abuso.",
            ]),
            ("Juego responsable con IA", [
                "La IA también puede usarse para proteger, no solo para vender. Un operador puede detectar cambios de comportamiento: depósitos más frecuentes, persecución de pérdidas, sesiones largas, aumento brusco de stake, apuestas nocturnas repetidas o uso compulsivo de cash out.",
                "El reto ético es que el mismo perfilado que detecta riesgo podría usarse para maximizar gasto. Por eso hacen falta políticas claras: límites, pausas, mensajes responsables, autoexclusión, no usar lenguaje de certeza y no promocionar 'risk free' cuando existe riesgo real. El código de marketing responsable de la AGA va en esa dirección al rechazar mensajes que sugieran ausencia de riesgo.",
            ]),
            ("Cómo auditar un modelo de apuestas", [
                "Separa backtest, validación temporal y producción. Publica o conserva todas las predicciones, no solo las ganadoras. Mide calibración por rangos de probabilidad, deporte, mercado y temporada. Compara contra closing line value. Revisa drawdowns y no escondas rachas negativas.",
                "También audita explicabilidad. Si un modelo cambia de 51% a 58%, debe haber una razón trazable: lesión, alineación, movimiento de mercado, cambio de clima, noticia, fatiga o actualización de rating. Si nadie puede explicar el salto, el sistema no está listo para automatizar stake.",
            ]),
            ("Señales de humo en productos de picks", [
                "Prometen rentabilidad fija.",
                "Muestran capturas de aciertos sin histórico completo.",
                "No publican cuotas tomadas ni hora de entrada.",
                "Confunden probabilidad con confianza narrativa.",
                "No hablan de límite de stake, varianza ni drawdown.",
                "Usan 'IA' como marca, pero no explican calibración ni metodología.",
                "Venden urgencia constante para empujar apuestas impulsivas.",
            ]),
            ("Dónde sí hay oportunidad", [
                "Para medios: explicar mercados y movimientos de cuotas con más rigor.",
                "Para operadores: mejorar pricing, trading, fraude y juego responsable.",
                "Para reguladores: detectar patrones sospechosos y auditar mercados vulnerables.",
                "Para analistas: acelerar investigación, limpiar datos y documentar hipótesis.",
                "Para usuarios avanzados: controlar banca, registrar decisiones y reducir sesgos, no perseguir milagros.",
            ]),
            ("Conclusión", [
                "La IA va a cambiar las apuestas deportivas, pero no de la forma que prometen los vendedores de picks. El cambio real estará en pricing más dinámico, mercados más granulares, detección de anomalías, análisis en tiempo real y regulación más exigente.",
                "La versión honesta es menos viral: la IA puede ayudarte a estimar mejor, explicar mejor y controlar mejor. No elimina el margen de la casa, no borra la varianza y no convierte el deporte en una hoja de cálculo determinista. Quien ignore eso no está usando IA; está automatizando autoengaño.",
            ]),
        ],
    },
    {
        "title": "Value betting: cómo calcular probabilidad implícita y edge sin engañarte",
        "slug": "value-betting-probabilidad-implicita-edge",
        "status": "scheduled",
        "published_at": "2026-05-27T08:00:00.000Z",
        "meta_description": "Guía técnica de value betting: probabilidad implícita, margen de la casa, edge, closing line value, stake y errores comunes.",
        "excerpt": "Value betting no es encontrar favoritos ni seguir rachas. Es comparar una probabilidad estimada contra una cuota, después de quitar margen, incertidumbre y coste de equivocarte.",
        "sources": [
            ("Machine learning for sports betting: accuracy or calibration?", "https://www.sciencedirect.com/science/article/pii/S266682702400015X"),
            ("NBAPropLab: NBA player props analysis", "https://nbaproplab.com/"),
            ("FutPicks: football picks and predictions", "https://futpicks.com/"),
            ("American Gaming Association: Responsible Marketing Code", "https://www.americangaming.org/marketing-code/"),
        ],
        "related": [
            ("IA en apuestas deportivas", "/ia-apuestas-deportivas-modelos-riesgos/"),
            ("Real-time chunking para RAG", "/real-time-chunking-rag-streaming/"),
            ("RTK: proxy CLI para reducir tokens", "/rtk-proxy-cli-reducir-tokens-ia/"),
        ],
        "sections": [
            ("La definicion practica", [
                "Value betting significa apostar solo cuando tu probabilidad estimada es mayor que la probabilidad implicita de la cuota, ajustada por margen y por error del modelo. No es adivinar ganadores. Es comprar una probabilidad mal valorada.",
                "Si una cuota decimal es 2.20, la probabilidad implicita bruta es 45,45%. Si tu modelo estima 52%, parece haber edge. Pero ese calculo todavia no basta: falta quitar margen de mercado, medir calibracion, revisar liquidez y decidir stake.",
            ]),
            ("Probabilidad implicita", [
                "La formula base es simple: probabilidad implicita = 1 / cuota decimal. Una cuota 1.50 implica 66,7%. Una cuota 2.00 implica 50%. Una cuota 3.25 implica 30,8%. El problema es que las casas no ofrecen probabilidades limpias: incorporan margen.",
                "En un mercado 1X2, si las probabilidades implicitas de local, empate y visitante suman 106%, ese 6% extra es overround. Para comparar tu modelo contra el mercado, primero normalizas esas probabilidades dividiendo cada una por la suma total. Sin ese paso, puedes creer que hay valor donde solo hay margen.",
            ]),
            ("Edge esperado", [
                "El valor esperado de una apuesta decimal puede expresarse como EV = p * cuota - 1. Si p = 0.52 y cuota = 2.10, EV = 0.52 * 2.10 - 1 = 0.092, es decir 9,2% teorico. Suena bien, pero un EV positivo calculado con una probabilidad mal calibrada es solo una ilusion numerica.",
                "Por eso los sistemas serios separan prediccion, calibracion y decision. Primero estiman probabilidad. Despues revisan si historicamente los eventos al 52% ocurren cerca del 52%. Solo entonces comparan contra cuota y deciden si hay apuesta.",
            ]),
            ("Closing line value", [
                "Closing line value, o CLV, mide si tu cuota fue mejor que la cuota de cierre. Si tomas 2.10 y el mercado cierra en 1.95, probablemente entraste antes de que el mercado corrigiera. Si tomas 2.10 y cierra en 2.30, quizas tu edge era falso o llego informacion contra tu posicion.",
                "CLV no garantiza beneficio en cada apuesta, pero es una buena senal de proceso. En mercados eficientes, batir consistentemente la linea de cierre suele importar mas que mirar una racha corta de aciertos.",
            ]),
            ("Aplicacion a productos reales", [
                "En player props de NBA, una herramienta como NBAPropLab puede usar el mismo marco: convertir linea y cuota en probabilidad implicita, estimar distribucion propia del jugador y comparar. La parte dificil esta en minutos esperados, rol, ritmo, matchup y bajas que cambian usage.",
                "En futbol, FutPicks encaja en el lado de picks y predicciones: el valor de un sistema no deberia medirse solo por aciertos, sino por si publica probabilidades, mercados, cuotas y track record con suficiente transparencia.",
            ]),
            ("Stake: donde se rompe la teoria", [
                "Aunque haya edge, apostar demasiado destruye una estrategia. Kelly Criterion propone stake proporcional a ventaja y cuota, pero en modelos con error se usa casi siempre Kelly fraccional o limites mas simples. La razon es pragmatica: tu probabilidad no es la verdad, es una estimacion.",
                "Un buen sistema aplica caps por mercado, deporte, evento y correlacion. Si tres picks dependen de la misma lesion, no son tres riesgos independientes. Son una sola tesis multiplicada.",
            ]),
            ("Errores comunes", [
                "Comparar contra la cuota sin quitar margen.",
                "Usar accuracy en lugar de calibracion.",
                "No guardar la hora exacta de la cuota tomada.",
                "Evaluar picks sin cuota disponible en ese momento.",
                "Subir stake despues de una mala racha para recuperar perdidas.",
                "Confundir una prediccion correcta con una apuesta de valor.",
            ]),
            ("Conclusion", [
                "Value betting es una disciplina de precios, no de corazonadas. La pregunta no es si algo va a pasar; la pregunta es si la cuota paga mas de lo que deberia pagar segun una probabilidad razonablemente calibrada.",
                "Cuando un producto de apuestas con IA no muestra probabilidad, cuota, margen, stake e historico, no esta haciendo value betting. Esta contando historias con numeros.",
            ]),
        ],
    },
    {
        "title": "Player props NBA: variables que debe mirar un modelo antes de recomendar una apuesta",
        "slug": "player-props-nba-modelo-variables",
        "status": "scheduled",
        "published_at": "2026-05-30T08:00:00.000Z",
        "meta_description": "Guía técnica de modelos para player props NBA: minutos, usage, ritmo, matchup, lesiones, líneas, cuotas, calibración y control de stake.",
        "excerpt": "Los player props parecen apuestas simples, pero un modelo serio necesita minutos, rol, matchup, ritmo, lesiones y precio. Sin cuota, una predicción no es una apuesta.",
        "sources": [
            ("NBAPropLab: NBA player props analysis", "https://nbaproplab.com/"),
            ("NBA Stats", "https://www.nba.com/stats"),
            ("Basketball Reference", "https://www.basketball-reference.com/"),
            ("Machine learning for sports betting: accuracy or calibration?", "https://www.sciencedirect.com/science/article/pii/S266682702400015X"),
        ],
        "related": [
            ("IA en apuestas deportivas", "/ia-apuestas-deportivas-modelos-riesgos/"),
            ("Value betting y probabilidad implicita", "/value-betting-probabilidad-implicita-edge/"),
            ("Real-time chunking para RAG", "/real-time-chunking-rag-streaming/"),
        ],
        "sections": [
            ("Por que los props son dificiles", [
                "Un prop de jugador parece una pregunta binaria: mas o menos que una linea. En realidad es una distribucion. Para puntos, rebotes, asistencias o triples, el modelo no deberia decir solo over o under. Debe estimar una distribucion alrededor de minutos esperados, rol y contexto de partido.",
                "La dificultad aumenta porque la NBA cambia rapido. Una baja de ultima hora puede convertir a un jugador secundario en primera opcion ofensiva. Un blowout puede cortar minutos. Una defensa que concede muchos rebotes a pivots no afecta igual a todos los perfiles.",
            ]),
            ("Minutos esperados", [
                "Los minutos son la variable reina. Muchos modelos fallan porque predicen produccion por minuto razonablemente bien, pero estiman mal cuanto tiempo jugara el jugador. Rotacion, faltas, back-to-back, gestion de carga, lesiones y blowout risk afectan directamente al techo y suelo de cualquier prop.",
                "Una practica sana es separar modelo de minutos y modelo de produccion. Primero estimas rango de minutos. Despues estimas tasas por minuto. Finalmente combinas ambas distribuciones. Mezclarlo todo en una unica caja negra dificulta saber por que fallo la apuesta.",
            ]),
            ("Usage y rol", [
                "Usage no es solo volumen de tiros. Cambia cuando faltan companeros, cuando un base dominante vuelve de lesion o cuando un equipo modifica quintetos. Para puntos y asistencias, las ausencias de alto usage pueden ser mas importantes que el promedio de temporada.",
                "Tambien importa el tipo de rol. Un tirador dependiente de catch-and-shoot necesita creacion externa. Un jugador con balon puede absorber mas posesiones si falta otro generador. El modelo debe distinguir oportunidad de eficiencia.",
            ]),
            ("Matchup y estilo", [
                "Ritmo, defensa del rival, switches, proteccion de aro, rebote defensivo y perfil de faltas cambian la distribucion. No basta con decir que un rival concede muchos puntos a una posicion; las posiciones son etiquetas pobres. Importa como defiende acciones concretas.",
                "Para rebotes, el modelo deberia mirar volumen de tiros esperados, eficiencia del rival, rebote ofensivo permitido y emparejamientos probables. Para asistencias, pace, conversion de companeros y defensa de pick-and-roll pueden pesar mas que el promedio bruto.",
            ]),
            ("Linea y cuota", [
                "Una buena prediccion no sirve si el precio es malo. Si el modelo estima media 24,1 puntos y la linea esta en 23,5, eso no implica apuesta automatica. Necesitas distribucion, probabilidad de over, cuota disponible y margen.",
                "Aqui una herramienta como NBAPropLab tiene sentido como interfaz: ayuda a pasar de analisis de jugador a decision cuantitativa. La decision final debe comparar probabilidad propia contra probabilidad implicita, no solo mostrar una proyeccion bonita.",
            ]),
            ("Calibracion por mercado", [
                "No todos los props calibran igual. Puntos, rebotes, asistencias, triples y combinados tienen distribuciones distintas. Un modelo puede ser bueno en puntos y flojo en asistencias. Tambien puede funcionar en titulares y romperse en suplentes con minutos volatiles.",
                "Evalua por segmento: jugadores con mas de 30 minutos, bench players, partidos con spread alto, back-to-backs, props alternativos y lineas principales. Si todo se mezcla en una sola metrica, los errores quedan escondidos.",
            ]),
            ("Errores comunes", [
                "Usar promedios de temporada sin ajustar por rol reciente.",
                "Ignorar lesiones de companeros que cambian usage.",
                "No modelar blowout risk.",
                "Tratar la linea como si fuera prediccion de mercado limpia.",
                "No guardar cuota, sportsbook y timestamp.",
                "Evaluar por aciertos sin mirar CLV ni calibracion.",
            ]),
            ("Conclusion", [
                "Un modelo de player props no compite por tener una proyeccion llamativa. Compite por estimar mejor la distribucion que el mercado y por saber cuando el precio compensa el riesgo.",
                "La ventaja aparece cuando conectas baloncesto, datos y mercado. Si falta cualquiera de las tres piezas, el modelo puede sonar tecnico y seguir apostando a ciegas.",
            ]),
        ],
    },
    {
        "title": "Predicciones de fútbol con Poisson, xG y calibración: qué puede hacer la IA",
        "slug": "predicciones-futbol-poisson-xg-calibracion",
        "status": "scheduled",
        "published_at": "2026-06-03T08:00:00.000Z",
        "meta_description": "Guía técnica de predicciones de fútbol con Poisson, expected goals, ratings, calibración, cuotas, value betting y límites de la IA.",
        "excerpt": "Predecir fútbol no va de acertar marcadores exactos. Va de estimar distribuciones de goles, calibrar probabilidades y compararlas con precios reales de mercado.",
        "sources": [
            ("FutPicks: football picks and predictions", "https://futpicks.com/"),
            ("StatsBomb: expected goals explained", "https://statsbomb.com/soccer-metrics/expected-goals-xg-explained/"),
            ("Machine learning for sports betting: accuracy or calibration?", "https://www.sciencedirect.com/science/article/pii/S266682702400015X"),
            ("American Gaming Association: Responsible Marketing Code", "https://www.americangaming.org/marketing-code/"),
        ],
        "related": [
            ("IA en apuestas deportivas", "/ia-apuestas-deportivas-modelos-riesgos/"),
            ("Value betting y probabilidad implicita", "/value-betting-probabilidad-implicita-edge/"),
            ("Real-time chunking para RAG", "/real-time-chunking-rag-streaming/"),
        ],
        "sections": [
            ("La dificultad del fútbol", [
                "El fútbol es un deporte de baja anotacion. Eso significa que el resultado final contiene mucho ruido. Un equipo puede generar mejores ocasiones y perder 0-1. Un modelo que aprende solo de resultados puede confundir varianza con calidad.",
                "Por eso muchos enfoques empiezan por distribuciones de goles, ratings ofensivos y defensivos, expected goals, localia y estado reciente. El objetivo no es acertar el marcador exacto, sino estimar probabilidades de mercados: 1X2, over/under, ambos marcan, handicaps o correct score.",
            ]),
            ("Modelo Poisson base", [
                "El modelo Poisson estima la probabilidad de que un equipo marque 0, 1, 2 o mas goles dado un promedio esperado. Si el local tiene lambda 1.55 y el visitante 0.95, puedes construir una matriz de marcadores y derivar probabilidades para victoria local, empate, visitante y totales.",
                "La ventaja es que es interpretable. La debilidad es que asume independencia y puede quedarse corto ante estilos, tarjetas, calendario, lesiones o cambios tacticos. Aun asi, como baseline es mas honesto que muchos modelos opacos.",
            ]),
            ("xG frente a goles", [
                "Expected goals intenta medir calidad de ocasiones, no solo goles marcados. Para prediccion, xG suele ser mas estable que resultado final porque reduce ruido. Un equipo que gana tres partidos con pocos tiros y bajo xG puede estar sobreperformando.",
                "El uso correcto no es meter xG sin pensar. Conviene separar xG a favor, xG en contra, calidad de rivales, localia, tiros concedidos, transiciones y balon parado. En ligas con datos pobres, la calidad del feed puede limitar mas que el algoritmo.",
            ]),
            ("De probabilidad a pick", [
                "Un sistema como FutPicks puede convertir modelos de futbol en picks legibles, pero la parte importante es conservar trazabilidad: mercado, cuota, probabilidad estimada, hora de publicacion y resultado. Sin eso, el usuario solo ve una recomendacion aislada.",
                "El salto de modelo a pick exige comparar contra mercado. Si el modelo da 58% para over 2.5 y la cuota implica 54% despues de quitar margen, puede haber valor. Si la cuota implica 60%, la misma prediccion no es apuesta.",
            ]),
            ("Calibracion", [
                "La calibracion responde a una pregunta simple: cuando el modelo dice 70%, ocurre cerca del 70%? En futbol, muchos modelos estan mal calibrados en favoritos fuertes, empates y mercados de baja frecuencia.",
                "Puedes usar calibration curves, Brier score y validacion temporal. No sirve mezclar temporadas al azar si el objetivo es simular decisiones reales. El modelo debe entrenar con pasado y predecir futuro, respetando cuando cada dato estaba disponible.",
            ]),
            ("IA generativa en fútbol", [
                "Un LLM puede resumir noticias, explicar lesiones, convertir reportes en variables candidatas o generar previews de partido. Pero no deberia inventar probabilidades. La probabilidad debe salir de un modelo cuantitativo o de un trader con proceso auditable.",
                "La mejor arquitectura combina modelo estadistico, capa de datos, explicacion generativa y control editorial. La IA generativa redacta; no decide stake.",
            ]),
            ("Errores comunes", [
                "Optimizar correct score como si fuera el mercado principal.",
                "No ajustar por margen de la casa.",
                "Usar goles recientes sin mirar calidad de ocasiones.",
                "Ignorar calendario, rotaciones y motivacion competitiva.",
                "No medir calibracion por liga y mercado.",
                "Presentar confianza alta en partidos con poca informacion.",
            ]),
            ("Conclusion", [
                "La IA en predicciones de futbol funciona mejor cuando respeta la naturaleza probabilistica del deporte. Poisson, xG y ratings no eliminan incertidumbre; la hacen mas visible.",
                "Un buen producto no promete acertar todos los picks. Explica como llega a una probabilidad, contra que cuota la compara y que historico tiene cuando se equivoca.",
            ]),
        ],
    },
    {
        "title": "MCP en producción: seguridad, permisos y supply chain para agentes de IA",
        "slug": "mcp-produccion-seguridad-permisos-supply-chain",
        "status": "scheduled",
        "published_at": "2026-06-06T08:00:00.000Z",
        "meta_description": "Guía técnica para usar MCP en producción: autorización, permisos, token passthrough, servidores externos, supply chain y controles de seguridad.",
        "excerpt": "MCP permite que los agentes usen herramientas reales. Esa es su fuerza y tambien su riesgo: cada servidor nuevo amplia la superficie de ataque.",
        "sources": [
            ("Model Context Protocol: Registry", "https://modelcontextprotocol.io/registry/about"),
            ("MCP Authorization specification", "https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization"),
            ("MCP Security Best Practices", "https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices"),
            ("NSA: MCP security design considerations", "https://www.nsa.gov/Press-Room/Press-Releases-Statements/Press-Release-View/Article/4496698/nsa-releases-security-design-considerations-for-ai-driven-automation-leveraging/"),
        ],
        "related": [
            ("Serena MCP: busqueda semantica", "/serena-mcp-busqueda-semantica-codigo/"),
            ("Real-time chunking para RAG", "/real-time-chunking-rag-streaming/"),
            ("RTK: proxy CLI para reducir tokens", "/rtk-proxy-cli-reducir-tokens-ia/"),
        ],
        "sections": [
            ("La promesa y el riesgo", [
                "Model Context Protocol resuelve un problema real: cada agente necesita acceso a herramientas, repositorios, bases de datos, navegadores, CRMs, tickets o documentacion. Sin un protocolo comun, cada integracion termina siendo una pieza ad hoc dificil de auditar.",
                "Pero MCP tambien convierte a los agentes en operadores de sistemas. Si un servidor puede leer archivos, ejecutar comandos, consultar clientes o escribir en produccion, el problema deja de ser solo de prompt engineering. Entra en seguridad, permisos, identidad, logging y supply chain.",
            ]),
            ("Modelo mental correcto", [
                "Un servidor MCP no deberia verse como un plugin inocente. Debe tratarse como una dependencia ejecutable con permisos. La pregunta no es si el servidor funciona, sino que puede hacer, con que identidad, sobre que datos, bajo que aprobaciones y con que trazabilidad.",
                "El registro oficial ayuda a descubrir servidores, pero descubrir no equivale a aprobar. En produccion, cada servidor necesita revision como cualquier paquete que toca datos o automatiza acciones.",
            ]),
            ("Permisos minimos", [
                "Empieza por scopes pequenos. Si un agente solo necesita leer issues, no le des permisos para cerrar issues. Si solo necesita consultar logs, no le des credenciales para modificar infraestructura. Si un flujo requiere escritura, separa lectura, propuesta y accion final.",
                "El patron sano es defensa por capas: permisos del servidor, permisos del token, permisos del usuario, allowlists de herramientas, confirmaciones para acciones destructivas y logs que permitan reconstruir quien pidio que.",
            ]),
            ("Autorizacion y token passthrough", [
                "La especificacion de seguridad de MCP es clara al tratar token passthrough como un riesgo. Pasar tokens entre componentes sin audiencia correcta rompe aislamiento: un token emitido para un servicio puede acabar siendo usado por otro contexto.",
                "En entornos serios, cada servidor debe recibir tokens con audiencia y alcance apropiados. Tambien conviene separar identidad humana de identidad de agente. Si todo ocurre con un token personal amplio, no podras distinguir automatizacion legitima de abuso.",
            ]),
            ("Supply chain de servidores MCP", [
                "El riesgo no esta solo en servidores maliciosos. Tambien esta en servidores abandonados, dependencias transitivas, comandos shell sin sanitizar, marketplaces sin revision y configuraciones copiadas de ejemplos. Un MCP que parece util puede convertirse en canal de ejecucion local.",
                "Antes de instalar, revisa repositorio, mantenedores, permisos solicitados, transporte usado, comandos ejecutados, dependencias y frecuencia de releases. Si el servidor pide mas de lo que necesita, esa es una senal para aislarlo o descartarlo.",
            ]),
            ("Checklist de adopcion", [
                "Inventario de servidores MCP aprobados.",
                "Scopes por servidor y por entorno.",
                "Tokens con audiencia separada.",
                "Logs de cada tool call relevante.",
                "Aprobacion humana para escritura sensible.",
                "Sandbox o contenedor para servidores no confiables.",
                "Proceso de retirada si una dependencia se vuelve insegura.",
            ]),
            ("Conclusion", [
                "MCP sera una pieza importante del stack de agentes, pero no deberia entrar en produccion como un conjunto de plugins instalados por conveniencia. Cuanto mas util es un servidor MCP, mas permisos suele necesitar.",
                "La regla practica: si no sabes explicar que puede hacer un servidor MCP en una frase concreta, todavia no deberia estar conectado a un agente con acceso a datos reales.",
            ]),
        ],
    },
    {
        "title": "AGENTS.md, CLAUDE.md y memoria de proyecto: cómo dar contexto a agentes de código",
        "slug": "agents-md-claude-md-memoria-proyecto",
        "status": "scheduled",
        "published_at": "2026-06-10T08:00:00.000Z",
        "meta_description": "Guía práctica para AGENTS.md, CLAUDE.md y memoria de proyecto: instrucciones, precedencia, testing, estilo, contexto y errores comunes.",
        "excerpt": "Los agentes de codigo no fallan solo por el modelo. Fallan porque no saben como se trabaja en tu repo. Las instrucciones de proyecto son parte del sistema.",
        "sources": [
            ("OpenAI Codex: AGENTS.md", "https://github.com/openai/codex/blob/main/docs/agents_md.md"),
            ("Claude Code memory", "https://code.claude.com/docs/en/memory"),
            ("Claude Help: CLAUDE.md and better prompts", "https://support.claude.com/en/articles/14553240-give-claude-context-claude-md-and-better-prompts"),
            ("Configuring Agentic AI Coding Tools", "https://arxiv.org/abs/2602.14690"),
        ],
        "related": [
            ("Claude Code: guia completa", "/claude-code-que-es-guia-completa/"),
            ("Serena MCP: busqueda semantica", "/serena-mcp-busqueda-semantica-codigo/"),
            ("VS Code y Copilot Co-authored-by", "/vs-code-copilot-coauthored-by-commits/"),
        ],
        "sections": [
            ("La idea", [
                "Un buen `AGENTS.md` o `CLAUDE.md` no intenta ensenar a programar al modelo. Le ensena como se trabaja en ese proyecto: comandos, limites, convenciones, arquitectura, pruebas, estilo de commits y zonas que no debe tocar sin permiso.",
                "Ese contexto reduce una clase de errores muy comun: el agente hace algo razonable en abstracto pero incorrecto para tu repo. Ejecuta el test equivocado, ignora un generador, edita codigo generado o aplica una convencion que el equipo no usa.",
            ]),
            ("Que debe contener", [
                "Comandos de instalacion, test y lint realmente usados.",
                "Estructura del repo y ownership basico.",
                "Patrones que debe copiar antes de crear abstracciones nuevas.",
                "Archivos generados o zonas que no debe editar manualmente.",
                "Politica de migraciones, seeds, fixtures y datos sensibles.",
                "Reglas de Git: ramas, commits, PRs y mensajes.",
                "Criterios de verificacion antes de dar una tarea por terminada.",
            ]),
            ("Que no debe contener", [
                "No metas documentacion completa. Un archivo de instrucciones demasiado largo se convierte en ruido. Tampoco incluyas secretos, tokens, informacion personal o decisiones temporales que caducan rapido.",
                "La memoria de proyecto debe ser estable. Si una regla solo aplica hoy, mejor ponerla en el ticket o en el prompt. Si aplica siempre, merece vivir en el archivo de contexto.",
            ]),
            ("Precedencia y alcance", [
                "El problema dificil no es escribir instrucciones, sino saber cuales aplican cuando hay varias. Codex, Claude Code y otros agentes pueden leer instrucciones globales, de proyecto o de subdirectorio. Eso permite precision, pero tambien conflictos.",
                "La regla practica es jerarquia clara: global para preferencias personales, raiz del repo para normas de proyecto, subdirectorios para excepciones locales. Si dos archivos se contradicen, el agente puede improvisar. Evitalo escribiendo instrucciones concretas y no filosoficas.",
            ]),
            ("Ejemplo de seccion util", [
                "`Tests`: usa `npm test -- --runInBand` para cambios en backend; usa `npm run test:ui` solo cuando cambien componentes. No ejecutes suites E2E completas salvo que el cambio toque checkout, login o permisos.",
                "Este tipo de instruccion es mejor que `ejecuta tests adecuados`, porque reduce decision ambigua. El agente no necesita adivinar que significa adecuado en tu equipo.",
            ]),
            ("Mantenimiento", [
                "Revisa las instrucciones cada vez que cambie el workflow. Si migras de Jest a Vitest y el archivo sigue diciendo Jest, el agente obedecera una mentira. Si cambias arquitectura y no actualizas ownership, empezara a tocar sitios equivocados.",
                "Tambien conviene auditar instrucciones despues de fallos repetidos. Cuando un agente comete el mismo error dos veces, no siempre hace falta un prompt mas largo; a veces falta una regla de proyecto corta y verificable.",
            ]),
            ("Conclusion", [
                "Los archivos de instrucciones son infraestructura de colaboracion humano-agente. No sustituyen tests ni revision, pero hacen que el agente empiece cada tarea con el mapa correcto.",
                "Un buen archivo no dice 'se cuidadoso'. Dice exactamente como se construye, prueba, revisa y limita el trabajo en ese repo.",
            ]),
        ],
    },
    {
        "title": "Pull requests hechos por agentes: cómo mantener gobernanza humana sin frenar el flujo",
        "slug": "pull-requests-agentes-ia-gobernanza-humana",
        "status": "scheduled",
        "published_at": "2026-06-13T08:00:00.000Z",
        "meta_description": "Cómo revisar pull requests creados por agentes de IA: ownership, aprobaciones, trazabilidad, tests, riesgos y merge governance.",
        "excerpt": "Los agentes pueden iniciar trabajo y abrir PRs, pero la autoridad de merge no deberia diluirse. La productividad aparece cuando automatizas trabajo, no responsabilidad.",
        "sources": [
            ("Collaborator or Assistant? AI Coding Agents Across PR Lifecycles", "https://arxiv.org/abs/2605.08017"),
            ("How AI Coding Agents Communicate in Pull Requests", "https://arxiv.org/abs/2602.17084"),
            ("AIDev: Studying AI Coding Agents on GitHub", "https://arxiv.org/abs/2602.09185"),
            ("GitHub Docs: pull request reviews", "https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests"),
        ],
        "related": [
            ("Copilot Code Review y GitHub Actions", "/copilot-code-review-minutos-github-actions/"),
            ("VS Code y Copilot Co-authored-by", "/vs-code-copilot-coauthored-by-commits/"),
            ("Zed Parallel Agents", "/zed-parallel-agents-editor-ia/"),
        ],
        "sections": [
            ("El cambio real", [
                "Los agentes de codigo ya no solo sugieren lineas dentro del editor. Pueden crear ramas, modificar varios archivos, ejecutar tests, abrir PRs y responder comentarios. Eso cambia el ciclo de desarrollo, pero no elimina la necesidad de gobernanza.",
                "La investigacion reciente sobre PRs de agentes muestra una separacion importante: la iniciativa operativa puede pasar al agente, mientras la autoridad final de merge sigue siendo humana. Ese desacoplamiento es sano si el equipo lo diseña conscientemente.",
            ]),
            ("Roles claros", [
                "Un PR de agente deberia declarar quien pidio el cambio, que objetivo tenia, que archivos toca, que pruebas corrio y que zonas quedan sin verificar. Si esa informacion no esta, el reviewer humano empieza en deuda.",
                "El agente puede ser autor operativo, pero el humano sigue siendo responsable de aceptar el cambio. La revision no debe convertirse en un sello rapido porque el diff 'lo hizo la IA'.",
            ]),
            ("Politica de aprobacion", [
                "No todos los PRs necesitan la misma rigidez. Documentacion, tests aislados o refactors mecanicos pueden tener una ruta ligera. Cambios de permisos, pagos, autenticacion, datos o migraciones necesitan revision fuerte y, a menudo, owner humano explicito.",
                "Una politica util separa PRs por riesgo: bajo, medio y alto. El agente puede abrir todos, pero no todos deberian poder fusionarse con el mismo numero de checks.",
            ]),
            ("Trazabilidad", [
                "El PR debe conservar la razon del cambio, no solo el resultado. Si un agente arreglo un bug, incluye reproduccion, causa probable, decision tomada y verificacion. Si genero tests, explica que comportamiento cubren y que no cubren.",
                "La trazabilidad importa mas con agentes porque el reviewer puede no haber visto el proceso. Sin contexto, un diff correcto puede esconder una suposicion fragil.",
            ]),
            ("Checklist para equipos", [
                "Etiqueta PRs creados o modificados por agentes.",
                "Exige resumen de cambios y comandos ejecutados.",
                "Bloquea auto-merge en zonas criticas.",
                "Mantiene CODEOWNERS o ownership equivalente.",
                "Pide tests nuevos cuando el agente cambia comportamiento.",
                "No aceptes PRs que mezclan refactor, estilo y logica sin necesidad.",
            ]),
            ("Senales de riesgo", [
                "Diff grande con resumen generico.",
                "Tests que solo prueban mocks nuevos.",
                "Cambios en seguridad sin explicacion de threat model.",
                "El agente toca archivos fuera del alcance pedido.",
                "El PR arregla el sintoma pero no reproduce el bug.",
                "Comentarios del reviewer se responden con texto plausible pero sin cambios verificables.",
            ]),
            ("Conclusion", [
                "La buena gobernanza no frena agentes; los vuelve utilizables. Permite que hagan trabajo repetitivo, exploratorio o mecanico sin perder control sobre decisiones irreversibles.",
                "La regla es simple: automatiza ejecucion, no aprobacion. Un agente puede empujar la rama; una persona debe seguir siendo responsable de por que entra en main.",
            ]),
        ],
    },
    {
        "title": "Codex, Claude Code y Cursor: cómo coordinar varios agentes sin duplicar trabajo",
        "slug": "coordinar-varios-agentes-codex-claude-cursor",
        "status": "scheduled",
        "published_at": "2026-06-17T08:00:00.000Z",
        "meta_description": "Guía práctica para coordinar varios agentes de código: Codex, Claude Code, Cursor, worktrees, ownership, tareas paralelas y revisión.",
        "excerpt": "El futuro cercano no es elegir un unico agente. Es saber dividir trabajo entre varios sin crear conflictos, duplicar contexto o perder trazabilidad.",
        "sources": [
            ("OpenAI: Codex", "https://openai.com/codex/"),
            ("OpenAI: Introducing the Codex app", "https://openai.com/index/introducing-the-codex-app/"),
            ("Claude Code GitHub Actions", "https://code.claude.com/docs/en/github-actions"),
            ("Zed Parallel Agents", "https://zed.dev/docs/ai/parallel-agents"),
        ],
        "related": [
            ("Zed Parallel Agents", "/zed-parallel-agents-editor-ia/"),
            ("Claude Code: guia completa", "/claude-code-que-es-guia-completa/"),
            ("Serena MCP: busqueda semantica", "/serena-mcp-busqueda-semantica-codigo/"),
        ],
        "sections": [
            ("El patron emergente", [
                "Muchos equipos ya no usan un solo asistente. Combinan autocomplete en IDE, agente de terminal, agente cloud para PRs, herramientas MCP y revisores automaticos. El problema deja de ser 'que modelo es mejor' y pasa a ser 'quien hace que parte del trabajo'.",
                "Sin coordinacion, varios agentes solo multiplican ruido: leen los mismos archivos, proponen cambios incompatibles y generan diffs dificiles de revisar. Con coordinacion, pueden convertir espera pasiva en avance paralelo.",
            ]),
            ("Divide por ownership", [
                "La division buena tiene fronteras claras. Un agente investiga sin editar. Otro escribe tests en un directorio. Otro actualiza documentacion. Otro prueba una alternativa en un worktree separado. La division mala pide a dos agentes que 'mejoren el mismo modulo'.",
                "Antes de lanzar trabajo paralelo, define contrato: objetivo, archivos permitidos, archivos prohibidos, salida esperada y verificacion. Si no puedes escribir ese contrato, la tarea no esta lista para paralelizarse.",
            ]),
            ("Worktrees y ramas", [
                "Los worktrees reducen conflictos porque cada agente trabaja en una copia separada del repo. Tambien permiten comparar alternativas sin contaminar la rama principal. Para refactors, bugs delicados o experimentos de arquitectura, son casi obligatorios.",
                "El coste es integracion. Alguien debe revisar que los cambios no se contradicen y decidir que se queda. El coordinador humano sigue siendo necesario.",
            ]),
            ("Que agente usar para que", [
                "Un agente de IDE suele ser mejor para cambios locales rapidos y feedback inmediato. Un agente de terminal funciona bien para tareas de repo, tests y scripts. Un agente cloud encaja en PRs, issues y trabajo asincrono. Un MCP especializado aporta contexto o herramientas que el modelo no deberia improvisar.",
                "La decision no deberia basarse solo en benchmark. Debe basarse en latencia, permisos, trazabilidad, coste, entorno y facilidad de revisar el resultado.",
            ]),
            ("Antipatrones", [
                "Lanzar varios agentes con el mismo prompt.",
                "Permitir que todos editen cualquier archivo.",
                "No fijar criterio de finalizacion.",
                "Mezclar tareas exploratorias y cambios de produccion.",
                "Aceptar el primer resultado solo porque ya compila.",
                "No guardar que agente hizo que y con que instrucciones.",
            ]),
            ("Workflow recomendado", [
                "Primero, descomponer: investigacion, tests, implementacion, docs, verificacion. Segundo, asignar ownership. Tercero, ejecutar en ramas o worktrees separados. Cuarto, integrar manualmente. Quinto, pasar una verificacion final con pruebas y review humana.",
                "El objetivo no es tener muchos agentes activos. Es reducir tiempo muerto sin perder control del resultado.",
            ]),
            ("Conclusion", [
                "Coordinar agentes se parece mas a liderar un equipo junior que a usar una herramienta magica. Hay que definir alcance, revisar entregables y mantener arquitectura.",
                "El equipo que gana no sera el que tenga mas agentes, sino el que mejor sepa darles fronteras pequenas, verificables y utiles.",
            ]),
        ],
    },
    {
        "title": "Métricas para agentes de código: cómo saber si realmente ahorran tiempo",
        "slug": "metricas-agentes-codigo-productividad-coste",
        "status": "scheduled",
        "published_at": "2026-06-20T08:00:00.000Z",
        "meta_description": "Métricas prácticas para evaluar agentes de código: tiempo ahorrado, acceptance rate, defectos, coste, PRs, revisiones y calidad.",
        "excerpt": "Un agente que genera mucho codigo no necesariamente ahorra tiempo. La metrica correcta es trabajo aceptado, verificado y mantenible por unidad de coste.",
        "sources": [
            ("AIDev: Studying AI Coding Agents on GitHub", "https://arxiv.org/abs/2602.09185"),
            ("Comparing AI Coding Agents: Task-Stratified PR Acceptance", "https://arxiv.org/abs/2602.08915"),
            ("How AI Coding Agents Modify Code", "https://arxiv.org/abs/2601.17581"),
            ("OpenAI Codex", "https://openai.com/codex/"),
        ],
        "related": [
            ("GitHub Copilot y AI Credits", "/github-copilot-ai-credits-pago-por-uso/"),
            ("RTK: proxy CLI para reducir tokens", "/rtk-proxy-cli-reducir-tokens-ia/"),
            ("Copilot Code Review y GitHub Actions", "/copilot-code-review-minutos-github-actions/"),
        ],
        "sections": [
            ("La trampa de medir output", [
                "Lineas generadas, commits creados o PRs abiertos no miden productividad. Pueden medir actividad. Un agente puede producir mucho codigo y aun asi aumentar trabajo si obliga a revisar, corregir y deshacer.",
                "La pregunta correcta es: cuanto trabajo aceptado y mantenible produce el sistema por unidad de tiempo, coste y riesgo. Esa metrica es menos vistosa, pero mucho mas cercana a valor real.",
            ]),
            ("Metricas basicas", [
                "Acceptance rate: porcentaje de cambios de agente que llegan a main sin reescritura sustancial.",
                "Review burden: numero y severidad de comentarios humanos por PR.",
                "Rework rate: porcentaje de cambios que requieren correccion posterior.",
                "Time to merge: tiempo desde tarea asignada hasta PR integrado.",
                "Defect escape rate: bugs que llegan despues de merge.",
                "Coste por PR aceptado: tokens, suscripciones, minutos de CI y tiempo humano.",
            ]),
            ("Segmenta por tipo de tarea", [
                "Un agente puede ser excelente escribiendo documentacion y mediocre en cambios de arquitectura. Puede arreglar bugs localizados y fallar en migraciones grandes. Si mezclas todo en una media global, no sabras donde usarlo.",
                "Segmenta por docs, tests, fixes, features, refactors, migraciones, frontend, backend y seguridad. Despues decide politicas por categoria. No todos los agentes deben poder tocar todo.",
            ]),
            ("Mide coste completo", [
                "El coste no es solo tokens. Incluye tiempo de reviewer, minutos de CI, ejecuciones fallidas, contexto perdido, deuda tecnica y riesgo. Una tarea barata en API puede salir cara si genera un diff confuso.",
                "Tambien hay coste de oportunidad: si el agente tarda veinte minutos en hacer algo que un senior hacia en diez, pero libera atencion durante esos veinte minutos, puede seguir siendo rentable. Por eso conviene medir calendario y foco humano, no solo duracion bruta.",
            ]),
            ("Senales positivas", [
                "El agente reduce espera en tareas repetibles.",
                "Los PRs son pequenos y faciles de revisar.",
                "Los tests agregados fallan antes del fix y pasan despues.",
                "Los comentarios humanos bajan con el tiempo.",
                "El equipo sabe en que tareas no usarlo.",
                "El coste por cambio aceptado se estabiliza.",
            ]),
            ("Senales negativas", [
                "Mucho codigo nuevo y pocas merges.",
                "PRs grandes con explicaciones genericas.",
                "Tests que solo validan mocks.",
                "Correcciones humanas constantes sobre el mismo patron.",
                "Coste creciente sin mayor throughput.",
                "Dependencia de un agente para entender cambios que nadie reviso bien.",
            ]),
            ("Conclusion", [
                "Medir agentes de codigo exige disciplina de producto, no fe en demos. El valor no esta en que escriban rapido, sino en que entreguen cambios correctos con menos carga humana total.",
                "La metrica final deberia ser aburrida: cambios aceptados, verificados y mantenibles por coste razonable. Todo lo demas es ruido de actividad.",
            ]),
        ],
    },
    {
        "title": "Hooks para agentes de código: cómo poner guardrails sin frenar a tu equipo",
        "slug": "hooks-agentes-codigo-guardrails-validacion",
        "status": "published",
        "meta_description": "Guía técnica para usar hooks en agentes de código: validaciones, aprobaciones, lint, tests, permisos y auditoría en Claude Code, Copilot y Codex.",
        "excerpt": "Los hooks convierten a los agentes de código en workflows gobernables: menos improvisación, más validación y mejores límites antes de tocar tu repo.",
        "sources": [
            ("Claude Code hooks", "https://docs.anthropic.com/en/docs/claude-code/hooks"),
            ("Claude Code settings", "https://docs.anthropic.com/en/docs/claude-code/settings"),
            ("GitHub Copilot coding agent: about hooks", "https://docs.github.com/en/enterprise-cloud@latest/copilot/concepts/agents/cloud-agent/about-hooks"),
            ("GitHub Copilot coding agent: create hooks", "https://docs.github.com/en/enterprise-cloud@latest/copilot/customizing-copilot/creating-hooks-for-the-coding-agent"),
            ("OpenAI: Introducing the Codex app", "https://openai.com/index/introducing-the-codex-app/"),
            ("OpenAI: Work with Codex from anywhere", "https://openai.com/index/work-with-codex-from-anywhere/"),
        ],
        "related": [
            ("Claude Code: guía completa", "/claude-code-que-es-guia-completa/"),
            ("Serena MCP: búsqueda semántica", "/serena-mcp-busqueda-semantica-codigo/"),
            ("RTK: reducir tokens en agentes", "/rtk-proxy-cli-reducir-tokens-ia/"),
        ],
        "sections": [
            ("Por qué los hooks importan ahora", [
                "Los agentes de código ya no solo completan líneas. Editan varios archivos, ejecutan comandos, responden a comentarios y trabajan en tareas remotas o asíncronas. En ese escenario, el problema ya no es solo qué modelo usas, sino qué barreras existen entre una sugerencia útil y una acción peligrosa.",
                "Los hooks son una forma práctica de insertar gobernanza técnica dentro del flujo del agente. Permiten validar contexto, bloquear operaciones, exigir confirmaciones o disparar comprobaciones automáticas antes o después de acciones concretas.",
            ]),
            ("Qué es un hook en este contexto", [
                "Un hook es un punto de intervención programable dentro del ciclo de trabajo del agente. Puede ejecutarse antes de una herramienta, después de editar archivos, al terminar una tarea o cuando se intenta hacer algo sensible.",
                "La idea es parecida a un middleware local para agentes: no cambias el modelo, cambias las reglas operativas que rodean sus acciones. Eso permite añadir controles sin depender de que el prompt siempre salga perfecto.",
            ]),
            ("Casos donde sí merece la pena", [
                "Ejecutar lint o tests rápidos tras modificar archivos críticos.",
                "Bloquear comandos destructivos o accesos fuera de rutas permitidas.",
                "Forzar revisión humana antes de tocar secretos, infra, pagos o autenticación.",
                "Comprobar que un diff no mezcla refactor, formato y lógica sin motivo.",
                "Registrar acciones sensibles para auditoría o debugging posterior.",
            ]),
            ("Patrones útiles de guardrail", [
                "PreTool guard: si el agente intenta usar shell, git o escritura sobre directorios delicados, el hook puede denegar o pedir elevación explícita.",
                "Post-edit validation: después de escribir código, el hook ejecuta un chequeo barato, por ejemplo typecheck parcial o tests de un paquete concreto.",
                "Scope guard: el hook comprueba que el cambio sigue dentro del objetivo pedido y no invade archivos no autorizados.",
                "Approval gate: antes de una operación irreversible, como merge, deploy o borrado, el flujo exige decisión humana.",
            ]),
            ("Cómo evitar que se conviertan en fricción inútil", [
                "El error clásico es meter hooks pesados en cada paso. Si cada edición dispara una suite lenta, el agente se vuelve caro y molesto. Los hooks buenos son rápidos, específicos y proporcionales al riesgo.",
                "Conviene separar controles baratos y frecuentes de controles caros y raros. Formato, rutas permitidas y validaciones pequeñas pueden correr a menudo. E2E, seguridad profunda o aprobaciones manuales deben reservarse para acciones de más impacto.",
            ]),
            ("Claude Code, Copilot y Codex: diferencias prácticas", [
                "Claude Code documenta hooks y settings con bastante detalle, lo que lo vuelve útil para equipos que quieren imponer validaciones operativas dentro del flujo de terminal.",
                "GitHub Copilot lleva hooks al coding agent en GitHub, con configuración de repositorio y eventos más ligados al trabajo remoto y a la automatización sobre issues o PRs.",
                "Codex enfatiza aprobaciones, aislamiento y tareas remotas. Aunque el nombre de la función cambie, el principio operativo es el mismo: un agente útil necesita límites explícitos, no solo instrucciones bonitas.",
            ]),
            ("Checklist de adopción para un equipo técnico", [
                "Empieza por un inventario de acciones que el agente puede ejecutar hoy.",
                "Marca qué operaciones son de bajo, medio y alto riesgo.",
                "Añade primero hooks baratos: rutas, comandos permitidos y validación rápida.",
                "Reserva aprobación humana para escritura sensible, merges, secretos e infraestructura.",
                "Mide falsos positivos: si el hook bloquea demasiado, el equipo lo acabará rodeando.",
                "Documenta el flujo en instrucciones de proyecto para que el guardrail sea visible y repetible.",
            ]),
            ("Conclusión", [
                "Los hooks no hacen más inteligente al modelo. Hacen más gobernable el sistema. Esa diferencia importa mucho en producción.",
                "Si un agente puede editar, ejecutar y decidir pasos, necesita límites verificables. Los hooks son una de las piezas más prácticas para convertir asistencia de IA en workflow técnico serio.",
            ]),
        ],
    },
    {
        "title": "Tabnine vs GitHub Copilot: privacidad, autocompletado y control enterprise",
        "slug": "tabnine-vs-github-copilot",
        "status": "scheduled",
        "published_at": "2026-06-24T08:00:00.000Z",
        "meta_description": "Comparativa técnica Tabnine vs GitHub Copilot: privacidad, entrenamiento, autocompletado, agentes, IDEs, modelos, pricing y uso enterprise.",
        "excerpt": "Tabnine y GitHub Copilot compiten como asistentes de código, pero no empujan exactamente el mismo ángulo: Copilot gana por ecosistema; Tabnine por control y privacidad.",
        "sources": [
            ("Tabnine Docs", "https://docs.tabnine.com/"),
            ("Tabnine privacy", "https://docs.tabnine.com/main/welcome/readme/privacy"),
            ("Tabnine code privacy", "https://www.tabnine.com/code-privacy/"),
            ("GitHub Copilot", "https://github.com/features/copilot"),
            ("GitHub Copilot Trust Center", "https://github.com/features/copilot/trust"),
        ],
        "related": [
            ("Tabnine: autocompletado de código con IA", "/tabnine-autocompletado-codigo-ia/"),
            ("GitHub Copilot: guía completa", "/github-copilot-guia-completa/"),
            ("Copilot y privacidad", "/github-copilot-datos-entrenamiento-privacidad/"),
        ],
        "sections": [
            ("La diferencia principal", [
                "Tabnine vs GitHub Copilot no es solo una comparación de calidad de sugerencias. Es una comparación de filosofía de producto. Copilot está profundamente integrado con GitHub, Microsoft y el ecosistema de modelos premium. Tabnine empuja más fuerte la idea de control: privacidad, despliegue enterprise, modelos gobernados y una plataforma que una organización puede limitar mejor.",
                "Para un desarrollador individual, Copilot suele ser la opción más obvia por popularidad, ecosistema y experiencia general. Para equipos regulados, consultoras o empresas que quieren aislar contexto y controlar políticas, Tabnine merece una lectura más seria.",
            ]),
            ("Autocompletado y flujo diario", [
                "Copilot se percibe como referencia porque su autocompletado está muy extendido y su experiencia en VS Code/GitHub es fluida. Funciona bien para código común, tests, boilerplate, explicación y chat.",
                "Tabnine también cubre completado, chat y asistencia en IDEs, pero su propuesta se vuelve más interesante cuando la organización valora consistencia, privacidad y administración. No intenta ganar solo por espectacularidad; intenta ser aceptable para equipos que no pueden abrir todo el contexto a cualquier proveedor.",
            ]),
            ("Privacidad y entrenamiento", [
                "Aquí está la diferencia que más pesa para empresas. Tabnine comunica con fuerza zero data retention, cifrado y opciones de despliegue privado o air-gapped según plan. También diferencia modelos propios y modelos de terceros, algo importante porque las garantías pueden cambiar según el modelo activado.",
                "Copilot ofrece controles y planes enterprise, pero para usuarios Free/Pro/Pro+ conviene revisar ajustes de uso de datos y entrenamiento. En organizaciones, la pregunta práctica no es quién promete más, sino qué cuenta se usa, qué plan aplica y qué datos puede procesar el asistente.",
            ]),
            ("Agentes y funciones avanzadas", [
                "Copilot ha avanzado hacia agent mode, code review, integración con GitHub y flujos de PR. Eso lo vuelve potente para equipos que ya viven dentro de GitHub y quieren que la IA participe en el ciclo completo de desarrollo.",
                "Tabnine también ha añadido Tabnine Agent y CLI, moviéndose más allá del autocompletado clásico. Aun así, su posición diferencial sigue siendo la gobernanza. Si quieres máxima integración con GitHub, Copilot tiene ventaja. Si quieres despliegue controlado y límites enterprise, Tabnine compite mejor.",
            ]),
            ("Cuándo elegir Tabnine", [
                "Tu empresa prioriza privacidad, cumplimiento o despliegue controlado.",
                "Necesitas políticas centralizadas para modelos y contexto.",
                "Trabajas en repos propietarios donde no quieres depender de configuraciones individuales.",
                "Prefieres productividad incremental y gobernable a agentes muy autónomos.",
            ]),
            ("Cuándo elegir Copilot", [
                "Tu equipo ya vive en GitHub y Microsoft.",
                "Quieres la experiencia más popular y con más integraciones.",
                "Te interesan code review, agent mode y flujos de PR dentro de GitHub.",
                "El riesgo de datos está cubierto por plan Business/Enterprise y políticas claras.",
            ]),
            ("Conclusión", [
                "Copilot es la opción más natural para muchos desarrolladores. Tabnine es la opción que conviene mirar cuando seguridad, control y despliegue pesan más que la inercia del ecosistema.",
                "La decisión correcta no es cuál completa mejor una función en una demo. Es qué asistente puedes permitir en tu organización sin que privacidad, coste y gobernanza dependan de preferencias locales de cada desarrollador.",
            ]),
        ],
    },
    {
        "title": "Tabnine vs Cursor: privacidad enterprise frente a editor agéntico",
        "slug": "tabnine-vs-cursor",
        "status": "scheduled",
        "published_at": "2026-06-27T08:00:00.000Z",
        "meta_description": "Comparativa Tabnine vs Cursor: privacidad, IDE, agentes, contexto de repo, productividad, costes y cuándo elegir cada herramienta.",
        "excerpt": "Cursor y Tabnine pertenecen a la misma conversación de IA para programar, pero resuelven problemas distintos: uno rediseña el editor; el otro prioriza control enterprise.",
        "sources": [
            ("Tabnine Docs", "https://docs.tabnine.com/"),
            ("Tabnine Agent", "https://docs.tabnine.com/main/getting-started/tabnine-agent"),
            ("Tabnine code privacy", "https://www.tabnine.com/code-privacy/"),
            ("Cursor data use and privacy", "https://cursor.com/en-US/data-use"),
            ("Cursor", "https://cursor.com/"),
        ],
        "related": [
            ("Tabnine: autocompletado de código con IA", "/tabnine-autocompletado-codigo-ia/"),
            ("Cursor AI: guía completa", "/cursor-ai-que-es-guia-completa/"),
            ("Windsurf IDE: editor con IA", "/windsurf-ide-editor-ia/"),
        ],
        "sections": [
            ("No compiten igual", [
                "Tabnine vs Cursor parece una comparación directa entre asistentes de código, pero el producto base es distinto. Cursor es un editor centrado en IA, diseñado para chat, edición multiarchivo, contexto de repo y flujos agénticos dentro de una experiencia propia. Tabnine se integra en IDEs existentes y vende más fuerte privacidad, control y adopción enterprise.",
                "Si tu pregunta es qué herramienta cambia más mi forma de programar, Cursor suele tener ventaja. Si la pregunta es qué herramienta puedo desplegar con más control en una organización sensible, Tabnine gana puntos.",
            ]),
            ("Experiencia de desarrollo", [
                "Cursor funciona mejor cuando aceptas vivir dentro de su editor. Su valor está en Composer, contexto de proyecto, ediciones amplias y una interacción muy directa con el código abierto en pantalla.",
                "Tabnine encaja cuando no quieres cambiar el editor del equipo o cuando hay una mezcla de VS Code, JetBrains, Visual Studio y otros entornos. La adopción puede ser menos disruptiva porque se suma al IDE existente.",
            ]),
            ("Privacidad y datos", [
                "Cursor ofrece privacy mode y opciones de zero data retention para proveedores de modelos, pero el equipo debe configurar y entender bien esas opciones. Como en cualquier herramienta agéntica, cuanto más contexto le das, más importante es la política de datos.",
                "Tabnine ha construido gran parte de su mensaje alrededor de privacidad, zero data retention, modelos privados y despliegue controlado. Para equipos con compliance fuerte, esa narrativa no es marketing secundario: puede ser el criterio de compra.",
            ]),
            ("Agentes y contexto", [
                "Cursor suele sentirse más potente en tareas agénticas interactivas: editar varios archivos, iterar con el modelo y moverse rápido por una base de código desde el editor.",
                "Tabnine Agent acerca Tabnine a esa categoría, pero su ventaja natural sigue siendo dar asistencia gobernable en entornos existentes. Para equipos que temen que un agente toque demasiado, eso puede ser una virtud.",
            ]),
            ("Cuándo elegir Cursor", [
                "Quieres un editor centrado en IA y aceptas cambiar el flujo de trabajo.",
                "Haces muchas ediciones multiarchivo y tareas exploratorias.",
                "Tu equipo prioriza velocidad de iteración y experiencia de producto.",
                "Puedes gobernar privacidad y contexto con políticas claras.",
            ]),
            ("Cuándo elegir Tabnine", [
                "No quieres cambiar de IDE o tienes varios IDEs en la organización.",
                "Privacidad, despliegue y administración pesan más que la experiencia agéntica más agresiva.",
                "Tu equipo quiere empezar por completions, chat y tareas controladas.",
                "Necesitas una historia clara para seguridad, legal o compliance.",
            ]),
            ("Conclusión", [
                "Cursor es más transformador como entorno de trabajo. Tabnine es más conservador y gobernable como plataforma de asistencia. Ninguno gana siempre.",
                "La decisión depende del riesgo que puedas aceptar. Para un equipo pequeño que quiere moverse rápido, Cursor puede ser mejor. Para una empresa que necesita control antes que velocidad máxima, Tabnine merece prioridad.",
            ]),
        ],
    },
    {
        "title": "Codex con acceso a internet: cómo configurar sandbox, permisos y auditoría sin abrir demasiado el repo",
        "slug": "codex-acceso-internet-sandbox-seguridad",
        "status": "published",
        "meta_description": "Guía técnica para usar Codex con acceso a internet de forma segura: sandbox, allowlists, permisos, MCP, aprobaciones, logs y revisión humana.",
        "excerpt": "Dar internet a un agente de código puede desbloquear tareas reales, pero también abre riesgos de prompt injection, exfiltración y dependencias no confiables.",
        "sources": [
            ("OpenAI: Running Codex safely", "https://openai.com/index/running-codex-safely/"),
            ("OpenAI Codex: agent internet access", "https://developers.openai.com/codex/cloud/internet-access"),
            ("OpenAI Codex web", "https://developers.openai.com/codex/cloud"),
            ("OpenAI: Introducing upgrades to Codex", "https://openai.com/index/introducing-upgrades-to-codex/"),
            ("OpenAI: Introducing Codex", "https://openai.com/index/introducing-codex/"),
            ("OpenAI Help: Codex with ChatGPT plan", "https://help.openai.com/en/articles/11369540-codex-in-chatgpt"),
        ],
        "related": [
            ("Hooks para agentes de código", "/hooks-agentes-codigo-guardrails-validacion/"),
            ("MCP en producción: seguridad y permisos", "/mcp-produccion-seguridad-permisos-supply-chain/"),
            ("AGENTS.md y memoria de proyecto", "/agents-md-claude-md-memoria-proyecto/"),
            ("Métricas para agentes de código", "/metricas-agentes-codigo-productividad-coste/"),
        ],
        "sections": [
            ("El problema no es internet, es internet sin límites", [
                "Un agente de código sin red puede leer, modificar y probar dentro de un entorno acotado. En cuanto le das internet, puede instalar dependencias, consultar documentación, abrir issues, llamar APIs y resolver tareas que antes exigían intervención humana. Ese salto es útil, pero cambia el modelo de amenaza.",
                "El riesgo principal no es que el agente se vuelva malicioso. Es que obedezca instrucciones externas que no debería obedecer: un issue manipulado, una página con prompt injection, un README de dependencia, un script pegado en una conversación o un dominio que intenta recibir datos del repo.",
                "La configuración madura de Codex no consiste en permitir todo o bloquear todo. Consiste en separar fases, limitar destinos, exigir aprobación para acciones sensibles y conservar trazabilidad suficiente para explicar qué hizo el agente y por qué.",
            ]),
            ("Modelo mental: tres capas de control", [
                "La primera capa es el sandbox. Define qué puede tocar el agente en el sistema de archivos, qué comandos puede ejecutar y cuánto daño puede causar si una instrucción sale mal.",
                "La segunda capa es la red. Define si el agente puede salir a internet durante la fase de trabajo, a qué dominios puede conectarse y con qué métodos HTTP. En Codex cloud, OpenAI documenta que el acceso a internet del agente está bloqueado por defecto y se habilita por entorno cuando hace falta.",
                "La tercera capa es la aprobación humana. Algunas acciones no deberían depender solo de una allowlist: publicar paquetes, tocar secretos, ejecutar migraciones, enviar datos externos, cambiar infraestructura o abrir un PR con impacto de seguridad.",
            ]),
            ("Qué permitir por defecto", [
                "Permite instalaciones de dependencias en la fase de setup cuando el entorno lo necesita, pero evita que el agente use red abierta durante toda la tarea si no aporta valor.",
                "Autoriza dominios concretos: registros de paquetes, documentación oficial, APIs internas de lectura y repositorios controlados. Evita el comodín de internet completo salvo en sandboxes de investigación sin secretos y con repos desechables.",
                "Empieza con métodos HTTP restrictivos. Muchas tareas solo necesitan GET o HEAD para leer documentación o descargar dependencias. POST, PUT, PATCH y DELETE deberían tener una justificación clara.",
            ]),
            ("Riesgos que debes diseñar explícitamente", [
                "Prompt injection: contenido externo que intenta cambiar la tarea, revelar secretos o ejecutar comandos no relacionados.",
                "Exfiltración: envío accidental de código, variables de entorno, tokens, logs o fragmentos de commits a dominios no confiables.",
                "Supply chain: descarga de dependencias vulnerables, typosquatting, scripts de instalación agresivos o paquetes con licencias incompatibles.",
                "Persistencia involuntaria: cambios en configuración, credenciales, workflows o scripts que sobreviven al sandbox y acaban en el repo.",
                "Falsa confianza: aceptar un PR porque el agente muestra tests verdes sin revisar qué comandos ejecutó, qué red usó y qué archivos modificó.",
            ]),
            ("Checklist de configuración para equipos", [
                "Define entornos separados para tareas normales, tareas con red y tareas de alto riesgo.",
                "Mantén secretos fuera del entorno del agente salvo que sean imprescindibles y de alcance mínimo.",
                "Usa allowlists de dominios en lugar de internet abierto.",
                "Exige aprobación para comandos destructivos, cambios de infraestructura, publicación y operaciones con datos sensibles.",
                "Registra prompts, decisiones de aprobación, comandos, resultados, uso de MCP y decisiones de red.",
                "Incluye instrucciones del repo en AGENTS.md para que el agente sepa qué tests correr y qué rutas no tocar.",
                "Revisa diffs como revisarías el trabajo de una persona nueva: intención, cobertura de tests, impacto y rollback.",
            ]),
            ("Dónde encajan MCP y herramientas externas", [
                "MCP amplía lo que el agente puede hacer: leer sistemas internos, consultar tickets, abrir herramientas de observabilidad o interactuar con servicios corporativos. Eso no es malo, pero convierte cada servidor MCP en parte de la superficie de seguridad.",
                "Un servidor MCP debería tener permisos mínimos, scopes claros, logs y separación por entorno. No mezcles herramientas de lectura inocuas con herramientas que pueden escribir en producción bajo el mismo nivel de aprobación.",
                "Si un agente tiene red y MCP a la vez, revisa el flujo completo: puede leer contexto por MCP, procesarlo y después intentar enviarlo a una URL externa. Las políticas deben pensar en cadenas de acciones, no solo en permisos aislados.",
            ]),
            ("Un rollout razonable", [
                "Empieza con repos internos de bajo riesgo y tareas acotadas: actualizar documentación, mejorar tests, corregir bugs pequeños o preparar refactors sin merge automático.",
                "Durante las primeras semanas, mide bloqueos de red, solicitudes de aprobación, comandos fallidos, PRs aceptados y revisiones humanas que encontraron problemas reales. Esa telemetría te dirá si tus límites son demasiado estrictos o demasiado abiertos.",
                "Cuando el flujo sea estable, amplía por tipo de tarea, no por entusiasmo. Dar internet a todos los agentes en todos los repos porque una demo salió bien es una mala estrategia de adopción.",
            ]),
            ("Conclusión", [
                "Codex con internet puede ser mucho más útil que un agente aislado, especialmente para tareas que dependen de documentación actual, dependencias, issues o APIs. Pero esa utilidad solo compensa si el entorno está diseñado para fallar de forma controlada.",
                "La configuración mínima seria combina sandbox, allowlists, aprobaciones, AGENTS.md, logging y revisión humana. Si falta una de esas piezas, el agente puede seguir siendo productivo, pero la organización pierde capacidad de explicar y contener sus acciones.",
            ]),
        ],
    },
    {
        "title": "Claude Code en GitHub Actions: CI/CD, permisos y seguridad para agentes de código",
        "slug": "claude-code-github-actions-ci-seguridad",
        "status": "published",
        "meta_description": "Guía técnica para usar Claude Code en GitHub Actions: workflows, permisos mínimos, GITHUB_TOKEN, secretos, MCP, costes y revisión humana.",
        "excerpt": "Claude Code puede vivir dentro de GitHub Actions, pero un agente en CI no debe tener los mismos permisos que un desarrollador interactivo.",
        "sources": [
            ("Claude Code GitHub Actions", "https://code.claude.com/docs/en/github-actions"),
            ("anthropics/claude-code-action", "https://github.com/anthropics/claude-code-action"),
            ("GitHub: Use GITHUB_TOKEN for authentication", "https://docs.github.com/en/actions/tutorials/authenticate-with-github_token"),
            ("GitHub Actions secure use reference", "https://docs.github.com/en/actions/reference/security/secure-use"),
            ("GitHub Actions OIDC reference", "https://docs.github.com/en/actions/reference/security/oidc"),
            ("Claude Code hooks", "https://code.claude.com/docs/en/hooks"),
            ("Claude Code MCP", "https://code.claude.com/docs/en/mcp"),
        ],
        "related": [
            ("Claude Code: guía completa", "/claude-code-que-es-guia-completa/"),
            ("Hooks para agentes de código", "/hooks-agentes-codigo-guardrails-validacion/"),
            ("Pull requests hechos por agentes", "/pull-requests-agentes-ia-gobernanza-humana/"),
            ("MCP en producción: seguridad y permisos", "/mcp-produccion-seguridad-permisos-supply-chain/"),
            ("Métricas para agentes de código", "/metricas-agentes-codigo-productividad-coste/"),
        ],
        "sections": [
            ("Por qué importa", [
                "Claude Code en GitHub Actions convierte una conversación con un agente en una automatización reproducible: puedes invocarlo desde comentarios, pull requests, issues, tareas programadas o workflows internos. La promesa es clara: revisar PRs, preparar cambios, clasificar issues o ejecutar mantenimiento sin abrir el editor.",
                "El riesgo también es claro. Un agente dentro de CI corre con permisos de workflow, acceso a secretos, checkout del repositorio y capacidad para comentar, abrir PRs o modificar archivos si se lo permites. No es lo mismo que pedir ayuda localmente a Claude Code y revisar cada comando en una terminal.",
                "La guía práctica no es activar `anthropics/claude-code-action@v1` y esperar magia. Es diseñar un workflow donde el agente tenga un mandato estrecho, permisos mínimos, salida auditable y límites de coste antes de que escriba en el repositorio.",
            ]),
            ("Qué cambió con la acción v1", [
                "La documentación actual de Anthropic recomienda usar `anthropics/claude-code-action@v1`. La versión v1 simplifica la configuración con entradas unificadas como `prompt` y `claude_args`, elimina parte de la configuración antigua de modos y permite pasar argumentos de Claude Code desde el workflow.",
                "Eso mejora la ergonomía, pero no elimina las decisiones importantes. Tienes que decidir qué evento dispara el agente, qué puede leer, qué puede escribir, qué modelo usar, cuántos turnos permitir, si tendrá MCP, si podrá usar proveedores como Bedrock o Vertex, y si el resultado será comentario, PR o cambio directo.",
                "Trata la migración desde beta como una revisión de seguridad, no como un reemplazo mecánico de YAML. Si el workflow anterior ya tenía permisos amplios, la actualización es un buen momento para recortarlos.",
            ]),
            ("Tres patrones útiles", [
                "El primer patrón es asistente bajo demanda: Claude solo actúa cuando alguien escribe `@claude` en un issue o pull request. Es el más fácil de introducir porque conserva intención humana explícita.",
                "El segundo patrón es revisión acotada: se ejecuta en PRs, pero solo para rutas críticas, cambios grandes o etiquetas concretas. Evita revisar cada cambio trivial y reduce coste de API y minutos de Actions.",
                "El tercer patrón es mantenimiento programado: informes diarios, actualización de documentación, triage de issues o propuestas de refactor. Aquí el riesgo no está en el comentario, sino en convertir recomendaciones automáticas en trabajo que nadie revisa.",
            ]),
            ("Permisos mínimos en GitHub Actions", [
                "Empieza con `permissions` explícito en el workflow o en el job. Si el agente solo comenta en PRs, no necesita permisos amplios sobre contents. Si debe abrir un PR, necesitará escritura en contenidos y pull requests, pero no necesariamente acceso a packages, deployments o id-token.",
                "GitHub documenta que una acción puede acceder a `GITHUB_TOKEN` desde el contexto `github.token` aunque no se lo pases explícitamente. Por eso no basta con ocultar el token como input: debes limitar los permisos concedidos al token.",
                "Para proveedores cloud, prefiere OIDC cuando sea posible en lugar de secretos largos. Si usas Bedrock o Vertex desde Actions, un rol temporal con condiciones de repositorio y rama suele ser más defendible que una clave estática guardada durante meses.",
            ]),
            ("Secretos y contexto", [
                "Guarda `ANTHROPIC_API_KEY` como secreto de GitHub, nunca en el YAML ni en `CLAUDE.md`. Si el workflow usa otros secretos, separa los jobs: el job que comenta o revisa código no debería heredar credenciales de despliegue si no despliega.",
                "No metas datos sensibles en el prompt. Los títulos de PR, comentarios de issues y bodies de usuarios externos son entrada no confiable. Si interpolas ese texto dentro de comandos shell o prompts con permisos de escritura, estás mezclando prompt injection con CI injection.",
                "GitHub recomienda tratar entradas del contexto como potencialmente peligrosas en scripts. En workflows con agentes, el mismo criterio aplica doblemente: lo que viene de un comentario puede influir en una decisión del modelo y también en lo que acaba ejecutando el job.",
            ]),
            ("Cómo acotar herramientas y MCP", [
                "MCP es útil cuando Claude necesita leer documentación interna, consultar tickets o hablar con sistemas corporativos. Pero en CI, cada servidor MCP aumenta la superficie de permisos. No conectes el mismo servidor que usas localmente si incluye acciones de escritura que el workflow no necesita.",
                "Usa allowlists de herramientas y servidores. En Claude Code, `claude_args` permite pasar opciones como `--allowedTools`, `--max-turns`, `--model` o una ruta de configuración MCP. Ese control debe estar en el YAML o en configuración versionada, no en una instrucción informal dentro del prompt.",
                "Si necesitas hooks, úsalos para validaciones deterministas: bloquear rutas sensibles, exigir tests después de editar, impedir cambios en migraciones sin etiqueta o registrar qué herramientas se invocaron. Los hooks no sustituyen revisión humana, pero reducen estados peligrosos antes de que el diff llegue al PR.",
            ]),
            ("Costes que conviene medir", [
                "Hay dos facturas. Una es GitHub Actions: cada ejecución consume minutos de runner, especialmente si el agente instala dependencias, corre tests o itera varias veces. La otra es la API de Claude: el coste depende del contexto, modelo, longitud del repo y número de turnos.",
                "Empieza con `--max-turns` conservador y timeouts de workflow. Añade `concurrency` para evitar que cinco comentarios disparen cinco sesiones simultáneas sobre el mismo PR. Si el workflow es automático en cada push, mide coste por PR, no solo coste mensual.",
                "La métrica útil no es cuántos comentarios genera Claude. Es cuántos comentarios terminan en cambios aceptados, cuántos falsos positivos produce y cuánto tiempo humano ahorra frente al coste de revisión adicional.",
            ]),
            ("Un workflow inicial razonable", [
                "Actívalo primero en un repositorio de riesgo medio, no en producción crítica ni en un sandbox irrelevante. Usa disparo manual por mención, `permissions` explícitos, `ANTHROPIC_API_KEY` en secrets, `--max-turns` bajo y un prompt que pida análisis antes de cambios.",
                "Durante dos semanas, prohíbe merges automáticos generados por el agente. Claude puede comentar, sugerir y abrir PRs, pero una persona debe aprobar. Registra duración de jobs, tokens aproximados, rutas tocadas, tests ejecutados y comentarios descartados.",
                "Después decide si ampliar por caso de uso. Si funcionó bien revisando PRs de backend, no significa que deba tocar despliegues, migraciones o infraestructura. La expansión sana es por permiso y por workflow, no por entusiasmo.",
            ]),
            ("Checklist de seguridad", [
                "Define `permissions` por job y evita permisos globales amplios.",
                "Usa secretos de GitHub y revisa qué jobs pueden acceder a ellos.",
                "Trata comentarios, títulos de PR e issues como entrada no confiable.",
                "Limita `--max-turns`, modelo y herramientas con `claude_args`.",
                "Separa revisión, edición y despliegue en workflows distintos.",
                "No concedas MCP de escritura salvo que el caso de uso lo exija.",
                "Añade hooks para rutas sensibles, tests obligatorios y logging.",
                "Usa OIDC para cloud cuando puedas evitar claves estáticas.",
                "Revisa cada diff como código humano nuevo: intención, pruebas, permisos y rollback.",
            ]),
            ("Conclusión", [
                "Claude Code en GitHub Actions es potente porque acerca los agentes al sitio donde el equipo ya decide: issues, PRs y CI. Eso lo hace más útil que un asistente aislado, pero también más peligroso si hereda permisos sin diseño.",
                "La configuración responsable combina `anthropics/claude-code-action@v1`, prompts estrechos, `GITHUB_TOKEN` mínimo, secretos bien separados, límites de turnos, hooks, MCP con permisos mínimos y revisión humana. Si una pieza falta, el workflow puede seguir funcionando, pero será más difícil explicar qué hizo el agente cuando algo salga mal.",
            ]),
        ],
    },
    {
        "title": "GitHub Copilot coding agent en producción: MCP, agentes personalizados y hooks",
        "slug": "copilot-coding-agent-mcp-hooks-produccion",
        "status": "published",
        "meta_description": "Guía técnica para desplegar GitHub Copilot coding agent con MCP, custom agents, hooks, permisos mínimos y métricas de coste.",
        "excerpt": "Copilot coding agent ya no es solo chat en el editor: puede trabajar en issues, abrir PRs y usar herramientas. Esta guía explica cómo llevarlo a producción sin perder control.",
        "sources": [
            ("GitHub Docs: About GitHub Copilot coding agent", "https://docs.github.com/en/copilot/using-github-copilot/coding-agent/about-assigning-tasks-to-copilot"),
            ("GitHub Docs: MCP and GitHub Copilot coding agent", "https://docs.github.com/en/copilot/concepts/coding-agent/mcp-and-coding-agent"),
            ("GitHub Docs: Extending Copilot coding agent with MCP", "https://docs.github.com/copilot/using-github-copilot/coding-agent/extending-copilot-coding-agent-with-mcp"),
            ("GitHub Docs: Custom agents configuration", "https://docs.github.com/en/copilot/reference/custom-agents-configuration"),
            ("GitHub Docs: About hooks for GitHub Copilot", "https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-hooks"),
            ("GitHub Docs: Customize agent workflows with hooks", "https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/use-hooks"),
        ],
        "related": [
            ("GitHub Copilot: guía completa para desarrolladores", "/github-copilot-guia-completa/"),
            ("MCP en producción: seguridad, permisos y supply chain", "/mcp-produccion-seguridad-permisos-supply-chain/"),
            ("Hooks para agentes de código: guardrails y validación", "/hooks-agentes-codigo-guardrails-validacion/"),
            ("PRs de agentes de IA: gobernanza humana", "/pull-requests-agentes-ia-gobernanza-humana/"),
        ],
        "sections": [
            ("Por qué este tema ya es arquitectura", [
                "GitHub Copilot coding agent mueve la asistencia de IA desde el editor hacia el flujo donde el equipo ya decide: issues, pull requests, revisiones y entornos de GitHub Actions. Eso cambia la pregunta. Ya no basta con saber si Copilot autocompleta bien; hay que diseñar qué permisos tendrá un agente que puede explorar código, ejecutar comandos, proponer cambios y abrir trabajo para revisión.",
                "La parte importante es que GitHub está juntando varias piezas que antes se evaluaban por separado: custom instructions, agentes personalizados, MCP, hooks, entornos efímeros, firewall, consumo de Actions y premium requests. En conjunto forman una plataforma de ejecución para trabajo de desarrollo asistido.",
                "Esta guía no intenta vender el agente como magia. Lo trata como cualquier otra automatización que toca código: debe tener alcance, permisos mínimos, evidencia, logs, costes medibles y revisión humana.",
            ]),
            ("Modelo mental: agente, herramientas y entorno", [
                "Copilot coding agent trabaja en un entorno efímero asociado a una tarea. Puede leer el repositorio, ejecutar comandos, crear ramas y preparar pull requests dentro de los límites que configure GitHub y la organización. Ese entorno está apoyado en GitHub Actions, así que los minutos de runner y la configuración de CI importan.",
                "MCP añade herramientas externas al agente: datos de GitHub, navegación con Playwright, documentación interna, sistemas de tickets o servicios propios. La documentación de GitHub deja claro un punto crítico: una vez configurado un servidor MCP, el agente puede usar sus herramientas de forma autónoma durante la tarea.",
                "Los hooks añaden puntos de control deterministas antes, durante o después de la ejecución. Sirven para logging, validación, bloqueo de comandos peligrosos, comprobaciones de rutas sensibles o auditoría. La combinación útil es esta: MCP amplía capacidades, custom agents reducen alcance, hooks imponen reglas verificables.",
            ]),
            ("Qué aporta MCP y dónde está el riesgo", [
                "MCP tiene sentido cuando el agente necesita contexto que no vive en el repositorio: documentación privada, incidencias, métricas, diseños, APIs internas o herramientas de exploración. Sin MCP, el agente puede quedarse corto y pedir al humano que copie información a mano. Con MCP mal configurado, el agente puede tener más herramientas de las necesarias.",
                "GitHub recomienda allowlists de herramientas y advierte que Copilot coding agent solo soporta herramientas MCP, no recursos ni prompts MCP. También hay una limitación práctica relevante: no soporta actualmente servidores MCP remotos que usen OAuth para autorización. Eso afecta al diseño de integraciones empresariales.",
                "La regla operativa es simple: no conectes el MCP que usas localmente sin revisarlo. Un servidor local cómodo para un desarrollador puede exponer acciones de escritura, credenciales o datos que no deberían estar disponibles para un agente que responde a una tarea de GitHub.",
            ]),
            ("Agentes personalizados: especializar sin abrir todo", [
                "Los custom agents permiten definir perfiles con descripción, prompt, modelo, herramientas permitidas y, en GitHub.com, configuración MCP específica. Esto es más sano que un único agente generalista con acceso a todo. Un agente de documentación no necesita editar backend. Un agente de seguridad no necesita publicar paquetes. Un agente de frontend no necesita credenciales de despliegue.",
                "La documentación de configuración permite limitar herramientas con listas explícitas. También explica que los nombres desconocidos se ignoran, lo que facilita compartir perfiles entre entornos, pero obliga a validar que la lista realmente coincide con las herramientas disponibles.",
                "Un patrón razonable es empezar con tres perfiles: `reviewer`, `test-writer` y `docs-maintainer`. El primero puede leer, buscar y comentar; el segundo puede editar tests y ejecutar comandos acotados; el tercero puede tocar documentación. Si una tarea necesita más permisos, no la escondas en el prompt: crea otro perfil o exige intervención humana.",
            ]),
            ("Hooks: guardrails que no dependen del modelo", [
                "Los hooks son útiles porque no piden al modelo que se porte bien; ejecutan comandos definidos por el equipo en puntos concretos. `preToolUse` puede bloquear comandos o rutas, `postToolUse` puede registrar resultados, `sessionStart` puede preparar contexto y `sessionEnd` puede archivar evidencia.",
                "Para repos profesionales, empezaría con hooks que bloqueen cambios en `.env`, secretos, migraciones críticas, infraestructura de despliegue y rutas de billing sin etiqueta explícita. También añadiría logging de comandos, archivos tocados y tests ejecutados. Ese log debe ser revisable en el PR o en artefactos del workflow.",
                "No conviene convertir hooks en un segundo CI completo. Úsalos para reglas rápidas y específicas. La validación pesada sigue viviendo mejor en CI normal: tests, linters, SAST, CodeQL, revisión de dependencias y políticas de branch protection.",
            ]),
            ("Permisos mínimos y secretos", [
                "Si un agente solo debe revisar, evita conceder permisos de escritura. Si debe abrir un PR, acota ramas, rutas y eventos. GitHub documenta protecciones integradas, pero eso no sustituye permisos explícitos ni políticas de organización.",
                "Para MCP con secretos, GitHub exige usar variables o secretos del entorno Copilot con nombres prefijados como `COPILOT_MCP_`. Ese prefijo ayuda a separar credenciales destinadas al agente de otras credenciales de CI, pero no elimina la obligación de revisar qué herramienta las recibe.",
                "No mezcles credenciales de despliegue con tareas de revisión. Si necesitas que el agente consulte un sistema externo, dale un token de solo lectura y scope estrecho. Si una herramienta MCP incluye acciones de escritura, habilita solo las herramientas concretas que justifican el caso de uso.",
            ]),
            ("Diseño de rollout en tres fases", [
                "Fase uno: agente de lectura. Permite que Copilot analice issues o PRs, use herramientas de lectura y deje comentarios. No edita código. El objetivo es medir señal: cuántos comentarios son útiles, cuántos son ruido y qué contexto le falta.",
                "Fase dos: agente de cambios acotados. Permite edición en rutas concretas, preferiblemente tests, documentación o módulos de bajo riesgo. Exige que el PR incluya qué comandos ejecutó y por qué el cambio está dentro de alcance.",
                "Fase tres: agentes especializados con MCP. Solo cuando las dos primeras fases hayan producido evidencia, añade integraciones externas. Cada servidor MCP debe tener dueño, lista de herramientas permitidas, secretos separados, logs y una razón escrita para estar disponible.",
            ]),
            ("Métricas que sí sirven", [
                "Mide tareas aceptadas, PRs fusionados, comentarios descartados, minutos de Actions, premium requests, tiempo hasta primera revisión y número de iteraciones humanas. Si solo mides cantidad de PRs abiertos por el agente, vas a optimizar volumen, no calidad.",
                "También mide clases de fallo: cambios fuera de alcance, tests no ejecutados, dependencia de contexto inexistente, herramientas MCP innecesarias, comandos bloqueados por hooks y comentarios que no aportan acción. Esas métricas te dicen si necesitas mejores instrucciones, menos permisos o más contexto.",
                "La métrica más honesta es porcentaje de trabajo que llega a merge con menos tiempo humano total. Si el agente ahorra escritura pero duplica revisión, no mejoró el flujo; solo cambió dónde se paga el coste.",
            ]),
            ("Plantilla mínima de política", [
                "Un repositorio puede usar Copilot coding agent solo si define: quién puede asignar tareas, qué agentes están disponibles, qué herramientas MCP usa cada uno, qué hooks bloquean acciones peligrosas, dónde quedan los logs y quién aprueba el PR final.",
                "Los prompts de sistema y perfiles deben vivir versionados. Las excepciones de permisos deben revisarse como cambios de infraestructura. Los secretos para MCP deben estar separados de secretos de despliegue. Los agentes no deben aprobar ni fusionar su propio trabajo.",
                "Esa política cabe en una página. Si necesitas diez páginas para explicar el rollout, probablemente estás habilitando demasiadas capacidades a la vez.",
            ]),
            ("Conclusión", [
                "Copilot coding agent se vuelve interesante cuando deja de ser un asistente genérico y se convierte en una automatización de ingeniería con límites claros. MCP le da contexto, custom agents le dan especialización y hooks le dan control determinista.",
                "La configuración profesional no empieza activando todo. Empieza con lectura, medición y permisos mínimos. Después se añaden edición, MCP y especialización donde haya evidencia de valor. Ese orden evita el error clásico de los agentes de código: confundir capacidad con permiso para usarla.",
            ]),
        ],
    },
    {
        "title": "Tabnine Enterprise Context Engine: por qué el contexto importa más que el modelo",
        "slug": "tabnine-enterprise-context-engine-agentes",
        "status": "published",
        "meta_description": "Guía técnica sobre Tabnine Enterprise Context Engine, agentes, contexto remoto, privacidad y adopción en equipos de desarrollo.",
        "excerpt": "Tabnine está empujando una idea pragmática para empresas: los agentes de código no mejoran solo con modelos más grandes, sino con contexto estructurado.",
        "sources": [
            ("Tabnine Blog: Enterprise Context Engine", "https://www.tabnine.com/blog/introducing-the-tabnine-enterprise-context-engine/"),
            ("Tabnine Docs: Context Engine", "https://docs.tabnine.com/main/getting-started/context-engine"),
            ("Tabnine Docs: Tabnine Agent", "https://docs.tabnine.com/main/getting-started/tabnine-agent"),
            ("Tabnine Docs: Privacy", "https://docs.tabnine.com/main/welcome/readme/privacy"),
            ("Tabnine code privacy", "https://www.tabnine.com/code-privacy/"),
        ],
        "related": [
            ("Tabnine: autocompletado de código con IA", "/tabnine-autocompletado-codigo-ia/"),
            ("Tabnine vs GitHub Copilot", "/tabnine-vs-github-copilot/"),
            ("MCP en producción: seguridad, permisos y supply chain", "/mcp-produccion-seguridad-permisos-supply-chain/"),
            ("Métricas para agentes de código", "/metricas-agentes-codigo-productividad-coste/"),
        ],
        "sections": [
            ("La idea central", [
                "La mayoría de comparativas de herramientas de IA para programar se quedan en el modelo: si usa GPT, Claude, Gemini, un modelo propio o una mezcla. Esa comparación cada vez explica menos. En equipos reales, el cuello de botella no suele ser que el modelo no sepa escribir una función aislada; suele ser que no entiende arquitectura, ownership, dependencias, servicios aguas abajo, convenciones internas y reglas de seguridad.",
                "Tabnine está posicionando su Enterprise Context Engine justo en ese hueco. La promesa no es solo completar líneas mejor, sino dar a los agentes una representación estructurada del entorno donde operan: repositorios, servicios, APIs, dependencias, documentación, límites de equipo y políticas.",
                "Para DevAI, el tema es interesante porque conecta con una tesis cada vez más clara: en 2026, la ventaja de las herramientas de coding agent no será solo el LLM. Será la calidad del contexto que reciben y los controles con los que actúan.",
            ]),
            ("Qué es el Context Engine", [
                "Según Tabnine, el Enterprise Context Engine analiza y modela el entorno de software de una organización para hacerlo accesible a sistemas de IA. No es un simple RAG sobre ficheros. La idea es construir capas de contexto con relaciones de arquitectura, dependencias, contratos, ownership y restricciones que un agente pueda consultar antes de proponer un cambio.",
                "En la documentación, el flujo incluye conectar repositorios, habilitar el Context Engine desde la administración, activar herramientas para usuarios finales, revisar assets generados y usar contexto remoto desde Tabnine Agent en IDE o CLI.",
                "Ese detalle operativo importa: si el contexto se genera pero los agentes no tienen herramientas habilitadas para consultarlo, no cambia nada en el flujo diario. La adopción no termina al indexar repositorios; termina cuando el agente lo usa de forma trazable y el equipo puede revisar qué contexto influyó en el cambio.",
            ]),
            ("Dónde encaja frente a MCP y RAG", [
                "MCP es un protocolo para exponer herramientas y contexto a agentes. RAG es un patrón para recuperar información relevante. Un context engine empresarial intenta ser una capa más persistente y específica: no solo traer documentos parecidos, sino representar cómo funciona el sistema.",
                "La diferencia práctica aparece en preguntas como: si cambio esta API, qué servicios se rompen; si edito este módulo, qué equipo debe revisar; si genero este PR, qué política interna aplica; si uso esta librería, qué convención del repositorio estoy violando.",
                "Tabnine documenta que el contexto remoto puede usarse en el agente mediante herramientas nativas MCP. Eso lo coloca en una categoría híbrida: no compite necesariamente con MCP, sino que puede alimentar herramientas MCP con contexto de repositorios y arquitectura.",
            ]),
            ("Por qué esto es más evergreen que una feature", [
                "La noticia concreta es Tabnine empujando su Enterprise Context Engine. La guía duradera es la decisión técnica: cómo evaluar cualquier herramienta de IA que prometa contexto empresarial.",
                "Un equipo debería preguntar cuatro cosas. Primero, qué fuentes indexa. Segundo, qué relaciones entiende más allá de texto suelto. Tercero, qué permisos usa para leer repositorios y documentación. Cuarto, cómo se audita el contexto que influye en una respuesta o cambio de código.",
                "Si una herramienta solo dice que tiene más contexto, pero no permite gobernarlo, probablemente solo amplió la ventana de tokens. Eso puede mejorar algunas respuestas, pero no resuelve el problema estructural de agentes trabajando dentro de sistemas grandes.",
            ]),
            ("Privacidad y control", [
                "Tabnine insiste en privacidad, procesamiento efímero y opciones privadas para Enterprise. La documentación de privacidad afirma que no retiene código de usuario más allá del tiempo inmediato necesario para inferencia. Para equipos con código sensible, esa promesa debe convertirse en requisitos verificables: contrato, configuración, despliegue, retención, logs y permisos.",
                "El Context Engine añade otra dimensión. Ya no hablamos solo de prompts y respuestas, sino de índices, assets de contexto, resúmenes de arquitectura y metadatos de repositorios. Esa información puede ser tan sensible como el código fuente, porque describe cómo está construido el sistema.",
                "Mi recomendación sería tratar el contexto generado como un activo interno: dueño claro, acceso limitado, revisión periódica y borrado cuando un repositorio o equipo sale del alcance.",
            ]),
            ("Cómo lo probaría en una empresa", [
                "No empezaría conectando todos los repositorios. Escogería un dominio con dolor real: por ejemplo, un monolito con servicios dependientes, una plataforma interna con APIs compartidas o un producto donde los PRs fallan por desconocer convenciones.",
                "Durante cuatro semanas mediría tareas concretas: generación de tests, explicación de impacto, búsqueda de APIs internas, revisión de PRs y propuestas de refactor. Compararía Tabnine Agent con y sin contexto remoto, y registraría cuántas respuestas citan piezas correctas de arquitectura.",
                "El resultado útil no es 'el agente parece más inteligente'. El resultado útil es: reduce cambios fuera de alcance, encuentra dependencias correctas, respeta convenciones, genera menos revisión inútil y ahorra tiempo humano neto.",
            ]),
            ("Riesgos técnicos", [
                "El primer riesgo es contexto obsoleto. Si el índice va por detrás del repositorio, el agente puede razonar con una arquitectura que ya no existe.",
                "El segundo es sobreconfianza. Un agente con contexto empresarial puede sonar más seguro aunque siga equivocándose. El reviewer debe comprobar evidencia, no tono.",
                "El tercero es permisos demasiado amplios. Si todos los agentes pueden consultar todo, el contexto se convierte en una vía lateral para exponer información que el desarrollador no debería ver.",
                "El cuarto es coste operativo. Indexar, revisar assets, mantener allowlists, resolver permisos y formar al equipo lleva trabajo. Si no hay un caso de uso fuerte, la capa de contexto puede convertirse en otra plataforma sin dueño.",
            ]),
            ("Checklist de evaluación", [
                "Lista las fuentes de contexto: repos, docs, issues, APIs, runbooks y ownership.",
                "Comprueba si el agente distingue contexto local, remoto y generado.",
                "Revisa permisos del usuario o servicio que ejecuta el preprocesado.",
                "Mide latencia y frescura del contexto antes de usarlo en tareas críticas.",
                "Define qué repos quedan fuera por confidencialidad o regulación.",
                "Audita cambios propuestos con contexto: por qué tocó ese archivo y qué dependencias vio.",
                "Crea métricas de calidad: menos PRs reabiertos, menos cambios fuera de patrón, menos preguntas repetidas al equipo senior.",
            ]),
            ("Conclusión", [
                "Tabnine Context Engine es relevante porque apunta al problema que muchos equipos ya sienten: los agentes escriben código suficiente, pero entienden poco del sistema real. Si una herramienta logra convertir arquitectura, dependencias y políticas en contexto accionable, puede mejorar más que cambiar de modelo.",
                "La adopción responsable no consiste en conectar todo y esperar mejores PRs. Consiste en elegir un dominio, gobernar permisos, medir calidad y comprobar que el contexto reduce revisión humana en lugar de producir una capa nueva de confianza injustificada.",
            ]),
        ],
    },
    {
        "title": "GitHub Copilot pasa a AI Credits por tokens: qué revisar antes del 1 de junio de 2026",
        "slug": "github-copilot-ai-credits-tokens-junio-2026",
        "status": "published",
        "meta_description": "El 1 de junio de 2026 Copilot migra a billing por uso con AI Credits y tokens. Guía para ajustar presupuestos, agentes y modelos.",
        "excerpt": "Mañana cambia el billing de Copilot: las premium requests dan paso a AI Credits calculados por tokens. Esto es lo que debe revisar un equipo técnico.",
        "sources": [
            ("GitHub Blog: Copilot moving to usage-based billing", "https://github.blog/news-insights/company-news/github-copilot-is-moving-to-usage-based-billing/"),
            ("GitHub Docs: usage-based billing for individuals", "https://docs.github.com/en/copilot/concepts/billing/usage-based-billing-for-individuals"),
            ("GitHub Docs: usage-based billing for organizations", "https://docs.github.com/en/copilot/concepts/billing/usage-based-billing-for-organizations-and-enterprises"),
            ("GitHub Docs: budgets for usage-based billing", "https://docs.github.com/en/copilot/concepts/billing/budgets-for-usage-based-billing"),
            ("GitHub Changelog: April reports for usage-based billing", "https://github.blog/changelog/2026-05-12-april-reports-are-now-available-to-prepare-for-usage-based-billing/"),
            ("GitHub Docs: models and pricing", "https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing"),
        ],
        "related": [
            ("GitHub Copilot y AI Credits", "/github-copilot-ai-credits-pago-por-uso/"),
            ("Copilot Code Review y GitHub Actions", "/copilot-code-review-minutos-github-actions/"),
            ("Copilot coding agent: MCP y hooks", "/copilot-coding-agent-mcp-hooks-produccion/"),
            ("Métricas para agentes de código", "/metricas-agentes-codigo-productividad-coste/"),
        ],
        "sections": [
            ("Qué cambia mañana", [
                "El 1 de junio de 2026 GitHub Copilot empieza a migrar desde el modelo de premium requests hacia billing por uso con GitHub AI Credits. La unidad deja de ser una petición premium más o menos abstracta y pasa a reflejar consumo de tokens: entrada, salida y tokens cacheados, con precios vinculados al modelo usado.",
                "La idea de GitHub es alinear precio con coste real. Una pregunta rápida a un modelo ligero y una sesión larga de agente sobre varios archivos ya no son equivalentes. Para equipos técnicos, eso obliga a tratar Copilot como infraestructura de IA, no como una extensión de editor de coste fijo.",
                "Este artículo complementa la guía previa de AI Credits, pero se centra en el cambio operativo inmediato: qué mirar antes de que el modelo entre en vigor mañana.",
            ]),
            ("Qué es un AI Credit", [
                "GitHub define AI Credits como una unidad de billing donde 1 AI Credit equivale a 0,01 USD. Cada interacción que usa modelos consume tokens. Esos tokens se valoran según el modelo y se convierten a créditos.",
                "En planes individuales, Copilot Pro, Pro+ y Max incluyen asignaciones mensuales de AI Credits. En organizaciones y empresas, cada licencia aporta créditos que se agrupan en un pool compartido a nivel de billing entity.",
                "La diferencia clave con el sistema anterior es que el consumo puede variar mucho dentro de una misma función. Dos sesiones de chat no cuestan igual si una es una pregunta corta y otra arrastra contexto de repositorio, varias iteraciones y generación de código extensa.",
            ]),
            ("Qué consume créditos y qué no", [
                "GitHub documenta que consumen AI Credits funciones como Copilot Chat, Copilot CLI, Copilot cloud agent, Copilot Spaces, Spark y agentes de terceros. Las code completions y Next Edit suggestions no se facturan en AI Credits y siguen incluidas en planes de pago.",
                "Esta distinción es importante para no sobrerreaccionar. El autocompletado diario no es el problema principal. El riesgo vive en sesiones agentic largas, modelos caros, cloud agent, revisiones automáticas y tareas que disparan varias llamadas al modelo sin que el usuario vea cada paso.",
                "Además, Copilot Code Review añade una segunda capa: también empezará a consumir minutos de GitHub Actions. Para equipos con revisión automática, el coste real puede venir de dos contadores: AI Credits y minutos de CI.",
            ]),
            ("Impacto en individuos", [
                "Para un desarrollador individual, el cambio práctico es revisar el panel de uso durante las primeras semanas. Si usas Copilot como autocomplete, chat corto y ayuda puntual, probablemente el consumo sea controlable. Si usas agentes para tareas multiarchivo, modelos frontier y sesiones largas, el gasto puede subir más rápido.",
                "La primera decisión no debería ser cambiar de herramienta. Debería ser separar tareas. Usa modelos ligeros para preguntas simples, reserva modelos caros para diseño o debugging complejo y evita pedir al agente que explore todo el repositorio cuando puedes darle un punto de entrada concreto.",
                "También conviene configurar presupuesto adicional solo si entiendes tu patrón de uso. Comprar margen sin medir puede ocultar el problema; bloquear todo sin margen puede cortar trabajo justo cuando necesitas una sesión larga legítima.",
            ]),
            ("Impacto en empresas", [
                "En Copilot Business y Enterprise, los créditos se agrupan. Esto reduce capacidad desperdiciada: usuarios ligeros compensan a usuarios intensivos. Pero también crea un riesgo nuevo: una minoría de power users o agentes automáticos puede consumir una parte desproporcionada del pool a principio de ciclo.",
                "GitHub documenta presupuestos a nivel usuario, cost center y enterprise. El user-level budget es especialmente importante porque aplica como límite duro al consumo individual. Los budgets de cost center y enterprise actúan sobre gasto medido después de agotar el pool, y necesitan configuración explícita para detener uso cuando se alcanza el límite.",
                "Para organizaciones existentes hay una fase promocional entre el 1 de junio y el 1 de septiembre de 2026 con más créditos incluidos. Eso puede suavizar el arranque, pero también puede ocultar el consumo real si no se revisa antes de que termine la promoción.",
            ]),
            ("Checklist antes del 1 de junio", [
                "Descarga o revisa los reportes de uso disponibles para estimar consumo con el nuevo modelo.",
                "Identifica usuarios con uso intensivo de agentes, modelos premium o cloud agent.",
                "Separa uso interactivo de automatizaciones en PRs, issues, CLI y workflows.",
                "Configura user-level budgets razonables para evitar que un usuario agote el pool.",
                "Define si se permite paid usage cuando se agoten los créditos incluidos.",
                "Activa límites con stop cuando aplique; un presupuesto que solo observa no controla coste.",
                "Revisa Copilot Code Review porque puede consumir AI Credits y minutos de Actions.",
                "Documenta qué modelos se recomiendan para tareas simples, tareas complejas y sesiones agentic.",
            ]),
            ("Cómo reducir consumo sin matar productividad", [
                "El ahorro más limpio es dar mejores tareas al agente. Un prompt con módulo, síntoma, test esperado y archivos permitidos consume menos que pedir 'arregla esto' y dejar que explore durante diez turnos.",
                "El segundo ajuste es modelo. No todo necesita el modelo más caro. Preguntas de sintaxis, explicación de errores y cambios mecánicos pueden ir a modelos más baratos. Diseño de arquitectura, debugging difícil o migraciones críticas justifican modelos más capaces.",
                "El tercer ajuste es automatización selectiva. Si cada push, PR o comentario dispara trabajo de IA, el consumo deja de estar ligado a intención humana. Usa etiquetas, rutas críticas y triggers manuales hasta tener datos.",
            ]),
            ("Qué métricas mirar en junio", [
                "Mira créditos por usuario, por repositorio, por tipo de función y por resultado. La métrica útil no es consumo bruto, sino coste por cambio aceptado, coste por PR revisado con comentario útil y coste por hora humana ahorrada.",
                "Registra falsos positivos y sesiones descartadas. Si una parte relevante del consumo termina en cambios rechazados, el problema no es solo precio; es mala configuración de contexto, modelo o alcance.",
                "Compara semanas, no días sueltos. Los lunes de triage, cierres de sprint y migraciones grandes pueden distorsionar el uso. Dos o tres ciclos de desarrollo dan una señal más justa.",
            ]),
            ("Conclusión", [
                "El cambio de Copilot a AI Credits por tokens no significa que Copilot deje de ser útil. Significa que el coste empieza a parecerse más al coste real de usar modelos y agentes. Eso es más honesto, pero exige más disciplina.",
                "La respuesta pragmática es medir, presupuestar y limitar por caso de uso. Autocomplete y chat corto pueden seguir siendo herramientas diarias. Agentes largos, modelos caros y revisión automática deben tratarse como capacidad de ingeniería con dueño, política y métricas.",
            ]),
        ],
    },
]


EXTRA_SECTIONS = {
    "github-copilot-ai-credits-pago-por-uso": [
        ("Cómo leer el consumo sin engañarte", [
            "Mira el consumo por tipo de tarea, no solo por usuario. Si un desarrollador gasta mucho porque resuelve migraciones complejas con agent mode, puede ser buen gasto. Si otro gasta parecido haciendo preguntas genéricas que podría resolver la documentación, ahí hay una oportunidad de formación.",
            "También conviene mirar consumo por repositorio. Un repo legado suele generar más preguntas, más contexto y más intentos fallidos que un servicio pequeño y bien documentado. Si mezclas todo en una cifra global, no sabrás si Copilot está caro o si tu codebase está haciendo que cualquier herramienta sea cara.",
        ]),
        ("Presupuesto inicial recomendado", [
            "Para un equipo pequeño, empezaría con un límite que no bloquee el trabajo normal pero sí fuerce conversación cuando aparece uso anómalo. La primera meta no es ahorrar al céntimo: es descubrir patrones. Durante el primer mes, apunta qué tareas generan más consumo y si acabaron en código aceptado.",
            "Después de ese mes, separa tres bolsas: uso diario normal, uso avanzado planificado y experimentación. La experimentación es importante porque muchas mejoras de productividad nacen probando agentes, pero debe tener techo. Sin techo, todo experimento parece gratis hasta que aparece en billing.",
        ]),
        ("Señales de que estás usando Copilot mal", [
            "Preguntas al chat cosas que deberían estar en README interno.",
            "Usas modelos premium para tareas mecánicas de búsqueda o formato.",
            "Pides refactors grandes sin tests y luego gastas más tokens corrigiendo daños.",
            "Activaste code review automático en repos que casi no tienen riesgo.",
            "Nadie revisa el dashboard porque “seguro que no será tanto”.",
        ]),
        ("FAQ", [
            "¿AI Credits significa que Copilot será necesariamente más caro? No siempre. Si usas funciones básicas y controlas modelos premium, puede mantenerse razonable. El riesgo está en tareas avanzadas y automáticas.",
            "¿Debo prohibir agent mode? No. Debes reservarlo para tareas donde el contexto multiarchivo tiene valor real.",
            "¿Qué hago si el equipo se queda sin crédito? Revisa primero patrones de uso antes de comprar más. Puede que estés pagando por ruido.",
        ]),
    ],
    "copilot-code-review-minutos-github-actions": [
        ("Cómo diseñar una prueba piloto", [
            "El peor despliegue posible es activar revisión automática en toda la organización el día uno. Mejor escoge dos repos: uno con riesgo real y otro con actividad media. Activa Copilot Code Review durante dos semanas y registra tres datos: minutos consumidos, comentarios generados y comentarios que terminaron en cambios.",
            "No cuentes como éxito que Copilot comente mucho. Un reviewer humano útil no es el que más habla; es el que detecta el problema adecuado en el momento adecuado. La IA debe medirse igual.",
        ]),
        ("Archivos que normalmente excluiría", [
            "Lockfiles y archivos generados.",
            "Snapshots de tests visuales.",
            "Migraciones generadas automáticamente, salvo que afecten datos críticos.",
            "Cambios de contenido editorial sin lógica.",
            "Bumps masivos de dependencias donde ya tienes CI fuerte.",
        ]),
        ("Dónde sí puede brillar", [
            "Copilot Code Review puede ser especialmente útil en PRs que tocan validaciones, permisos, serialización, parsing, concurrencia o manejo de errores. Son zonas donde un comentario temprano puede ahorrar una regresión real.",
            "También puede ayudar en equipos con reviewers junior. No porque sustituya criterio senior, sino porque genera una segunda lista de cosas que mirar. El valor está en enseñar a revisar mejor, no en delegar la responsabilidad.",
        ]),
        ("FAQ", [
            "¿Consume minutos en repos públicos y privados igual? Revisa la documentación de GitHub para tu plan, porque el impacto depende del tipo de runner y configuración.",
            "¿Lo activo en dependabot? Solo si tus dependencias suelen romper código de forma sutil. Para bumps rutinarios, CI suele dar mejor señal.",
            "¿Sirve para seguridad? Puede encontrar problemas, pero no sustituye SAST, revisión humana ni threat modeling.",
        ]),
        ("Plan de acción de 30 minutos", [
            "Abre los últimos 20 pull requests del repo y clasifícalos en tres grupos: triviales, normales y críticos. Si más de la mitad son triviales, no actives revisión automática global. Si hay muchos críticos, define primero qué rutas y tipos de cambio merecen revisión de IA.",
            "Después mira el consumo actual de Actions. Si ya estás cerca del límite mensual, Copilot Code Review debe entrar con etiquetas manuales o reglas de exclusión. Si tienes margen amplio, puedes probar dos semanas con un único repositorio y revisar si los comentarios generaron cambios reales.",
            "El resultado de esa revisión debería ser una regla operativa, no una sensación. Por ejemplo: revisión automática solo para PRs que toquen `src/auth`, `src/billing`, migraciones o más de 300 líneas de código real.",
        ]),
    ],
    "github-copilot-datos-entrenamiento-privacidad": [
        ("Plantilla de política interna", [
            "Puedes empezar con una política corta: Copilot está permitido para repos internos no regulados, prohibido para secretos o datos personales, limitado en proyectos de cliente salvo aprobación escrita, y cualquier sugerencia debe revisarse como código propio.",
            "Añade una sección de cuentas: trabajo profesional solo con cuentas gestionadas por la organización. Si alguien usa una cuenta personal, la empresa pierde visibilidad de configuración, facturación y políticas.",
        ]),
        ("Qué hacer con clientes", [
            "Si trabajas para terceros, no asumas permiso. Muchos contratos antiguos no mencionan IA, pero sí confidencialidad, subprocesadores o transferencia de datos. Antes de usar Copilot en código de cliente, documenta qué herramienta se usará, qué datos puede procesar y qué controles están activados.",
            "No hace falta convertirlo en burocracia eterna. Basta con una cláusula clara y una matriz simple: permitido, permitido con restricciones, prohibido.",
        ]),
        ("Errores de seguridad muy normales", [
            "Pegar un stack trace con tokens en una conversación.",
            "Abrir un archivo `.env` mientras el asistente tiene contexto amplio.",
            "Pedir explicación de código con nombres de clientes dentro.",
            "Usar una cuenta personal en repos de empresa.",
            "No revisar cambios generados en autenticación o permisos.",
        ]),
        ("FAQ", [
            "¿Copilot ve todo mi repositorio? Depende de la función y configuración. Algunas funciones usan contexto local o de repositorio; por eso importa leer la documentación del plan.",
            "¿Opt-out basta? Ayuda, pero no sustituye una política de uso. Opt-out de entrenamiento no significa que no haya procesamiento para responder.",
            "¿Qué alternativa uso para código sensible? Modelos locales, entornos aislados o simplemente no usar IA en esos módulos.",
        ]),
        ("Preguntas para tu equipo legal o tu cliente", [
            "¿El contrato permite enviar fragmentos de código a proveedores externos de IA? ¿Hay restricciones de país, subprocesadores o retención? ¿El cliente considera los prompts y respuestas como información confidencial? Estas preguntas suenan lentas, pero evitan discusiones peores cuando ya hay commits hechos.",
            "Si no hay respuesta, actúa con principio de mínimo contexto: usa Copilot solo en partes no sensibles, evita prompts con datos reales y documenta qué configuración de privacidad se aplicó. La falta de política explícita no debería interpretarse como permiso total.",
            "También conviene acordar cómo se revisan cambios generados con ayuda de IA. La privacidad no termina al enviar el prompt: si una sugerencia introduce código inseguro o licencias dudosas, el responsable sigue siendo el equipo que la acepta.",
        ]),
    ],
    "serena-mcp-busqueda-semantica-codigo": [
        ("Cómo introducir Serena en un equipo", [
            "No lo presentes como “otra herramienta de IA”. Preséntalo como infraestructura para que los agentes no trabajen a ciegas. Esa diferencia importa: el equipo no evalúa Serena por si escribe código bonito, sino por si reduce lecturas inútiles, ediciones equivocadas y tiempo de revisión.",
            "Empieza en un repo donde ya tengáis fricción con agentes. Si el proyecto es demasiado simple, no vas a ver el valor. Si es demasiado caótico, tampoco sabrás si el fallo viene de Serena o de la arquitectura.",
        ]),
        ("Comparativa práctica", [
            "Grep responde: dónde aparece esta cadena.",
            "El IDE responde: qué símbolo es, dónde se define y quién lo usa.",
            "Serena intenta dar esa segunda clase de respuesta a un agente.",
            "Un RAG genérico responde por similitud semántica, pero puede perder estructura de código.",
            "Un LSP expone estructura, pero el agente necesita herramientas que se la presenten de forma usable.",
        ]),
        ("Criterios de éxito", [
            "Menos archivos leídos por tarea.",
            "Menos cambios fuera del alcance pedido.",
            "Más referencias correctas al modificar una función.",
            "Menos tiempo humano explicando al agente dónde está cada cosa.",
            "Mejor comportamiento en refactors con tests existentes.",
        ]),
        ("FAQ", [
            "¿Serena reemplaza a Cursor o Claude Code? No. Es una capa de herramientas que puede mejorar cómo trabajan agentes o clientes compatibles.",
            "¿Hace falta MCP? Para integrarlo como herramienta de agente, sí: MCP es el canal que permite exponer esas capacidades.",
            "¿Es para todos los equipos? No. Brilla más cuanto más grande y semánticamente rico es el proyecto.",
        ]),
        ("Cómo escribir mejores tareas para un agente con Serena", [
            "No digas solo “arregla el bug”. Da un punto de entrada: módulo, síntoma, test que falla o función sospechosa. Serena puede ayudar a navegar, pero el agente sigue necesitando una dirección inicial. Cuanto más clara sea la frontera, menos probable será que lea medio repositorio.",
            "Un buen encargo sería: “investiga por qué `calculateInvoiceTotal` ignora descuentos de tipo anual; localiza referencias, añade un test y toca solo el módulo de billing salvo que encuentres una dependencia directa”. Ese prompt permite usar símbolos, referencias y tests con intención concreta.",
            "La combinación ideal es contexto humano breve más navegación semántica automática. El humano define el objetivo y las restricciones; Serena ayuda al agente a no perderse entre nombres parecidos, archivos grandes y dependencias laterales.",
            "Si además tienes convenciones en `AGENTS.md` o documentación interna, el resultado mejora: el agente sabe cómo moverse y Serena le ayuda a comprobar dónde aplicar ese conocimiento.",
            "Sin esa capa de instrucciones, incluso una buena herramienta semántica puede terminar acelerando una decisión mal planteada.",
        ]),
    ],
    "rtk-proxy-cli-reducir-tokens-ia": [
        ("Ejemplo de salida que conviene compactar", [
            "Piensa en un test runner que imprime 300 líneas, de las cuales 260 son inicialización, warnings conocidos y rutas repetidas. El agente no necesita todo eso para actuar. Necesita saber qué comando se ejecutó, si falló, qué test falló, el mensaje principal y quizá 20 líneas de contexto.",
            "Ese es el espacio donde RTK tiene sentido. No intenta hacer al modelo más inteligente; intenta no alimentarlo con ruido caro.",
        ]),
        ("Cómo probarlo sin arriesgarte", [
            "Durante una semana, guarda salidas completas y salidas compactadas de los mismos comandos. Luego mira si la versión compactada habría bastado para arreglar el problema.",
            "Si en tres de cada diez casos necesitas volver a la salida completa, no pasa nada. Eso puede seguir siendo rentable. Si en ocho de cada diez casos falta información crítica, estás compactando mal o usando RTK en comandos equivocados.",
        ]),
        ("Relación con observabilidad", [
            "RTK no arregla logs malos. Si tu aplicación imprime mensajes ambiguos, el resumen será ambiguo. Antes de optimizar tokens, conviene mejorar errores: códigos claros, mensajes específicos, rutas de archivo y contexto mínimo.",
            "Los equipos que más se benefician de herramientas así suelen ser los que ya tienen buenos tests y logs. La compactación funciona mejor cuando la señal original existe.",
        ]),
        ("FAQ", [
            "¿RTK reduce coste siempre? No. Reduce coste cuando hay ruido eliminable.",
            "¿Puede ocultar bugs? Sí, si se usa sin acceso fácil a la salida completa.",
            "¿Lo usaría en CI? Primero lo usaría en sesiones interactivas. CI crítico requiere más cuidado.",
        ]),
        ("Comandos donde empezaría", [
            "Empezaría con comandos de alta verbosidad y bajo riesgo: `npm test`, `pytest`, `pnpm lint`, logs locales y salidas de build. No empezaría por comandos de migración, despliegue o datos de producción, porque ahí prefiero ver todo hasta entender bien el comportamiento.",
            "La señal de que RTK funciona no es solo que la salida sea más corta. Es que el agente toma la misma decisión correcta con menos contexto. Si después de compactar empieza a pedir “muéstrame la salida completa” constantemente, el ahorro teórico no se está materializando.",
            "Guarda algunos ejemplos de antes y después. Si el resumen conserva comando, exit code, error principal y ruta afectada, probablemente va bien. Si solo deja una frase bonita, has convertido depuración en adivinanza.",
            "Mi criterio sería simple: la salida compactada debe permitir a otro desarrollador entender qué falló sin abrir el log completo en el 70% de los casos cotidianos.",
            "Cuando no alcance ese listón, deja el comando fuera del flujo optimizado.",
            "La optimización debe ser reversible y observable; si no puedes comparar, no sabes si mejoraste.",
            "Ese control es lo que evita confundir ahorro de tokens con pérdida de señal.",
        ]),
    ],
    "zed-parallel-agents-editor-ia": [
        ("Un flujo realista de trabajo", [
            "Supón que tienes que cambiar una API interna. No lanzaría tres agentes a tocar código. Haría esto: un agente investiga consumidores actuales, otro prepara tests de comportamiento esperado y tú decides el diseño. Solo después daría a un agente una tarea de implementación con alcance claro.",
            "El paralelismo bueno adelanta investigación y preparación. El paralelismo malo reparte decisiones que deberían estar centralizadas.",
        ]),
        ("Cómo revisar resultados", [
            "Revisa cada hilo como si fuera una rama de trabajo distinta. Primero intención: qué intentaba hacer. Después diff: qué cambió. Después pruebas: qué evidencia trae. Si un agente no puede explicar su propio resultado de forma concreta, no mezcles su trabajo con el resto.",
            "No aceptes cambios de varios agentes en un único commit gigante. La promesa de velocidad desaparece si luego nadie puede aislar qué agente introdujo qué decisión.",
        ]),
        ("Patrones de coordinación", [
            "Un agente investigador no edita archivos.",
            "Un agente de tests solo toca tests.",
            "Un agente de implementación solo toca el módulo asignado.",
            "Un agente de documentación espera a que el comportamiento esté cerrado.",
            "El humano integra, no delega la integración.",
        ]),
        ("FAQ", [
            "¿Parallel Agents es mejor que un solo agente? Solo si las tareas son independientes.",
            "¿Necesito worktrees? Para tareas grandes, sí ayuda mucho.",
            "¿Es buena idea para juniors? Puede serlo si hay revisión fuerte. Sin revisión, multiplica errores.",
        ]),
        ("Un protocolo de uso que sí aplicaría", [
            "Antes de lanzar agentes, escribe una mini tabla en una nota: agente, objetivo, archivos permitidos, salida esperada y criterio de aceptación. Parece burocrático, pero tarda dos minutos y evita que cada hilo improvise su propio alcance.",
            "Cuando terminen, no revises en el orden en que acabaron. Revisa primero la investigación, luego tests, luego implementación y por último documentación. Ese orden reduce sesgos: si miras primero el código generado, es fácil aceptar una solución solo porque ya existe.",
        ]),
        ("Cuándo apagar el paralelismo", [
            "Si ves que dos agentes empiezan a tocar los mismos archivos, pausa uno. Si un agente cambia arquitectura sin pedir confirmación, descártalo. Si el diff deja de ser explicable en un minuto, divide de nuevo. La velocidad solo cuenta si el resultado se puede revisar.",
            "También lo apagaría cuando el equipo está aprendiendo una parte nueva del dominio. En esa fase, leer y entender importa más que producir cambios rápido. Los agentes paralelos son mejores cuando ya sabes qué quieres conseguir y solo necesitas avanzar varias piezas independientes.",
            "En otras palabras: paraleliza ejecución, no criterio. El criterio técnico debe seguir viviendo en una persona o en una decisión de diseño compartida.",
            "Ese matiz separa un flujo profesional de una carrera para generar diffs.",
            "El objetivo no es producir más cambios, sino producir cambios que puedas defender.",
            "Si el resultado no se puede explicar en revisión, el paralelismo no ayudó.",
            "La velocidad solo cuenta cuando mantiene trazabilidad.",
            "Sin trazabilidad, solo has generado más trabajo pendiente para el reviewer.",
        ]),
    ],
    "vs-code-copilot-coauthored-by-commits": [
        ("Por qué coautoría no es lo mismo que asistencia", [
            "En GitHub, `Co-authored-by` tiene un significado social y técnico: atribuye participación en un commit. Usarlo para señalar que una herramienta hizo una sugerencia menor puede ser demasiado fuerte. Usarlo cuando la herramienta no participó es directamente engañoso.",
            "El sector necesita mejores convenciones para asistencia de IA. Mientras tanto, equipos y herramientas están reutilizando etiquetas pensadas para humanos. Esa fricción explica por qué este cambio molestó tanto.",
        ]),
        ("Cómo detectarlo en repos existentes", [
            "Puedes buscar en el historial con `git log --grep=\"Co-authored-by: Copilot\"`. Si aparece, revisa si fue intencional. No hace falta reescribir historia salvo que haya una razón fuerte, pero sí conviene entender cuándo empezó y desde qué herramienta se generó.",
            "En repos regulados o de cliente, crea una nota interna. No esperes a una auditoría para descubrir que el historial afirma una participación de IA que nadie aprobó.",
        ]),
        ("Qué deberían hacer las herramientas", [
            "Pedir confirmación explícita antes de añadir atribución.",
            "Distinguir sugerencia menor de generación sustancial.",
            "Respetar configuraciones globales de desactivar IA.",
            "Mostrar el trailer antes de commit, no después.",
            "Explicar qué condición disparó la atribución.",
        ]),
        ("FAQ", [
            "¿Debo borrar todos los trailers de Copilot? No necesariamente. Si reflejan uso real y tu política lo permite, pueden quedarse.",
            "¿Terminal evita el problema? En muchos casos la UI del editor es la que modifica mensajes, pero revisa tu configuración concreta.",
            "¿La IA puede ser coautora legal? No lo trates como asesoría legal. Para repos profesionales, define una convención interna y consúltala si hay obligaciones contractuales.",
        ]),
        ("Comando de auditoría rápida", [
            "Para revisar un repositorio, puedes empezar con `git log --grep=\"Co-authored-by: Copilot\" --oneline`. Si aparecen commits inesperados, mira si fueron creados desde la UI de VS Code, desde terminal o desde otra extensión. El objetivo no es buscar culpables, sino entender qué herramienta está modificando mensajes.",
            "Si el repositorio pertenece a un cliente, guarda la conclusión: fecha, configuración revisada y decisión del equipo. Una nota simple puede ahorrar una discusión incómoda meses después, cuando alguien pregunte por qué aparece Copilot en el historial.",
            "Para trabajo futuro, añade esta revisión al checklist de onboarding del editor. No es suficiente configurar linters y formatters; con herramientas de IA, también hay que revisar qué metadatos pueden tocar.",
            "Este tipo de higiene parece menor hasta que un contrato, una auditoría o una revisión de propiedad intelectual convierte el historial Git en evidencia.",
            "Por eso conviene resolverlo como configuración de equipo, no como preferencia individual.",
            "Un repositorio compartido necesita reglas compartidas también para la metadata.",
        ]),
    ],
}

for article in ARTICLES:
    article["sections"].extend(EXTRA_SECTIONS.get(article["slug"], []))


GUIDE_EXCERPTS = {
    "v0-dev-generar-ui-ia": "Guía de v0.dev para generar interfaces React y Tailwind con IA, entender sus límites y usarlo mejor en proyectos reales.",
    "bolt-new-crear-apps-ia-navegador": "Guía de Bolt.new para crear aplicaciones completas desde el navegador con IA, WebContainers y despliegue rápido.",
    "replit-programar-navegador-ia": "Replit combina IDE online, colaboración y funciones de IA para crear prototipos y aprender programación sin instalar nada.",
    "amazon-q-developer-ia-aws": "Amazon Q Developer ayuda a programar, revisar y entender proyectos dentro del ecosistema AWS con asistencia de IA.",
    "tabnine-autocompletado-codigo-ia": "Tabnine ofrece autocompletado de código con IA para equipos que priorizan compatibilidad con IDEs y privacidad.",
    "windsurf-ide-editor-ia": "Windsurf IDE combina editor, agente de IA y contexto de proyecto para competir con Cursor en flujos de desarrollo asistido.",
    "github-copilot-guia-completa": "Guía completa de GitHub Copilot: instalación, chat, instrucciones personalizadas, privacidad, pricing y alternativas.",
    "cursor-ai-que-es-guia-completa": "Guía de Cursor AI para entender Composer, reglas de proyecto, edición con IA y diferencias frente a Copilot y Claude Code.",
    "claude-code-que-es-guia-completa": "Guía de Claude Code para usar agentes de terminal, permisos, comandos, contexto de proyecto y automatización de desarrollo.",
}


PATTERN_BY_SLUG = {
    "github-copilot-ai-credits-pago-por-uso": "decision_memo",
    "copilot-code-review-minutos-github-actions": "rollout_playbook",
    "github-copilot-datos-entrenamiento-privacidad": "policy_brief",
    "serena-mcp-busqueda-semantica-codigo": "field_guide",
    "rtk-proxy-cli-reducir-tokens-ia": "lab_notes",
    "zed-parallel-agents-editor-ia": "operating_manual",
    "vs-code-copilot-coauthored-by-commits": "audit_note",
    "real-time-chunking-rag-streaming": "architecture_deep_dive",
    "ia-apuestas-deportivas-modelos-riesgos": "risk_model_brief",
    "value-betting-probabilidad-implicita-edge": "risk_model_brief",
    "player-props-nba-modelo-variables": "field_guide",
    "predicciones-futbol-poisson-xg-calibracion": "field_guide",
    "mcp-produccion-seguridad-permisos-supply-chain": "policy_brief",
    "agents-md-claude-md-memoria-proyecto": "operating_manual",
    "pull-requests-agentes-ia-gobernanza-humana": "audit_note",
    "coordinar-varios-agentes-codex-claude-cursor": "operating_manual",
    "metricas-agentes-codigo-productividad-coste": "decision_memo",
    "hooks-agentes-codigo-guardrails-validacion": "operating_manual",
    "tabnine-vs-github-copilot": "decision_memo",
    "tabnine-vs-cursor": "decision_memo",
    "codex-acceso-internet-sandbox-seguridad": "policy_brief",
    "claude-code-github-actions-ci-seguridad": "rollout_playbook",
    "copilot-coding-agent-mcp-hooks-produccion": "rollout_playbook",
    "tabnine-enterprise-context-engine-agentes": "field_guide",
    "github-copilot-ai-credits-tokens-junio-2026": "decision_memo",
}


SEO_META_TITLES = {
    "github-copilot-ai-credits-pago-por-uso": "GitHub Copilot AI Credits: coste y límites",
    "copilot-code-review-minutos-github-actions": "Copilot Code Review y GitHub Actions",
    "github-copilot-datos-entrenamiento-privacidad": "Copilot y privacidad: guía para equipos",
    "serena-mcp-busqueda-semantica-codigo": "Serena MCP: código semántico para agentes",
    "rtk-proxy-cli-reducir-tokens-ia": "RTK: menos tokens para agentes de IA",
    "zed-parallel-agents-editor-ia": "Zed Parallel Agents: guía práctica",
    "vs-code-copilot-coauthored-by-commits": "VS Code y Copilot Co-authored-by",
    "real-time-chunking-rag-streaming": "Real-time chunking para RAG y agentes",
    "ia-apuestas-deportivas-modelos-riesgos": "IA en apuestas deportivas: modelos y riesgos",
    "value-betting-probabilidad-implicita-edge": "Value betting: probabilidad y edge",
    "player-props-nba-modelo-variables": "Player props NBA: variables de modelo",
    "predicciones-futbol-poisson-xg-calibracion": "Predicciones de fútbol con Poisson y xG",
    "mcp-produccion-seguridad-permisos-supply-chain": "MCP en producción: seguridad y permisos",
    "agents-md-claude-md-memoria-proyecto": "AGENTS.md y CLAUDE.md: contexto para agentes",
    "pull-requests-agentes-ia-gobernanza-humana": "PRs de agentes de IA: gobernanza humana",
    "coordinar-varios-agentes-codex-claude-cursor": "Cómo coordinar varios agentes de código",
    "metricas-agentes-codigo-productividad-coste": "Métricas para agentes de código",
    "hooks-agentes-codigo-guardrails-validacion": "Hooks para agentes de código: guardrails y validación",
    "tabnine-vs-github-copilot": "Tabnine vs GitHub Copilot",
    "tabnine-vs-cursor": "Tabnine vs Cursor",
    "codex-acceso-internet-sandbox-seguridad": "Codex con internet: sandbox y seguridad",
    "claude-code-github-actions-ci-seguridad": "Claude Code en GitHub Actions",
    "copilot-coding-agent-mcp-hooks-produccion": "Copilot coding agent: MCP y hooks",
    "tabnine-enterprise-context-engine-agentes": "Tabnine Context Engine para agentes",
    "github-copilot-ai-credits-tokens-junio-2026": "Copilot AI Credits por tokens: junio 2026",
}


ARTICLE_FEATURE_IMAGES = {
    "github-copilot-ai-credits-pago-por-uso": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1200&h=628&fit=crop&q=80",
    "copilot-code-review-minutos-github-actions": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=1200&h=628&fit=crop&q=80",
    "github-copilot-datos-entrenamiento-privacidad": "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=1200&h=628&fit=crop&q=80",
    "serena-mcp-busqueda-semantica-codigo": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?w=1200&h=628&fit=crop&q=80",
    "rtk-proxy-cli-reducir-tokens-ia": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?w=1200&h=628&fit=crop&q=80",
    "zed-parallel-agents-editor-ia": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=1200&h=628&fit=crop&q=80",
    "vs-code-copilot-coauthored-by-commits": "https://images.unsplash.com/photo-1556075798-4825dfaaf498?w=1200&h=628&fit=crop&q=80",
    "real-time-chunking-rag-streaming": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1200&h=628&fit=crop&q=80",
    "ia-apuestas-deportivas-modelos-riesgos": "https://images.unsplash.com/photo-1517649763962-0c623066013b?w=1200&h=628&fit=crop&q=80",
    "value-betting-probabilidad-implicita-edge": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=1200&h=628&fit=crop&q=80",
    "player-props-nba-modelo-variables": "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=1200&h=628&fit=crop&q=80",
    "predicciones-futbol-poisson-xg-calibracion": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?w=1200&h=628&fit=crop&q=80",
    "mcp-produccion-seguridad-permisos-supply-chain": "https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=1200&h=628&fit=crop&q=80",
    "agents-md-claude-md-memoria-proyecto": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?w=1200&h=628&fit=crop&q=80",
    "pull-requests-agentes-ia-gobernanza-humana": "https://images.unsplash.com/photo-1556075798-4825dfaaf498?w=1200&h=628&fit=crop&q=80",
    "coordinar-varios-agentes-codex-claude-cursor": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=1200&h=628&fit=crop&q=80",
    "metricas-agentes-codigo-productividad-coste": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1200&h=628&fit=crop&q=80",
    "hooks-agentes-codigo-guardrails-validacion": "https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=1200&h=628&fit=crop&q=80",
    "tabnine-vs-github-copilot": "https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=1200&h=628&fit=crop&q=80",
    "tabnine-vs-cursor": "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=1200&h=628&fit=crop&q=80",
    "codex-acceso-internet-sandbox-seguridad": "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=1200&h=628&fit=crop&q=80",
    "claude-code-github-actions-ci-seguridad": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=1200&h=628&fit=crop&q=80",
    "copilot-coding-agent-mcp-hooks-produccion": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=1200&h=628&fit=crop&q=80",
    "tabnine-enterprise-context-engine-agentes": "https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=1200&h=628&fit=crop&q=80",
    "github-copilot-ai-credits-tokens-junio-2026": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1200&h=628&fit=crop&q=80",
}


EDITORIAL_PATTERNS = {
    "decision_memo": {
        "kicker": "Decisión rápida",
        "cycle": ["briefing", "card", "checklist", "essay", "card", "compact"],
        "close": ("Criterio final", "Si no puedes medir consumo, limitar funciones avanzadas y revisar excepciones, todavía no estás listo para tratarlo como coste controlado."),
    },
    "rollout_playbook": {
        "kicker": "Plan de despliegue",
        "cycle": ["checklist", "briefing", "card", "essay", "compact", "checklist"],
        "close": ("Regla operativa", "Activa la automatización donde el comentario pueda cambiar una decisión técnica, no donde solo vaya a producir ruido revisable."),
    },
    "policy_brief": {
        "kicker": "Riesgo principal",
        "cycle": ["briefing", "card", "essay", "checklist", "card", "compact"],
        "close": ("Política mínima", "Cuenta gestionada, límites de contexto y revisión humana explícita. Sin esas tres piezas, la privacidad queda demasiado abierta a interpretaciones."),
    },
    "field_guide": {
        "kicker": "Regla práctica",
        "cycle": ["essay", "compact", "card", "checklist", "briefing", "card"],
        "close": ("Dónde aporta", "Serena tiene sentido cuando el problema no es escribir más código, sino moverse por un repositorio sin perder significado."),
    },
    "lab_notes": {
        "kicker": "Hipótesis de prueba",
        "cycle": ["briefing", "card", "essay", "compact", "checklist", "card"],
        "close": ("Medida útil", "La compactación funciona si conserva la decisión técnica que tomaría una persona con el log completo delante."),
    },
    "operating_manual": {
        "kicker": "Modo de trabajo",
        "cycle": ["card", "essay", "checklist", "briefing", "compact", "card"],
        "close": ("Límite sano", "Paraleliza investigación y tareas acotadas. No paralelices criterio técnico ni integración final."),
    },
    "audit_note": {
        "kicker": "Punto de auditoría",
        "cycle": ["briefing", "card", "checklist", "essay", "compact", "card"],
        "close": ("Higiene de equipo", "La autoría en Git no debería depender de una preferencia local del editor. Debe estar definida como política del repositorio."),
    },
    "architecture_deep_dive": {
        "kicker": "Arquitectura base",
        "cycle": ["briefing", "essay", "card", "checklist", "compact", "essay", "card"],
        "close": ("Criterio técnico", "Un buen chunk en tiempo real no es el más corto ni el más semántico: es el que conserva evidencia, tiempo y estado suficiente para responder sin inventar continuidad."),
    },
    "risk_model_brief": {
        "kicker": "Riesgo principal",
        "cycle": ["briefing", "essay", "card", "checklist", "essay", "compact", "card"],
        "close": ("Línea roja", "Si un producto de apuestas con IA no muestra incertidumbre, calibración e histórico completo, no está haciendo análisis serio: está vendiendo confianza."),
    },
}


def editorial_pattern(spec: dict) -> dict:
    pattern_name = PATTERN_BY_SLUG.get(spec["slug"])
    if not pattern_name:
        names = sorted(EDITORIAL_PATTERNS)
        digest = hashlib.sha1(spec["slug"].encode()).hexdigest()
        pattern_name = names[int(digest[:6], 16) % len(names)]
    return EDITORIAL_PATTERNS[pattern_name]


def _html_paragraphs(blocks: list[str] | str) -> str:
    if isinstance(blocks, str):
        blocks = [blocks]
    return "".join(
        f'<p style="margin:0 0 12px;color:#334155;line-height:1.65;font-size:15px;">{escape(block)}</p>'
        for block in blocks
        if block
    )


def editorial_card(kicker: str, title: str, blocks: list[str] | str) -> dict:
    return html_card(
        f"""<aside style="background:#f8fafc;border-left:4px solid #0ea5e9;border-radius:8px;padding:22px 24px;margin:30px 0;font-family:system-ui,sans-serif;">
  <p style="font-size:12px;font-weight:800;color:#0369a1;text-transform:uppercase;letter-spacing:.06em;margin:0 0 8px;">{escape(kicker)}</p>
  <p style="font-size:20px;font-weight:750;color:#0f172a;line-height:1.35;margin:0 0 12px;">{escape(title)}</p>
  {_html_paragraphs(blocks)}
</aside>"""
    )


def list_card(kicker: str, title: str, items: list[str]) -> dict:
    if all(len(item) <= 190 for item in items):
        body = "".join(
            f'<li style="margin:0 0 10px;color:#334155;line-height:1.55;font-size:15px;">{escape(item)}</li>'
            for item in items
        )
        content = f'<ul style="margin:0;padding-left:20px;">{body}</ul>'
    else:
        content = _html_paragraphs(items)
    return html_card(
        f"""<div style="background:#fff;border:1px solid #dbeafe;border-radius:10px;padding:22px 24px;margin:30px 0;font-family:system-ui,sans-serif;">
  <p style="font-size:12px;font-weight:800;color:#1d4ed8;text-transform:uppercase;letter-spacing:.06em;margin:0 0 8px;">{escape(kicker)}</p>
  <p style="font-size:19px;font-weight:750;color:#111827;line-height:1.35;margin:0 0 14px;">{escape(title)}</p>
  {content}
</div>"""
    )


def faq_card(blocks: list[str]) -> dict:
    rows = []
    schema_items = []
    for block in blocks:
        if "?" in block:
            question, answer = block.split("?", 1)
            schema_items.append(
                {
                    "@type": "Question",
                    "name": f"{question.strip()}?",
                    "acceptedAnswer": {"@type": "Answer", "text": answer.strip()},
                }
            )
            rows.append(
                f"""<details style="border-top:1px solid #e2e8f0;padding:14px 0;">
  <summary style="cursor:pointer;font-weight:700;color:#0f172a;">{escape(question.strip())}?</summary>
  <p style="margin:10px 0 0;color:#334155;line-height:1.65;font-size:15px;">{escape(answer.strip())}</p>
</details>"""
            )
        else:
            rows.append(f'<p style="margin:14px 0;color:#334155;line-height:1.65;font-size:15px;">{escape(block)}</p>')
    schema = ""
    if schema_items:
        schema = (
            '<script type="application/ld+json">'
            + json.dumps(
                {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": schema_items},
                ensure_ascii=False,
            )
            + "</script>"
        )
    return html_card(
        f"""<section style="margin:36px 0;font-family:system-ui,sans-serif;">
  {schema}
  <h2 style="font-size:28px;line-height:1.2;margin:0 0 12px;color:#0f172a;">Preguntas frecuentes</h2>
  {''.join(rows)}
</section>"""
    )


def looks_like_checklist(blocks: list[str]) -> bool:
    return len(blocks) >= 3 and all(block.endswith(".") and len(block) < 170 for block in blocks)


def render_section(title: str, blocks: list[str], variant: str) -> list[dict]:
    if title.strip().lower() == "faq":
        return [faq_card(blocks)]
    if variant == "card":
        return [editorial_card("Lectura práctica", title, blocks)]
    if variant == "checklist" or looks_like_checklist(blocks):
        if looks_like_checklist(blocks):
            return [heading(title), bullet_list(blocks)]
        return [list_card("Checklist", title, blocks)]
    if variant == "compact":
        nodes = [heading(title)]
        nodes.append(paragraph(blocks[0]))
        if len(blocks) > 1:
            nodes.append(list_card("Puntos a revisar", "Lo que conviene comprobar", blocks[1:]))
        return nodes
    if variant == "briefing":
        joined = blocks[:2] if len(blocks) > 1 else blocks
        nodes = [editorial_card("Briefing", title, joined)]
        for block in blocks[2:]:
            nodes.append(paragraph(block))
        return nodes
    nodes = [heading(title)]
    nodes.extend(paragraph(block) for block in blocks)
    return nodes


def render_article_body(spec: dict) -> list[dict]:
    pattern = editorial_pattern(spec)
    sections = list(spec["sections"])
    first_title, first_blocks = sections[0]

    nodes = [paragraph(spec["excerpt"])]
    if first_blocks:
        nodes.append(paragraph(first_blocks[0]))
    if len(first_blocks) > 1:
        nodes.append(editorial_card(pattern["kicker"], first_title, first_blocks[1:]))

    cycle = pattern["cycle"]
    for index, (title, blocks) in enumerate(sections[1:]):
        nodes.extend(render_section(title, blocks, cycle[index % len(cycle)]))

    close_title, close_body = pattern["close"]
    nodes.append(editorial_card("Cierre editorial", close_title, close_body))
    return nodes


def build_article(spec: dict) -> dict:
    nodes = render_article_body(spec)
    nodes.append(sources_card(spec["sources"]))
    nodes.append(related_card(spec["related"]))
    nodes.append(html_card(CTA_HTML))

    return {
        "title": spec["title"],
        "slug": spec["slug"],
        "status": spec.get("status", "published"),
        "visibility": "public",
        "custom_excerpt": spec["excerpt"],
        "meta_title": SEO_META_TITLES.get(spec["slug"], spec["title"]),
        "meta_description": spec["meta_description"],
        "feature_image": ARTICLE_FEATURE_IMAGES.get(spec["slug"]),
        "tags": [{"name": "Guías", "slug": "guias"}, {"name": "evergreen", "slug": "evergreen"}],
        "lexical": build_lexical(nodes),
    } | ({"published_at": spec["published_at"]} if spec.get("published_at") else {})


def get_post_by_slug(client: httpx.Client, admin_api_key: str, slug: str) -> dict | None:
    resp = client.get(
        f"{GHOST_URL}/ghost/api/admin/posts/",
        headers=headers(admin_api_key),
        params={"filter": f"slug:{slug}", "formats": "lexical", "limit": "1"},
    )
    resp.raise_for_status()
    posts = resp.json().get("posts", [])
    return posts[0] if posts else None


def upsert_article(client: httpx.Client, admin_api_key: str, spec: dict) -> str:
    post = get_post_by_slug(client, admin_api_key, spec["slug"])
    payload = build_article(spec)
    if post:
        payload["updated_at"] = post["updated_at"]
        resp = client.put(
            f"{GHOST_URL}/ghost/api/admin/posts/{post['id']}/",
            headers=headers(admin_api_key),
            json={"posts": [payload]},
        )
        action = "updated"
    else:
        resp = client.post(
            f"{GHOST_URL}/ghost/api/admin/posts/",
            headers=headers(admin_api_key),
            json={"posts": [payload]},
        )
        action = "created"
    resp.raise_for_status()
    return action


def update_existing_guides(client: httpx.Client, admin_api_key: str) -> int:
    updated = 0
    for slug, excerpt in GUIDE_EXCERPTS.items():
        post = get_post_by_slug(client, admin_api_key, slug)
        if not post:
            continue
        payload = {
            "custom_excerpt": excerpt,
            "updated_at": post["updated_at"],
        }
        if not post.get("meta_title"):
            payload["meta_title"] = post["title"]
        if not post.get("meta_description"):
            payload["meta_description"] = excerpt
        resp = client.put(
            f"{GHOST_URL}/ghost/api/admin/posts/{post['id']}/",
            headers=headers(admin_api_key),
            json={"posts": [payload]},
        )
        resp.raise_for_status()
        updated += 1
    return updated


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish DevAI evergreen articles to Ghost.")
    parser.add_argument(
        "--slugs",
        nargs="+",
        help="Only publish these slugs. Accepts space-separated values or comma-separated groups.",
    )
    parser.add_argument(
        "--skip-guides",
        action="store_true",
        help="Skip updating existing guide excerpts.",
    )
    return parser.parse_args()


def selected_articles(slugs: list[str] | None) -> list[dict]:
    if not slugs:
        return ARTICLES

    requested = [
        slug.strip()
        for group in slugs
        for slug in group.split(",")
        if slug.strip()
    ]
    by_slug = {spec["slug"]: spec for spec in ARTICLES}
    missing = [slug for slug in requested if slug not in by_slug]
    if missing:
        raise SystemExit(f"Unknown article slug(s): {', '.join(missing)}")
    return [by_slug[slug] for slug in requested]


def main() -> None:
    args = parse_args()
    load_dotenv(ROOT / ".env")
    admin_api_key = os.getenv("GHOST_ADMIN_API_KEY", "").strip()
    if not admin_api_key:
        raise SystemExit("GHOST_ADMIN_API_KEY is required")

    with httpx.Client(timeout=30) as client:
        for spec in selected_articles(args.slugs):
            action = upsert_article(client, admin_api_key, spec)
            print(f"{action}: {spec['slug']}")
            time.sleep(1)
        if not args.skip_guides:
            guide_count = update_existing_guides(client, admin_api_key)
            print(f"updated existing guides: {guide_count}")


if __name__ == "__main__":
    main()
