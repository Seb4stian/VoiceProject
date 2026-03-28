# Documentación de APIs y Páginas — VoiceProject

## Tabla de contenidos

1. [Requisitos del sistema](#1-requisitos-del-sistema)
2. [Variables de entorno](#2-variables-de-entorno)
3. [Cómo ejecutar el servidor](#3-cómo-ejecutar-el-servidor)
4. [Páginas de la aplicación](#4-páginas-de-la-aplicación)
   - [Grabadora de Voz (`/`)](#41-grabadora-de-voz-)
   - [Texto a Voz — TTS (`/tts`)](#42-texto-a-voz--tts-tts)
   - [Voz a Texto — STT (`/stt`)](#43-voz-a-texto--stt-stt)
   - [Análisis de Sentimientos (`/sentiment`)](#44-análisis-de-sentimientos-sentiment)
   - [Chat de Psicología (`/chat`)](#45-chat-de-psicología-chat)
   - [Chat de Voz (`/voice-chat`)](#46-chat-de-voz-voice-chat)
5. [Referencia completa de la API](#5-referencia-completa-de-la-api)
   - [Módulo Grabadora](#51-módulo-grabadora)
   - [Módulo STT](#52-módulo-stt)
   - [Módulo TTS](#53-módulo-tts)
   - [Módulo Análisis de Sentimientos](#54-módulo-análisis-de-sentimientos)
   - [Módulo Chat de Psicología](#55-módulo-chat-de-psicología)
   - [Módulo Chat de Voz](#56-módulo-chat-de-voz)
6. [Códigos de error comunes](#6-códigos-de-error-comunes)

---

## 1. Requisitos del sistema

| Requisito | Versión mínima |
|-----------|---------------|
| Python    | 3.11          |
| Flask     | 3.0.0         |
| elevenlabs SDK | 1.0.0    |
| openai SDK     | 1.0.0    |
| python-dotenv  | 1.0.0    |

Para instalar todas las dependencias:

```bash
pip install -r requirements.txt
```

---

## 2. Variables de entorno

La aplicación requiere las siguientes variables de entorno. Se pueden definir en un archivo `.env` en la raíz del proyecto o exportarlas directamente en la terminal.

| Variable              | Obligatoria | Descripción |
|-----------------------|-------------|-------------|
| `OPENAI_API_KEY`      | Sí          | Clave de API de OpenAI. Se usa para el chat de psicología y el análisis de sentimientos. |
| `ELEVENLABS_API_KEY`  | Sí          | Clave de API de ElevenLabs. Se usa para la síntesis de voz (TTS) y el reconocimiento de voz (STT). |
| `FLASK_DEBUG`         | No          | Si se establece en `1`, Flask corre en modo de depuración con recarga automática. Por defecto es `0`. |

Ejemplo de archivo `.env`:

```env
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=sk_...
FLASK_DEBUG=0
```

---

## 3. Cómo ejecutar el servidor

### Ejecución estándar

```bash
python app.py
```

El servidor se inicia en `http://localhost:5000` de forma predeterminada.

### Ejecución en modo de depuración

```bash
FLASK_DEBUG=1 python app.py
```

En modo de depuración, Flask recarga el servidor automáticamente ante cualquier cambio en el código fuente.

### Ejecución con Gunicorn (producción)

Para entornos de producción se recomienda usar un servidor WSGI como Gunicorn:

```bash
pip install gunicorn
gunicorn "app:create_app()" --bind 0.0.0.0:5000
```

### Configuración adicional (`config.json`)

El archivo `config.json` en la raíz del proyecto permite ajustar dos parámetros:

```json
{
  "openai_model": "gpt-4o-mini",
  "default_language": "es"
}
```

| Campo              | Descripción | Valores posibles |
|--------------------|-------------|-----------------|
| `openai_model`     | Modelo de OpenAI utilizado para el chat y el análisis de sentimientos. | Cualquier identificador de modelo de OpenAI, por ejemplo `gpt-4o`, `gpt-4o-mini`. |
| `default_language` | Idioma predeterminado para el saludo inicial del psicólogo y el resumen de la sesión. | `"es"` (español), `"en"` (inglés), `"de"` (alemán), `"fr"` (francés), `"ja"` (japonés), `"pt"` (portugués), `"it"` (italiano), `"zh"` (chino), `"ko"` (coreano). |

---

## 4. Páginas de la aplicación

### 4.1 Grabadora de Voz (`/`)

**Propósito:** Permite al usuario grabar su voz directamente desde el navegador y guardar las grabaciones en el servidor. Estas grabaciones son la fuente de datos para la clonación de voz utilizada por los módulos TTS.

**Cómo usar:**

1. Abrir `http://localhost:5000/` en el navegador.
2. Hacer clic en el botón **Record** (rojo). El navegador solicitará permiso para acceder al micrófono; concederlo.
3. Hablar durante al menos unos segundos para obtener una muestra de buena calidad.
4. Hacer clic en **Stop** para detener la grabación.
5. Escuchar la previsualización en el reproductor que aparece.
6. Si la grabación es satisfactoria, hacer clic en **Save to server**. Si no, hacer clic en **Discard** y volver al paso 2.
7. Las grabaciones guardadas aparecen en la lista inferior con un reproductor individual por archivo.

**Notas importantes:**
- Se recomienda guardar **varias grabaciones** (3 o más) de frases diferentes para obtener una mejor clonación de voz.
- Las grabaciones se almacenan en la carpeta `recordings/` del servidor con nombres únicos generados automáticamente.
- Formatos de audio admitidos: `webm`, `ogg`, `wav`, `mp4`.

---

### 4.2 Texto a Voz — TTS (`/tts`)

**Propósito:** Convierte texto escrito en audio hablado utilizando una voz clonada del propio usuario (construida a partir de las grabaciones guardadas).

**Requisito previo:** Haber guardado al menos una grabación en la página Grabadora de Voz.

**Cómo usar:**

1. Abrir `http://localhost:5000/tts`.
2. Seleccionar el idioma de pronunciación en el menú desplegable (Inglés, Español, Alemán, Francés, Italiano, Portugués, Japonés, Chino o Coreano).
3. Escribir el texto que se desea escuchar en el área de texto.
4. Hacer clic en **Read Aloud**.
5. El servidor genera el audio con la voz clonada y lo reproduce automáticamente en el reproductor que aparece.

**Notas:**
- La primera vez que se usa el TTS después de iniciar el servidor, el sistema clona la voz a partir de todas las grabaciones disponibles. Las llamadas siguientes reutilizan la voz clonada mientras el conjunto de grabaciones no cambie.
- Los idiomas soportados para la síntesis son: Inglés (`en`), Español (`es`), Alemán (`de`), Francés (`fr`), Italiano (`it`), Portugués (`pt`), Japonés (`ja`), Chino (`zh`) y Coreano (`ko`).

---

### 4.3 Voz a Texto — STT (`/stt`)

**Propósito:** Transcribe audio grabado en tiempo real a texto escrito utilizando el modelo de reconocimiento de voz de ElevenLabs (`scribe_v1`).

**Cómo usar:**

1. Abrir `http://localhost:5000/stt`.
2. Seleccionar el idioma hablado en el menú desplegable (Inglés, Español, Alemán, Francés, Italiano, Portugués, Japonés, Chino o Coreano).
3. Hacer clic en **Record** y hablar claramente.
4. Hacer clic en **Stop** al terminar.
5. La transcripción aparece automáticamente en el área de texto inferior.

---

### 4.4 Análisis de Sentimientos (`/sentiment`)

**Propósito:** Analiza el tono emocional de un texto y devuelve una puntuación numérica y una etiqueta cualitativa (Bueno, Neutral, Malo) usando la API de OpenAI.

**Cómo usar:**

1. Abrir `http://localhost:5000/sentiment`.
2. Escribir o pegar el texto a analizar en el área de texto.
3. Hacer clic en **Analyze Sentiment**.
4. El resultado muestra:
   - **Etiqueta:** Good (😊), Neutral (😐) o Bad (😞).
   - **Puntuación:** Un número entre `-1.0` (muy negativo) y `+1.0` (muy positivo).
   - **Barra visual:** Un indicador gráfico que posiciona la puntuación en el espectro completo.

**Interpretación de la puntuación:**

| Rango            | Etiqueta | Significado |
|------------------|----------|-------------|
| `> +0.25`        | Good     | Sentimiento positivo. |
| Entre `-0.25` y `+0.25` | Neutral | Sentimiento neutro. |
| `< -0.25`        | Bad      | Sentimiento negativo. |

---

### 4.5 Chat de Psicología (`/chat`)

**Propósito:** Proporciona una sesión de conversación textual con un psicólogo de IA especializado en el bienestar emocional de adultos mayores. Al finalizar la sesión genera un informe psicológico detallado.

**Cómo usar:**

1. Abrir `http://localhost:5000/chat`.
2. El psicólogo de IA inicia automáticamente la conversación con un saludo en el idioma configurado en `config.json`.
3. Escribir mensajes en el campo de texto inferior y presionar **Send** o la tecla **Enter**.
4. Cada mensaje del usuario muestra una insignia de sentimiento (Good/Neutral/Bad) con su puntuación.
5. Al finalizar la conversación, hacer clic en **End Chat & Get Summary** para obtener el informe psicológico.

**Informe psicológico incluye:**
- Sentimiento general de la sesión (puntuación y etiqueta).
- Estado emocional predominante.
- Principales preocupaciones detectadas.
- Señales positivas observadas.
- Evaluación del estado mental.
- Recomendaciones del psicólogo.
- Resumen narrativo de la sesión.

**Notas:**
- El psicólogo responde siempre en el mismo idioma que usa el usuario.
- Se requiere al menos un intercambio de mensajes para poder generar el resumen.

---

### 4.6 Chat de Voz (`/voice-chat`)

**Propósito:** Versión de voz del chat de psicología. El usuario habla con el micrófono y escucha las respuestas del psicólogo con la voz clonada del propio usuario.

**Requisito previo:** Haber guardado al menos una grabación en la página Grabadora de Voz.

**Cómo usar:**

1. Abrir `http://localhost:5000/voice-chat`.
2. Hacer clic en **▶ Start Conversation** para iniciar (este paso es necesario para que el navegador permita la reproducción automática de audio).
3. El psicólogo pronuncia su saludo inicial con la voz clonada.
4. Hacer clic en **Record** y hablar la respuesta.
5. Hacer clic en **Stop** al terminar de hablar.
6. El sistema transcribe el audio, obtiene la respuesta del psicólogo y la reproduce en voz alta automáticamente.
7. Repetir los pasos 4-6 para continuar la conversación.
8. Al finalizar, hacer clic en **End Chat & Get Summary** para obtener el informe psicológico (idéntico al del Chat de Psicología).

**Flujo interno de cada turno:**
1. Grabación de audio del usuario en el navegador.
2. Envío del audio a `/voice-chat/transcribe` (STT).
3. Envío del texto transcrito a `/chat/message` (respuesta + sentimiento).
4. Envío de la respuesta a `/voice-chat/speak` (TTS con voz clonada).
5. Reproducción del audio resultante en el navegador.

---

## 5. Referencia completa de la API

Todas las rutas retornan JSON en caso de error. En las respuestas exitosas, el formato varía según el endpoint (JSON, archivo de audio, etc.).

### 5.1 Módulo Grabadora

#### `GET /`

Renderiza la página principal de la grabadora de voz.

- **Respuesta:** Página HTML.

---

#### `POST /upload`

Sube un archivo de audio al servidor y lo guarda en la carpeta `recordings/`.

- **Tipo de contenido:** `multipart/form-data`
- **Campos del formulario:**

  | Campo   | Tipo   | Obligatorio | Descripción |
  |---------|--------|-------------|-------------|
  | `audio` | archivo | Sí         | Archivo de audio a guardar. Formatos válidos: `webm`, `ogg`, `wav`, `mp4`. |

- **Respuesta exitosa (`201 Created`):**

  ```json
  {
    "filename": "3f8a1b2c9d4e5f6a7b8c9d0e.webm"
  }
  ```

- **Respuestas de error:**

  | Código | Motivo |
  |--------|--------|
  | `400`  | No se proporcionó ningún archivo de audio. |

---

#### `GET /recordings`

Devuelve la lista de grabaciones guardadas en el servidor, ordenadas de la más reciente a la más antigua.

- **Respuesta exitosa (`200 OK`):**

  ```json
  ["3f8a1b2c.webm", "1a2b3c4d.webm"]
  ```

---

#### `GET /recordings/<filename>`

Descarga o sirve un archivo de audio específico.

- **Parámetros de ruta:**

  | Parámetro  | Descripción |
  |------------|-------------|
  | `filename` | Nombre del archivo de grabación. |

- **Respuesta exitosa (`200 OK`):** El archivo de audio binario con el MIME type correspondiente.

- **Respuestas de error:**

  | Código | Motivo |
  |--------|--------|
  | `400`  | Extensión de archivo no permitida. |
  | `404`  | El archivo no existe. |

---

### 5.2 Módulo STT

#### `GET /stt/`

Renderiza la página de Speech-to-Text.

- **Respuesta:** Página HTML.

---

#### `POST /stt/transcribe`

Transcribe un archivo de audio a texto usando el modelo `scribe_v1` de ElevenLabs.

- **Tipo de contenido:** `multipart/form-data`
- **Campos del formulario:**

  | Campo      | Tipo    | Obligatorio | Descripción |
  |------------|---------|-------------|-------------|
  | `audio`    | archivo | Sí          | Archivo de audio a transcribir. |
  | `language` | string  | No          | Código de idioma. Valores válidos: `"en"`, `"es"`, `"de"`, `"fr"`, `"it"`, `"pt"`, `"ja"`, `"zh"`, `"ko"`. Por defecto `"en"`. |

- **Respuesta exitosa (`200 OK`):**

  ```json
  {
    "text": "Texto transcrito del audio."
  }
  ```

- **Respuestas de error:**

  | Código | Motivo |
  |--------|--------|
  | `400`  | No se proporcionó ningún archivo de audio. |
  | `500`  | `ELEVENLABS_API_KEY` no configurada, o fallo en la transcripción. |

---

### 5.3 Módulo TTS

#### `GET /tts/`

Renderiza la página de Text-to-Speech.

- **Respuesta:** Página HTML.

---

#### `POST /tts/speak`

Convierte texto a audio usando la voz clonada del usuario y el modelo `eleven_multilingual_v2` de ElevenLabs.

- **Tipo de contenido:** `application/json`
- **Cuerpo de la petición:**

  | Campo      | Tipo   | Obligatorio | Descripción |
  |------------|--------|-------------|-------------|
  | `text`     | string | Sí          | Texto a sintetizar. |
  | `language` | string | No          | Código de idioma. Valores válidos: `"en"`, `"es"`, `"de"`, `"fr"`, `"it"`, `"pt"`, `"ja"`, `"zh"`, `"ko"`. Por defecto `"en"`. |

  Ejemplo:
  ```json
  {
    "text": "Hola, ¿cómo estás?",
    "language": "en"
  }
  ```

- **Respuesta exitosa (`200 OK`):** Archivo de audio MP3 (`audio/mpeg`).

- **Respuestas de error:**

  | Código | Motivo |
  |--------|--------|
  | `400`  | No se proporcionó texto, o no hay grabaciones para clonar la voz. |
  | `500`  | `ELEVENLABS_API_KEY` no configurada, fallo en la clonación de voz, o fallo en la síntesis. |

---

### 5.4 Módulo Análisis de Sentimientos

#### `GET /sentiment/`

Renderiza la página de análisis de sentimientos.

- **Respuesta:** Página HTML.

---

#### `POST /sentiment/analyze`

Analiza el sentimiento de un texto usando el modelo de OpenAI configurado.

- **Tipo de contenido:** `application/json`
- **Cuerpo de la petición:**

  | Campo  | Tipo   | Obligatorio | Descripción |
  |--------|--------|-------------|-------------|
  | `text` | string | Sí          | Texto a analizar. |

  Ejemplo:
  ```json
  {
    "text": "Me siento muy feliz hoy."
  }
  ```

- **Respuesta exitosa (`200 OK`):**

  ```json
  {
    "score": 0.85,
    "label": "Good"
  }
  ```

  | Campo   | Tipo   | Descripción |
  |---------|--------|-------------|
  | `score` | float  | Puntuación entre `-1.0` (muy negativo) y `+1.0` (muy positivo). |
  | `label` | string | `"Good"`, `"Neutral"` o `"Bad"`. |

- **Respuestas de error:**

  | Código | Motivo |
  |--------|--------|
  | `400`  | No se proporcionó texto. |
  | `500`  | `OPENAI_API_KEY` no configurada, o fallo en el análisis. |

---

### 5.5 Módulo Chat de Psicología

#### `GET /chat/`

Renderiza la página del chat de psicología.

- **Respuesta:** Página HTML.

---

#### `POST /chat/start`

Solicita al psicólogo de IA que inicie la conversación con un saludo en el idioma configurado en `config.json`.

- **Tipo de contenido:** No requiere cuerpo.
- **Respuesta exitosa (`200 OK`):**

  ```json
  {
    "reply": "¡Buenos días! Me alegra que esté aquí. ¿Cómo se siente hoy?"
  }
  ```

- **Respuestas de error:**

  | Código | Motivo |
  |--------|--------|
  | `500`  | `OPENAI_API_KEY` no configurada, o fallo al generar el saludo. |

---

#### `POST /chat/message`

Envía un mensaje del usuario al psicólogo de IA y recibe la respuesta junto con el análisis de sentimiento del mensaje del usuario.

- **Tipo de contenido:** `application/json`
- **Cuerpo de la petición:**

  | Campo     | Tipo   | Obligatorio | Descripción |
  |-----------|--------|-------------|-------------|
  | `message` | string | Sí          | Mensaje del usuario. |
  | `history` | array  | No          | Historial de la conversación. Lista de objetos `{"role": "user"/"assistant", "content": "..."}`. |

  Ejemplo:
  ```json
  {
    "message": "Me siento un poco solo hoy.",
    "history": [
      { "role": "assistant", "content": "¡Buenos días! ¿Cómo se siente hoy?" }
    ]
  }
  ```

- **Respuesta exitosa (`200 OK`):**

  ```json
  {
    "reply": "Entiendo cómo se siente. La soledad puede ser difícil...",
    "sentiment": {
      "score": -0.4,
      "label": "Bad"
    }
  }
  ```

- **Respuestas de error:**

  | Código | Motivo |
  |--------|--------|
  | `400`  | No se proporcionó mensaje. |
  | `500`  | `OPENAI_API_KEY` no configurada, o fallo en el chat. |

---

#### `POST /chat/summary`

Genera un informe psicológico completo a partir del historial de la conversación.

- **Tipo de contenido:** `application/json`
- **Cuerpo de la petición:**

  | Campo     | Tipo  | Obligatorio | Descripción |
  |-----------|-------|-------------|-------------|
  | `history` | array | Sí          | Historial completo de la conversación. Lista de objetos `{"role": "...", "content": "..."}`. |

- **Respuesta exitosa (`200 OK`):**

  ```json
  {
    "overall_sentiment": -0.15,
    "emotional_state": "Melancolía con momentos de esperanza",
    "key_concerns": ["Soledad", "Distancia familiar"],
    "positive_signs": ["Deseo de conexión", "Actitud reflexiva"],
    "mental_state_assessment": "El paciente muestra signos de soledad moderada...",
    "recommendations": ["Fomentar actividades sociales", "Contacto regular con la familia"],
    "summary": "La conversación reveló un estado emocional de tristeza leve..."
  }
  ```

- **Respuestas de error:**

  | Código | Motivo |
  |--------|--------|
  | `400`  | No se proporcionó historial. |
  | `500`  | `OPENAI_API_KEY` no configurada, o fallo al generar el resumen. |

---

### 5.6 Módulo Chat de Voz

#### `GET /voice-chat/`

Renderiza la página del chat de voz.

- **Respuesta:** Página HTML.

---

#### `POST /voice-chat/speak`

Sintetiza texto a audio usando la voz clonada del usuario. A diferencia de `/tts/speak`, detecta automáticamente el idioma del texto (no requiere el parámetro `language`).

- **Tipo de contenido:** `application/json`
- **Cuerpo de la petición:**

  | Campo  | Tipo   | Obligatorio | Descripción |
  |--------|--------|-------------|-------------|
  | `text` | string | Sí          | Texto a sintetizar. |

  Ejemplo:
  ```json
  {
    "text": "¿Cómo puedo ayudarle hoy?"
  }
  ```

- **Respuesta exitosa (`200 OK`):** Archivo de audio MP3 (`audio/mpeg`).

- **Respuestas de error:**

  | Código | Motivo |
  |--------|--------|
  | `400`  | No se proporcionó texto, o no hay grabaciones. |
  | `500`  | `ELEVENLABS_API_KEY` no configurada, o fallo en la síntesis. |

---

#### `POST /voice-chat/transcribe`

Transcribe el audio del usuario a texto con detección automática de idioma (no requiere el parámetro `language`).

- **Tipo de contenido:** `multipart/form-data`
- **Campos del formulario:**

  | Campo   | Tipo    | Obligatorio | Descripción |
  |---------|---------|-------------|-------------|
  | `audio` | archivo | Sí          | Archivo de audio a transcribir. |

- **Respuesta exitosa (`200 OK`):**

  ```json
  {
    "text": "Me siento bien, gracias."
  }
  ```

- **Respuestas de error:**

  | Código | Motivo |
  |--------|--------|
  | `400`  | No se proporcionó ningún archivo de audio. |
  | `500`  | `ELEVENLABS_API_KEY` no configurada, o fallo en la transcripción. |

---

## 6. Códigos de error comunes

| Código HTTP | Significado | Acción recomendada |
|-------------|-------------|-------------------|
| `400 Bad Request` | Faltan parámetros obligatorios o los datos son inválidos. | Revisar el cuerpo de la petición. |
| `404 Not Found` | El archivo solicitado no existe. | Verificar el nombre del archivo. |
| `500 Internal Server Error` | Fallo en el servidor, generalmente por una clave de API no configurada o un error en un servicio externo. | Revisar las variables de entorno y los logs del servidor. |

Todos los errores devuelven un objeto JSON con la siguiente estructura:

```json
{
  "error": "Descripción del error."
}
```
