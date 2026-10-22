"""Interfaz de Streamlit para el simulador de entrevistas."""

import logging
import os
from html import escape
from pathlib import Path

import streamlit as st

from .configuracion import LIMITE_RESPUESTA, TOTAL_PREGUNTAS, VACANTES
from .entrevista import (
    Entrevista,
    finalizar,
    iniciar,
    marcar_error,
    proponer_respuesta,
    recibir_pregunta,
    reintentar,
    resolver_respuesta,
)
from .gemini import ServicioGemini

CLAVE_SESION = "simulador_entrevista"
CLAVE_MODAL = "mostrar_modal_resultado"


def _cargar_estilos() -> None:
    """Aplica los estilos de la interfaz y del modal."""
    ruta = Path(__file__).with_name("estilos.css")
    estilos = ruta.read_text(encoding="utf-8")
    st.markdown(f"<style>{estilos}</style>", unsafe_allow_html=True)


def _clave_api() -> str:
    """Obtiene la clave del entorno o de los secretos de Streamlit."""
    clave = os.environ.get("GEMINI_API_KEY", "").strip()
    if clave:
        return clave
    try:
        return str(st.secrets.get("GEMINI_API_KEY", "")).strip()
    except Exception:
        return ""


def _reiniciar() -> None:
    st.session_state.pop("vacante_seleccionada", None)
    st.session_state.pop(CLAVE_MODAL, None)
    st.session_state[CLAVE_SESION] = Entrevista()


def _mensaje_error_gemini(error: Exception) -> str | None:
    """Distingue los errores de la API sin revelar información privada."""
    codigo = getattr(error, "code", None)
    if codigo == 503:
        return (
            "Gemini no está disponible temporalmente. Tu progreso se conservó; "
            "puedes reintentar más tarde."
        )
    if codigo == 429:
        return (
            "Se alcanzó el límite de solicitudes de Gemini. Tu progreso se "
            "conservó; vuelve a intentarlo cuando se restablezca el acceso."
        )
    if codigo in (401, 403):
        return (
            "Gemini rechazó el acceso. Revisa la API key y los permisos "
            "configurados en Streamlit Secrets."
        )
    return None


def _resolver_operacion(entrevista: Entrevista) -> None:
    """Procesa una acción de Gemini conservando el estado ante errores."""
    if entrevista.estado not in ("generando", "validando", "evaluando"):
        return

    clave = _clave_api()
    if not clave:
        marcar_error(entrevista)
        entrevista.aviso = "Falta configurar GEMINI_API_KEY."
        st.rerun()
        return

    try:
        with st.spinner("El líder técnico está procesando la entrevista..."):
            servicio = ServicioGemini(clave)
            if entrevista.estado == "generando":
                pregunta = servicio.preguntar(entrevista.vacante, entrevista.turnos)
                recibir_pregunta(entrevista, pregunta)
            elif entrevista.estado == "validando":
                pertinente = servicio.es_respuesta_pertinente(
                    entrevista.turnos[-1].pregunta,
                    entrevista.respuesta_pendiente,
                )
                resolver_respuesta(entrevista, pertinente)
            else:
                reporte = servicio.evaluar(entrevista.vacante, entrevista.turnos)
                finalizar(entrevista, reporte)
                st.session_state[CLAVE_MODAL] = True
    except Exception as error:
        logging.exception("Falló una operación con Gemini")
        marcar_error(entrevista)
        entrevista.aviso = _mensaje_error_gemini(error) or entrevista.aviso

    st.rerun()


def _mostrar_conversacion(entrevista: Entrevista) -> None:
    for numero, turno in enumerate(entrevista.turnos, start=1):
        with st.chat_message("assistant"):
            st.markdown(f"**Pregunta {numero} de {TOTAL_PREGUNTAS}**")
            st.write(turno.pregunta)
        if turno.respuesta is not None:
            with st.chat_message("user"):
                st.write(turno.respuesta)


def _mostrar_reporte(entrevista: Entrevista) -> None:
    reporte = entrevista.reporte
    st.divider()
    st.subheader("Evaluación final")
    st.metric("Calificación global", f"{reporte.calificacion}/10")
    if reporte.dictamen == "APROBADO":
        st.success("Dictamen: APROBADO")
    else:
        st.error("Dictamen: NO APROBADO")
    st.markdown(reporte.markdown)
    st.caption(
        "Simulación educativa. El dictamen no constituye una decisión "
        "de contratación real."
    )


@st.dialog("Resultado de la entrevista", width="medium")
def _mostrar_modal_resultado(entrevista: Entrevista) -> None:
    """Presenta un resumen sin reemplazar el reporte detallado."""
    reporte = entrevista.reporte
    aprobado = reporte.dictamen == "APROBADO"
    estilo = "aprobado" if aprobado else "no-aprobado"
    titulo = "¡Felicidades! 🎉" if aprobado else "¡Ups! Sigue participando 😂"
    descripcion = (
        "Has aprobado la entrevista técnica."
        if aprobado
        else "No eres apto para el puesto por el momento."
    )
    icono = "🎉" if aprobado else "😂"
    progreso = max(0, min(100, reporte.calificacion * 10))

    # La vista móvil resume un punto por sección; el reporte conserva todos.
    fortalezas = "".join(
        f'<li title="{escape(str(texto), quote=True)}">{escape(str(texto))}</li>'
        for texto in reporte.fortalezas[:2]
    )
    mejoras = "".join(
        f'<li title="{escape(str(texto), quote=True)}">{escape(str(texto))}</li>'
        for texto in reporte.areas_mejora[:2]
    )

    st.markdown(
        f"""
<article class="resultado-modal {estilo}">
  <header class="resumen-cabecera">
    <div class="resumen-icono" aria-hidden="true">{icono}</div>
    <div>
      <p class="resumen-etiqueta">Entrevista finalizada</p>
      <h3>{titulo}</h3>
      <p class="resumen-descripcion">{descripcion}</p>
    </div>
  </header>
  <div class="resumen-resultado">
    <div>
      <p class="resumen-etiqueta">Calificación global</p>
      <div class="resumen-nota">{reporte.calificacion}<span>/10</span></div>
    </div>
    <span class="resumen-dictamen">{escape(reporte.dictamen)}</span>
  </div>
  <div class="resumen-barra" role="progressbar" aria-label="Calificación"
       aria-valuemin="0" aria-valuemax="10" aria-valuenow="{reporte.calificacion}">
    <span style="width: {progreso}%"></span>
  </div>
  <div class="resumen-secciones">
    <section class="resumen-seccion">
      <h4>Fortalezas detectadas</h4>
      <ul>{fortalezas}</ul>
    </section>
    <section class="resumen-seccion mejoras">
      <h4>Áreas de mejora</h4>
      <ul>{mejoras}</ul>
    </section>
  </div>
  <p class="resumen-pie">Consulta todos los detalles en el reporte completo.</p>
</article>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Ver reporte completo", type="primary", use_container_width=True):
        st.rerun()


def mostrar_aplicacion() -> None:
    if CLAVE_SESION not in st.session_state:
        _reiniciar()
    entrevista: Entrevista = st.session_state[CLAVE_SESION]

    _cargar_estilos()

    with st.sidebar:
        st.header("Configuración")
        vacante = st.selectbox(
            "Selecciona la vacante",
            VACANTES,
            key="vacante_seleccionada",
            disabled=entrevista.estado != "inicio",
        )
        st.button(
            "Reiniciar Entrevista",
            on_click=_reiniciar,
            use_container_width=True,
        )
        st.caption("3 preguntas adaptativas · Evaluación con Gemini")

    st.title("Simulador de Entrevistas Técnicas")
    st.caption("Líder Técnico Virtual · Google Gemini")
    st.progress(
        entrevista.respondidas / TOTAL_PREGUNTAS,
        text=f"Preguntas respondidas: {entrevista.respondidas} de {TOTAL_PREGUNTAS}",
    )

    if entrevista.estado == "inicio":
        st.write(
            "Elige una vacante e inicia la entrevista. Responderás tres "
            "preguntas técnicas que se adaptan a tus respuestas. Al terminar, "
            "recibirás un reporte de evaluación."
        )
        if st.button("Comenzar entrevista", type="primary"):
            if not _clave_api():
                st.error(
                    "No está configurada GEMINI_API_KEY. "
                    "Agrégala como secreto de Streamlit o variable de entorno."
                )
            else:
                iniciar(entrevista, vacante)
                st.rerun()
        return

    st.markdown(f"**Vacante:** {entrevista.vacante}")
    _resolver_operacion(entrevista)
    _mostrar_conversacion(entrevista)

    if entrevista.aviso:
        st.warning(entrevista.aviso)

    if entrevista.estado.startswith("error_"):
        if st.button("Reintentar operación", type="primary"):
            reintentar(entrevista)
            st.rerun()

    if entrevista.estado == "finalizada":
        _mostrar_reporte(entrevista)
        # El modal aparece una sola vez por evaluación terminada.
        if st.session_state.pop(CLAVE_MODAL, False):
            _mostrar_modal_resultado(entrevista)
        return

    respuesta = st.chat_input(
        "Responde la pregunta técnica...",
        disabled=entrevista.estado != "preguntando",
        max_chars=LIMITE_RESPUESTA,
    )
    if respuesta and entrevista.estado == "preguntando":
        try:
            proponer_respuesta(entrevista, respuesta)
        except ValueError as error:
            st.warning(str(error))
        else:
            st.rerun()

