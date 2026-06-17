# Maintenance and handoff

Este documento e o handoff para mantenedores que vao evoluir a senior engine sem quebrar a fundacao existente.

## Como os modulos se encaixam

Fluxo operacional principal:

```text
config -> http -> crawler -> inventory -> audits -> opportunities -> planning -> readiness -> senior report
```

Responsabilidades atuais:

| Modulo | Papel |
|---|---|
| `core` | Modelos compartilhados, severidade, evidencia e utilitarios de URL. |
| `config` | Carrega e valida `geo-seo.yml`; nao deve fazer rede. |
| `http` | Cliente HTTP centralizado com limites, timeout, redirects e politica de hosts privados. |
| `crawler` | Descoberta interna limitada por host, profundidade, pagina e padroes include/exclude. |
| `inventory` | Resume paginas crawleadas sem refazer requests. |
| `technical` | Converte inventario em findings tecnicos. |
| `analyzers` | Auditores legados de page, robots, sitemap, structured data e site agregado. |
| `content` | Extrai conteudo principal de HTML coletado. |
| `content_quality` | Avalia sinais deterministicos de utilidade e cobertura. |
| `entity_readiness` | Avalia sinais deterministicos de entidade, autoria, publisher e topicos. |
| `internal_links` | Analisa grafo de links internos. |
| `images`, `social`, `i18n` | Auditam imagens, metadados sociais e `hreflang` a partir de HTML estatico. |
| `rendering` | Compara HTML inicial e renderizado quando um renderer explicito esta disponivel. |
| `performance` | Importa payload local PageSpeed/Lighthouse e audita sem chamada externa. |
| `search_console` | Importa export local de Search Console sem credenciais. |
| `opportunities` | Converte diagnosticos e dados locais em backlog priorizado. |
| `content_briefs` | Gera briefs deterministicos com base em inputs locais. |
| `content_clusters` | Planeja clusters auditaveis. |
| `ai_readiness` | Simula readiness heuristico para experiencias generativas sem prometer inclusao. |
| `senior_report` | Agrega resumo executivo, operacional, riscos e proximas acoes. |
| `quality_gates` | Bloqueia arquivos gerados ou sensiveis rastreados pelo Git. |
| `cli` | Orquestra comandos publicos e serializacao de outputs. |

## Boundaries de manutencao

- `core` deve permanecer puro e sem rede.
- `config` valida shape e escopo, mas nao deve buscar recursos externos.
- `inventory`, `technical`, `opportunities`, `content_briefs`, `content_clusters`, `ai_readiness` e `senior_report` devem operar sobre dados ja fornecidos.
- Comandos que crawleiam devem manter limites explicitos e defaults conservadores.
- Integracoes externas devem ser opcionais, testaveis com fixtures locais e claras sobre ausencia de credenciais ou dados.

## Troubleshooting local

| Sintoma | Diagnostico provavel | Proxima acao |
|---|---|---|
| `ModuleNotFoundError: geo_seo_engine` | Pacote nao instalado no worktree. | Rode `python -m pip install -e ".[dev]"` ou prefixe com `PYTHONPATH=src`. |
| `geo: command not found` | Entry point nao instalado no ambiente ativo. | Ative o virtualenv correto e rode instalacao editavel. |
| `git diff --check` falha | Whitespace, trailing spaces ou conflito de marcadores. | Corrija o arquivo indicado e rode o comando novamente. |
| `quality_gates` falha | Arquivo gerado/sensivel rastreado pelo Git. | Remova do controle de versao ou mova para `/tmp`; nao remova arquivos de terceiros sem coordenar. |
| Teste tenta acessar rede real | Fixture ou fake client ausente. | Use HTML sintetico, fake HTTP client ou `httpx.MockTransport`. |
| `audit-rendering` sai com erro usando renderer default | Nenhum renderer JS real esta configurado. | Use `--renderer static` para modo de teste ou integre renderer explicito em feature futura. |
| Crawl sai do escopo esperado | Host ou padroes insuficientes. | Use `--allowed-host`, `--include-pattern`, `--exclude-pattern`, `--max-pages` e `--max-depth`. |
| Output privado aparece em `git status` | Caminho de output dentro do repo. | Gere novamente em `/tmp` e remova o artefato do controle de versao se ele tiver sido adicionado. |

## Politica de novas features

Antes de adicionar uma nova camada, responda:

1. Qual input local ou externo ela consome?
2. Ela faz rede? Se sim, passa pelo cliente HTTP seguro ou por interface mockavel?
3. Qual modelo tipado representa o output?
4. Cada finding tem diagnostico, evidencia, risco, prioridade e proxima acao?
5. Como a ausencia de dados ou credenciais aparece no output?
6. Quais fixtures sinteticas cobrem o comportamento?
7. O output pode conter dados privados? Se sim, qual e a politica de arquivo seguro?

## Politica de claims

Nao adicione textos ou outputs que prometam:

- crescimento de trafego;
- ranking;
- indexacao;
- citacao por IA;
- inclusao em mecanismos generativos;
- ROI ou impacto numerico sem dados verificaveis.

Use formulacoes como diagnostico, risco, sinal, hipotese, recomendacao e proxima acao. Quando a confianca for limitada, documente a limitacao.

## Handoff para proximos mantenedores

- Preserve a CLI publica e seus outputs JSON sempre que possivel.
- Se um contrato JSON precisar mudar, atualize testes, exemplos e documentacao no mesmo diff.
- Mantenha fixtures pequenas, sinteticas e sem dados reais.
- Prefira regras deterministicas e explicaveis antes de qualquer dependencia de LLM ou API externa.
- Documente qualquer dependencia externa como opcional e falivel.
- Rode os gates locais completos antes de commit.
