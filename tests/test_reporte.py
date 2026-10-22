"""Validaciones de calificaciones y estructura Markdown."""

import unittest

from simulador.reporte import validar_reporte


class PruebasReporte(unittest.TestCase):
    def datos(self, nota=7, dictamen="APROBADO"):
        return {
            "calificacion": nota,
            "fortalezas": ["Entiende listas", "Describe funciones"],
            "areas_mejora": ["Reforzar excepciones", "Practicar diccionarios"],
            "dictamen": dictamen,
            "reporte_markdown": (
                f"## Calificación global\n{nota}/10\n"
                "## Fortalezas detectadas\n- Entiende listas\n- Describe funciones\n"
                "## Áreas de mejora\n- Reforzar excepciones\n- Practicar diccionarios\n"
                f"## Dictamen final\n**{dictamen}**"
            ),
        }

    def test_nota_limite_aprueba(self):
        self.assertEqual(validar_reporte(self.datos()).dictamen, "APROBADO")

    def test_nota_seis_no_aprueba(self):
        datos = self.datos(6, "NO APROBADO")
        self.assertEqual(validar_reporte(datos).dictamen, "NO APROBADO")

    def test_rechaza_nota_fuera_de_rango(self):
        for valor in (0, 11, "8", True):
            datos = self.datos()
            datos["calificacion"] = valor
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                validar_reporte(datos)

    def test_rechaza_menos_de_dos_fortalezas(self):
        datos = self.datos()
        datos["fortalezas"] = ["Solo una"]
        with self.assertRaises(ValueError):
            validar_reporte(datos)

    def test_rechaza_dictamen_incoherente(self):
        datos = self.datos(3, "APROBADO")
        with self.assertRaises(ValueError):
            validar_reporte(datos)

    def test_rechaza_markdown_incompleto(self):
        datos = self.datos()
        datos["reporte_markdown"] = "8/10, aprobado"
        with self.assertRaises(ValueError):
            validar_reporte(datos)


if __name__ == "__main__":
    unittest.main()
