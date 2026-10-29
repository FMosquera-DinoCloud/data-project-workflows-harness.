"""Tests de las guardas y del lint. Correr: py -X utf8 -m unittest discover -s ~/claude-workspace/harness/tests"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

H = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(H / "scripts"))
import harness_lint  # noqa: E402


def guard(name: str, event: dict, env: dict | None = None) -> int:
    r = subprocess.run([sys.executable, "-X", "utf8", str(H / "hooks" / "guards.py"), name], input=json.dumps(event),
                       capture_output=True, text=True, env={**os.environ, **(env or {})})
    return r.returncode


def project(tmp: Path) -> Path:
    (tmp / "project.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    return tmp


class Guards(unittest.TestCase):
    def test_credencial_se_bloquea_siempre(self):
        with tempfile.TemporaryDirectory() as t:
            ev = {"tool_name": "mcp__claude_ai_Slack__slack_send_message", "cwd": t, "tool_input": {"text": "key AKIAABCDEFGHIJKLMNOP"}}
            self.assertEqual(guard("outbound", ev), 2)

    def test_ids_internos_solo_en_proyecto(self):
        with tempfile.TemporaryDirectory() as t:
            ev = {"tool_name": "mcp__claude_ai_ClickUp__clickup_create_task_comment", "cwd": t, "tool_input": {"text": "ver D-050"}}
            self.assertEqual(guard("outbound", ev), 0)
            project(Path(t))
            self.assertEqual(guard("outbound", ev), 2)
            ev["tool_input"]["text"] = "sin ids"
            self.assertEqual(guard("outbound", ev), 0)

    def test_lecturas_no_se_tocan(self):
        with tempfile.TemporaryDirectory() as t:
            project(Path(t))
            ev = {"tool_name": "mcp__claude_ai_ClickUp__clickup_get_task", "cwd": t, "tool_input": {"id": "T-012"}}
            self.assertEqual(guard("outbound", ev), 0)

    def test_desatendida_no_reescribe_reglas(self):
        ev = {"tool_name": "Write", "tool_input": {"file_path": "C:/x/proj/CLAUDE.md"}}
        self.assertEqual(guard("unattended-write", ev, {"HARNESS_UNATTENDED": "1"}), 2)
        self.assertEqual(guard("unattended-write", ev, {"HARNESS_UNATTENDED": "0"}), 0)
        self.assertEqual(guard("unattended-write", {"tool_name": "Write", "tool_input": {"file_path": "C:/x/proj/claude.MD"}}, {"HARNESS_UNATTENDED": "1"}), 2)
        bash = {"tool_name": "Bash", "tool_input": {"command": "mv /tmp/x CLAUDE.md"}}
        self.assertEqual(guard("unattended-write", bash, {"HARNESS_UNATTENDED": "1"}), 2)
        self.assertEqual(guard("unattended-write", {"tool_name": "Bash", "tool_input": {"command": "git add status"}}, {"HARNESS_UNATTENDED": "1"}), 0)
        ok = {"tool_name": "Write", "tool_input": {"file_path": "C:/x/proj/status/2026-10-15.md"}}
        self.assertEqual(guard("unattended-write", ok, {"HARNESS_UNATTENDED": "1"}), 0)

    def test_desatendida_no_toca_git_ni_el_registro_del_espejo(self):
        env = {"HARNESS_UNATTENDED": "1"}
        for path in ("C:/x/proj/.git/hooks/pre-commit", "C:/x/proj/.git/config", "C:/x/proj/.harness/team-mirror-review.csv"):
            self.assertEqual(guard("unattended-write", {"tool_name": "Write", "tool_input": {"file_path": path}}, env), 2, path)
        for cmd in ("cp x .git/hooks/pre-push", "echo y > .harness/team-mirror-review.csv"):
            self.assertEqual(guard("unattended-write", {"tool_name": "Bash", "tool_input": {"command": cmd}}, env), 2, cmd)
        self.assertEqual(guard("unattended-write", {"tool_name": "Write", "tool_input": {"file_path": "C:/x/proj/status/2026-10-21.md"}}, env), 0)

    def test_desatendida_no_cambia_la_config_de_git(self):
        env = {"HARNESS_UNATTENDED": "1"}
        for cmd in ("git config core.sshCommand 'sh x'", "git -c core.hooksPath=/tmp/h push", "GIT_SSH_COMMAND=x git push",
                    "GIT_EXEC_PATH=/tmp/x git push", "git -C . config --local alias.st '!sh x'", "git -P config core.sshCommand x",
                    "git --config-env=core.sshCommand=X push", "git \"config\" core.sshCommand x", "git -C /x/proj -c core.fsmonitor=sh push"):
            self.assertEqual(guard("unattended-write", {"tool_name": "Bash", "tool_input": {"command": cmd}}, env), 2, cmd)
        for cmd in ("git status", "git add status/2026-10-21.md", "git commit -m x", "git commit -m 'ajusta config del proyecto'", "git log --oneline",
                    "git -C /x/proj status", "git -C /x/proj add status/a.md", "git add notes/git_ssh.md", "git add config.toml",
                    'git commit -m "documenta git config local"'):
            self.assertEqual(guard("unattended-write", {"tool_name": "Bash", "tool_input": {"command": cmd}}, env), 0, cmd)

    def test_marca_de_confidencialidad(self):
        with tempfile.TemporaryDirectory() as t:
            root = project(Path(t))
            f = root / "notas.md"
            f.write_text("# sin marca\n", encoding="utf-8")
            ev = {"tool_name": "Write", "tool_input": {"file_path": str(f)}}
            self.assertEqual(guard("marker", ev), 2)
            f.write_text("> **DinoCloud Internal - Confidential**\n# con marca\n", encoding="utf-8")
            self.assertEqual(guard("marker", ev), 0)


class Lint(unittest.TestCase):
    def test_detecta_indice_roto_y_decision_sin_indexar(self):
        with tempfile.TemporaryDirectory() as t:
            root = project(Path(t))
            (root / "index.toon").write_text('index[1]{path,type,date,summary,tags}:\n  no-existe.md,other,2026-10-15,"x",y\n', encoding="utf-8")
            (root / "docs/decisions").mkdir(parents=True)
            (root / "docs/decisions/decisions.md").write_text("> **DinoCloud Internal - Confidential**\n## D-77 — algo\n", encoding="utf-8")
            errors, warns = harness_lint.lint(root)
            self.assertTrue(any("no-existe.md" in e for e in errors))
            self.assertTrue(any("D-77" in w for w in warns))



class HarnessRun(unittest.TestCase):
    def test_comandos_del_loop_no_consumen_stdin(self):
        # El loop de proyectos recibe la lista por stdin: claude -p y los scripts del loop tienen que leer de /dev/null.
        src = (H / "bin" / "harness-run").read_text(encoding="utf-8")
        run = src[src.index("run_claude() {"):src.index("}", src.index("run_claude() {"))]
        self.assertIn("</dev/null", run)
        self.assertIn("config --local --list", src)
        # El push de cada proyecto y el del workspace quedan condicionados a que la config de git no haya cambiado.
        i = src.index('[ "$cfg_before" != "$cfg_after" ]')
        self.assertLess(i, src.index('git_sync "$dir" push', i))
        self.assertIn("else\n    git_sync \"$dir\" push", src[i:])
        j = src.index('ws_cfg_before" != ')
        self.assertIn('else\n  git_sync "$WS" push', src[j:])


if __name__ == "__main__":
    unittest.main()
