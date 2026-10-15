"""A skill `analisar-lotes` versionada e igual para Claude Code e Antigravity/Codex (feature 006; D-106; RF-01)."""

import re
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CLAUDE = RAIZ / ".claude" / "skills" / "analisar-lotes"
AGENTS = RAIZ / ".agents" / "skills" / "analisar-lotes"


def _arquivos(pasta: Path) -> dict[str, bytes]:
    return {str(p.relative_to(pasta)): p.read_bytes() for p in sorted(pasta.rglob("*")) if p.is_file()}


def test_as_duas_copias_sao_identicas():
    assert (CLAUDE / "SKILL.md").exists()
    assert _arquivos(CLAUDE) == _arquivos(AGENTS)


def test_cabecalho_com_nome_e_descricao():
    texto = (CLAUDE / "SKILL.md").read_text(encoding="utf-8")
    cabecalho = re.match(r"^---\n(.*?)\n---\n", texto, re.S)
    assert cabecalho, "SKILL.md começa com o cabeçalho YAML"
    assert re.search(r"^name: analisar-lotes$", cabecalho.group(1), re.M)
    assert re.search(r"^description: .{40,}", cabecalho.group(1), re.M)


def test_nenhum_segredo_na_skill():
    for nome, conteudo in _arquivos(CLAUDE).items():
        texto = conteudo.decode("utf-8", errors="ignore")
        assert not re.search(r"apify_api_[A-Za-z0-9]{20,}|\d{8,}:[A-Za-z0-9_-]{30,}", texto), nome


def test_a_skill_nao_e_ignorada_pelo_git():
    for pasta in (CLAUDE, AGENTS):
        ignorado = subprocess.run(["git", "check-ignore", "-q", str(pasta / "SKILL.md")], cwd=RAIZ).returncode == 0
        assert not ignorado, pasta
