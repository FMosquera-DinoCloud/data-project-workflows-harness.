"""Tests de los controles de team_mirror. Correr: py -X utf8 -m unittest discover -s ~/claude-workspace/harness/tests"""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import team_mirror as tm  # noqa: E402


class Privado(unittest.TestCase):
    def test_archivo_marcado_no_sale(self):
        self.assertIsNone(tm.strip_private("<!-- privado -->\n# x\ntexto\n"))

    def test_seccion_marcada_se_quita(self):
        text = "# D\n\n## D-001 — a\nok\n\n## D-002 — b\n<!-- privado -->\nmargen\n\n## D-003 — c\nok\n"
        out = tm.strip_private(text)
        self.assertIn("D-001", out)
        self.assertIn("D-003", out)
        self.assertNotIn("D-002", out)
        self.assertNotIn("margen", out)

    def test_sin_marca_queda_igual(self):
        self.assertEqual(tm.strip_private("## a\nb\n"), "## a\nb\n")


class UnoAUno(unittest.TestCase):
    def test_dos_personas_es_1a1(self):
        self.assertTrue(tm.one_to_one("context/meetings/2026-10-06-sync-ana.md", "**Participantes:** Ana, Juan · **Fuente:** x\n"))

    def test_daily_con_dos_no_es_1a1(self):
        self.assertFalse(tm.one_to_one("context/meetings/2026-10-13-daily-meeting.md", "**Participantes:** Ana, Juan · x\n"))

    def test_reunion_de_equipo_no_es_1a1(self):
        self.assertFalse(tm.one_to_one("context/meetings/2026-10-05-sync.md", "**Participantes:** Ana, Juan, Eva, Leo · x\n"))

    def test_fuera_de_reuniones_no_aplica(self):
        self.assertFalse(tm.one_to_one("docs/decisions/decisions.md", "texto"))


class Terminos(unittest.TestCase):
    def pat(self, term):
        return re.compile(rf"(?<![\w:]){re.escape(term)}(?![\w:])", re.I)

    def test_1a1_no_coincide_con_horas(self):
        self.assertIsNone(self.pat("1:1").search("2026-10-12 11:17 · Ever"))

    def test_1a1_coincide_como_palabra(self):
        self.assertIsNotNone(self.pat("1:1").search("en el 1:1 con Ana"))


class Coincidencia(unittest.TestCase):
    def test_include_y_exclude(self):
        inc, exc = ["docs/architecture/", "clickup/tasks.toon"], ["docs/architecture/x.html"]
        self.assertTrue(tm.matches("docs/architecture/a/b.png", inc, exc))
        self.assertTrue(tm.matches("clickup/tasks.toon", inc, exc))
        self.assertFalse(tm.matches("docs/architecture/x.html", inc, exc))
        self.assertFalse(tm.matches("context/digest/a.md", inc, exc))


if __name__ == "__main__":
    unittest.main()
