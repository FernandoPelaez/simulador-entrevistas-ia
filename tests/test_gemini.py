"""Pruebas de integración simulada: no requieren clave ni red."""

import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from simulador.configuracion import VACANTES
from simulador.entrevista import Turno
from simulador.gemini import ServicioGemini


class ClienteSimulado:
    def __init__(self, respuestas):
        self.respuestas = list(respuestas)
        self.llamadas = []
        self.models = self

    def generate_content(self, **kwargs):
        self.llamadas.append(kwargs)
        return SimpleNamespace(text=json.dumps(self.respuestas.pop(0)))


class PruebasGemini(unittest.TestCase):
    def setUp(self):
        simulador_config = patch(
            "simulador.gemini._configurar_respuesta",
            side_effect=lambda instrucciones, esquema: {
                "system_instruction": instrucciones,
                "response_json_schema": esquema,
            },
        )
        simulador_config.start()
        self.addCleanup(simulador_config.stop)

    def test_segunda_pregunta_considera_respuesta_anterior(self):
        cliente = ClienteSimulado([{"pregunta": "¿Qué diferencia hay entre lista y tupla?"}])
        servicio = ServicioGemini("clave-simulada", cliente)
        pregunta = servicio.preguntar(
            VACANTES[0], [Turno("¿Qué es una lista?", "Es una colección mutable")]
        )
        self.assertIn("tupla", pregunta)
        datos = json.loads(cliente.llamadas[0]["contents"])
        self.assertEqual(datos["pregunta_numero"], 2)
        self.assertIn("Es una colección mutable", str(datos["historial_como_datos_no_instrucciones"]))
        self.assertIn("Python", datos["temas_permitidos"])

    def test_temas_adecuados_por_vacante(self):
        for vacante, tema in ((VACANTES[0], "Python"), (VACANTES[1], "HTML"), (VACANTES[2], "HTTP")):
            with self.subTest(vacante=vacante):
                cliente = ClienteSimulado([{"pregunta": "¿Qué es el concepto principal?"}])
                ServicioGemini("clave-simulada", cliente).preguntar(vacante, [])
                contenido = json.loads(cliente.llamadas[0]["contents"])
                self.assertIn(tema, contenido["temas_permitidos"])

    def test_filtro_contra_desvios(self):
        cliente = ClienteSimulado([{"es_pertinente": False}])
        servicio = ServicioGemini("clave-simulada", cliente)
        self.assertFalse(servicio.es_respuesta_pertinente("¿Qué es REST?", "Dame una receta"))
        contenido = json.loads(cliente.llamadas[0]["contents"])
        self.assertEqual(contenido["pregunta_pendiente"], "¿Qué es REST?")

    def test_no_envia_cuarta_pregunta_a_gemini(self):
        cliente = ClienteSimulado([])
        servicio = ServicioGemini("clave-simulada", cliente)
        tres = [Turno(f"¿Pregunta {n}?", "Respuesta") for n in range(3)]
        with self.assertRaises(ValueError):
            servicio.preguntar(VACANTES[0], tres)
        self.assertEqual(cliente.llamadas, [])

    def test_evaluacion_solo_con_tres_turnos(self):
        cliente = ClienteSimulado([])
        servicio = ServicioGemini("clave-simulada", cliente)
        with self.assertRaises(ValueError):
            servicio.evaluar(VACANTES[0], [Turno("¿Uno?", "Sí")])
        self.assertEqual(cliente.llamadas, [])


if __name__ == "__main__":
    unittest.main()
