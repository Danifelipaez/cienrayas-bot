# CienRayas Bot (v1.1) 🎣🦀
### Asistente Conversacional y de Seguridad para la Pesca Artesanal en la Ciénaga Grande de Santa Marta

CienRayas Bot es un chatbot de WhatsApp que integra **saber tradicional pesquero** (nombres locales de vientos, lunas para el camarón, colores del agua, marcas territoriales) con **datos científicos en tiempo real** (calidad del agua del IDEAM, satélites de la NASA y pronósticos de clima) para proveer alertas de seguridad y recomendaciones de faena a pescadores artesanales en la Ciénaga Grande de Santa Marta, Colombia.

El bot fue diseñado en el marco del Seminario Aluna IA (Universidad del Magdalena, 2026), combinando reportes de campo y el sistema de cogestión pesquera de INVEMAR.

---

## 🚀 Características Principales

*   **🚦 Semáforo de Seguridad Diario**: Determina de forma automática si es seguro salir a pescar (Verde, Amarillo, Rojo) evaluando vientos locales, lluvias y niveles de oxígeno.
*   ** índice de Potencial Pesquero (IPP)**: Clasifica y prioriza 6 zonas de la ciénaga de 0 a 100 usando pesos multivariados (oxígeno, pH, temperatura, salinidad, clorofila y turbidez).
*   **📍 Mapas Dinámicos en Tiempo Real**: Genera un mapa náutico (PNG) personalizado con matplotlib, localizando las mejores zonas y puntos tradicionales del pescador (saber de Sr. Adelmo).
*   **💬 Inteligencia Artificial Adaptada**: Utiliza Groq (Llama 3) para dialogar con los pescadores en su dialecto regional ("compa") de forma empática y clara.
*   **⚡ Soporte de Alta Concurrencia (Demo En Vivo)**: Caches integradas en memoria para Clima (10m), Satélite (6h), Calidad de Agua (24h) y Mapas (10m) que permiten soportar de 15 a 50 consultas simultáneas en auditorios sin caídas del servicio ni problemas de concurrencia de matplotlib.

---

## 📁 Estructura del Proyecto

```text
cienrayas-bot/
├── core/                   # Lógica central del negocio y conocimiento
│   ├── knowledge.py        # Coordenadas locales, especies, vientos y saber tradicional
│   ├── semaphore.py        # Evaluación de reglas de seguridad (Semáforo)
│   ├── zone_analysis.py    # Cálculo de IPP (Índice de Potencial Pesquero)
│   └── state.py            # Manejo de estados de conversación (feedback, de-duplicación)
├── services/               # Conexiones con APIs externas e imagen corporativa
│   ├── weather.py          # Conector del Clima (wttr.in) - Con Caché
│   ├── satellite.py        # Conector Satelital (NASA/NOAA ERDDAP) - Con Caché
│   ├── water_quality.py    # Sensores de Calidad del Agua (IDEAM/DHIME) - Con Caché
│   ├── map_generator.py    # Generador de mapas náuticos con matplotlib - Con Caché
│   ├── llm.py              # Respuestas dinámicas usando Groq API
│   └── whatsapp.py         # Envío de mensajes a través de WhatsApp Cloud API
├── routers/
│   └── webhook.py          # Endpoints de API de WhatsApp (FastAPI)
├── main.py                 # Inicializador de la aplicación
├── requirements.txt        # Dependencias de Python
└── .env.example            # Plantilla de variables de entorno
```

---

## 🛠️ Requisitos e Instalación

### 1. Requisitos Previos
*   Python 3.10 o superior instalado.
*   Una cuenta en [Meta Developers Portal](https://developers.facebook.com/) con el producto de WhatsApp Cloud API configurado (puedes usar el número de prueba gratuito).
*   Una API Key de Groq (se puede obtener de forma gratuita en [Groq Console](https://console.groq.com)).

### 2. Configuración del Repositorio
Clona o descarga este repositorio en tu máquina local y accede a la carpeta raíz:

```bash
cd cienrayas-bot
```

Instala todas las librerías necesarias ejecutando:

```bash
pip install -r requirements.txt
```

### 3. Variables de Entorno (`.env`)
Crea un archivo `.env` en la raíz del proyecto copiando el contenido de `.env.example` y rellena con tus claves:

```env
# ── Groq (API Key del LLM)
GROQ_API_KEY=gsk_tu_api_key_aqui

# ── Meta WhatsApp Cloud API
WHATSAPP_TOKEN=tu_token_de_acceso_temporal_o_permanente
WHATSAPP_PHONE_NUMBER_ID=tu_phone_number_id
WEBHOOK_VERIFY_TOKEN=cienrayas_secreto   # Clave de verificación que registras en Meta

# ── Servidor
# En local, debe ser la URL de ngrok (ver paso siguiente)
BASE_URL=https://tu-subdominio.ngrok-free.app
MEDIA_DIR=media
```

---

## 🏃 Cómo Correr el Programa en Local

### Paso 1: Iniciar el Servidor de FastAPI
Ejecuta el servidor web local con Uvicorn:

```bash
uvicorn main:app --reload --port 8000
```
El servidor estará corriendo en `http://localhost:8000`.

### Paso 2: Exponer el Servidor a Internet (Necesario para Meta)
WhatsApp requiere conectarse a una URL pública con HTTPS. Para pruebas locales, utiliza **ngrok**:

```bash
ngrok http 8000
```
Ngrok te proporcionará una URL pública similar a `https://a1b2-cd34.ngrok-free.app`. 
Copia esa URL y pégala en tu archivo `.env` como valor de `BASE_URL`. Reinicia el servidor de FastAPI para que tome el cambio.

### Paso 3: Configurar el Webhook en Meta Portal
1. Ve al panel de control de tu aplicación en Meta Developers Portal.
2. Ve a **WhatsApp** > **Configuración** (Webhook).
3. Haz clic en **Editar** en la sección de Webhooks y configura:
   *   **URL de devolución**: `https://tu-subdominio.ngrok-free.app/webhook` (reemplaza con tu URL de ngrok, asegúrate de incluir el path `/webhook` al final).
   *   **Token de verificación**: `cienrayas_secreto` (o el valor que hayas definido en `WEBHOOK_VERIFY_TOKEN`).
4. Haz clic en **Verificar y guardar**.
5. En la sección **Campos de webhook**, suscríbete al campo `messages` para recibir los mensajes entrantes.

---

## 🧪 Pruebas Locales (Scripts de Prueba)

El proyecto cuenta con dos scripts para verificar el correcto funcionamiento de los conectores y la lógica sin necesidad de enviar mensajes desde WhatsApp:

*   **Probar la obtención de datos**:
    ```bash
    python test_data.py
    ```
    *(Verifica la conexión con los servidores de clima, calidad de agua de IDEAM y satélites de la NASA, y genera un mapa de prueba en tu carpeta local).*

*   **Simular un mensaje entrante en el Webhook**:
    ```bash
    python test_bot.py
    ```
    *(Simula la llegada de un mensaje del pescador al endpoint local para verificar la lógica de semáforo, el LLM y la simulación del envío).*

---

## 🛡️ Notas de la Demo en Vivo (Auditorios)

Este código está optimizado para demostraciones ante audiencias concurrentes (15 a 50 personas escaneando un código QR simultáneamente):
*   El mapa se genera y almacena en caché por 10 minutos. No sobrecargará la CPU del servidor ni dará error en hilos de Matplotlib.
*   Las APIs de clima y satélite están cacheadas, eliminando bloqueos de IP (Error 429) de los proveedores públicos.
*   **Nota**: Asegúrate de contar con una API Key de Groq con un tier de pago o límites altos de RPM (Requests Per Minute) si esperas que todos los asistentes reciban respuestas personalizadas redactadas por el modelo en segundos.
