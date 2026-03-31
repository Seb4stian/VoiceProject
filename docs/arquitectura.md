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
   - [Base de datos — `db.py`](#54-base-de-datos--dbpy)
   - [Consultas SQL — `sql/`](#55-consultas-sql--sql)
   - [Blueprints de rutas — `routes/`](#56-blueprints-de-rutas--routes)
   - [Plantillas HTML — `templates/`](#57-plantillas-html--templates)
   - [Hojas de estilo — `static/css/`](#58-hojas-de-estilo--staticcss)
   - [Prompts de IA — `prompts/`](#59-prompts-de-ia--prompts)
   - [Grabaciones — `recordings/`](#510-grabaciones--recordings)
   - [Configuración — `config.json` y `.env`](#511-configuración--configjson-y-env)
6. [Base de datos — PostgreSQL](#6-base-de-datos--postgresql)
   - [Instalación de PostgreSQL](#61-instalación-de-postgresql)
   - [Creación de la base de datos](#62-creación-de-la-base-de-datos)
   - [Esquema de tablas](#63-esquema-de-tablas)
   - [Diagrama entidad-relación](#64-diagrama-entidad-relación)
7. [Flujos de datos principales](#7-flujos-de-datos-principales)
   - [Flujo de autenticación](#71-flujo-de-autenticación)
   - [Flujo de grabación de voz](#72-flujo-de-grabación-de-voz)
   - [Flujo de Text-to-Speech (TTS)](#73-flujo-de-text-to-speech-tts)
   - [Flujo de Speech-to-Text (STT)](#74-flujo-de-speech-to-text-stt)
   - [Flujo de análisis de sentimientos](#75-flujo-de-análisis-de-sentimientos)
   - [Flujo del chat de psicología](#76-flujo-del-chat-de-psicología)
   - [Flujo del chat de voz](#77-flujo-del-chat-de-voz)
8. [Patrones de diseño aplicados](#8-patrones-de-diseño-aplicados)
9. [Seguridad](#9-seguridad)
10. [Decisiones de diseño destacadas](#10-decisiones-de-diseño-destacadas)

---

## 1. Visión general

VoiceProject es una aplicación web monolítica construida con el micro-framework **Flask** de Python. Su propósito principal es ofrecer un conjunto integrado de herramientas de procesamiento de voz e inteligencia artificial orientadas al bienestar emocional de adultos mayores.

La aplicación actúa como una **capa de orquestación** entre el navegador web del usuario y dos proveedores externos de IA:

- **ElevenLabs** — para síntesis de voz (TTS) y transcripción de voz (STT), incluyendo clonación de voz a partir de grabaciones del usuario.
- **OpenAI** — para conversación psicológica y análisis de sentimientos mediante modelos de lenguaje grande (LLM).

El servidor no almacena estado de sesión entre peticiones HTTP (es **sin estado** a nivel de lógica de negocio). Sin embargo, **persiste las sesiones de chat, los mensajes y los resúmenes psicológicos en una base de datos PostgreSQL**, lo que permite continuidad terapéutica entre sesiones. La autenticación de usuarios se gestiona mediante sesiones de Flask firmadas con una clave secreta.

---

## 2. Diagrama de arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                        NAVEGADOR                            │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌──────────┐  │
│  │ login /  │  │ index.   │  │  chat /   │  │  about   │  │
│  │ register │  │  html    │  │ voice_    │  │  .html   │  │
│  │  .html   │  │  (/)     │  │  chat     │  │          │  │
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
                    │  │  db.py    │  │  ← Conexión PostgreSQL
                    │  └───────────┘  │
                    │                 │
                    │  ┌───────────────────────────────────┐  │
                    │  │           routes/                 │  │
                    │  │  ┌──────────┐  ┌──────────────┐  │  │
                    │  │  │  auth    │  │   recorder   │  │  │
                    │  │  │   .py    │  │     .py      │  │  │
                    │  │  └──────────┘  └──────────────┘  │  │
                    │  │  ┌──────────┐  ┌──────────────┐  │  │
                    │  │  │   stt    │  │     tts      │  │  │
                    │  │  │   .py    │  │     .py      │  │  │
                    │  │  └──────────┘  └──────────────┘  │  │
                    │  │  ┌──────────┐  ┌──────────────┐  │  │
                    │  │  │  chat    │  │ voice_chat   │  │  │
                    │  │  │   .py    │  │     .py      │  │  │
                    │  │  └──────────┘  └──────────────┘  │  │
                    │  │  ┌──────────┐  ┌──────────────┐  │  │
                    │  │  │sentiment │  │    about     │  │  │
                    │  │  │   .py    │  │     .py      │  │  │
                    │  │  └──────────┘  └──────────────┘  │  │
                    │  └───────────────────────────────────┘  │
                    │                 │
                    │  ┌───────────┐  │
                    │  │recordings/│  │  ← Archivos de audio
                    │  │<user_id>/ │  │    por usuario
                    │  └───────────┘  │
                    └───────┬─────────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
┌─────────▼─────────┐ ┌────▼──────────┐ ┌────▼────────────────┐
│  ELEVENLABS API   │ │  OPENAI API   │ │  POSTGRESQL         │
│                   │ │               │ │                     │
│  • TTS (síntesis) │ │ • Chat (LLM)  │ │ • users             │
│  • STT (transcr.) │ │ • Sentiment   │ │ • chat_sessions     │
│  • IVC (clonar)   │ │               │ │ • chat_messages     │
└───────────────────┘ └───────────────┘ └─────────────────────┘
```

---

## 3. Tecnologías y dependencias externas

### Servidor

| Tecnología | Rol |
|------------|-----|
| **Python 3.11+** | Lenguaje de programación principal. |
| **Flask 3.x** | Micro-framework web. Gestiona el enrutamiento HTTP, la renderización de plantillas, sesiones de usuario y el ciclo de vida de la aplicación. |
| **python-dotenv** | Carga variables de entorno desde un archivo `.env` al iniciar la aplicación. |
| **psycopg2-binary** | Driver PostgreSQL para Python. Usado por `db.py` para gestionar la conexión y las consultas a la base de datos. |
| **PostgreSQL 14+** | Base de datos relacional. Almacena usuarios, sesiones de chat, mensajes y resúmenes psicológicos. |

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
| **CSS3** | Estilos visuales en hojas de estilo externas (`static/css/`), una por página. |
| **JavaScript (Vanilla ES2022+)** | Lógica de grabación (`MediaRecorder API`), llamadas a la API (`fetch`), manipulación del DOM. |
| **Chart.js 4.x** (CDN) | Gráfica de línea temporal de sentimientos en las páginas de chat. |
| **MediaRecorder API** | Grabación de audio directamente en el navegador. |
| **Web Audio API** | Reproducción de audio generado por el TTS. |

---

## 4. Estructura de directorios

```
VoiceProject/
│
├── app.py               # Punto de entrada: crea la app Flask, registra blueprints,
│                        #   configura sesiones, login_required y context_processor.
├── shared.py            # Configuración centralizada, prompts, helpers reutilizables.
├── voice.py             # Clonación de voz con ElevenLabs (caché por usuario).
├── db.py                # Conexión PostgreSQL y funciones de consulta.
│                        #   Carga queries con nombre desde sql/*.sql.
├── config.json          # Parámetros configurables (modelo OpenAI, idioma, base de datos).
├── requirements.txt     # Dependencias Python.
│
├── sql/                 # Consultas SQL separadas del código Python.
│   ├── create_tables.sql    # DDL: CREATE TABLE users, chat_sessions, chat_messages.
│   ├── users.sql            # Queries de usuario: crear, buscar, verificar existencia.
│   └── chat.sql             # Queries de chat: sesiones, mensajes, takeaways, timeline.
│
├── routes/              # Blueprints Flask (un archivo por módulo funcional).
│   ├── __init__.py
│   ├── auth.py          # Autenticación: login, registro, logout, login_required.
│   ├── recorder.py      # Subida, listado, eliminación y servicio de grabaciones (por usuario).
│   ├── stt.py           # Speech-to-Text.
│   ├── tts.py           # Text-to-Speech.
│   ├── sentiment.py     # Análisis de sentimientos.
│   ├── chat.py          # Chat de psicología (texto). Persistencia en BD, takeaways, timeline.
│   ├── voice_chat.py    # Chat de psicología (voz).
│   └── about.py         # Página «Acerca de» con los contribuyentes.
│
├── static/              # Archivos estáticos servidos por Flask.
│   └── css/             # Hojas de estilo externas (una por página).
│       ├── auth.css         # Estilos de login y registro.
│       ├── recorder.css     # Estilos de la grabadora de voz.
│       ├── stt.css          # Estilos de Speech-to-Text.
│       ├── tts.css          # Estilos de Text-to-Speech.
│       ├── sentiment.css    # Estilos de análisis de sentimientos.
│       ├── chat.css         # Estilos del chat de psicología + timeline.
│       ├── voice_chat.css   # Estilos del chat de voz + timeline.
│       └── about.css        # Estilos de la página «Acerca de».
│
├── templates/           # Plantillas HTML (Jinja2, una por página).
│   ├── login.html       # Inicio de sesión.
│   ├── register.html    # Registro de usuario.
│   ├── index.html       # Grabadora de voz.
│   ├── stt.html         # Speech-to-Text.
│   ├── tts.html         # Text-to-Speech.
│   ├── sentiment.html   # Análisis de sentimientos.
│   ├── chat.html        # Chat de psicología + gráfica de sentimientos.
│   ├── voice_chat.html  # Chat de voz + gráfica de sentimientos.
│   └── about.html       # Página «Acerca de».
│
├── prompts/             # Textos de instrucción (system prompts) para los LLM.
│   ├── chat_psychologist_system.txt  # Rol del psicólogo de IA.
│   ├── chat_sentiment.txt            # Instrucción de análisis para mensajes del chat.
│   ├── chat_summary.txt              # Instrucción para generar el informe psicológico.
│   ├── chat_takeaway.txt             # Instrucción para generar takeaways de continuidad.
│   ├── sentiment_system.txt          # System prompt para análisis de sentimiento.
│   └── sentiment_user.txt            # Prefijo para el texto a analizar.
│
└── recordings/          # Directorio de grabaciones de audio (por usuario).
    ├── 1/               # Grabaciones del usuario con id=1.
    ├── 2/               # Grabaciones del usuario con id=2.
    └── ...
```

---

## 5. Componentes del sistema

### 5.1 Punto de entrada — `app.py`

`app.py` implementa el patrón **Application Factory**: la función `create_app()` instancia Flask, importa y registra los ocho blueprints de rutas (incluyendo autenticación), y devuelve la aplicación lista para ser ejecutada.

El bloque `if __name__ == "__main__"` permite ejecutar el servidor directamente con `python app.py`. Delega la configuración del modo de depuración a la variable de entorno `FLASK_DEBUG`.

**Responsabilidades:**
- Construir y configurar la instancia Flask (incluyendo `secret_key` para sesiones).
- Registrar todos los blueprints.
- Ejecutar `init_db()` al inicio para garantizar que las tablas existen.
- `before_request`: Interceptar todas las peticiones y redirigir a `/auth/login` si el usuario no está autenticado (excepto rutas de auth y archivos estáticos).
- `context_processor`: Inyectar `current_user` (nombre de usuario) en todas las plantillas Jinja2.

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
  - `get_user_recordings_dir(user_id)` — Retorna el directorio de grabaciones para un usuario específico (`recordings/<user_id>/`), creándolo si no existe.
  - `get_recording_files(user_id)` — Retorna las rutas absolutas de las grabaciones de un usuario, ordenadas de la más nueva a la más antigua.
  - `compute_sentiment_label(score)` — Convierte una puntuación numérica en una etiqueta textual (`"Good"`, `"Neutral"`, `"Bad"`).
  - `get_default_language_name()` — Resuelve el nombre del idioma por defecto a partir de la configuración.

---

### 5.3 Clonación de voz — `voice.py`

`voice.py` encapsula la lógica de clonación de voz mediante el servicio **Instant Voice Cloning (IVC)** de ElevenLabs.

**Mecanismo de caché:**

El módulo mantiene un diccionario `_voice_cache` que almacena la voz clonada **por usuario**:
- Clave: `user_id` (entero).
- Valor: tupla `(voice_id, files_hash)`.

La función `get_or_create_voice(client, user_id)` sigue este proceso:

1. Obtiene la lista de grabaciones del usuario específico (`recordings/<user_id>/`).
2. Calcula el hash del conjunto actual de grabaciones.
3. Si existe una entrada en caché para este usuario y el hash coincide, **devuelve el ID en caché**.
4. Si no hay caché o el conjunto de grabaciones ha cambiado, **crea una nueva voz clonada** y actualiza la caché.

Esta estrategia garantiza aislamiento entre usuarios y que la clonación solo se realiza cuando es estrictamente necesario.

---

### 5.4 Base de datos — `db.py`

`db.py` es el **módulo de acceso a datos**. Proporciona funciones Python para todas las operaciones con la base de datos PostgreSQL.

**Carga de consultas:** Al importarse, `db.py` lee los archivos `.sql` de la carpeta `sql/` y parsea las consultas con nombre (marcadas con `-- name: <nombre>`). Esto permite que todas las consultas SQL estén externalizadas y sean mantenibles de forma independiente.

**Funciones principales:**

| Función | Descripción |
|---------|-------------|
| `get_connection()` | Crea una nueva conexión PostgreSQL usando los datos de `config.json` y `DB_PASSWORD` de `.env`. |
| `init_db()` | Ejecuta `sql/create_tables.sql` para crear las tablas si no existen. |
| `create_user()` | Inserta un nuevo usuario y devuelve su ID. |
| `get_user_by_username()` | Busca un usuario por nombre de usuario. |
| `username_exists()` / `email_exists()` | Verifican unicidad antes del registro. |
| `create_chat_session()` | Crea una nueva sesión de chat para un usuario. |
| `save_chat_message()` | Guarda un mensaje (usuario o asistente) con su sentimiento. |
| `end_chat_session()` | Marca una sesión como finalizada y guarda el resumen JSON + takeaway. |
| `get_user_takeaways()` | Obtiene los takeaways de sesiones anteriores (para continuidad). |
| `get_session_timeline()` | Obtiene fechas y sentimientos de sesiones completadas (para la gráfica). |

---

### 5.5 Consultas SQL — `sql/`

Todas las consultas SQL están externalizadas en archivos `.sql` dentro de la carpeta `sql/`. Cada consulta se identifica con un comentario `-- name: <nombre>` que `db.py` usa para indexarlas.

| Archivo | Contenido |
|---------|-----------|
| `create_tables.sql` | DDL: `CREATE TABLE IF NOT EXISTS` para `users`, `chat_sessions`, `chat_messages` e índices. Puede ejecutarse directamente con `psql`. |
| `users.sql` | Consultas CRUD de usuarios: crear, buscar por nombre, verificar existencia. |
| `chat.sql` | Consultas de chat: crear sesiones, guardar mensajes, finalizar sesiones, obtener takeaways, obtener timeline de sentimientos. |

---

### 5.6 Blueprints de rutas — `routes/`

Cada archivo en `routes/` define un Flask Blueprint, agrupando lógicamente las rutas de un módulo funcional. Los blueprints se registran en `app.py` con sus prefijos de URL correspondientes:

| Blueprint       | Prefijo URL   | Archivo          |
|-----------------|---------------|------------------|
| `auth`          | `/auth`       | `auth.py`        |
| `recorder`      | `/`           | `recorder.py`    |
| `stt`           | `/stt`        | `stt.py`         |
| `tts`           | `/tts`        | `tts.py`         |
| `sentiment`     | `/sentiment`  | `sentiment.py`   |
| `chat`          | `/chat`       | `chat.py`        |
| `voice_chat`    | `/voice-chat` | `voice_chat.py`  |
| `about`         | `/about`      | `about.py`       |

Cada blueprint sigue el mismo patrón:
1. Una ruta `GET /` que renderiza la plantilla HTML correspondiente.
2. Una o más rutas `POST` que implementan la lógica de negocio y retornan JSON.

---

### 5.7 Plantillas HTML — `templates/`

Cada página de la aplicación tiene su propia plantilla HTML en la carpeta `templates/`. Las plantillas usan el motor de plantillas **Jinja2** (integrado en Flask). Ahora las plantillas utilizan la variable de contexto `current_user` (inyectada por el context_processor de `app.py`) para mostrar el nombre del usuario en la barra de navegación y el enlace de cierre de sesión.

Todas las páginas comparten un diseño visual consistente basado en una paleta de colores suave (`#f0f4f8` de fondo, `#fff` para tarjetas) y tipografía `Segoe UI`. Los estilos CSS se encuentran en hojas de estilo externas dentro de `static/css/` (una por página), enlazadas mediante `<link>` con `url_for('static', ...)` de Jinja2. Esto separa la presentación de la estructura, facilita el mantenimiento y permite al navegador cachear los estilos de forma independiente.

---

### 5.8 Hojas de estilo — `static/css/`

Cada página tiene su propia hoja de estilo CSS en `static/css/`, enlazada desde la plantilla HTML mediante `<link rel="stylesheet" href="{{ url_for('static', filename='css/<nombre>.css') }}">`.

| Archivo | Página |
|---------|--------|
| `auth.css` | Login y registro (`login.html`, `register.html`). |
| `recorder.css` | Grabadora de voz (`index.html`). |
| `tts.css` | Text-to-Speech (`tts.html`). |
| `stt.css` | Speech-to-Text (`stt.html`). |
| `sentiment.css` | Análisis de sentimientos (`sentiment.html`). |
| `chat.css` | Chat de psicología (`chat.html`). |
| `voice_chat.css` | Chat de voz (`voice_chat.html`). |
| `about.css` | Página «Acerca de» (`about.html`). |

Todas las hojas comparten convenciones de diseño: reset universal (`box-sizing: border-box`), tipografía `Segoe UI`, paleta de colores consistente y componentes reutilizables (`.card`, `.controls`, botones, animaciones `@keyframes`). Al ser archivos separados del HTML, el navegador puede cachearlos de forma independiente, mejorando los tiempos de carga en visitas posteriores.

---

### 5.9 Prompts de IA — `prompts/`

Los prompts son archivos de texto plano que contienen las instrucciones que se envían a los modelos de lenguaje de OpenAI. Separarlos del código Python permite modificarlos sin necesidad de cambiar el código fuente.

| Archivo | Uso |
|---------|-----|
| `sentiment_system.txt` | System prompt para el análisis de sentimientos independiente. Instruye al modelo a responder solo con JSON válido. |
| `sentiment_user.txt` | Prefijo añadido antes del texto del usuario en las peticiones de análisis de sentimiento. |
| `chat_psychologist_system.txt` | Define la personalidad, el rol y las instrucciones de comportamiento del psicólogo de IA. Incluye instrucciones de idioma (responder siempre en el idioma del usuario). |
| `chat_sentiment.txt` | Instrucción para analizar el sentimiento de un mensaje individual dentro del contexto del chat. |
| `chat_summary.txt` | Instrucción para generar el informe psicológico estructurado en JSON al final de una sesión. |
| `chat_takeaway.txt` | Instrucción para generar un takeaway condensado (2-3 frases) que capture los puntos clave de la sesión para dar continuidad en sesiones futuras. |

---

### 5.10 Grabaciones — `recordings/`

La carpeta `recordings/` es el almacenamiento persistente de archivos de audio. **Cada usuario tiene su propio subdirectorio** (`recordings/<user_id>/`), lo que garantiza aislamiento total entre usuarios.

- Cada grabación se guarda con un nombre único generado mediante `uuid.uuid4().hex`.
- Los subdirectorios de usuario se crean automáticamente al primer acceso.
- Los archivos de grabación de cada usuario son la única entrada del proceso de clonación de voz para ese usuario.

---

### 5.11 Configuración — `config.json` y `.env`

El archivo `config.json` centraliza los parámetros operativos de la aplicación, incluyendo:

| Clave | Descripción |
|-------|-------------|
| `openai_model` | Modelo de OpenAI a usar (permite cambiar sin tocar código). |
| `default_language` | Idioma por defecto para STT, TTS y el informe psicológico. |
| `languages` | Diccionario de idiomas disponibles con sus modelos de voz. |
| `database.host` | Dirección del servidor PostgreSQL (default: `localhost`). |
| `database.port` | Puerto de PostgreSQL (default: `5432`). |
| `database.name` | Nombre de la base de datos (`VoiceProject`). |
| `database.user` | Usuario de PostgreSQL (`edcastr`). |

> **Nota:** La contraseña de la base de datos (`DB_PASSWORD`) se almacena en el archivo `.env` y **no** en `config.json`, siguiendo las mejores prácticas de seguridad. El archivo `.env` está incluido en `.gitignore`.

Variables de entorno requeridas en `.env`:

| Variable | Descripción |
|----------|-------------|
| `ELEVENLABS_API_KEY` | Clave de API para ElevenLabs (clonación de voz y TTS). |
| `OPENAI_API_KEY` | Clave de API para OpenAI (chat, STT, análisis de sentimiento). |
| `DB_PASSWORD` | Contraseña del usuario de PostgreSQL. |

---

## 6. Base de datos — PostgreSQL

### 6.1 Instalación de PostgreSQL

| Plataforma | Enlace |
|------------|--------|
| **Windows** | [https://www.postgresql.org/download/windows/](https://www.postgresql.org/download/windows/) |
| **macOS** | [https://www.postgresql.org/download/macosx/](https://www.postgresql.org/download/macosx/) o `brew install postgresql` |
| **Linux (Debian/Ubuntu)** | `sudo apt install postgresql postgresql-contrib` |
| **Linux (Fedora/RHEL)** | `sudo dnf install postgresql-server postgresql-contrib` |

Documentación oficial: [https://www.postgresql.org/docs/](https://www.postgresql.org/docs/)

### 6.2 Creación y configuración de la base de datos

Ejecutar los siguientes comandos como superusuario de PostgreSQL (`postgres`):

```sql
-- 1. Crear el usuario de la aplicación
CREATE USER edcastr WITH PASSWORD '12345aB.';

-- 2. Crear la base de datos
CREATE DATABASE "VoiceProject" OWNER edcastr;

-- 3. Conceder permisos en el esquema public
\c "VoiceProject"
GRANT ALL ON SCHEMA public TO edcastr;
```

Luego, ejecutar el DDL para crear las tablas:

```bash
psql -U edcastr -d VoiceProject -f sql/create_tables.sql
```

### 6.3 Esquema de tablas

#### `users`
| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | `SERIAL PRIMARY KEY` | Identificador único auto-incremental. |
| `username` | `VARCHAR(80) UNIQUE NOT NULL` | Nombre de usuario para login. |
| `email` | `VARCHAR(120) UNIQUE NOT NULL` | Correo electrónico del usuario. |
| `password_hash` | `VARCHAR(256) NOT NULL` | Hash de la contraseña (generado con werkzeug). |
| `created_at` | `TIMESTAMP DEFAULT NOW()` | Fecha de registro. |

#### `chat_sessions`
| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | `SERIAL PRIMARY KEY` | Identificador único de la sesión. |
| `user_id` | `INTEGER REFERENCES users(id)` | Usuario propietario de la sesión. |
| `started_at` | `TIMESTAMP DEFAULT NOW()` | Inicio de la sesión. |
| `ended_at` | `TIMESTAMP` | Fin de la sesión (NULL si activa). |
| `summary_json` | `JSONB` | Informe psicológico completo en JSON. |
| `takeaway` | `TEXT` | Resumen condensado para continuidad. |

#### `chat_messages`
| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | `SERIAL PRIMARY KEY` | Identificador único del mensaje. |
| `session_id` | `INTEGER REFERENCES chat_sessions(id)` | Sesión a la que pertenece. |
| `role` | `VARCHAR(20) NOT NULL` | `"user"` o `"assistant"`. |
| `content` | `TEXT NOT NULL` | Contenido del mensaje. |
| `sentiment_score` | `REAL` | Puntuación de sentimiento (solo mensajes del usuario). |
| `sentiment_label` | `VARCHAR(20)` | Etiqueta: `"Good"`, `"Neutral"`, `"Bad"`. |
| `created_at` | `TIMESTAMP DEFAULT NOW()` | Marca temporal del mensaje. |

### 6.4 Diagrama entidad-relación

```
┌──────────────┐       ┌───────────────────┐       ┌──────────────────┐
│    users     │       │   chat_sessions   │       │  chat_messages   │
├──────────────┤       ├───────────────────┤       ├──────────────────┤
│ id (PK)      │──1:N─▶│ id (PK)           │──1:N─▶│ id (PK)          │
│ username     │       │ user_id (FK)      │       │ session_id (FK)  │
│ email        │       │ started_at        │       │ role             │
│ password_hash│       │ ended_at          │       │ content          │
│ created_at   │       │ summary_json      │       │ sentiment_score  │
└──────────────┘       │ takeaway          │       │ sentiment_label  │
                       └───────────────────┘       │ created_at       │
                                                   └──────────────────┘
```

---

## 7. Flujos de datos principales

### 7.1 Flujo de autenticación

```
REGISTRO:
Navegador ──▶ GET /auth/register ──▶ Formulario de registro
  └──▶ POST /auth/register (username, email, password)
         ├─ Valida unicidad (username, email)
         ├─ Hash de contraseña (werkzeug.security)
         ├─ INSERT en tabla users
         └─ Redirige a /auth/login

LOGIN:
Navegador ──▶ GET /auth/login ──▶ Formulario de login
  └──▶ POST /auth/login (username, password)
         ├─ Busca usuario por username
         ├─ Verifica hash de contraseña
         ├─ Establece session['user_id']
         └─ Redirige a /

LOGOUT:
Navegador ──▶ GET /auth/logout
  └──▶ Limpia session, redirige a /auth/login
```

### 7.2 Flujo de grabación de voz

```
Navegador
  │
  ├─1─▶ [MediaRecorder API] Captura audio del micrófono
  │
  ├─2─▶ [Vista previa local] El usuario escucha la grabación
  │
  ├─3─▶ POST /upload (FormData: audio=<blob>)
  │        │
  │        └──▶ Flask guarda el archivo en recordings/<user_id>/<uuid>.webm
  │             └──▶ Responde: {"filename": "..."}
  │
  └─4─▶ DELETE /recordings/<filename>  (opcional, desde botón «Delete»)
           │
           └──▶ Flask elimina el archivo del disco
                └──▶ Responde: {"deleted": "<filename>"}
```

---

### 7.3 Flujo de Text-to-Speech (TTS)

```
Navegador
  │
  └─1─▶ POST /tts/speak (JSON: {text, language})
           │
           ├─2─▶ voice.get_or_create_voice(client, user_id)
           │        ├─[Caché válida para usuario]──▶ Retorna voice_id en caché
           │        └─[Sin caché]─────────────────▶ ElevenLabs IVC API
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

### 7.4 Flujo de Speech-to-Text (STT)

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

### 7.5 Flujo de análisis de sentimientos

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

### 7.6 Flujo del chat de psicología (con persistencia)

```
INICIO DE SESIÓN:
Navegador ──▶ POST /chat/start
                ├──▶ db.create_chat_session(user_id)  →  session_id
                ├──▶ db.get_user_takeaways(user_id)   →  takeaways anteriores
                ├──▶ Construye system_prompt + takeaways inyectados
                ├──▶ OpenAI (system: psicólogo + contexto, user: "Greet in <lang>")
                │        └──▶ reply del psicólogo
                ├──▶ db.save_chat_message(session_id, "assistant", reply)
                └──▶ {"reply": "...", "session_id": <id>}

MENSAJE DEL USUARIO:
Navegador ──▶ POST /chat/message (JSON: {message, history, session_id})
                ├──▶ db.save_chat_message(session_id, "user", message, sentiment)
                ├──▶ OpenAI (system: psicólogo + takeaways + history + mensaje)
                │        └──▶ reply del psicólogo
                ├──▶ db.save_chat_message(session_id, "assistant", reply)
                ├──▶ OpenAI (system: sentiment + mensaje del usuario)
                │        └──▶ {"score": ..., "label": ...}
                └──▶ {"reply": "...", "sentiment": {...}}

FIN DE SESIÓN:
Navegador ──▶ POST /chat/summary (JSON: {history, session_id})
                ├──▶ OpenAI (system: psicólogo clínico + transcript)
                │        └──▶ JSON con informe completo
                ├──▶ OpenAI (takeaway prompt + transcript)
                │        └──▶ takeaway (2-3 frases clave)
                ├──▶ db.end_chat_session(session_id, summary_json, takeaway)
                └──▶ Respuesta con informe JSON
```

---

### 7.7 Flujo del chat de voz

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

## 8. Patrones de diseño aplicados

### Application Factory
`app.py` expone `create_app()` en lugar de crear la instancia de Flask a nivel de módulo. Esto facilita la configuración para diferentes entornos (desarrollo, pruebas, producción) sin modificar el código.

### Blueprint (Modularidad)
Cada funcionalidad se encapsula en un Blueprint de Flask independiente. Esto mantiene el código organizado y permite añadir, modificar o eliminar un módulo sin afectar a los demás.

### Módulo de configuración centralizado (Singleton de facto)
`shared.py` actúa como un módulo de configuración global. Python garantiza que un módulo solo se importa e inicializa una vez, por lo que todas las referencias a `shared.CONFIG`, `shared.SENTIMENT_SYSTEM_PROMPT`, etc., apuntan a los mismos objetos en memoria.

### Caché en memoria por usuario (Memoización)
`voice.py` implementa una forma de memoización por usuario: la voz clonada se calcula una vez por usuario y se reutiliza mientras su conjunto de grabaciones no cambie. El hash de los archivos actúa como clave de caché, garantizando invalidación automática.

### Consultas SQL con nombre (Named Queries)
Las consultas SQL se almacenan en archivos `.sql` en la carpeta `sql/`, cada una marcada con `-- name: <nombre>`. `db.py` las parsea en un diccionario al importarse. Este patrón separa SQL de Python, facilitando la revisión y el mantenimiento de consultas.

### Continuidad terapéutica (Takeaway Injection)
Al iniciar una nueva sesión de chat, el sistema recupera los takeaways de sesiones anteriores del usuario y los inyecta en el system prompt. Esto permite que la IA continúe la conversación sin repetir preguntas introductorias, proporcionando una experiencia terapéutica continua.

### Aislamiento por usuario
Las grabaciones de audio, las sesiones de chat y la caché de voz clonada están separadas por `user_id`. Cada usuario tiene su propio subdirectorio de grabaciones y sus datos de chat son inaccesibles para otros usuarios.

### Separación de prompts del código
Los prompts de IA se almacenan como archivos de texto independientes en la carpeta `prompts/`. Esto separa el contenido (las instrucciones al modelo) del código (la lógica de la aplicación), facilitando su mantenimiento y ajuste sin necesidad de modificar Python.

---

## 9. Seguridad

### Autenticación de usuarios
La aplicación requiere autenticación para acceder a todas las páginas (excepto login y registro). Las contraseñas se almacenan como hashes generados con `werkzeug.security.generate_password_hash()` (PBKDF2 + sal). La verificación se realiza con `check_password_hash()`.

### Sesiones Flask
La identidad del usuario se mantiene en la sesión de Flask (`session['user_id']`), protegida con `app.secret_key`. El hook `before_request` verifica la autenticación en cada petición.

### Prevención de directory traversal
La función `safe_filename()` en `shared.py` aplica `os.path.basename()` a cualquier nombre de archivo recibido en parámetros de ruta. Esto elimina componentes de ruta como `../` que podrían usarse para acceder a archivos fuera del directorio de grabaciones.

### Validación de extensiones de archivo
`allowed_file()` comprueba que la extensión del archivo subido pertenece a la lista de extensiones permitidas (`webm`, `ogg`, `wav`, `mp4`). Los archivos con extensiones no permitidas se rechazan o se fuerza la extensión `webm` por defecto.

### Secretos en variables de entorno
Las claves de API de OpenAI y ElevenLabs, así como la contraseña de la base de datos (`DB_PASSWORD`), nunca se codifican en el código fuente. Se leen exclusivamente de variables de entorno (archivo `.env`), y el `.gitignore` excluye este archivo del control de versiones.

### Nombres de archivo únicos
Las grabaciones subidas se guardan con nombres generados por `uuid.uuid4().hex`, evitando colisiones y previniendo que un usuario pueda sobrescribir o predecir el nombre de un archivo existente.

### Aislamiento de datos por usuario
Cada usuario solo puede acceder a sus propias grabaciones y sesiones de chat. Las grabaciones están en subdirectorios separados (`recordings/<user_id>/`) y las consultas SQL filtran siempre por `user_id`.

---

## 10. Decisiones de diseño destacadas

### PostgreSQL como base de datos
Se eligió PostgreSQL por su soporte nativo de JSONB (para almacenar informes psicológicos estructurados), su robustez y escalabilidad. El tipo JSONB permite consultar campos específicos del resumen (como `overall_sentiment`) directamente en SQL sin necesidad de deserializar en Python.

### Continuidad terapéutica vía takeaways
Al finalizar una sesión, el sistema genera un "takeaway" — un resumen condensado de 2-3 frases con los puntos clave. En la siguiente sesión, los takeaways anteriores se inyectan en el system prompt. Esto permite a la IA retomar la conversación sin repetir preguntas introductorias, mejorando significativamente la experiencia terapéutica.

### Sin framework de frontend
Toda la interfaz de usuario está construida con JavaScript Vanilla, HTML y CSS sin dependencias externas. Esto elimina un paso de compilación (build step), simplifica la depuración y reduce la superficie de ataque.

### Separación de estilos CSS
Los estilos de cada página se mantienen en hojas de estilo externas dentro de `static/css/` en lugar de embebidos en las plantillas HTML. Esto separa la presentación de la estructura, facilita la colaboración y permite al navegador cachear los estilos de forma independiente.

### Clonación de voz perezosa (lazy)
La voz clonada no se crea al arrancar el servidor sino en la primera petición de TTS. Esto evita fallos al inicio si no hay grabaciones disponibles aún, y da al usuario tiempo para grabar su voz antes de usar el TTS.

### Historial de conversación en el cliente
El historial de conversación se mantiene en el navegador y se envía completo en cada petición, mientras que la persistencia se maneja en el servidor vía PostgreSQL. Esto combina la simplicidad del enfoque stateless con la durabilidad de una base de datos.

### Respuesta en el idioma del usuario
El system prompt del psicólogo instruye explícitamente al modelo a responder siempre en el mismo idioma que el usuario. Esto, combinado con la generación de resúmenes en el idioma de la conversación, hace la aplicación accesible para hablantes de cualquier idioma sin configuración adicional.

### Consultas SQL externalizadas
Todas las consultas SQL están en archivos `.sql` separados del código Python. Esto facilita la revisión por DBAs, el ajuste de rendimiento, y evita la tentación de construir SQL dinámico (prevención de inyección SQL).
