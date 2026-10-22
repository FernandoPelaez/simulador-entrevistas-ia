"""Presentación Streamlit: no contiene reglas de negocio ni prompts."""

import logging
import os
from html import escape

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


def _clave_api() -> str:
    """Obtiene la clave del entorno o de los secretos de Streamlit."""
    clave = os.environ.get("GEMINI_API_KEY", "").strip()
    if clave:
        return clave
    try:
        return str(st.secrets.get("GEMINI_API_KEY", "")).strip()
    except Exception:
        # Streamlit puede fallar si no existe secrets.toml local.
        return ""


def _reiniciar() -> None:
    # El reinicio también descarta cualquier resultado pendiente de mostrar.
    st.session_state.pop("vacante_seleccionada", None)
    st.session_state.pop(CLAVE_MODAL, None)
    st.session_state[CLAVE_SESION] = Entrevista()


def _resolver_operacion(entrevista: Entrevista) -> None:
    """Procesa la siguiente acción sin duplicar turnos en las recargas."""
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
    except Exception:
        logging.exception("Falló una operación con Gemini")
        marcar_error(entrevista)
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


# Diseño del resumen: el reporte completo permanece en la página.
ESTILOS_MODAL = """
<style>
.resultado-modal {
    --acento: #b42318;
    --fondo-acento: #fff4f2;
    --borde-acento: #fecdca;
    color: #18243a;
    font-family: inherit;
}
.resultado-modal.aprobado {
    --acento: #067647;
    --fondo-acento: #ecfdf3;
    --borde-acento: #abefc6;
}
.resultado-modal .resultado-encabezado {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 18px;
    background: var(--fondo-acento);
    border: 1px solid var(--borde-acento);
    border-radius: 14px;
}
.resultado-modal .resultado-icono {
    display: grid;
    place-items: center;
    width: 48px;
    height: 48px;
    flex-shrink: 0;
    border-radius: 13px;
    background: #ffffff;
    font-size: 26px;
}
.resultado-modal .resultado-etiqueta {
    margin: 0 0 4px;
    color: #667085;
    font-size: 11px;
    font-weight: 750;
    letter-spacing: .09em;
    text-transform: uppercase;
}
.resultado-modal h3 {
    margin: 0 0 4px;
    color: #18243a;
    font-size: 20px;
    font-weight: 750;
    line-height: 1.2;
}
.resultado-modal .resultado-descripcion {
    margin: 0;
    color: #475467;
    font-size: 13px;
    line-height: 1.5;
}
.resultado-modal .resultado-puntuacion {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    margin: 20px 0 12px;
}
.resultado-modal .resultado-valor {
    display: flex;
    align-items: baseline;
    gap: 4px;
    line-height: 1;
}
.resultado-modal .resultado-valor strong {
    font-size: 44px;
    font-weight: 800;
    letter-spacing: -.06em;
}
.resultado-modal .resultado-valor span {
    font-size: 19px;
    color: #667085;
}
.resultado-modal .resultado-dictamen {
    padding: 8px 11px;
    color: var(--acento);
    background: var(--fondo-acento);
    border: 1px solid var(--borde-acento);
    border-radius: 999px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: .03em;
    white-space: nowrap;
}
.resultado-modal .resultado-progreso {
    width: 100%;
    height: 7px;
    overflow: hidden;
    background: #edf0f5;
    border-radius: 999px;
}
.resultado-modal .resultado-progreso span {
    display: block;
    height: 100%;
    background: var(--acento);
    border-radius: inherit;
}
.resultado-modal .resultado-seccion {
    padding-top: 17px;
    margin-top: 17px;
    border-top: 1px solid #e9edf3;
}
.resultado-modal .resultado-seccion h4 {
    margin: 0 0 10px;
    color: #18243a;
    font-size: 14px;
    font-weight: 750;
}
.resultado-modal .resultado-seccion ul {
    padding: 0;
    margin: 0;
    list-style: none;
}
.resultado-modal .resultado-seccion li {
    position: relative;
    margin: 0 0 8px;
    padding-left: 19px;
    color: #475467;
    font-size: 13px;
    line-height: 1.48;
    overflow-wrap: anywhere;
}
.resultado-modal .resultado-seccion li::before {
    content: "";
    position: absolute;
    left: 0;
    top: 7px;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #12b76a;
}
.resultado-modal .resultado-seccion.mejoras li::before {
    background: #f79009;
}
.resultado-modal .resultado-nota {
    margin: 14px 0 9px;
    color: #667085;
    font-size: 12px;
    text-align: center;
}
[data-testid="stDialog"] div.stButton > button[kind="primary"] {
    height: 44px;
    border-radius: 10px;
    font-weight: 650;
}
</style>
"""


@st.dialog("Resultado de la entrevista", width="small")
def _mostrar_modal_resultado(entrevista: Entrevista) -> None:
    """Muestra un resumen compacto sin repetir el reporte completo."""
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

    # Se muestran dos puntos por apartado; el reporte conserva todos los detalles.
    fortalezas = "".join(
        f"<li>{escape(str(punto))}</li>" for punto in reporte.fortalezas[:2]
    )
    mejoras = "".join(
        f"<li>{escape(str(punto))}</li>" for punto in reporte.areas_mejora[:2]
    )
    progreso = max(0, min(100, reporte.calificacion * 10))

    st.markdown(ESTILOS_MODAL, unsafe_allow_html=True)
    st.markdown(
        f"""
<article class="resultado-modal {estilo}">
  <header class="resultado-encabezado">
    <div class="resultado-icono" aria-hidden="true">{icono}</div>
    <div>
      <p class="resultado-etiqueta">Entrevista finalizada</p>
      <h3>{titulo}</h3>
      <p class="resultado-descripcion">{descripcion}</p>
    </div>
  </header>
  <div class="resultado-puntuacion">
    <div>
      <p class="resultado-etiqueta">Calificación global</p>
      <div class="resultado-valor"><strong>{reporte.calificacion}</strong><span>/10</span></div>
    </div>
    <span class="resultado-dictamen">{escape(reporte.dictamen)}</span>
  </div>
  <div class="resultado-progreso" role="progressbar" aria-label="Calificación"
       aria-valuemin="0" aria-valuemax="10" aria-valuenow="{reporte.calificacion}">
    <span style="width: {progreso}%"></span>
  </div>
  <section class="resultado-seccion">
    <h4>Fortalezas detectadas</h4>
    <ul>{fortalezas}</ul>
  </section>
  <section class="resultado-seccion mejoras">
    <h4>Áreas de mejora</h4>
    <ul>{mejoras}</ul>
  </section>
  <p class="resultado-nota">Consulta el análisis detallado en el reporte completo.</p>
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
        # Solo se abre al completar una evaluación nueva.
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

