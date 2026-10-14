"""Captura páginas reais dos leiloeiros para os testes dos parsers e dos adaptadores.

Uso (rede necessária, cerca de 30 segundos cada):

    python scripts/capturar_fixtures.py                  # Vip Leilões
    python scripts/capturar_fixtures.py --claudio-kuss   # Claudio Kuss Leilões
    python scripts/capturar_fixtures.py --copart         # Copart (busca pública em JSON)
    python scripts/capturar_fixtures.py --freitas        # Freitas Leiloeiro (busca pública em HTML)
    python scripts/capturar_fixtures.py --milan          # Milan Leilões, pelo Apify (custa ~US$ 0,24)

Grava em tests/fixtures/<leiloeiro>/. Respeita a mesma conduta do coletor: sessão com
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

    for seq, nome in (("282341", "detalhe_282341.json"), ("282327", "detalhe_282327_sucata.json")):
        detalhe = post("json_lance_info_lote.php", {"op": "D", "leilaoID": "897", "le_id": seq, "loteado": "N"},
                       f"{KUSS}/lance/897/0/{seq}")
        gravar_kuss(nome, json.loads(detalhe))


# --- Copart (feature 003; interfaces/copart-busca.md) -------------------------------------------

COPART = "https://www.copart.com.br"
DESTINO_COPART = DESTINO.parent / "copart"
CABECALHOS_COPART = {"Accept": "application/json, text/javascript, */*; q=0.01", "X-Requested-With": "XMLHttpRequest",
                     "Origin": COPART, "Referer": f"{COPART}/vehicleFinderSearch"}


def main_copart() -> None:
    DESTINO_COPART.mkdir(parents=True, exist_ok=True)
    cap = Capturador()
    cap.get(f"{COPART}/vehicleFinderSearch")

    def buscar(condicao: str, pagina: int) -> dict:
        cap._esperar()
        resposta = cap.cliente.post(f"{COPART}/public/vehicleFinder/search", headers=CABECALHOS_COPART, data={
            "query": "*", "filter[condicao]": f'condicao:"{condicao}"', "sort": "lot_number asc",
            "page": str(pagina), "size": "100", "start": str(pagina * 100)})
        resposta.raise_for_status()
        dados = resposta.json()
        for lote in dados["data"]["results"]["content"]:
            if lote.get("currentHighBidder"):
                lote["currentHighBidder"] = 999999  # cadastro de quem deu o lance: dado de terceiro, não lido
        return dados

    def gravar_copart(nome: str, dados: dict) -> None:
        (DESTINO_COPART / nome).write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
        print(f"gravado tests/fixtures/copart/{nome}")

    primeira = buscar("FINANCIAMENTO", 0)
    gravar_copart("busca_pag00.json", primeira)
    total = primeira["data"]["results"]["totalElements"]
    gravar_copart("busca_ultima.json", buscar("FINANCIAMENTO", max(0, math.ceil(total / 100) - 1)))
    gravar_copart("busca_zero.json", buscar("INEXISTENTE", 0))
    print(f"financiamento: {total} lotes. lotes_selecionados.json é composto à mão (ver amostras da feature 003).")


# --- Freitas Leiloeiro (feature 004; interfaces/freitas.md) ----------------------------------------

FREITAS = "https://www.freitasleiloeiro.com.br"
DESTINO_FREITAS = DESTINO.parent / "freitas"
CERTIFICADOS = Path(__file__).resolve().parent.parent / "src" / "bot_leilao" / "coleta" / "certificados"
PARAMETROS_FREITAS = {"Nome": "", "Categoria": "1", "TipoLoteId": "0", "FaixaValor": "0", "Condicao": "inteiros",
                      "PatioId": "0", "AnoModeloMin": "0", "AnoModeloMax": "0", "ArCondicionado": "false",
                      "DirecaoAssistida": "false", "Tag": "", "Estado": "", "Cidade": "", "ClienteSclId": "0",
                      "TopRows": "200"}


def main_freitas() -> None:
    """O servidor do Freitas envia o intermediário errado: a cadeia é completada com os .pem oficiais da pasta
    de certificados do bot (D-83). A verificação nunca é desligada."""
    import ssl

    import certifi

    DESTINO_FREITAS.mkdir(parents=True, exist_ok=True)
    contexto = ssl.create_default_context(cafile=certifi.where())
    for pem in sorted(CERTIFICADOS.glob("*.pem")):
        contexto.load_verify_locations(str(pem))
    cap = Capturador()
    cap.cliente = httpx.Client(headers=CABECALHOS, follow_redirects=True, max_redirects=3, timeout=60.0, verify=contexto)
    cabecalhos = {"X-Requested-With": "XMLHttpRequest", "Referer": f"{FREITAS}/Leiloes/Pesquisar?query=&categoria=1"}

    def gravar_freitas(nome: str, conteudo: str) -> None:
        (DESTINO_FREITAS / nome).write_text(conteudo, encoding="utf-8")
        print(f"gravado tests/fixtures/freitas/{nome} ({len(conteudo.encode()) // 1024} KB)")

    pagina, primeira_com_lotes = 1, ""
    while True:
        cap._esperar()
        resposta = cap.cliente.get(f"{FREITAS}/Leiloes/PesquisarLotes", headers=cabecalhos,
                                   params={**PARAMETROS_FREITAS, "PageNumber": str(pagina)})
        resposta.raise_for_status()
        if "Nenhum lote localizado" in resposta.text:
            gravar_freitas("lotes_fim.html", resposta.text)
            break
        primeira_com_lotes = primeira_com_lotes or resposta.text
        if pagina == 2:
            gravar_freitas("lotes_pag2.html", resposta.text)
        pagina += 1
    lote = re.search(r"leilaoId=(\d+)&loteNumero=(\d+)", primeira_com_lotes)
    if lote:
        detalhe = cap.get(f"{FREITAS}/Leiloes/LoteDetalhes?leilaoId={lote.group(1)}&loteNumero={lote.group(2)}")
        gravar_freitas(f"detalhe_{lote.group(1)}_{lote.group(2)}.html", detalhe.text)
    print("cards_selecionados.html é composto à mão (ver amostras da feature 004).")


# --- Milan Leilões (feature 005; interfaces/milan.md e interfaces/apify.md) ----------------------------

MILAN = "https://milanleiloes.com.br"
DESTINO_MILAN = DESTINO.parent / "milan"
ATOR_MILAN = "neatrat~cloudflare-scraper"
PRECO_PAGINA_USD = 0.08


def _anonimizar_milan(item: dict) -> dict:
    """Mesmo tratamento das amostras: sem cookies (cf_clearance e rastreadores) e sem apelidos de licitantes."""
    item = dict(item)
    item.pop("cookies", None)
    item["content"] = re.sub(r'([^\s<>"\\*])\*{3,}([^\s<>"\\*])', "U*****1", item.get("content") or "")
    return item


def main_milan() -> None:
    """O site inteiro está atrás do Cloudflare: as páginas vêm pelo ator do Apify, com o token do .env."""
    from dotenv import dotenv_values

    raiz = Path(__file__).resolve().parent.parent
    token = (dotenv_values(raiz / ".env").get("APIFY_TOKEN") or "").strip()
    if not token:
        raise SystemExit("APIFY_TOKEN ausente no .env.")
    print(f"Serão 3 páginas pelo Apify, cerca de US$ {3 * PRECO_PAGINA_USD:.2f}. Ctrl+C em 5 s para cancelar.")
    time.sleep(5)
    DESTINO_MILAN.mkdir(parents=True, exist_ok=True)
    cliente = httpx.Client(timeout=240.0, headers={"Authorization": f"Bearer {token}"})

    def pagina(url: str) -> dict:
        resposta = cliente.post(f"https://api.apify.com/v2/acts/{ATOR_MILAN}/run-sync-get-dataset-items",
                                params={"timeout": "180"}, json={"url": url})
        resposta.raise_for_status()
        (item,) = resposta.json()
        if item.get("status") != 200:
            raise SystemExit(f"{url}: status {item.get('status')} (desafio não resolvido?)")
        return _anonimizar_milan(item)

    def gravar_milan(nome: str, item: dict) -> None:
        texto = json.dumps([item], ensure_ascii=False)
        (DESTINO_MILAN / nome).write_text(texto, encoding="utf-8")
        print(f"gravado tests/fixtures/milan/{nome} ({len(texto.encode()) // 1024} KB)")

    agenda = pagina(f"{MILAN}/agenda/veiculos")
    gravar_milan("agenda.json", agenda)
    leilao = next((m.group(1) for m in re.finditer(r'href="/leilao/veiculos/(\d+)"[^>]*>(?:(?!</a>).)*?RECUPERADOS DE '
                                                   r"FINANCIAMENTO", agenda["content"], re.S)), None)
    if leilao is None:
        print("Nenhum leilão 'recuperados de financiamento' na agenda hoje; só a agenda foi gravada.")
        return
    catalogo = pagina(f"{MILAN}/leilao/{leilao}/catalogo")
    gravar_milan(f"catalogo_{leilao}.json", catalogo)
    numero = re.search(r"Lote\s+(\d{3}[A-Z]?)", catalogo["content"])
    if numero:
        gravar_milan(f"lote_{numero.group(1)}.json", pagina(f"{MILAN}/leilao/{leilao}/lote/{numero.group(1)}"))
    print("Os testes usam os nomes da captura de 2026-10-13 (catalogo_15618.json, lote_001/046/209.json); "
          "ajuste-os se trocar as fixtures.")


if __name__ == "__main__":
    if "--claudio-kuss" in sys.argv[1:]:
        main_kuss()
    elif "--copart" in sys.argv[1:]:
        main_copart()
    elif "--freitas" in sys.argv[1:]:
        main_freitas()
    elif "--milan" in sys.argv[1:]:
        main_milan()
    else:
        main()
