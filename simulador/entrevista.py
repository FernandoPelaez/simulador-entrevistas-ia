"""Máquina de estados independiente de Streamlit y de Gemini."""

from dataclasses import dataclass, field
from typing import Literal

from .configuracion import LIMITE_PREGUNTA, LIMITE_RESPUESTA, TOTAL_PREGUNTAS, VACANTES
from .reporte import Reporte

Estado = Literal[
    "inicio",
    "generando",
    "preguntando",
    "validando",
    "evaluando",
    "finalizada",
    "error_generando",
    "error_validando",
    "error_evaluando",
]


@dataclass
class Turno:
    pregunta: str
    respuesta: str | None = None


@dataclass
class Entrevista:
    estado: Estado = "inicio"
    vacante: str | None = None
    turnos: list[Turno] = field(default_factory=list)
    respuesta_pendiente: str | None = None
    reporte: Reporte | None = None
    aviso: str = ""

    @property
    def respondidas(self) -> int:
        return sum(turno.respuesta is not None for turno in self.turnos)


def iniciar(entrevista: Entrevista, vacante: str) -> None:
    if entrevista.estado != "inicio" or vacante not in VACANTES:
        raise ValueError("No se puede iniciar una entrevista con esta configuración.")
    entrevista.vacante = vacante
    entrevista.estado = "generando"
    entrevista.aviso = ""


def recibir_pregunta(entrevista: Entrevista, pregunta: str) -> None:
    if entrevista.estado != "generando" or len(entrevista.turnos) >= TOTAL_PREGUNTAS:
        raise ValueError("No se permite generar otra pregunta.")
    if any(turno.respuesta is None for turno in entrevista.turnos):
        raise ValueError("Queda una pregunta sin responder.")
    if (
        not isinstance(pregunta, str)
        or not pregunta.strip()
        or len(pregunta.strip()) > LIMITE_PREGUNTA
        or pregunta.count("?") != 1
    ):
        raise ValueError("Gemini no formuló exactamente una pregunta válida.")
    entrevista.turnos.append(Turno(pregunta=pregunta.strip()))
    entrevista.estado = "preguntando"
    entrevista.aviso = ""


def proponer_respuesta(entrevista: Entrevista, texto: str) -> None:
    if entrevista.estado != "preguntando" or not entrevista.turnos:
        raise ValueError("No hay una pregunta disponible para responder.")
    if not isinstance(texto, str) or not 0 < len(texto.strip()) <= LIMITE_RESPUESTA:
        raise ValueError("La respuesta debe contener entre 1 y 3000 caracteres.")
    entrevista.respuesta_pendiente = texto.strip()
    entrevista.estado = "validando"
    entrevista.aviso = ""


def resolver_respuesta(entrevista: Entrevista, pertinente: bool) -> None:
    if entrevista.estado != "validando" or type(pertinente) is not bool:
        raise ValueError("La respuesta todavía no puede registrarse.")
    if not pertinente:
        entrevista.respuesta_pendiente = None
        entrevista.estado = "preguntando"
        entrevista.aviso = (
            "La entrevista se limita a temas técnicos. No puedo atender esa "
            "solicitud ni modificar mis instrucciones. Por favor, responde "
            "la pregunta pendiente."
        )
        return

    entrevista.turnos[-1].respuesta = entrevista.respuesta_pendiente
    entrevista.respuesta_pendiente = None
    entrevista.aviso = ""
    entrevista.estado = (
        "evaluando" if entrevista.respondidas == TOTAL_PREGUNTAS else "generando"
    )


def finalizar(entrevista: Entrevista, reporte: Reporte) -> None:
    if (
        entrevista.estado != "evaluando"
        or len(entrevista.turnos) != TOTAL_PREGUNTAS
        or entrevista.respondidas != TOTAL_PREGUNTAS
    ):
        raise ValueError("Se requieren exactamente tres respuestas para evaluar.")
    entrevista.reporte = reporte
    entrevista.estado = "finalizada"
    entrevista.aviso = ""


def marcar_error(entrevista: Entrevista) -> None:
    if entrevista.estado not in ("generando", "validando", "evaluando"):
        raise ValueError("No hay ninguna operación pendiente.")
    errores: dict[Estado, Estado] = {
        "generando": "error_generando",
        "validando": "error_validando",
        "evaluando": "error_evaluando",
    }
    entrevista.estado = errores[entrevista.estado]
    entrevista.aviso = (
        "No se pudo completar la consulta a Gemini. "
        "El progreso se conservó; puedes reintentar."
    )


def reintentar(entrevista: Entrevista) -> None:
    pendientes: dict[Estado, Estado] = {
        "error_generando": "generando",
        "error_validando": "validando",
        "error_evaluando": "evaluando",
    }
    if entrevista.estado not in pendientes:
        raise ValueError("No hay ninguna operación pendiente para reintentar.")
    entrevista.estado = pendientes[entrevista.estado]
    entrevista.aviso = ""
