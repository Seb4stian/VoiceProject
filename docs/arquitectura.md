# Diseño Arquitectónico del Sistema — VoiceProject

## Tabla de contenidos

1. [Visión general](#1-visión-general)
2. [Diagrama de arquitectura](#2-diagrama-de-arquitectura)
3. [Tecnologías y dependencias externas](#3-tecnologías-y-dependencias-externas)
4. [Estructura de directorios](#4-estructura-de-directorios)
5. [Componentes del sistema](#5-componentes-del-sistema)
   - [Punto de entrada — `app.py`](#51-punto-de-entrada--apppy)
   - [Módulo compartido — `shared.py`](#52-módulo-compartido--sharedpy)
   - [Clonación de voz — `voice.py`](#53-clonación-de-voz--voicepy)
   - [Blueprints de rutas — `routes/`](#54-blueprints-de-rutas--routes)
   - [Plantillas HTML — `templates/`](#55-plantillas-html--templates)
   - [Prompts de IA — `prompts/`](#56-prompts-de-ia--prompts)
   - [Grabaciones — `recordings/`](#57-grabaciones--recordings)
   - [Configuración — `config.json`](#58-configuración--configjson)
6. [Flujos de datos principales](#6-flujos-de-datos-principales)
   - [Flujo de grabación de voz](#61-flujo-de-grabación-de-voz)
   - [Flujo de Text-to-Speech (TTS)](#62-flujo-de-text-to-speech-tts)
   - [Flujo de Speech-to-Text (STT)](#63-flujo-de-speech-to-text-stt)
   - [Flujo de análisis de sentimientos](#64-flujo-de-análisis-de-sentimientos)
   - [Flujo del chat de psicología](#65-flujo-del-chat-de-psicología)
   - [Flujo del chat de voz](#66-flujo-del-chat-de-voz)
7. [Patrones de diseño aplicados](#7-patrones-de-diseño-aplicados)
8. [Seguridad](#8-seguridad)
9. [Decisiones de diseño destacadas](#9-decisiones-de-diseño-destacadas)

---

## 1. Visión general

VoiceProject es una aplicación web monolítica construida con el micro-framework **Flask** de Python. Su propósito principal es ofrecer un conjunto integrado de herramientas de procesamiento de voz e inteligencia artificial orientadas al bienestar emocional de adultos mayores.

La aplicación actúa como una **capa de orquestación** entre el navegador web del usuario y dos proveedores externos de IA:

- **ElevenLabs** — para síntesis de voz (TTS) y transcripción de voz (STT), incluyendo clonación de voz a partir de grabaciones del usuario.
- **OpenAI** — para conversación psicológica y análisis de sentimientos mediante modelos de lenguaje grande (LLM).

El servidor no almacena estado de sesión entre peticiones HTTP (es **sin estado**). El historial de conversación se gestiona completamente en el navegador del cliente y se envía con cada petición al chat.

---

## 2. Diagrama de arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                        NAVEGADOR                            │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌──────────┐  │
│  │ index.   │  │  tts /   │  │ sentiment │  │  chat /  │  │
│  │  html    │  │  stt .   │  │   .html   │  │ voice_   │  │
│  │  (/)     │  │  html    │  │(/sentiment│  │  chat    │  │
│  └────┬─────┘  └────┬─────┘  └─────┬─────┘  └────┬─────┘  │
│       │             │              │              │        │
│       └─────────────┴──────────────┴──────────────┘        │
│                          HTTP / JSON / FormData             │
└────────────────────────────┬────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   FLASK SERVER  │
                    │   (app.py)      │
                    │                 │
                    │  ┌───────────┐  │
                    │  │  shared.py│  │  ← Configuración, prompts,
                    │  │  voice.py │  │    helpers, caché de voz
                    │  └───────────┘  │
                    │                 │
                    │  ┌───────────────────────────────────┐  │
                    │  │           routes/                 │  │
                    │  │  ┌──────────┐  ┌──────────────┐  │  │
                    │  │  │recorder  │  │     stt      │  │  │
                    │  │  │   .py    │  │     .py      │  │  │
                    │  │  └──────────┘  └──────────────┘  │  │
                    │  │  ┌──────────┐  ┌──────────────┐  │  │
                    │  │  │   tts    │  │  sentiment   │  │  │
                    │  │  │   .py    │  │     .py      │  │  │
                    │  │  └──────────┘  └──────────────┘  │  │
                    │  │  ┌──────────┐  ┌──────────────┐  │  │
                    │  │  │  chat    │  │ voice_chat   │  │  │
                    │  │  │   .py    │  │     .py      │  │  │
                    │  │  └──────────┘  └──────────────┘  │  │
                    │  └───────────────────────────────────┘  │
                    │                 │
                    │  ┌───────────┐  │
                    │  │recordings/│  │  ← Archivos de audio
                    │  │  (disco)  │  │    guardados localmente
                    │  └───────────┘  │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
   ┌──────────▼──────────┐      ┌───────────▼───────────┐
   │     ELEVENLABS API  │      │      OPENAI API        │
   │                     │      │                        │
   │  • TTS (síntesis)   │      │  • Chat (LLM)          │
   │  • STT (transcr.)   │      │  • Análisis sentiment. │
   │  • IVC (clonación)  │      │                        │
   └─────────────────────┘      └────────────────────────┘
```

---

## 3. Tecnologías y dependencias externas

### Servidor

| Tecnología | Rol |
|------------|-----|
| **Python 3.11+** | Lenguaje de programación principal. |
| **Flask 3.x** | Micro-framework web. Gestiona el enrutamiento HTTP, la renderización de plantillas y el ciclo de vida de la aplicación. |
| **python-dotenv** | Carga variables de entorno desde un archivo `.env` al iniciar la aplicación. |

### APIs de terceros

| Servicio | SDK Python | Funcionalidades usadas |
|----------|-----------|----------------------|
| **ElevenLabs** | `elevenlabs >= 1.0.0` | `speech_to_text.convert` (STT), `text_to_speech.convert` (TTS), `voices.ivc.create` (clonación de voz). |
| **OpenAI** | `openai >= 1.0.0` | `chat.completions.create` (chat LLM y análisis de sentimientos). |

### Frontend

La interfaz de usuario está construida con tecnologías web estándar sin ningún framework de frontend:

| Tecnología | Uso |
|------------|-----|
| **HTML5** | Estructura de las páginas, renderizada por Jinja2. |
| **CSS3** | Estilos visuales embebidos en cada plantilla (sin CSS externo). |
| **JavaScript (Vanilla ES2022+)** | Lógica de grabación (`MediaRecorder API`), llamadas a la API (`fetch`), manipulación del DOM. |
| **MediaRecorder API** | Grabación de audio directamente en el navegador. |
| **Web Audio API** | Reproducción de audio generado por el TTS. |

---

## 4. Estructura de directorios

```
VoiceProject/
│
├── app.py               # Punto de entrada: crea la app Flask y registra blueprints.
├── shared.py            # Configuración centralizada, prompts, helpers reutilizables.
├── voice.py             # Clonación de voz con ElevenLabs (caché en memoria).
├── config.json          # Parámetros configurables (modelo OpenAI, idioma por defecto).
├── requirements.txt     # Dependencias Python.
│
├── routes/              # Blueprints Flask (un archivo por módulo funcional).
│   ├── __init__.py
│   ├── recorder.py      # Subida, listado y servicio de grabaciones.
│   ├── stt.py           # Speech-to-Text.
│   ├── tts.py           # Text-to-Speech.
│   ├── sentiment.py     # Análisis de sentimientos.
│   ├── chat.py          # Chat de psicología (texto).
│   └── voice_chat.py    # Chat de psicología (voz).
│
├── templates/           # Plantillas HTML (Jinja2, una por página).
│   ├── index.html       # Grabadora de voz.
│   ├── stt.html         # Speech-to-Text.
│   ├── tts.html         # Text-to-Speech.
│   ├── sentiment.html   # Análisis de sentimientos.
│   ├── chat.html        # Chat de psicología.
│   └── voice_chat.html  # Chat de voz.
│
├── prompts/             # Textos de instrucción (system prompts) para los LLM.
│   ├── chat_psychologist_system.txt  # Rol del psicólogo de IA.
│   ├── chat_sentiment.txt            # Instrucción de análisis para mensajes del chat.
│   ├── chat_summary.txt              # Instrucción para generar el informe psicológico.
│   ├── sentiment_system.txt          # System prompt para análisis de sentimiento.
│   └── sentiment_user.txt            # Prefijo para el texto a analizar.
│
└── recordings/          # Directorio de grabaciones de audio (creado automáticamente).
    └── .gitkeep
```

---

## 5. Componentes del sistema

### 5.1 Punto de entrada — `app.py`

`app.py` implementa el patrón **Application Factory**: la función `create_app()` instancia Flask, importa y registra los seis blueprints de rutas, y devuelve la aplicación lista para ser ejecutada.

El bloque `if __name__ == "__main__"` permite ejecutar el servidor directamente con `python app.py`. Delega la configuración del modo de depuración a la variable de entorno `FLASK_DEBUG`.

**Responsabilidades:**
- Construir y configurar la instancia Flask.
- Registrar todos los blueprints.
- Arrancar el servidor de desarrollo.

---

### 5.2 Módulo compartido — `shared.py`

`shared.py` es el **núcleo de configuración** de la aplicación. Se carga una única vez al importarse y pone a disposición de todos los módulos:

- **Rutas del sistema de archivos:** `BASE_DIR`, `RECORDINGS_DIR`.
- **Configuración:** Lee `config.json` y expone el diccionario `CONFIG`.
- **Prompts de IA:** Carga los archivos `.txt` de la carpeta `prompts/` y los expone como constantes de cadena de texto.
- **Mapa de idiomas:** Diccionario `LANGUAGE_NAMES` que convierte códigos ISO (p.ej. `"es"`) a nombres completos (`"Spanish"`).
- **Funciones helper:**
  - `safe_filename(name)` — Previene ataques de directory traversal al normalizar nombres de archivo.
  - `allowed_file(filename)` — Valida que la extensión del archivo sea permitida.
  - `get_recording_files()` — Retorna las rutas absolutas de todas las grabaciones, ordenadas de la más nueva a la más antigua.
  - `compute_sentiment_label(score)` — Convierte una puntuación numérica en una etiqueta textual (`"Good"`, `"Neutral"`, `"Bad"`).
  - `get_default_language_name()` — Resuelve el nombre del idioma por defecto a partir de la configuración.

---

### 5.3 Clonación de voz — `voice.py`

`voice.py` encapsula la lógica de clonación de voz mediante el servicio **Instant Voice Cloning (IVC)** de ElevenLabs.

**Mecanismo de caché:**

El módulo mantiene dos variables globales en memoria:
- `_cloned_voice_id` — El identificador de la voz clonada actualmente activa.
- `_cloned_files_hash` — Un hash calculado a partir de los nombres y tamaños de todos los archivos de grabación disponibles.

La función `get_or_create_voice(client)` sigue este proceso:

1. Obtiene la lista de grabaciones disponibles.
2. Calcula el hash del conjunto actual de grabaciones.
3. Si existe un `voice_id` en caché y el hash coincide con el actual, **devuelve el ID en caché** sin realizar ninguna llamada a la API (optimización).
4. Si no hay caché o el conjunto de grabaciones ha cambiado, **crea una nueva voz clonada** con ElevenLabs y actualiza la caché.

Esta estrategia garantiza que la clonación de voz solo se realiza cuando es estrictamente necesario, reduciendo la latencia y el consumo de la API.

---

### 5.4 Blueprints de rutas — `routes/`

Cada archivo en `routes/` define un Flask Blueprint, agrupando lógicamente las rutas de un módulo funcional. Los blueprints se registran en `app.py` con sus prefijos de URL correspondientes:

| Blueprint       | Prefijo URL   | Archivo          |
|-----------------|---------------|------------------|
| `recorder`      | `/`           | `recorder.py`    |
| `stt`           | `/stt`        | `stt.py`         |
| `tts`           | `/tts`        | `tts.py`         |
| `sentiment`     | `/sentiment`  | `sentiment.py`   |
| `chat`          | `/chat`       | `chat.py`        |
| `voice_chat`    | `/voice-chat` | `voice_chat.py`  |

Cada blueprint sigue el mismo patrón:
1. Una ruta `GET /` que renderiza la plantilla HTML correspondiente.
2. Una o más rutas `POST` que implementan la lógica de negocio y retornan JSON.

---

### 5.5 Plantillas HTML — `templates/`

Cada página de la aplicación tiene su propia plantilla HTML en la carpeta `templates/`. Las plantillas usan el motor de plantillas **Jinja2** (integrado en Flask), aunque en la implementación actual no hacen uso de variables de contexto desde el servidor; toda la interactividad se implementa mediante **JavaScript en el lado del cliente**.

Todas las páginas comparten un diseño visual consistente basado en una paleta de colores suave (`#f0f4f8` de fondo, `#fff` para tarjetas), tipografía `Segoe UI`, y estilos CSS embebidos (sin hojas de estilo externas).

---

### 5.6 Prompts de IA — `prompts/`

Los prompts son archivos de texto plano que contienen las instrucciones que se envían a los modelos de lenguaje de OpenAI. Separarlos del código Python permite modificarlos sin necesidad de cambiar el código fuente.

| Archivo | Uso |
|---------|-----|
| `sentiment_system.txt` | System prompt para el análisis de sentimientos independiente. Instruye al modelo a responder solo con JSON válido. |
| `sentiment_user.txt` | Prefijo añadido antes del texto del usuario en las peticiones de análisis de sentimiento. |
| `chat_psychologist_system.txt` | Define la personalidad, el rol y las instrucciones de comportamiento del psicólogo de IA. Incluye instrucciones de idioma (responder siempre en el idioma del usuario). |
| `chat_sentiment.txt` | Instrucción para analizar el sentimiento de un mensaje individual dentro del contexto del chat. |
| `chat_summary.txt` | Instrucción para generar el informe psicológico estructurado en JSON al final de una sesión. |

---

### 5.7 Grabaciones — `recordings/`

La carpeta `recordings/` es el almacenamiento persistente de la aplicación. Es el único estado que persiste entre reinicios del servidor.

- Cada grabación se guarda con un nombre único generado mediante `uuid.uuid4().hex`, eliminando la posibilidad de colisiones.
- El directorio se crea automáticamente al iniciar la aplicación (si no existe) en `shared.py`.
- Los archivos de grabación son la única entrada del proceso de clonación de voz.

---

### 5.8 Configuración — `config.json`

El archivo `config.json` externaliza los parámetros que con mayor probabilidad se desean cambiar sin tocar el código:

- **`openai_model`:** Permite actualizar a un modelo más reciente o cambiar a uno de mayor capacidad sin modificar ningún archivo Python.
- **`default_language`:** Determina el idioma del saludo inicial del psicólogo y del informe psicológico generado al final de la sesión.

---

## 6. Flujos de datos principales

### 6.1 Flujo de grabación de voz

```
Navegador
  │
  ├─1─▶ [MediaRecorder API] Captura audio del micrófono
  │
  ├─2─▶ [Vista previa local] El usuario escucha la grabación
  │
  └─3─▶ POST /upload (FormData: audio=<blob>)
           │
           └──▶ Flask guarda el archivo en recordings/<uuid>.webm
                └──▶ Responde: {"filename": "..."}
```

---

### 6.2 Flujo de Text-to-Speech (TTS)

```
Navegador
  │
  └─1─▶ POST /tts/speak (JSON: {text, language})
           │
           ├─2─▶ voice.get_or_create_voice(client)
           │        ├─[Caché válida]──▶ Retorna voice_id en caché
           │        └─[Sin caché]────▶ ElevenLabs IVC API
           │                              └──▶ Retorna nuevo voice_id
           │
           ├─3─▶ ElevenLabs TTS API (eleven_multilingual_v2)
           │        └──▶ Retorna stream de audio MP3
           │
           └─4─▶ Responde con archivo MP3 (audio/mpeg)
                    │
                    └──▶ Navegador reproduce el audio
```

---

### 6.3 Flujo de Speech-to-Text (STT)

```
Navegador
  │
  ├─1─▶ [MediaRecorder API] Captura audio del micrófono
  │
  └─2─▶ POST /stt/transcribe (FormData: audio=<blob>, language=<code>)
           │
           └─3─▶ ElevenLabs STT API (scribe_v1)
                    └──▶ Retorna texto transcrito
                           │
                           └──▶ Responde: {"text": "..."}
                                    │
                                    └──▶ Navegador muestra la transcripción
```

---

### 6.4 Flujo de análisis de sentimientos

```
Navegador
  │
  └─1─▶ POST /sentiment/analyze (JSON: {text})
           │
           └─2─▶ OpenAI Chat Completions API
                    ├─ System: sentiment_system.txt
                    └─ User:   sentiment_user.txt + <texto>
                         │
                         └──▶ Retorna JSON: {"score": <float>}
                                  │
                                  ├─3─▶ compute_sentiment_label(score)
                                  │
                                  └──▶ Responde: {"score": 0.85, "label": "Good"}
```

---

### 6.5 Flujo del chat de psicología

```
INICIO DE SESIÓN:
Navegador ──▶ POST /chat/start
                └──▶ OpenAI (system: psicólogo, user: "Greet in <lang>")
                         └──▶ {"reply": "¡Buenos días!..."}

MENSAJE DEL USUARIO:
Navegador ──▶ POST /chat/message (JSON: {message, history})
                ├──▶ OpenAI (system: psicólogo + history + mensaje)
                │        └──▶ reply del psicólogo
                │
                └──▶ OpenAI (system: sentiment + mensaje del usuario)
                         └──▶ {"score": ..., "label": ...}
                                  │
                                  └──▶ {"reply": "...", "sentiment": {...}}

FIN DE SESIÓN:
Navegador ──▶ POST /chat/summary (JSON: {history})
                └──▶ OpenAI (system: psicólogo clínico + transcript)
                         └──▶ JSON con informe completo
```

---

### 6.6 Flujo del chat de voz

El chat de voz orquesta tres flujos en secuencia para cada turno del usuario:

```
INICIO:
Navegador ──▶ POST /chat/start ──▶ {reply}
                └──▶ POST /voice-chat/speak ({text: reply})
                         └──▶ ElevenLabs TTS ──▶ MP3
                                  └──▶ Reproducción en navegador

TURNO DEL USUARIO:
  1. [MediaRecorder] Graba audio

  2. POST /voice-chat/transcribe (audio)
        └──▶ ElevenLabs STT ──▶ {text: "mensaje del usuario"}

  3. POST /chat/message ({message, history})
        └──▶ OpenAI ──▶ {reply, sentiment}

  4. POST /voice-chat/speak ({text: reply})
        └──▶ ElevenLabs TTS ──▶ MP3
                 └──▶ Reproducción en navegador

FIN: igual que el chat de texto (/chat/summary)
```

---

## 7. Patrones de diseño aplicados

### Application Factory
`app.py` expone `create_app()` en lugar de crear la instancia de Flask a nivel de módulo. Esto facilita la configuración para diferentes entornos (desarrollo, pruebas, producción) sin modificar el código.

### Blueprint (Modularidad)
Cada funcionalidad se encapsula en un Blueprint de Flask independiente. Esto mantiene el código organizado y permite añadir, modificar o eliminar un módulo sin afectar a los demás.

### Módulo de configuración centralizado (Singleton de facto)
`shared.py` actúa como un módulo de configuración global. Python garantiza que un módulo solo se importa e inicializa una vez, por lo que todas las referencias a `shared.CONFIG`, `shared.SENTIMENT_SYSTEM_PROMPT`, etc., apuntan a los mismos objetos en memoria.

### Caché en memoria (Memoización)
`voice.py` implementa una forma de memoización: la voz clonada se calcula una vez y se reutiliza mientras el conjunto de grabaciones no cambie. El hash del conjunto de archivos actúa como clave de caché, garantizando la invalidación automática.

### Estado en el cliente (Stateless Server)
El servidor no mantiene sesiones ni historial de conversación. El cliente (navegador) es responsable de almacenar el historial y enviarlo completo en cada petición. Esto simplifica el servidor y lo hace horizontalmente escalable.

### Separación de prompts del código
Los prompts de IA se almacenan como archivos de texto independientes en la carpeta `prompts/`. Esto separa el contenido (las instrucciones al modelo) del código (la lógica de la aplicación), facilitando su mantenimiento y ajuste sin necesidad de modificar Python.

---

## 8. Seguridad

### Prevención de directory traversal
La función `safe_filename()` en `shared.py` aplica `os.path.basename()` a cualquier nombre de archivo recibido en parámetros de ruta. Esto elimina componentes de ruta como `../` que podrían usarse para acceder a archivos fuera del directorio `recordings/`.

### Validación de extensiones de archivo
`allowed_file()` comprueba que la extensión del archivo subido pertenece a la lista de extensiones permitidas (`webm`, `ogg`, `wav`, `mp4`). Los archivos con extensiones no permitidas se rechazan o se fuerza la extensión `webm` por defecto.

### Claves de API en variables de entorno
Las claves de API de OpenAI y ElevenLabs nunca se codifican en el código fuente. Se leen exclusivamente de variables de entorno, y el `.gitignore` excluye el archivo `.env` del control de versiones.

### Nombres de archivo únicos
Las grabaciones subidas se guardan con nombres generados por `uuid.uuid4().hex`, evitando colisiones y previniendo que un usuario pueda sobrescribir o predecir el nombre de un archivo existente.

---

## 9. Decisiones de diseño destacadas

### Sin base de datos
La aplicación prescinde deliberadamente de una base de datos. Las grabaciones de audio son el único estado persistente y se almacenan directamente en el sistema de archivos. Esto simplifica enormemente el despliegue y el mantenimiento para el caso de uso objetivo.

### Sin framework de frontend
Toda la interfaz de usuario está construida con JavaScript Vanilla, HTML y CSS sin dependencias externas. Esto elimina un paso de compilación (build step), simplifica la depuración y reduce la superficie de ataque.

### Clonación de voz perezosa (lazy)
La voz clonada no se crea al arrancar el servidor sino en la primera petición de TTS. Esto evita fallos al inicio si no hay grabaciones disponibles aún, y da al usuario tiempo para grabar su voz antes de usar el TTS.

### Historial de conversación en el cliente
Mantener el historial de conversación en el navegador en lugar de en el servidor significa que cada sesión de chat es completamente independiente y efímera. No se almacena información personal del usuario en el servidor.

### Respuesta en el idioma del usuario
El sistema prompt del psicólogo instruye explícitamente al modelo a responder siempre en el mismo idioma que el usuario. Esto, combinado con la generación de resúmenes en el idioma de la conversación, hace la aplicación accesible para hablantes de cualquier idioma sin configuración adicional.
