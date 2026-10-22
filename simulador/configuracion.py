"""Parámetros generales de la entrevista."""

import os

TOTAL_PREGUNTAS = 3
CALIFICACION_APROBATORIA = 7
LIMITE_RESPUESTA = 3000
LIMITE_PREGUNTA = 450
MODELO_GEMINI = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()

VACANTES = (
    "Desarrollador Python Junior",
    "Desarrollador Web Frontend",
    "Integrador de APIs/Bots",
)

TEMAS_POR_VACANTE = {
    "Desarrollador Python Junior": (
        "estructuras de datos, funciones, control de flujo, excepciones "
        "y fundamentos de Python"
    ),
    "Desarrollador Web Frontend": (
        "HTML semántico, CSS, JavaScript, DOM, accesibilidad y desarrollo web"
    ),
    "Integrador de APIs/Bots": (
        "HTTP, APIs REST, JSON, autenticación, manejo de errores "
        "e integración de servicios y bots"
    ),
}
