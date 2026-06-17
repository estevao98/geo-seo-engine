# Contributing

## Fluxo

1. Criar uma branch pequena.
2. Fazer alterações em chunks.
3. Rodar validações.
4. Revisar diff.
5. Só commitar depois de revisão.

## Antes de finalizar

```bash
git status --short
git diff --stat
git diff --check
python -m geo_seo_engine.quality_gates
python -m pytest
```

O guardrail `python -m geo_seo_engine.quality_gates` falha quando arquivos gerados,
exports privados, caches, `.env` reais ou outputs de scanners aparecem como arquivos
versionados. A exceção permitida é `.env.example`, que deve conter apenas nomes de
variáveis e valores vazios ou sintéticos.

Para releases, documentação de handoff ou mudanças de maior escopo, siga também
[`docs/senior-engine/release-process.md`](docs/senior-engine/release-process.md) e
[`docs/senior-engine/maintenance.md`](docs/senior-engine/maintenance.md).

## Padrões

* Markdown claro.
* JSON/YAML válido.
* Sem segredos.
* Sem dados reais.
* Sem promessas não verificáveis.

## Arquivos que nao devem ser commitados

* `.env` ou `.env.*` reais.
* Tokens, service accounts, credenciais e dumps.
* `site_config.json` e `terraform.tfstate`.
* `reports/raw`.
* Exports brutos de Search Console, Analytics ou clientes.
* Outputs de scanners como `gitleaks*.json`, `detect-secrets*.json`, `semgrep*.json`, `bandit*.json`, `pip-audit*.json`, `trivy*.json`, `grype*.json` ou `zap-report*`.
* JSONs gerados por relatorios, oportunidades, briefs, clusters ou simulacoes quando contiverem dados reais.
