"""Modelo y validación del reporte que produce Gemini."""

from dataclasses import dataclass
import re

from .configuracion import CALIFICACION_APROBATORIA


@dataclass(frozen=True)
class Reporte:
    calificacion: int
    fortalezas: tuple[str, ...]
    areas_mejora: tuple[str, ...]
    dictamen: str
    markdown: str


def _lista_no_vacia(datos: dict, clave: str) -> tuple[str, ...]:
    elementos = datos.get(clave)
    if (
        not isinstance(elementos, list)
        or len(elementos) < 2
        or any(not isinstance(texto, str) or not texto.strip() for texto in elementos)
    ):
        raise ValueError(f"La sección '{clave}' necesita al menos dos elementos.")
    return tuple(elemento.strip() for elemento in elementos)


def validar_reporte(datos: dict) -> Reporte:
    """Rechaza resultados incompletos o contradictorios de Gemini."""
    if not isinstance(datos, dict):
        raise ValueError("El reporte debe ser un objeto JSON.")

    nota = datos.get("calificacion")
    if type(nota) is not int or not 1 <= nota <= 10:
        raise ValueError("La calificación debe ser un entero entre 1 y 10.")

    fortalezas = _lista_no_vacia(datos, "fortalezas")
    mejoras = _lista_no_vacia(datos, "areas_mejora")
    dictamen = "APROBADO" if nota >= CALIFICACION_APROBATORIA else "NO APROBADO"

    if datos.get("dictamen") != dictamen:
        raise ValueError("El dictamen no corresponde a la calificación.")

    markdown = datos.get("reporte_markdown")
    if not isinstance(markdown, str) or not markdown.strip():
        raise ValueError("Gemini no generó el reporte en Markdown.")

    titulos = (
        "Calificación global",
        "Fortalezas detectadas",
        "Áreas de mejora",
        "Dictamen final",
    )
    if any(titulo.casefold() not in markdown.casefold() for titulo in titulos):
        raise ValueError("Faltan secciones obligatorias del reporte Markdown.")

    if not re.search(rf"(?<!\d){nota}\s*/\s*10(?!\d)", markdown):
        raise ValueError("La calificación escrita en Markdown no coincide.")

    if dictamen == "NO APROBADO":
        if not re.search(r"\bNO\s+APROBADO\b", markdown, re.IGNORECASE):
            raise ValueError("El dictamen escrito en Markdown es incorrecto.")
    elif (
        not re.search(r"\bAPROBADO\b", markdown, re.IGNORECASE)
        or re.search(r"\bNO\s+APROBADO\b", markdown, re.IGNORECASE)
    ):
        raise ValueError("El dictamen escrito en Markdown es incorrecto.")

    # Normaliza el contenido evaluado por Gemini para mostrar siempre 2 listas.
    salida = (
        f"### Calificación global\n\n**{nota}/10**\n\n"
        "### Fortalezas detectadas\n\n"
        + "\n".join(f"- {texto}" for texto in fortalezas)
        + "\n\n### Áreas de mejora\n\n"
        + "\n".join(f"- {texto}" for texto in mejoras)
        + f"\n\n### Dictamen final\n\n**{dictamen}**"
    )
    return Reporte(
        calificacion=nota,
        fortalezas=fortalezas,
        areas_mejora=mejoras,
        dictamen=dictamen,
        markdown=salida,
    )
