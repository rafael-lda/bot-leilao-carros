# Certificados intermediários: o que são e o que fazer quando der alerta

> Feature de origem: `004-leiloeiro-freitas` (D-83 a D-85); cópia de `_reversa_forward/004-leiloeiro-freitas/runbook-certificado.md`
> Para: o Rafael ou um agente (Claude, Antigravity, Codex) que receber o alerta de certificado

Esta pasta guarda certificados **intermediários oficiais** que alguns leiloeiros esquecem de enviar (hoje: o do Freitas,
`globalsign-gcc-r6-alphassl-ca-2025.pem`, SHA-256 `A8:83:55:92:…:08:CA`, válido até 2027-05-21). O cliente HTTP do bot
confia no pacote `certifi` **mais** os `.pem` daqui, sempre com verificação completa.

## 1. Sintoma

- Telegram: "Alerta do sistema — **Freitas Leiloeiro**: ... **certificado** ..." (no máximo 1 por dia).
- Relatório da varredura, seção "Leiloeiros": `Freitas Leiloeiro | falha de acesso (certificado: www.freitasleiloeiro.com.br)`.
- Log: `coleta  | ... certificado: www.freitasleiloeiro.com.br`.

Os outros leiloeiros seguem normalmente. Nada se perde: os lotes do Freitas voltam a ser lidos assim que a conexão for corrigida (os que já eram conhecidos não são avisados de novo).

## 2. Regras que não mudam

1. **Nunca desligar a verificação** (`verify=False` ou equivalente), nem "só para o Freitas", nem "só por um dia". Um teste do projeto falha se isso aparecer no código.
2. **Só usar certificado intermediário baixado da própria autoridade certificadora**, pelo endereço que vem dentro do certificado do site (campo "CA Issuers"). Nunca de fórum, site de terceiros ou de dentro da página do leiloeiro.
3. A cadeia tem de terminar numa **raiz que já está no pacote `certifi`**. Guardar um intermediário não cria confiança nova: só completa um elo que o site esqueceu de enviar.

## 3. Diagnóstico (5 minutos)

Rodar no container (tem `openssl`) ou no Git Bash do Windows (que também tem).

```bash
# 3.1 O que o servidor envia hoje: "0 s:" é o certificado do site, "i:" quem o emitiu; "1 s:" é o intermediário enviado
echo | openssl s_client -connect www.freitasleiloeiro.com.br:443 -servername www.freitasleiloeiro.com.br -showcerts 2>/dev/null \
  | grep -E "^ ?[0-9] s:|^ +i:|Verify return"

# 3.2 Endereço oficial do intermediário que emitiu o certificado do site
echo | openssl s_client -connect www.freitasleiloeiro.com.br:443 -servername www.freitasleiloeiro.com.br 2>/dev/null \
  | openssl x509 -noout -text | grep "CA Issuers"

# 3.3 O que o bot tem guardado (nome, emissor e validade)
for f in src/bot_leilao/coleta/certificados/*.pem; do echo "== $f"; openssl x509 -in "$f" -noout -subject -issuer -enddate; done
```

Compare o emissor (`i:` da linha 0) com o `subject` dos arquivos guardados.

## 4. Qual caso é, e o que fazer

| Caso | Como reconhecer | O que fazer |
|------|-----------------|-------------|
| **A. O Freitas renovou e o emissor mudou** | O `i:` da linha 0 é diferente de todos os `subject` guardados | Seção 5 (guardar o novo intermediário) |
| **B. O intermediário guardado venceu** | `notAfter` do arquivo já passou (o atual vence em **2027-05-21**) | Normalmente o site já renovou antes e caiu no caso A; seguir a seção 5. Remover o arquivo vencido depois que o novo funcionar |
| **C. O Freitas corrigiu a cadeia** | `Verify return code: 0 (ok)` no comando 3.1 | Nada a fazer: o arquivo guardado não atrapalha. Se o alerta continuar, é outro caso |
| **D. Falta a raiz no `certifi`** | Mesmo com o intermediário certo, o erro continua; o `issuer` do intermediário é uma raiz que o `certifi` não conhece | Atualizar o pacote: `pip install -U certifi` (no venv do Windows e no container) e testar. Não acrescentar raiz à mão |
| **E. Problema do próprio certificado do site** | Erro de nome (`hostname mismatch`) ou certificado do site vencido (`notAfter` da linha 0) | É do Freitas: não há correção segura do nosso lado. Esperar; se passar de alguns dias, `ativo: false` no bloco do Freitas e reativar quando normalizar |

## 5. Guardar um intermediário novo (casos A e B)

```bash
# 5.1 Baixar do endereço "CA Issuers" obtido em 3.2 (exemplo do certificado de 2026)
curl -s -o novo.crt http://secure.globalsign.com/cacert/gsgccr6alphasslca2025.crt

# 5.2 Converter para PEM (os .crt da autoridade costumam vir em DER)
openssl x509 -inform DER -in novo.crt -out novo.pem 2>/dev/null || cp novo.crt novo.pem

# 5.3 Conferir: o subject tem de ser igual ao "i:" da linha 0; anotar emissor, validade e impressão digital
openssl x509 -in novo.pem -noout -subject -issuer -enddate -fingerprint -sha256

# 5.4 Testar a cadeia completa sem atalhos (deve terminar em "Verify return code: 0 (ok)")
python -c "import certifi; print(certifi.where())"   # caminho do pacote de raízes
cat "$(python -c 'import certifi; print(certifi.where())')" novo.pem > /tmp/teste-cadeia.pem
echo | openssl s_client -connect www.freitasleiloeiro.com.br:443 -servername www.freitasleiloeiro.com.br \
  -CAfile /tmp/teste-cadeia.pem 2>/dev/null | grep "Verify return"
```

Se deu `0 (ok)`:

1. Copiar `novo.pem` para `src/bot_leilao/coleta/certificados/` com nome descritivo (ex.: `globalsign-<nome-do-intermediario>-<ano>.pem`).
2. Rodar `pytest -q` e `python -m bot_leilao varrer --dry-run`; no log, o Freitas tem de aparecer lido ("ok: N lote(s) lido(s)").
3. Atualizar a impressão digital e a validade em `_reversa_forward/004-leiloeiro-freitas/interfaces/freitas.md` §1 e no item do `regression-watch.md` da feature.
4. Commit com a mensagem "Certificado: intermediário <nome> para <leiloeiro> (validade <data>)".

## 6. Outro leiloeiro com o mesmo problema

O procedimento é o mesmo, trocando o host. O bot confia nos intermediários da pasta para **todos** os hosts, então um arquivo serve a qualquer site emitido por aquele intermediário.
