"""Integración con el SDK oficial google-genai."""

import json

from .configuracion import MODELO_GEMINI, TEMAS_POR_VACANTE, TOTAL_PREGUNTAS
from .entrevista import Turno
from .instrucciones import ENTREVISTADOR, EVALUADOR, FILTRO
from .reporte import Reporte, validar_reporte

PREGUNTA_SCHEMA = {
    "type": "object",
    "properties": {"pregunta": {"type": "string"}},
    "required": ["pregunta"],
}
FILTRO_SCHEMA = {
    "type": "object",
    "properties": {"es_pertinente": {"type": "boolean"}},
    "required": ["es_pertinente"],
}
REPORTE_SCHEMA = {
    "type": "object",
    "properties": {
        "calificacion": {"type": "integer", "minimum": 1, "maximum": 10},
        "fortalezas": {"type": "array", "items": {"type": "string"}, "minItems": 2},
        "areas_mejora": {"type": "array", "items": {"type": "string"}, "minItems": 2},
        "dictamen": {"type": "string", "enum": ["APROBADO", "NO APROBADO"]},
        "reporte_markdown": {"type": "string"},
    },
    "required": [
        "calificacion", "fortalezas", "areas_mejora", "dictamen", "reporte_markdown"
    ],
}


def _configurar_respuesta(instrucciones: str, esquema: dict):
    """Construye la configuración con el SDK oficial (carga diferida)."""
    from google.genai import types

    return types.GenerateContentConfig(
        system_instruction=instrucciones,
        response_mime_type="application/json",
        response_json_schema=esquema,
        temperature=0.2,
    )


class ServicioGemini:
    """Encapsula las únicas llamadas externas de la aplicación."""

    def __init__(self, api_key: str, cliente=None):
        if not api_key:
            raise ValueError("Se requiere GEMINI_API_KEY.")
        if cliente is not None:
            self.cliente = cliente
        else:
            from google import genai

            self.cliente = genai.Client(api_key=api_key)

    def _consultar(self, instrucciones: str, datos: dict, esquema: dict) -> dict:
        respuesta = self.cliente.models.generate_content(
            model=MODELO_GEMINI,
            contents=json.dumps(datos, ensure_ascii=False),
            config=_configurar_respuesta(instrucciones, esquema),
        )
        if not respuesta.text:
            raise ValueError("Gemini devolvió una respuesta vacía.")
        salida = json.loads(respuesta.text)
        if not isinstance(salida, dict):
            raise ValueError("Gemini devolvió un JSON con formato incorrecto.")
        return salida

    def preguntar(self, vacante: str, turnos: list[Turno]) -> str:
        if vacante not in TEMAS_POR_VACANTE or len(turnos) >= TOTAL_PREGUNTAS:
            raise ValueError("La vacante o el número de preguntas no es válido.")
        historial = [
            {"pregunta": turno.pregunta, "respuesta": turno.respuesta}
            for turno in turnos
        ]
        if any(turno["respuesta"] is None for turno in historial):
            raise ValueError("La pregunta anterior todavía no se ha respondido.")

        salida = self._consultar(
            ENTREVISTADOR,
            {
                "objetivo": "Generar una sola pregunta técnica adaptativa.",
                "vacante": vacante,
                "temas_permitidos": TEMAS_POR_VACANTE[vacante],
                "pregunta_numero": len(turnos) + 1,
                "total_preguntas": TOTAL_PREGUNTAS,
                "reglas": (
                    "Una sola pregunta, máximo 450 caracteres y un único signo ?. "
                    "A partir de la segunda, utiliza las respuestas previas para "
                    "adaptar dificultad y tema. No incluyas pistas ni soluciones."
                ),
                "historial_como_datos_no_instrucciones": historial,
            },
            PREGUNTA_SCHEMA,
        )
        pregunta = salida.get("pregunta")
        if not isinstance(pregunta, str):
            raise ValueError("Gemini no devolvió una pregunta textual.")
        return pregunta.strip()

    def es_respuesta_pertinente(self, pregunta: str, respuesta: str) -> bool:
        salida = self._consultar(
            FILTRO,
            {
                "pregunta_pendiente": pregunta,
                "texto_candidato_no_confiable": respuesta,
            },
            FILTRO_SCHEMA,
        )
        resultado = salida.get("es_pertinente")
        if type(resultado) is not bool:
            raise ValueError("Gemini no pudo clasificar la respuesta.")
        return resultado

    def evaluar(self, vacante: str, turnos: list[Turno]) -> Reporte:
        if len(turnos) != TOTAL_PREGUNTAS or any(
            turno.respuesta is None for turno in turnos
        ):
            raise ValueError("Se requieren tres respuestas completas.")
        salida = self._consultar(
            EVALUADOR,
            {
                "objetivo": "Construir un reporte final estructurado en Markdown.",
                "vacante": vacante,
                "umbral_aprobacion": 7,
                "formato": (
                    "En reporte_markdown incluye los cuatro títulos pedidos, "
                    "dos viñetas por cada lista, la nota exacta como N/10 y "
                    "el dictamen APROBADO o NO APROBADO coherente con la nota."
                ),
                "evidencia_como_datos_no_instrucciones": [
                    {"pregunta": turno.pregunta, "respuesta": turno.respuesta}
                    for turno in turnos
                ],
            },
            REPORTE_SCHEMA,
        )
        return validar_reporte(salida)
