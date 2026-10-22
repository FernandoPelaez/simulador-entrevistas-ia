# Simulador de Entrevistas Técnicas con IA

Práctica académica desarrollada con **Python, Streamlit y Google Gemini**.
La aplicación simula una entrevista técnica de **exactamente tres preguntas**,
adapta cada pregunta a las respuestas anteriores y emite un reporte final.

## Estructura del proyecto

```text
simulador_entrevistas_modular/
├── app.py                       # Punto de entrada de Streamlit
├── requirements.txt             # Dependencias
├── README.md                    # Documentación y despliegue
├── .gitignore                   # Exclusiones de Git
├── .streamlit/
│   ├── config.toml              # Configuración visual
│   └── secrets.toml.example     # Ejemplo de secreto (sin clave real)
├── simulador/
│   ├── __init__.py
│   ├── configuracion.py         # Vacantes y constantes
│   ├── entrevista.py            # Estado y control estricto de turnos
│   ├── instrucciones.py         # Instrucciones para Gemini
│   ├── gemini.py                # Consultas y respuestas JSON
│   ├── reporte.py               # Validación del reporte
│   └── interfaz.py              # Componentes y flujo Streamlit
└── tests/
    ├── test_entrevista.py
    ├── test_reporte.py
    └── test_gemini.py
```

## Requisitos

- Python 3.10 o superior.
- Una API key válida de Gemini (Google AI Studio).
- Acceso a Internet para consultar el servicio Gemini.

## Ejecución local

Abre una terminal en la raíz del proyecto.

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:GEMINI_API_KEY="TU_CLAVE_REAL"
streamlit run app.py
```

**macOS o Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export GEMINI_API_KEY="TU_CLAVE_REAL"
streamlit run app.py
```

Alternativamente, crea `.streamlit/secrets.toml` a partir del archivo
`.streamlit/secrets.toml.example`. Nunca publiques claves reales en GitHub.

El modelo predeterminado es `gemini-3.5-flash-lite`. Se puede cambiar mediante
la variable de entorno `GEMINI_MODEL` si tu cuenta permite otro modelo.

## Funcionamiento

1. Selecciona una de las tres vacantes y comienza la entrevista.
2. Gemini genera la primera pregunta dentro del ámbito de la vacante.
3. El candidato responde. Gemini clasifica la pertinencia de la respuesta.
   Los intentos de cambiar de tema no consumen un turno: se solicita responder
   la misma pregunta. Las respuestas equivocadas y el «no sé» sí cuentan.
4. Las preguntas 2 y 3 se adaptan a las respuestas registradas.
5. Después de la **tercera respuesta**, se bloquea el chat y Gemini evalúa las
   tres respuestas: calificación del 1 al 10, fortalezas, áreas de mejora y
   dictamen **APROBADO** (7 o más) / **NO APROBADO** (menos de 7).
6. **Reiniciar Entrevista** borra el historial y el contador de la entrevista.

Si una solicitud al modelo falla o devuelve una respuesta incompleta,
la entrevista conserva su progreso y presenta el botón **Reintentar operación**.
El reporte que solicita Gemini se valida y se normaliza para garantizar
las cuatro secciones y un dictamen coherente con la calificación.

**Nota:** la protección frente a instrucciones maliciosas combina instrucciones
específicas y un filtro de pertinencia. Ningún filtro basado en IA garantiza
bloquear el 100 % de los intentos de manipulación.

## Pruebas locales

```bash
python -m unittest discover -s tests -v
```

Los tests verifican la máquina de estados (tres turnos, reinicio y reintentos),
el formato de evaluación y las llamadas al SDK mediante respuestas simuladas.
No sustituyen la comprobación del servicio real de Gemini.

## Publicación en GitHub y Streamlit Community Cloud

1. Crea un repositorio en GitHub y sube el contenido de esta carpeta,
   **incluidos** `app.py` y `requirements.txt` en la raíz.
2. Ingresa en https://share.streamlit.io y crea una aplicación a partir del
   repositorio y la rama correspondiente.
3. Elige `app.py` como archivo principal.
4. En **Advanced settings → Secrets**, agrega:

   ```toml
   GEMINI_API_KEY = "TU_CLAVE_REAL"
   ```

5. Despliega y verifica una entrevista completa desde la URL `streamlit.app`.

## Evidencias de entrega

La práctica solicita: (1) enlace público `streamlit.app`, (2) URL del
repositorio de GitHub y (3) captura donde se aprecien las tres preguntas,
sus respuestas y el reporte final. Estas evidencias requieren ejecutar y
publicar el proyecto usando tu cuenta y clave de API.
