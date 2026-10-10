"""Captura páginas reais dos leiloeiros para os testes dos parsers e dos adaptadores.

Uso (rede necessária, cerca de 30 segundos cada):

    python scripts/capturar_fixtures.py                  # Vip Leilões
    python scripts/capturar_fixtures.py --claudio-kuss   # Claudio Kuss Leilões

Grava em tests/fixtures/vip/ ou tests/fixtures/claudio_kuss/. Respeita a mesma conduta do coletor: sessão com
cookies, no máximo 3 redirecionamentos e 5 segundos entre requisições.
Rodar de novo só quando o layout do Vip mudar e o parser precisar de conserto.
"""

from __future__ import annotations

import json
import math
import re
import sys
import time
from datetime import date
from pathlib import Path

import httpx

BASE = "https://www.vipleiloes.com.br"
DESTINO = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "vip"
INTERVALO = 5.0
CABECALHOS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}
CABECALHOS_AJAX = {
    "X-Requested-With": "XMLHttpRequest",
    "Referer": f"{BASE}/pesquisa/index",
}
CAMPOS_FIXOS = [("Filtro.OrdenarPor", "DataInicio"), ("Filtro.SelecaoVeiculos", "true")]

# (arquivo, filtros, página)
BUSCA_AMPLA = [("Filtro.Procedencia", "4"), ("Filtro.Monta", "1")]
UM_RESULTADO = [("Filtro.Marca", "NISSAN"), ("Filtro.Procedencia", "4"), ("Filtro.Monta", "1")]
ZERO_RESULTADOS = [("Filtro.Marca", "GURGEL"), ("Filtro.Procedencia", "4"), ("Filtro.Monta", "1")]


def url_pagina(numero: int) -> str:
    if numero == 1:
        return f"{BASE}/pesquisa?handler=pesquisar"
    return f"{BASE}/pesquisa?SortOrder=DataInicio&pageNumber={numero}&handler=pesquisar"


def total_resultados(html: str) -> int:
    achado = re.search(r'id="resultadosEncontrados"[^>]*>\s*(\d+)', html)
    if not achado:
        raise SystemExit("Indicador de total não encontrado: o layout do Vip mudou?")
    return int(achado.group(1))


class Capturador:
    def __init__(self) -> None:
        self.cliente = httpx.Client(
            headers=CABECALHOS, follow_redirects=True, max_redirects=3, timeout=30.0
        )
        self.ultima = 0.0

    def _esperar(self) -> None:
        falta = self.ultima + INTERVALO - time.monotonic()
        if falta > 0:
            time.sleep(falta)
        self.ultima = time.monotonic()

    def get(self, url: str) -> httpx.Response:
        self._esperar()
        resposta = self.cliente.get(url)
        resposta.raise_for_status()
        return resposta

    def pesquisar(self, filtros: list[tuple[str, str]], pagina: int) -> str:
        self._esperar()
        resposta = self.cliente.post(
            url_pagina(pagina), data=dict(CAMPOS_FIXOS + filtros), headers=CABECALHOS_AJAX
        )
        resposta.raise_for_status()
        return resposta.text


def gravar(nome: str, conteudo: str) -> None:
    caminho = DESTINO / nome
    caminho.write_text(conteudo, encoding="utf-8")
    print(f"gravado {caminho.relative_to(DESTINO.parent.parent.parent)} ({len(conteudo.encode()) // 1024} KB)")


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    cap = Capturador()

    cap.get(f"{BASE}/")
    if "__CBCanal" not in cap.cliente.cookies:
        raise SystemExit("Cookie de canal __CBCanal não foi emitido: o fluxo de sessão do Vip mudou?")
    print("sessão preparada: cookie __CBCanal obtido")

    primeira = cap.pesquisar(BUSCA_AMPLA, 1)
    gravar("busca_ampla_pagina_1.html", primeira)
    total = total_resultados(primeira)
    ultima_pagina = max(1, math.ceil(total / 12))
    print(f"busca ampla: {total} resultados, {ultima_pagina} páginas")

    if ultima_pagina > 1:
        gravar("busca_ampla_ultima_pagina.html", cap.pesquisar(BUSCA_AMPLA, ultima_pagina))

    gravar("busca_um_resultado.html", cap.pesquisar(UM_RESULTADO, 1))
    gravar("busca_zero_resultados.html", cap.pesquisar(ZERO_RESULTADOS, 1))

    (DESTINO / "LEIAME.md").write_text(
        "# Fixtures do Vip Leilões\n\n"
        f"Capturadas em {date.today().isoformat()} por `scripts/capturar_fixtures.py`.\n\n"
        "| Arquivo | Busca |\n|---|---|\n"
        f"| `busca_ampla_pagina_1.html` | procedencia=4, monta=1, página 1 ({total} resultados) |\n"
        f"| `busca_ampla_ultima_pagina.html` | mesma busca, página {ultima_pagina} (última) |\n"
        "| `busca_um_resultado.html` | marca=NISSAN, procedencia=4, monta=1 |\n"
        "| `busca_zero_resultados.html` | marca=GURGEL, procedencia=4, monta=1 |\n\n"
        "Os totais refletem o dia da captura. Os testes leem a estrutura, e não números exatos,\n"
        "exceto onde o próprio arquivo é a fonte (contagem de cards, total informado).\n",
        encoding="utf-8",
    )


# --- Claudio Kuss (feature 002; interfaces/claudio-kuss.md) ---------------------------------

KUSS = "https://www.claudiokussleiloes.com.br"
DESTINO_KUSS = DESTINO.parent / "claudio_kuss"
EVENTOS_KUSS = ("897", "898")  # eventos "Veículos - Financeiras" de 13/10 e 20/10/2026


def _sem_apelidos(lotes: list[dict]) -> list[dict]:
    """O apelido de quem deu lance é dado de pessoa e o bot não o lê."""
    return [{**lote, "usuario": "(removido)" if lote.get("usuario") else ""} for lote in lotes]


def main_kuss() -> None:
    DESTINO_KUSS.mkdir(parents=True, exist_ok=True)
    cap = Capturador()

    def post(caminho: str, dados: dict, referer: str) -> str:
        cap._esperar()
        resposta = cap.cliente.post(f"{KUSS}/{caminho}", data=dados,
                                    headers={"X-Requested-With": "XMLHttpRequest", "Referer": referer})
        resposta.raise_for_status()
        return resposta.text

    def gravar_kuss(nome: str, dados: object) -> None:
        caminho = DESTINO_KUSS / nome
        caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
        print(f"gravado tests/fixtures/claudio_kuss/{nome}")

    def lotes(evento: str, pagina: int, pesq: str = "") -> list[dict]:
        texto = post("json_edital.php", {"leilaoID": evento, "op": "P", "pag": str(pagina), "loteado": "",
                                         "pesq": pesq}, f"{KUSS}/relacao-foto/{evento}")
        return _sem_apelidos(json.loads(texto))

    quantidades = {}
    for evento in EVENTOS_KUSS:
        quantidades[evento] = json.loads(post("json_edital.php", {"op": "Q", "leilaoID": evento, "pesq": ""},
                                              f"{KUSS}/relacao-foto/{evento}"))
        gravar_kuss(f"quantidade_{evento}.json", quantidades[evento])

    fluence = lotes("897", 1, "FLUENCE")
    if not any(l["seq"] == "282622" for l in fluence):
        raise SystemExit("O Fluence 282622 não veio na busca por FLUENCE: o evento mudou?")
    gravar_kuss("lotes_897_fluence.json", fluence)

    com_lance = lotes("897", 1, "COMPASS")
    if not any(l["valor"] for l in com_lance):
        raise SystemExit("Nenhum lote com valor na busca por COMPASS: escolha outro modelo com lance (op=T).")
    gravar_kuss("lotes_897_com_lance.json", com_lance)

    ultima = int(quantidades["898"]["qtdePag"])
    gravar_kuss("lotes_898_ultima_pagina.json", lotes("898", ultima))

    detalhe = post("json_lance_info_lote.php", {"op": "D", "leilaoID": "897", "le_id": "282341", "loteado": "N"},
                   f"{KUSS}/lance/897/0/282341")
    gravar_kuss("detalhe_282341.json", json.loads(detalhe))


if __name__ == "__main__":
    main_kuss() if "--claudio-kuss" in sys.argv[1:] else main()
