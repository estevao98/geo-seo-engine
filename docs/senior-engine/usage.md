# Senior engine usage

Este documento descreve como instalar, rodar e interpretar a engine atual com seguranca. Ele cobre o comportamento implementado no codigo, nao capacidades futuras.

## Setup local

Requisitos:

- Python 3.12 ou superior para desenvolvimento local.
- Python 3.13 tambem deve ser suportado, pois e a versao usada no CI.
- Rede somente quando voce executar comandos que buscam URLs publicas.

Instalacao a partir da raiz do repositorio:

```bash
python -m pip install -e ".[dev]"
geo version
```

Em worktrees locais onde o pacote nao esta instalado, use `PYTHONPATH=src` para os comandos de modulo:

```bash
PYTHONPATH=src python -m geo_seo_engine.quality_gates
PYTHONPATH=src python -m pytest
```

## Configuracao de projeto

Crie um arquivo inicial seguro:

```bash
geo init
geo config validate --config geo-seo.yml
```

O arquivo `geo-seo.yml` deve conter apenas configuracao de escopo e politicas. Nao coloque tokens, credenciais, exports brutos ou dados privados nele.

## Comandos principais

Todos os comandos abaixo aceitam `--output PATH` quando documentado pelo help da CLI. Prefira caminhos temporarios, como `/tmp/...`, para artefatos gerados que nao devem ser versionados.

| Comando | Proposito | Exemplo de formato |
|---|---|---|
| `geo version` | Mostra a versao instalada. | `geo version` |
| `geo init` | Cria `geo-seo.yml` inicial. | `geo init --config geo-seo.yml` |
| `geo config validate` | Valida configuracao local. | `geo config validate --config geo-seo.yml` |
| `geo audit-page` | Audita uma pagina HTML publica. | `geo audit-page https://example.com --format json` |
| `geo audit-robots` | Audita um `robots.txt`. | `geo audit-robots https://example.com/robots.txt --format json` |
| `geo audit-sitemap` | Audita sitemap XML ou sitemap index. | `geo audit-sitemap https://example.com/sitemap.xml --format json` |
| `geo audit-site` | Agrega page, robots, sitemap e structured data. | `geo audit-site https://example.com --format markdown` |
| `geo crawl` | Faz crawl interno limitado e deterministico. | `geo crawl https://example.com --max-pages 25 --max-depth 2` |
| `geo inventory` | Resume URLs coletadas pelo crawl. | `geo inventory https://example.com --format json` |
| `geo audit-technical` | Emite findings tecnicos a partir de inventario crawleado. | `geo audit-technical https://example.com --format json` |
| `geo extract-content` | Extrai conteudo principal de paginas HTML crawleadas. | `geo extract-content https://example.com --format json` |
| `geo audit-content-quality` | Audita sinais deterministicos de qualidade de conteudo. | `geo audit-content-quality https://example.com --format json` |
| `geo audit-entity-readiness` | Audita sinais deterministicos de entidade, autoria, publisher e topicos. | `geo audit-entity-readiness https://example.com --format json` |
| `geo audit-internal-links` | Audita grafo de links internos a partir de crawl ou JSON local. | `geo audit-internal-links https://example.com --format json` |
| `geo audit-images` | Audita tags de imagem sem baixar os arquivos de imagem. | `geo audit-images https://example.com --format json` |
| `geo audit-social` | Audita Open Graph e Twitter/X metadata estaticos. | `geo audit-social https://example.com --format json` |
| `geo audit-hreflang` | Audita anotacoes `hreflang` estaticas. | `geo audit-hreflang https://example.com --format json` |
| `geo audit-rendering` | Compara HTML coletado com renderer configurado. | `geo audit-rendering https://example.com --renderer static --format json` |
| `geo audit-performance` | Audita JSON local estilo PageSpeed/Lighthouse, sem chamadas externas. | `geo audit-performance --input /tmp/pagespeed.json --format json` |
| `geo search-console-analytics` | Resume export local de Search Console, sem credenciais. | `geo search-console-analytics --input /tmp/gsc.csv --format json` |
| `geo opportunity` | Prioriza oportunidades a partir de JSON local agregado. | `geo opportunity --input /tmp/audits.json --format json` |
| `geo content-brief` | Gera briefs deterministicos a partir de JSON local. | `geo content-brief --input /tmp/audits.json --format json` |
| `geo content-cluster` | Planeja clusters deterministicos a partir de JSON local. | `geo content-cluster --input /tmp/planning.json --format json` |
| `geo ai-readiness` | Simula readiness local para experiencias generativas, sem promessa de presenca. | `geo ai-readiness --input /tmp/planning.json --format json` |
| `geo senior-report` | Gera dados de relatorio executivo e operacional a partir de JSON local. | `geo senior-report --input /tmp/planning.json --format json` |

## Como rodar com seguranca

- Use `--max-pages` e `--max-depth` baixos durante desenvolvimento.
- Use `--allowed-host` quando precisar limitar o escopo explicitamente.
- Use `--include-pattern` e `--exclude-pattern` para evitar areas privadas, parametros infinitos ou secoes irrelevantes.
- Grave outputs em `/tmp` ou outro diretorio fora do repositorio quando o resultado contiver dados reais.
- Nao rode crawls contra dominios de terceiros sem autorizacao e sem limites conservadores.
- Nao use exports reais de Search Console ou PageSpeed como fixtures versionadas.

## Como interpretar outputs

Os outputs JSON sao contratos de automacao e devem ser tratados como evidencias operacionais, nao como promessa de resultado de negocio.

Campos recorrentes:

- `score`: resumo heuristico. Leia junto com findings e evidencias.
- `issues` ou `findings`: lista de problemas detectados por regras deterministicas.
- `severity`: prioridade tecnica relativa, normalmente `critical`, `high`, `medium`, `low` ou `info` conforme o modelo.
- `evidence`: observacao que sustenta o finding.
- `risk`: impacto tecnico ou operacional esperado se o problema permanecer.
- `recommendation`: direcao de correcao.
- `next_action`: proxima acao concreta e revisavel.

Para relatorios Markdown, mantenha a mesma leitura: diagnostico, evidencia, risco, prioridade e proxima acao. Se nao houver evidencia suficiente, trate a saida como hipotese ou sinal fraco.

## Politica deterministica e sem claims externos

A engine atual nao faz afirmacoes externas sem dados locais fornecidos pelo operador. Ela nao promete trafego, ranking, indexacao, citacao, inclusao em respostas de IA ou crescimento organico garantido.

Modulos como `ai-readiness`, `entity-readiness`, `content-brief`, `content-cluster` e `senior-report` sao deterministicos e devem explicar readiness, lacunas, riscos e proximas acoes com base nos inputs locais. Nao invente fontes, metricas, cases, reviews, estatisticas ou credenciais de autoridade.

## Arquivos gerados

Outputs com nomes como `senior-report*.json`, `opportunity*.json`, `content-brief*.json`, `cluster*.json`, `ai-readiness*.json`, exports de Search Console e outputs de scanners sao bloqueados pelo quality gate quando rastreados pelo Git. Use `/tmp` para esses artefatos e revise `git status --short` antes de commitar.
