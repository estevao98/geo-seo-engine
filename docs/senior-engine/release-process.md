# Release process

Este processo descreve como preparar um release local ou uma PR de release sem adicionar automacao de deploy.

## Principios de release

- Release e documentacao, codigo e validacao reproduzivel; nao e promessa de ranking, trafego ou visibilidade em IA.
- Cada release deve separar fato, inferencia, hipotese e recomendacao.
- Nenhum release deve incluir segredos, `.env` real, dados privados de clientes, exports brutos ou grandes artefatos gerados.
- O estado final deve passar nos mesmos gates essenciais do CI.

## Checklist antes de alterar

1. Confirme o escopo da issue atual.
2. Leia `README.md`, `CONTRIBUTING.md`, `SECURITY.md` e os documentos relevantes em `docs/senior-engine/`.
3. Verifique a arvore de trabalho:

```bash
git status --short
```

4. Se houver mudancas nao relacionadas feitas por outra pessoa, preserve-as e limite seu diff ao escopo da issue.

## Checklist de implementacao

1. Atualize os documentos no menor conjunto de arquivos possivel.
2. Garanta que comandos documentados existem na CLI ou no CI.
3. Use exemplos com dominios neutros, como `https://example.com`, ou caminhos temporarios em `/tmp`.
4. Nao adicione outputs reais da ferramenta como JSON versionado, exceto exemplos sinteticos explicitamente seguros.
5. Documente riscos restantes e dependencias externas quando existirem.

## Gates locais obrigatorios

Rode da raiz do worktree:

```bash
git status --short
git diff --stat
git diff --check
PYTHONPATH=src python -m geo_seo_engine.quality_gates
PYTHONPATH=src python -m pytest
```

Se estiver usando o virtualenv compartilhado do repositorio principal, a forma equivalente e:

```bash
PYTHONPATH=src ~/Projetos/geo-seo-engine/.venv/bin/python -m geo_seo_engine.quality_gates
PYTHONPATH=src ~/Projetos/geo-seo-engine/.venv/bin/python -m pytest
```

Antes de commit, execute tambem a checagem explicita de nomes sensiveis:

```bash
git ls-files | grep -E '__pycache__|\.pyc$|reports/raw|site-audit-example.json|robots-audit-example.json|sitemap-audit-google.json|page-audit-example.json|gitleaks.*json|detect-secrets.*json|semgrep.*json|bandit.*json|pip-audit.*json|zap-report|trivy.*json|grype.*json|terraform.tfstate|site_config.json|\.env$|\.env\.|egg-info' || true
```

A saida esperada para essa ultima checagem e vazia.

## CI documentado

O workflow `.github/workflows/ci.yml` roda em push para `master` e em pull requests. O job principal usa Ubuntu e Python 3.13.

Etapas atuais:

1. Checkout com historico suficiente para diff.
2. Setup de Python 3.13 com cache de pip.
3. Instalacao editavel com dependencias de desenvolvimento: `python -m pip install -e ".[dev]"`.
4. Smoke check de import publico: `import geo_seo_engine` e import da CLI.
5. Smoke check da CLI: `geo version`.
6. Higiene de whitespace/diff com `git diff --check` ou `git diff-tree --check`.
7. Guard de arquivos gerados e sensiveis (`Generated and sensitive file guard`): `python -m geo_seo_engine.quality_gates`.
8. Suite de testes: `python -m pytest`.

## Politica de arquivos seguros

Permitido versionar:

- Codigo fonte em `src/`.
- Testes e fixtures sinteticas em `tests/`.
- Documentacao em Markdown.
- Exemplos sem segredos e sem dados reais.
- `.env.example` com valores vazios ou sinteticos.

Nao permitido versionar:

- `.env` ou `.env.*` reais.
- Tokens, service accounts, credenciais ou dumps de banco.
- `site_config.json`.
- `terraform.tfstate`.
- `reports/raw`.
- Exports brutos de Search Console ou Analytics.
- Outputs de scanners como `gitleaks*.json`, `detect-secrets*.json`, `semgrep*.json`, `bandit*.json`, `pip-audit*.json`, `trivy*.json`, `grype*.json` ou `zap-report*`.
- JSONs gerados por comandos de planejamento ou relatorio quando contiverem dados reais.

## Commit local

Faca commit somente depois de todos os gates passarem e o diff estar revisado:

```bash
git status --short
git diff --stat
git diff --check
git add README.md CONTRIBUTING.md docs/senior-engine tests
git commit -m "docs: document release process"
```

Nao faca push, nao feche issue e nao atualize epic sem autorizacao explicita.

## Pos-release

Depois do push autorizado, acompanhe o CI em `master` ou na PR e registre qualquer falha como follow-up com evidencia, comando, ambiente e proxima acao. Se a falha envolver segredo ou arquivo privado, remova o artefato com o processo de seguranca adequado antes de prosseguir.
