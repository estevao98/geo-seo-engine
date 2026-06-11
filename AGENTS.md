# AGENTS.md

## Objetivo do repositório

Este repositório implementa um sistema universal de SEO + GEO para auditar, planejar, gerar, validar e monitorar estratégias de crescimento orgânico para SaaS, micro SaaS, blogs, documentação, landing pages e sites institucionais.

GEO aqui significa otimização para mecanismos generativos e experiências de busca com IA, sem tratar isso como hack, manipulação ou promessa de tráfego garantido.

## Princípios obrigatórios

- Priorize conteúdo útil, original, verificável e orientado ao usuário.
- Não crie conteúdo em massa apenas para manipular rankings ou respostas de IA.
- Não invente dados, fontes, métricas, cases, reviews ou estatísticas.
- Separe fato, inferência, hipótese e recomendação.
- Não recomende técnicas black hat, PBN, spam, cloaking, doorway pages ou backlinks artificiais.
- Todo conteúdo deve ter intenção de busca, persona, entidade principal, entidades secundárias, links internos sugeridos e critérios de qualidade.
- Todo relatório deve conter diagnóstico, evidência, risco, prioridade e próxima ação.
- Para decisões técnicas, prefira documentação oficial e fontes primárias.
- Para informações recentes, use MCP de busca/fetch quando disponível.

## MCPs disponíveis

Use estes MCPs quando fizer sentido:

- `filesystem_geo`: ler/criar/editar arquivos dentro de `/home/estevao/Projetos`.
- `fetch`: buscar HTML, documentação, robots.txt, sitemap.xml e páginas públicas.
- `git_geo`: inspecionar status, diff, log e arquivos do repo.
- `playwright`: renderizar páginas, testar conteúdo com JavaScript e coletar evidência visual/técnica.
- `gh_grep`: pesquisar código público.

MCPs configurados mas desativados:

- `github`: só ativar com token e autorização explícita.
- `brave_search`: só ativar com API key e autorização explícita.
- `postgres`: só ativar com conexão local/segura e autorização explícita.

## Segurança

Nunca commitar:

- `.env`
- tokens
- service accounts
- credenciais
- exports brutos de Search Console
- exports brutos de Analytics
- dados reais de clientes
- logs de LLM com dados sensíveis
- dumps de banco
- relatórios privados
- `site_config.json`
- `terraform.tfstate`

Arquivos permitidos:

- `.env.example`
- exemplos sintéticos
- documentação sem segredo
- schemas
- templates
- prompts
- relatórios públicos ou anonimizados

## Comandos obrigatórios antes de finalizar alterações

Rode sempre:

```bash
git status --short
git diff --stat
git diff --check
```

Para revisão grande:

```bash
{ echo "===== STATUS ====="; git status --short; echo; echo "===== DIFF STAT ====="; git diff --stat; echo; echo "===== DIFF CHECK ====="; git diff --check; echo; echo "===== LOG ====="; git log --oneline --decorate -10; } > /tmp/revisao.txt 2>&1; featherpad /tmp/revisao.txt &
```

Para checar arquivos sensíveis:

```bash
git ls-files | grep -E 'reports/raw|gitleaks.*json|detect-secrets.*json|semgrep.*json|bandit.*json|pip-audit.*json|zap-report|trivy.*json|grype.*json|terraform.tfstate|site_config.json|\.env$|\.env\.'
```

## Definition of Done

Uma tarefa só está pronta quando:

* os arquivos foram criados/alterados no local correto;
* o markdown está legível;
* JSON/YAML gerados estão válidos;
* não há segredos;
* os riscos foram documentados;
* `git diff --check` não aponta erro;
* foi indicado o que ficou pronto, o que ficou pendente e o que depende de API externa.

## Estilo de entrega

* Trabalhe em chunks pequenos.
* Prefira diffs pequenos.
* Explique decisões técnicas relevantes.
* Não faça commit sem autorização explícita.
* Não faça push sem autorização explícita.
* Não use comandos destrutivos sem diagnóstico e autorização.
