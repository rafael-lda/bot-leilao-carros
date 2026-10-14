"""Roteamento das requisições pelo nível de coleta (feature 005; roadmap D-87).

O `Coletor` e o enriquecimento carimbam em cada `Requisicao` o `nivel_coleta` do leiloeiro; este cliente entrega
a requisição ao cliente daquele nível (`script` → `ClienteHTTP`, `apify` → `ClienteApify`). Um leiloeiro em
`apify` nunca sai pelo IP local.
"""

from __future__ import annotations

from collections.abc import Mapping

from bot_leilao.coleta.modelos import Requisicao, ResultadoHTTP


class ClienteRoteado:
    def __init__(self, clientes: Mapping[str, object]) -> None:
        self.clientes = dict(clientes)

    def requisitar(self, requisicao: Requisicao) -> ResultadoHTTP:
        cliente = self.clientes.get(requisicao.nivel)
        if cliente is None:
            raise ValueError(f"nenhum cliente para o nível de coleta '{requisicao.nivel}' nesta varredura")
        return cliente.requisitar(requisicao)

    @property
    def cookies(self):
        return self.clientes["script"].cookies

    @property
    def tentativas(self) -> int:
        return self.clientes["script"].tentativas

    def tentativas_de(self, nivel: str) -> int:
        """Máximo de tentativas do cliente daquele nível (para o log do coletor: o Apify tenta 2 vezes)."""
        return self.clientes.get(nivel, self.clientes["script"]).tentativas

    def fechar(self) -> None:
        for cliente in self.clientes.values():
            cliente.fechar()
