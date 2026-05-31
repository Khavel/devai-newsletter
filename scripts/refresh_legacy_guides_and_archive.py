"""Refresh older SEO guides and rebuild the public archive page."""

from __future__ import annotations

import html
import json
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent))
from publish_evergreen_articles import (  # noqa: E402
    GHOST_URL,
    build_lexical,
    headers,
    heading,
    html_card,
    paragraph,
    related_card,
)


ROOT = Path(__file__).resolve().parents[1]
REFRESH_MARKER = "legacy-guide-refresh-2026-05-11"


GUIDE_REFRESHES = {
    "v0-dev-generar-ui-ia": {
        "excerpt": "v0 sirve para pasar de una idea a una interfaz o app desplegable en Vercel, pero funciona mejor cuando lo tratas como un par de producto, no como un generador mágico.",
        "meta": "Guía actualizada de v0: cuándo usarlo, cómo pedir mejores interfaces, límites reales y comparación con Bolt, Cursor y Copilot.",
        "sources": [
            ("Documentación de v0", "https://vercel.com/docs/v0"),
            ("Crear una app full-stack con v0", "https://vercel.com/docs/v0/workflows/full-stack-app"),
            ("v0.dev pasa a v0.app", "https://vercel.com/blog/v0-app"),
        ],
        "related": [
            ("Bolt.new: crear apps con IA en el navegador", "/bolt-new-crear-apps-ia-navegador/"),
            ("Cursor AI: guía completa", "/cursor-ai-que-es-guia-completa/"),
            ("GitHub Copilot: guía completa", "/github-copilot-guia-completa/"),
        ],
        "kicker": "Patrón editorial: diseño primero",
        "title": "Cómo usar v0 sin acabar con una demo bonita pero frágil",
        "intro": [
            "v0 ha cambiado bastante respecto a la primera ola de generadores de componentes. Ya no conviene explicarlo solo como “una herramienta que crea UI con Tailwind”. En la documentación actual, Vercel lo presenta como un par programador capaz de generar proyectos, integrarse con infraestructura de Vercel y desplegar desde la propia interfaz. Eso lo coloca más cerca de un constructor de producto que de una simple caja de prompts.",
            "La forma sensata de usarlo es empezar por decisiones de interfaz: flujo, estados, datos que se muestran, comportamiento esperado y restricciones del stack. Si el prompt solo dice “hazme un dashboard moderno”, el resultado puede parecer correcto pero será intercambiable. Si le das casos reales, errores, permisos y estados vacíos, el output empieza a parecerse a una pantalla que un equipo podría mantener.",
        ],
        "checks_title": "Antes de aceptar el resultado",
        "checks": [
            "Revisa si la UI tiene estados de carga, error, vacío y permisos, no solo el estado feliz.",
            "Comprueba si los componentes generados encajan con tu sistema de diseño o crean una segunda gramática visual.",
            "No despliegues sin mirar dependencias, variables de entorno y rutas creadas por la generación.",
            "Si usas Vercel, aprovecha previews; si no, exporta pronto el código y revísalo en tu flujo habitual.",
        ],
        "decision": "Usaría v0 para acelerar pantallas, prototipos y primeras versiones de producto. No lo usaría como sustituto de arquitectura frontend cuando ya existe un diseño de datos complejo, permisos finos o un sistema visual establecido.",
        "faq": [
            ("¿v0 reemplaza a un frontend developer?", "No. Reduce tiempo de arranque y exploración visual, pero alguien debe revisar accesibilidad, estados, integración real y deuda de componentes."),
            ("¿Es mejor que Bolt?", "Depende. v0 encaja mejor si tu destino natural es Vercel y te importa mucho la UI. Bolt suele ser más fuerte cuando quieres ejecutar una app completa dentro del navegador desde el primer minuto."),
        ],
    },
    "bolt-new-crear-apps-ia-navegador": {
        "excerpt": "Bolt.new es útil para prototipar apps web completas en el navegador, pero su coste real aparece cuando el proyecto crece y cada prompt arrastra más contexto.",
        "meta": "Guía actualizada de Bolt.new: WebContainers, prototipos full-stack, tokens, GitHub, límites y cuándo usarlo frente a v0 o Replit.",
        "sources": [
            ("Repositorio oficial de Bolt.new", "https://github.com/stackblitz/bolt.new"),
            ("Tokens en Bolt", "https://support.bolt.new/account-and-subscription/tokens"),
            ("Version history y GitHub en Bolt", "https://support.bolt.new/concepts/version-history-github"),
        ],
        "related": [
            ("v0.dev: generar UI con IA", "/v0-dev-generar-ui-ia/"),
            ("Replit: programar desde el navegador", "/replit-programar-navegador-ia/"),
            ("RTK: reducir tokens en agentes de IA", "/rtk-proxy-cli-reducir-tokens-ia/"),
            ("Métricas para agentes de código", "/metricas-agentes-codigo-productividad-coste/"),
        ],
        "kicker": "Patrón editorial: prototipo ejecutable",
        "title": "El valor de Bolt está en ver la app funcionando, no solo en generar código",
        "intro": [
            "Bolt.new destaca porque junta generación de código con un entorno de ejecución en el navegador. El repositorio oficial lo describe como una forma de pedir, ejecutar, editar y desplegar aplicaciones full-stack desde el browser. Esa diferencia importa: cuando el asistente puede instalar paquetes, levantar un servidor y mostrar preview, la conversación deja de ser solo “dame código” y pasa a ser “haz que esto funcione”.",
            "El riesgo está en confundir velocidad inicial con coste final. La propia documentación de Bolt sobre tokens explica que buena parte del consumo viene de leer, entender y sincronizar archivos del proyecto. Cuanto más crece la app, más caro puede ser cada mensaje si no cierras alcance, eliminas ruido y divides tareas.",
        ],
        "checks_title": "Flujo recomendado",
        "checks": [
            "Empieza con una app pequeña y una única ruta crítica: registro, dashboard, formulario o integración principal.",
            "Cuando funcione, conecta GitHub o exporta el proyecto antes de hacer cambios grandes.",
            "No pidas diez features en un prompt; separa UI, datos, autenticación y despliegue.",
            "Si Bolt entra en bucle arreglando errores, detén la sesión, lee el diff y reencuadra el problema.",
        ],
        "decision": "Bolt es muy bueno para validar si una idea puede convertirse en producto navegable. Para una base de código que ya tiene arquitectura, tests y estándares, lo usaría con mucha más cautela y siempre con control de versiones fuera de la conversación.",
        "faq": [
            ("¿Bolt sirve para producción?", "Puede acercarte a una primera versión, pero producción exige revisar seguridad, dependencias, persistencia, observabilidad y costes."),
            ("¿Por qué se gastan tantos tokens?", "Porque el asistente no solo responde: lee archivos, mantiene contexto del proyecto y genera cambios. En proyectos grandes, cada iteración puede arrastrar mucho más material."),
        ],
    },
    "replit-programar-navegador-ia": {
        "excerpt": "Replit ya no es solo un IDE online para aprender: con Agent se ha convertido en una plataforma para crear, probar y desplegar apps desde lenguaje natural.",
        "meta": "Guía actualizada de Replit AI y Replit Agent: usos reales, checkpoints, despliegue, aprendizaje, límites y comparación con Bolt.",
        "sources": [
            ("Replit AI", "https://docs.replit.com/replitai/getting-started"),
            ("Replit Agent", "https://docs.replit.com/core-concepts/agent/"),
            ("Agents & Automations", "https://docs.replit.com/core-concepts/agent/agents-and-automations"),
        ],
        "related": [
            ("Bolt.new: crear apps con IA", "/bolt-new-crear-apps-ia-navegador/"),
            ("Claude Code: guía completa", "/claude-code-que-es-guia-completa/"),
            ("Zed Parallel Agents", "/zed-parallel-agents-editor-ia/"),
            ("Métricas para agentes de código", "/metricas-agentes-codigo-productividad-coste/"),
        ],
        "kicker": "Patrón editorial: aprendizaje con ejecución",
        "title": "Replit funciona mejor cuando quieres aprender, probar y publicar sin montar entorno local",
        "intro": [
            "La guía antigua trataba Replit sobre todo como un IDE online con IA. Eso se queda corto. La documentación actual de Replit AI habla de convertir ideas en apps listas para producción mediante Agent, con generación de aplicaciones, ayuda contextual, debugging y explicaciones mientras construyes. Para principiantes esto es potente, pero para equipos también cambia el uso: Replit puede ser un laboratorio de prototipos y automatizaciones.",
            "La diferencia frente a un editor local es la fricción. En Replit no empiezas por instalar Node, Python, dependencias, base de datos y despliegue. Empiezas describiendo el resultado. Esa comodidad es útil, pero también puede tapar decisiones importantes: dónde viven los secretos, cómo se versiona el código, qué pasa con el coste y cómo sales de Replit si el proyecto crece.",
        ],
        "checks_title": "Cuándo encaja mejor",
        "checks": [
            "Cursos, bootcamps y aprendizaje guiado donde instalar herramientas sería una barrera.",
            "Prototipos que necesitan preview y despliegue rápido más que arquitectura perfecta.",
            "Bots, dashboards internos y pequeñas automatizaciones con alcance claro.",
            "Sesiones de exploración donde el valor es ver algo funcionando en minutos.",
        ],
        "decision": "Usaría Replit como entorno de arranque y aprendizaje, no como destino automático para cualquier producto complejo. Cuando la app tenga usuarios reales, conviene revisar versionado, backups, permisos y ruta de migración.",
        "faq": [
            ("¿Replit Agent es para gente que no programa?", "Puede ayudar a no programadores, pero los mejores resultados siguen llegando cuando alguien entiende qué está pidiendo y revisa lo generado."),
            ("¿Compite con Bolt?", "Sí en prototipado web, aunque Replit tiene una dimensión más amplia de workspace, aprendizaje, automatizaciones y despliegue continuo."),
        ],
    },
    "amazon-q-developer-ia-aws": {
        "excerpt": "Amazon Q Developer tiene más sentido en equipos que ya viven en AWS: combina asistencia de código, IDE, CLI y conocimiento del ecosistema cloud.",
        "meta": "Guía actualizada de Amazon Q Developer: IDE, CLI, agente, AWS, seguridad, casos de uso y límites frente a Copilot o Claude Code.",
        "sources": [
            ("Qué es Amazon Q Developer", "https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/what-is.html"),
            ("Amazon Q en el IDE", "https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/q-in-IDE.html"),
            ("Amazon Q Developer CLI agent", "https://aws.amazon.com/q/developer/build/"),
        ],
        "related": [
            ("GitHub Copilot: guía completa", "/github-copilot-guia-completa/"),
            ("Claude Code: guía completa", "/claude-code-que-es-guia-completa/"),
            ("GitHub Copilot y privacidad", "/github-copilot-datos-entrenamiento-privacidad/"),
            ("Tabnine: privacidad y autocompletado", "/tabnine-autocompletado-codigo-ia/"),
        ],
        "kicker": "Patrón editorial: AWS primero",
        "title": "Amazon Q Developer no debería evaluarse como un Copilot genérico",
        "intro": [
            "Amazon Q Developer se entiende mejor si lo miras desde AWS hacia fuera. La documentación oficial lo presenta como asistencia de desarrollo en el IDE, pero también como una herramienta conectada al ciclo de construir, documentar, transformar y operar software dentro del ecosistema de Amazon. Si tu equipo usa IAM, Lambda, ECS, CloudFormation, CDK o servicios gestionados de AWS, ese contexto pesa.",
            "Eso no significa que sea la mejor herramienta universal para cualquier repo. Para código frontend genérico quizá prefieras Cursor, Copilot o Claude Code. Pero cuando las preguntas mezclan código y decisiones cloud, Q tiene una ventaja natural: entiende el vocabulario, los servicios y las prácticas de AWS mejor que una herramienta que solo ve archivos locales.",
        ],
        "checks_title": "Preguntas antes de adoptarlo",
        "checks": [
            "¿El equipo ya trabaja con AWS a diario o solo quiere autocompletado de código?",
            "¿Necesitas políticas centralizadas de acceso mediante identidades de empresa?",
            "¿Las tareas habituales mezclan código, documentación y recursos cloud?",
            "¿Tienes normas para revisar comandos sugeridos por un agente con acceso a CLI?",
        ],
        "decision": "Lo usaría en equipos AWS-heavy, especialmente para documentación, explicación de servicios, ayuda en IDE y tareas donde el contexto cloud importa. No lo elegiría solo por autocompletado si el proyecto casi no toca AWS.",
        "faq": [
            ("¿Amazon Q sustituye a CodeWhisperer?", "AWS ha movido el foco hacia Amazon Q Developer; conviene revisar la documentación actual antes de hablar de CodeWhisperer como producto separado."),
            ("¿Es seguro dejarle ejecutar comandos?", "La respuesta práctica es revisar permisos y flujos. Un agente con herramientas debe operar con privilegios mínimos y revisión explícita."),
        ],
    },
    "tabnine-autocompletado-codigo-ia": {
        "excerpt": "Tabnine es un asistente de código con IA centrado en privacidad, control enterprise, autocompletado, chat, agent y despliegues gobernables.",
        "meta": "Qué es Tabnine en 2026: autocompletado de código con IA, Agent, CLI, privacidad, modelos, IDEs compatibles y comparación frente a Copilot y Cursor.",
        "meta_title": "Tabnine: qué es, privacidad y alternativas",
        "sources": [
            ("Tabnine Docs", "https://docs.tabnine.com/"),
            ("Code completions en Tabnine", "https://docs.tabnine.com/main/getting-started/code-completion"),
            ("Tabnine Agent", "https://docs.tabnine.com/main/getting-started/tabnine-agent"),
            ("Tabnine CLI", "https://docs.tabnine.com/main/getting-started/tabnine-cli"),
            ("Tabnine code privacy", "https://www.tabnine.com/code-privacy/"),
            ("Tabnine pricing", "https://www.tabnine.com/pricing/"),
            ("Inline actions sunset", "https://docs.tabnine.com/main/getting-started/inline-actions"),
        ],
        "related": [
            ("GitHub Copilot: guía completa", "/github-copilot-guia-completa/"),
            ("Amazon Q Developer", "/amazon-q-developer-ia-aws/"),
            ("Copilot y privacidad", "/github-copilot-datos-entrenamiento-privacidad/"),
            ("Métricas para agentes de código", "/metricas-agentes-codigo-productividad-coste/"),
        ],
        "kicker": "Guía 2026: privacidad antes que espectáculo",
        "title": "Tabnine: qué es, cómo funciona y cuándo elegirlo frente a Copilot o Cursor",
        "intro": [
            "Tabnine es un asistente de código con IA para autocompletado, chat, tareas agénticas y flujos de desarrollo dentro del IDE. Su posicionamiento no es ser la demo más agresiva del mercado, sino una plataforma de IA para equipos que quieren controlar privacidad, modelos, contexto y despliegue.",
            "Ese matiz importa para la keyword genérica `tabnine`: quien la busca no solo quiere saber si completa código. Quiere entender qué es Tabnine, cómo se diferencia de GitHub Copilot o Cursor, qué IDEs soporta, qué pasa con su código y si tiene sentido para un equipo enterprise.",
            "En 2026, Tabnine ya no se explica solo como autocompletado. La documentación oficial incluye Tabnine Agent para tareas orientadas a objetivos, Tabnine CLI para trabajar desde terminal, controles de modelos para enterprise y una narrativa fuerte de privacidad: cifrado, zero data retention y opciones de despliegue SaaS, VPC, on-premises o air-gapped según plan.",
        ],
        "checks_title": "Dónde Tabnine tiene más sentido",
        "checks": [
            "Equipos regulados que necesitan controlar retención de datos, modelos disponibles y despliegue.",
            "Repos grandes donde el contexto propio y los patrones internos importan más que una demo genérica.",
            "Organizaciones que quieren empezar por completado, chat y agent controlado antes de delegar PRs completos.",
            "Desarrolladores que trabajan en VS Code, JetBrains, Visual Studio o Eclipse y quieren ayuda integrada sin cambiar todo el flujo.",
            "Empresas que necesitan reporting, políticas centralizadas y una historia clara de privacidad para seguridad/compliance.",
        ],
        "decision": "Tabnine es una elección fuerte cuando la prioridad es privacidad, gobernanza y asistencia integrada. Si buscas el agente más autónomo para abrir PRs y modificar repos completos, compararía también Claude Code, Codex, Cursor y Copilot. Si necesitas desplegar IA de código con controles enterprise, Tabnine merece estar en la shortlist.",
        "faq": [
            ("¿Qué es Tabnine?", "Tabnine es un asistente de código con IA que ofrece autocompletado, chat, agent y CLI para ayudar a escribir, explicar, revisar y transformar código dentro del flujo de desarrollo."),
            ("¿Tabnine es gratis?", "Tabnine tiene planes de entrada y planes de pago. Para equipos, el valor diferencial suele estar en funciones enterprise, privacidad, administración, modelos y despliegue controlado."),
            ("¿Tabnine usa mi código para entrenar modelos?", "Tabnine posiciona su producto alrededor de privacidad, zero data retention y control de datos. En entornos enterprise, conviene revisar el plan concreto, los modelos activados y la configuración de despliegue."),
            ("¿Tabnine es mejor que GitHub Copilot?", "Depende del criterio. Copilot suele destacar por integración con GitHub y ecosistema Microsoft. Tabnine compite mejor cuando privacidad, despliegue controlado y gobernanza pesan más que tener el asistente más popular."),
            ("¿Tabnine tiene agente de IA?", "Sí. Tabnine Agent extiende el producto más allá del autocompletado y chat, con un asistente orientado a tareas dentro del entorno del desarrollador."),
            ("¿Qué pasa con Inline Actions?", "La documentación oficial indica que Inline Actions se retirará alrededor de la versión 6.2.0 en mayo de 2026, por lo que conviene mirar Tabnine Agent y CLI para flujos nuevos."),
        ],
    },
    "windsurf-ide-editor-ia": {
        "excerpt": "Windsurf destaca por Cascade: un asistente agéntico integrado en el editor con modos de chat/código, herramientas, checkpoints y conciencia del contexto.",
        "meta": "Guía actualizada de Windsurf: Cascade, reglas, MCP, checkpoints, linter, límites y cuándo usarlo frente a Cursor o Claude Code.",
        "sources": [
            ("Windsurf Cascade", "https://docs.windsurf.com/windsurf/cascade/cascade"),
            ("Windsurf Cascade en español", "https://docs.windsurf.com/es/windsurf/cascade"),
            ("Web and Docs Search en Windsurf", "https://docs.windsurf.com/plugins/cascade/web-search"),
        ],
        "related": [
            ("Cursor AI: guía completa", "/cursor-ai-que-es-guia-completa/"),
            ("Claude Code: guía completa", "/claude-code-que-es-guia-completa/"),
            ("Zed Parallel Agents", "/zed-parallel-agents-editor-ia/"),
        ],
        "kicker": "Patrón editorial: editor agéntico",
        "title": "Windsurf compite por el flujo completo, no solo por el autocompletado",
        "intro": [
            "La pieza central de Windsurf es Cascade. La documentación lo describe como un asistente agéntico con modos Code y Chat, llamadas a herramientas, voz, checkpoints, conciencia en tiempo real e integración con linters. Eso lo coloca en la misma conversación que Cursor: no es un plugin añadido al editor, sino un editor diseñado alrededor de trabajar con IA.",
            "La parte interesante es la conciencia de contexto. Windsurf intenta reducir la necesidad de repetir qué has seleccionado, qué error apareció o qué estabas haciendo. Si funciona bien, ahorra mucha fricción. Si funciona mal, puede crear una falsa sensación de que el asistente “ya sabe” más de lo que realmente sabe. Por eso conviene usar reglas, archivos ignorados y checkpoints desde el primer día.",
        ],
        "checks_title": "Buenas prácticas",
        "checks": [
            "Define reglas del proyecto para estilo, tests, arquitectura y límites de edición.",
            "Usa `.codeiumignore` para excluir secretos, generados y zonas que Cascade no debe tocar.",
            "Crea checkpoints antes de tareas largas o refactors multiarchivo.",
            "Separa preguntas en Chat de cambios reales en Code para mantener control del diff.",
        ],
        "decision": "Windsurf tiene sentido si quieres un IDE IA-first y aceptas adaptar tu flujo al editor. Si tu prioridad es quedarte en terminal o en VS Code puro, Claude Code o Copilot pueden encajar mejor.",
        "faq": [
            ("¿Windsurf es mejor que Cursor?", "No hay una respuesta universal. Cursor tiene mucha adopción y ecosistema; Windsurf compite fuerte en experiencia integrada de Cascade y contexto en tiempo real."),
            ("¿MCP importa aquí?", "Sí, porque permite conectar herramientas externas y ampliar lo que el agente puede consultar o hacer más allá del editor."),
        ],
    },
    "github-copilot-guia-completa": {
        "excerpt": "GitHub Copilot ya no es solo autocompletado: ahora incluye chat, revisión, agentes, memoria, instrucciones y controles de coste que conviene entender.",
        "meta": "Guía actualizada de GitHub Copilot: chat, agente, code review, instrucciones, privacidad, billing y cómo adoptarlo en equipos.",
        "sources": [
            ("Documentación de GitHub Copilot", "https://docs.github.com/en/copilot"),
            ("Features de GitHub Copilot", "https://docs.github.com/en/copilot/get-started/features"),
            ("Copilot coding agent", "https://docs.github.com/en/copilot/using-github-copilot/coding-agent/about-assigning-tasks-to-copilot"),
        ],
        "related": [
            ("Copilot y AI Credits", "/github-copilot-ai-credits-pago-por-uso/"),
            ("Copilot y privacidad", "/github-copilot-datos-entrenamiento-privacidad/"),
            ("Copilot Code Review y Actions", "/copilot-code-review-minutos-github-actions/"),
        ],
        "kicker": "Patrón editorial: plataforma Copilot",
        "title": "Copilot dejó de ser una función y pasó a ser una capa de desarrollo",
        "intro": [
            "La guía antigua de Copilot se quedaba en una visión demasiado simple: autocompletado, chat y poco más. La documentación actual de GitHub muestra una suite mucho más amplia: inline suggestions, Chat, code review, cloud agent, agent mode en IDEs, integraciones, personalización, memoria y controles administrativos. Eso cambia cómo deberías evaluarlo.",
            "En un equipo profesional, Copilot ya no se adopta solo instalando una extensión. Hay que decidir qué funciones se permiten, qué modelos se usan, qué repos pueden recibir agentes, cómo se mide el coste y qué políticas se aplican a privacidad, seguridad y revisión humana. La herramienta se volvió más potente, pero también más administrativa.",
        ],
        "checks_title": "Plan de adopción razonable",
        "checks": [
            "Empieza por inline suggestions y chat, mide uso y calidad antes de activar agentes.",
            "Define instrucciones de repositorio para tests, estilo, arquitectura y comandos seguros.",
            "Separa funciones asistivas de funciones agénticas: no tienen el mismo riesgo.",
            "Revisa AI Credits, premium requests y consumo de Code Review antes de escalar.",
        ],
        "decision": "Copilot es la opción más natural si tu equipo ya vive en GitHub. Pero su valor real depende menos de instalarlo y más de gobernarlo: políticas, contexto, coste, revisión y límites por repositorio.",
        "faq": [
            ("¿Copilot puede abrir PRs solo?", "Sí, con Copilot coding agent o cloud agent puede trabajar en una rama y pedir revisión, bajo las condiciones y permisos definidos por GitHub."),
            ("¿Debo activar todo a la vez?", "No. Las funciones agénticas deben entrar después de tener tests, revisión y normas claras."),
        ],
    },
    "cursor-ai-que-es-guia-completa": {
        "excerpt": "Cursor es potente cuando combinas Agent, Ask, reglas y revisión de diffs; usarlo como chat genérico desaprovecha su ventaja principal.",
        "meta": "Guía actualizada de Cursor AI: Agent, Ask, rules, edición multiarchivo, revisión de diffs, límites y buenas prácticas.",
        "sources": [
            ("Cursor Overview", "https://docs.cursor.com/chat/overview"),
            ("Cursor Modes", "https://docs.cursor.com/es/agent/modes"),
            ("Cursor Rules", "https://docs.cursor.com/en/context"),
        ],
        "related": [
            ("Windsurf IDE", "/windsurf-ide-editor-ia/"),
            ("Claude Code", "/claude-code-que-es-guia-completa/"),
            ("Serena MCP", "/serena-mcp-busqueda-semantica-codigo/"),
        ],
        "kicker": "Patrón editorial: contexto gobernado",
        "title": "Cursor no mejora por hablarle más: mejora cuando le das reglas y fronteras",
        "intro": [
            "Cursor se ha movido hacia un flujo donde Agent puede explorar el codebase, editar varios archivos, ejecutar comandos y corregir errores. Ask queda como modo de lectura y aprendizaje, y las reglas permiten fijar instrucciones persistentes para el proyecto. Esa combinación es la clave: usar el modo adecuado para cada tarea.",
            "El error típico es abrir Agent para cualquier duda. Si solo quieres entender un módulo, Ask reduce riesgo. Si quieres cambiar comportamiento, Agent tiene sentido, pero con alcance claro: archivos permitidos, tests esperados, comandos seguros y criterio de aceptación. Sin esa frontera, Cursor puede producir mucho diff antes de que hayas decidido si el diseño era correcto.",
        ],
        "checks_title": "Cómo pedir mejor",
        "checks": [
            "Usa Ask para entender antes de modificar.",
            "Escribe reglas de proyecto versionadas en `.cursor/rules` o instrucciones compatibles.",
            "Pide cambios pequeños con pruebas concretas, no refactors ambiguos de media aplicación.",
            "Revisa el diff como código de otro desarrollador, no como output automático fiable.",
        ],
        "decision": "Cursor es fuerte para equipos que aceptan convertir instrucciones, reglas y revisión en parte del flujo. Si solo quieres un autocompletado pasivo, puede ser más herramienta de la que necesitas.",
        "faq": [
            ("¿Rules reemplaza documentación?", "No. Las reglas son instrucciones operativas para la IA; la documentación sigue siendo necesaria para humanos y decisiones de producto."),
            ("¿Agent debería ejecutar comandos automáticamente?", "Solo en repos donde tengas tests, entorno controlado y confianza en que los comandos no tienen efectos destructivos."),
        ],
    },
    "claude-code-que-es-guia-completa": {
        "excerpt": "Claude Code brilla cuando quieres trabajar desde terminal con un agente que edita, ejecuta comandos y razona sobre el proyecto completo.",
        "meta": "Guía actualizada de Claude Code: terminal, permisos, MCP, comandos, CI, seguridad, casos de uso y comparación con Cursor.",
        "sources": [
            ("Claude Code overview", "https://docs.anthropic.com/en/docs/claude-code/overview"),
            ("Claude Code en español", "https://docs.anthropic.com/es/docs/claude-code/overview"),
            ("Claude Code settings", "https://docs.anthropic.com/en/docs/claude-code/settings"),
        ],
        "related": [
            ("Cursor AI", "/cursor-ai-que-es-guia-completa/"),
            ("Serena MCP", "/serena-mcp-busqueda-semantica-codigo/"),
            ("RTK y reducción de tokens", "/rtk-proxy-cli-reducir-tokens-ia/"),
        ],
        "kicker": "Patrón editorial: terminal como interfaz",
        "title": "Claude Code es más interesante cuando lo tratas como herramienta Unix",
        "intro": [
            "Anthropic define Claude Code como una herramienta agéntica de coding que vive en la terminal. Esa frase resume bien su ventaja: no exige que cambies de editor, y puede trabajar con archivos, comandos, commits, MCP y automatizaciones. Para desarrolladores acostumbrados a terminal, eso encaja mejor que una interfaz visual cerrada.",
            "La potencia también exige disciplina. Un agente que puede editar y ejecutar comandos necesita permisos claros, instrucciones de proyecto y tareas bien acotadas. La diferencia entre “arregla esto” y “añade un test, localiza la función responsable y toca solo el módulo de billing” es enorme. Claude Code suele rendir mejor cuando el encargo parece un ticket de ingeniería, no una frase improvisada.",
        ],
        "checks_title": "Dónde lo usaría",
        "checks": [
            "Depurar fallos con logs, tests y comandos reproducibles.",
            "Refactors pequeños o medianos con una frontera de archivos clara.",
            "Automatizar tareas repetitivas como changelogs, migraciones mecánicas o limpieza de lint.",
            "Conectar contexto externo mediante MCP cuando el repo por sí solo no basta.",
        ],
        "decision": "Claude Code es una muy buena opción si tu flujo natural está en terminal y sabes revisar cambios. No lo usaría para delegar decisiones grandes sin tests ni límites de edición.",
        "faq": [
            ("¿Necesita Node?", "La documentación oficial indica Node.js 18 o superior para instalarlo con npm."),
            ("¿Compite con Cursor?", "Sí, pero desde otra interfaz. Cursor organiza la experiencia dentro del editor; Claude Code la organiza desde terminal y composición con herramientas."),
        ],
    },
}


def source_links_html(items: list[tuple[str, str]]) -> str:
    links = "".join(
        f'<li><a href="{html.escape(url)}" rel="nofollow noopener" target="_blank">{html.escape(label)}</a></li>'
        for label, url in items
    )
    return f'<ul style="margin:0;padding-left:20px;line-height:1.7;">{links}</ul>'


def guide_refresh_html(data: dict) -> str:
    intro = "".join(f"<p>{html.escape(p)}</p>" for p in data["intro"])
    checks = "".join(f"<li>{html.escape(item)}</li>" for item in data["checks"])
    faq = "".join(
        f"<details><summary>{html.escape(question)}</summary><p>{html.escape(answer)}</p></details>"
        for question, answer in data["faq"]
    )
    faq_schema = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": question,
                    "acceptedAnswer": {"@type": "Answer", "text": answer},
                }
                for question, answer in data["faq"]
            ],
        },
        ensure_ascii=False,
    )
    return f"""<section data-devai-refresh="{REFRESH_MARKER}" style="margin:44px 0;font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <script type="application/ld+json">{faq_schema}</script>
  <style>
    [data-devai-refresh="{REFRESH_MARKER}"] p {{ color:#334155; line-height:1.72; font-size:16px; margin:0 0 16px; }}
    [data-devai-refresh="{REFRESH_MARKER}"] h2 {{ color:#0f172a; font-size:30px; line-height:1.18; margin:0 0 18px; }}
    [data-devai-refresh="{REFRESH_MARKER}"] h3 {{ color:#111827; font-size:21px; line-height:1.3; margin:0 0 12px; }}
    [data-devai-refresh="{REFRESH_MARKER}"] li {{ color:#334155; line-height:1.6; margin:0 0 10px; }}
    [data-devai-refresh="{REFRESH_MARKER}"] details {{ border-top:1px solid #e2e8f0; padding:14px 0; }}
    [data-devai-refresh="{REFRESH_MARKER}"] summary {{ cursor:pointer; color:#0f172a; font-weight:750; }}
  </style>
  <p style="font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.06em;color:#0369a1;margin:0 0 10px;">{html.escape(data["kicker"])}</p>
  <h2>{html.escape(data["title"])}</h2>
  {intro}
  <div style="background:#f8fafc;border-left:4px solid #0ea5e9;border-radius:8px;padding:22px 24px;margin:28px 0;">
    <h3>{html.escape(data["checks_title"])}</h3>
    <ul style="margin:0;padding-left:20px;">{checks}</ul>
  </div>
  <div style="background:#fff;border:1px solid #dbeafe;border-radius:10px;padding:22px 24px;margin:28px 0;">
    <h3>Mi criterio práctico</h3>
    <p>{html.escape(data["decision"])}</p>
  </div>
  <h3>Preguntas frecuentes</h3>
  {faq}
  <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:20px;margin:30px 0;">
    <p style="font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.06em;color:#475569;margin:0 0 12px;">Fuentes revisadas</p>
    {source_links_html(data["sources"])}
  </div>
</section>"""


def get_post(client: httpx.Client, admin_api_key: str, slug: str) -> dict | None:
    resp = client.get(
        f"{GHOST_URL}/ghost/api/admin/posts/",
        headers=headers(admin_api_key),
        params={"filter": f"slug:{slug}", "formats": "lexical", "limit": "1"},
    )
    resp.raise_for_status()
    posts = resp.json().get("posts", [])
    return posts[0] if posts else None


def cta_index(children: list[dict]) -> int:
    for index, child in enumerate(children):
        html_value = child.get("html", "") if child.get("type") == "html" else ""
        if "portal/signup" in html_value or "También te puede interesar" in html_value:
            return index
    return len(children)


def refresh_guide(client: httpx.Client, admin_api_key: str, slug: str, data: dict) -> str:
    post = get_post(client, admin_api_key, slug)
    if not post:
        return "missing"

    lexical = json.loads(post["lexical"])
    children = lexical["root"]["children"]
    children = [
        child
        for child in children
        if not (
            child.get("type") == "html"
            and (
                REFRESH_MARKER in child.get("html", "")
                or "También te puede interesar" in child.get("html", "")
            )
        )
    ]
    insert_at = cta_index(children)
    refresh_nodes = [
        html_card(guide_refresh_html(data)),
        related_card(data["related"]),
    ]
    children[insert_at:insert_at] = refresh_nodes
    lexical["root"]["children"] = children

    payload = {
        "lexical": json.dumps(lexical, ensure_ascii=False),
        "custom_excerpt": data["excerpt"],
        "meta_description": data["meta"],
        "updated_at": post["updated_at"],
        "tags": [{"name": "Guías", "slug": "guias"}, {"name": "evergreen", "slug": "evergreen"}],
    }
    if data.get("meta_title"):
        payload["meta_title"] = data["meta_title"]
    resp = client.put(
        f"{GHOST_URL}/ghost/api/admin/posts/{post['id']}/",
        headers=headers(admin_api_key),
        json={"posts": [payload]},
    )
    resp.raise_for_status()
    return "updated"


def fetch_posts(client: httpx.Client, admin_api_key: str, tag: str) -> list[dict]:
    resp = client.get(
        f"{GHOST_URL}/ghost/api/admin/posts/",
        headers=headers(admin_api_key),
        params={
            "filter": f"tag:{tag}",
            "fields": "title,slug,published_at,custom_excerpt,url",
            "order": "published_at desc",
            "limit": "all",
        },
    )
    resp.raise_for_status()
    return resp.json().get("posts", [])


def archive_list_html(title: str, posts: list[dict]) -> str:
    cards = []
    for post in posts:
        date = (post.get("published_at") or "")[:10]
        excerpt = post.get("custom_excerpt") or ""
        cards.append(
            f"""<a href="/{html.escape(post["slug"])}/" style="display:block;text-decoration:none;color:inherit;border-bottom:1px solid #e5e7eb;padding:18px 0;">
  <p style="font-size:12px;font-weight:700;color:#64748b;margin:0 0 6px;">{html.escape(date)}</p>
  <h3 style="font-size:21px;line-height:1.28;margin:0 0 8px;color:#0f172a;">{html.escape(post["title"])}</h3>
  <p style="font-size:15px;line-height:1.6;color:#475569;margin:0;">{html.escape(excerpt)}</p>
</a>"""
        )
    return f"""<section style="margin:42px 0;">
  <h2 style="font-size:30px;line-height:1.2;margin:0 0 10px;color:#0f172a;">{html.escape(title)}</h2>
  {''.join(cards)}
</section>"""


def archive_page_html(newsletters: list[dict], guides: list[dict]) -> str:
    return f"""<div style="font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:860px;margin:0 auto;">
  <p style="font-size:18px;line-height:1.65;color:#334155;margin:0 0 24px;">Aquí tienes el archivo público de DevAI Semanal: ediciones completas de la newsletter y guías evergreen sobre herramientas de IA para desarrolladores.</p>
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin:28px 0 38px;">
    <a href="#newsletters" style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:10px;padding:18px;text-decoration:none;color:#0c4a6e;font-weight:750;">Ver newsletters</a>
    <a href="#guias" style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:18px;text-decoration:none;color:#0f172a;font-weight:750;">Ver guías evergreen</a>
  </div>
  <div id="newsletters">{archive_list_html("Newsletters", newsletters)}</div>
  <div id="guias">{archive_list_html("Guías evergreen", guides)}</div>
</div>"""


def get_page(client: httpx.Client, admin_api_key: str, slug: str) -> dict | None:
    resp = client.get(
        f"{GHOST_URL}/ghost/api/admin/pages/",
        headers=headers(admin_api_key),
        params={"filter": f"slug:{slug}", "formats": "lexical", "limit": "1"},
    )
    resp.raise_for_status()
    pages = resp.json().get("pages", [])
    return pages[0] if pages else None


def upsert_archive_page(client: httpx.Client, admin_api_key: str) -> str:
    newsletters = fetch_posts(client, admin_api_key, "newsletter")
    guides = fetch_posts(client, admin_api_key, "guias")
    nodes = [
        paragraph("Archivo de DevAI Semanal"),
        html_card(archive_page_html(newsletters, guides)),
    ]
    payload = {
        "title": "Archivo",
        "slug": "archivo",
        "status": "published",
        "visibility": "public",
        "custom_excerpt": "Archivo público con todas las newsletters y guías evergreen de DevAI Semanal.",
        "meta_title": "Archivo de DevAI Semanal - newsletters y guías de IA para devs",
        "meta_description": "Consulta las newsletters publicadas y las guías evergreen de DevAI Semanal sobre herramientas de IA para desarrolladores.",
        "lexical": build_lexical(nodes),
    }
    page = get_page(client, admin_api_key, "archivo")
    if page:
        payload["updated_at"] = page["updated_at"]
        resp = client.put(
            f"{GHOST_URL}/ghost/api/admin/pages/{page['id']}/",
            headers=headers(admin_api_key),
            json={"pages": [payload]},
        )
        action = "updated"
    else:
        resp = client.post(
            f"{GHOST_URL}/ghost/api/admin/pages/",
            headers=headers(admin_api_key),
            json={"pages": [payload]},
        )
        action = "created"
    resp.raise_for_status()
    return f"{action}: {len(newsletters)} newsletters, {len(guides)} guides"


def main() -> None:
    load_dotenv(ROOT / ".env")
    admin_api_key = os.getenv("GHOST_ADMIN_API_KEY", "").strip()
    if not admin_api_key:
        raise SystemExit("GHOST_ADMIN_API_KEY is required")

    with httpx.Client(timeout=30) as client:
        for slug, data in GUIDE_REFRESHES.items():
            print(f"{refresh_guide(client, admin_api_key, slug, data)}: {slug}")
            time.sleep(1)
        print(upsert_archive_page(client, admin_api_key))


if __name__ == "__main__":
    main()
