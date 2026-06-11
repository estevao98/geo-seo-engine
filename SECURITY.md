# Security

## Política de segredos

- Não commitar segredos.
- Não salvar credenciais reais, tokens, chaves privadas ou service accounts no repositório.
- Não versionar exports brutos com dados sensíveis.
- Usar dados sintéticos em exemplos.
- Separar dados brutos de relatórios públicos.
- Manter `.env.example` somente com nomes de variáveis e valores vazios ou sintéticos.
- Configurar credenciais reais apenas via ambiente local, gerenciador de segredos ou configuração fora do Git.

## Como reportar problemas

Reporte vulnerabilidades, segredos commitados por engano ou exposição de dados privados por uma issue privada/segura no GitHub quando disponível. Se isso não estiver disponível, abra uma issue pública sem incluir o segredo, dado privado, token, URL interna ou payload sensível; descreva apenas o impacto, o arquivo afetado e uma forma segura de contato.

Ao reportar, inclua:

- arquivo ou área afetada;
- tipo de risco;
- evidência mínima sem expor segredo real;
- recomendação de mitigação, se conhecida.

## Arquivos proibidos

- `.env`
- `.env.*`, exceto `.env.example`
- tokens e credenciais reais
- chaves privadas, certificados e arquivos `*.pem`, `*.key`, `*.p12`, `*.pfx`
- service accounts
- dumps de banco e arquivos locais como `*.sqlite`, `*.sqlite3`, `*.db`, `*.duckdb`
- exports privados de Search Console, Analytics, CRM ou clientes
- relatórios raw ou privados em `reports/`, `reports/raw/` ou `exports/`
- outputs brutos de scanners como `gitleaks*.json`, `detect-secrets*.json`, `semgrep*.json`, `bandit*.json`, `pip-audit*.json`, `trivy*.json`, `grype*.json` e `zap-report*`
- `terraform.tfstate`
- `site_config.json`

## Varredura antes de publicar

Antes de tornar o repositório público, abrir PR ou fechar uma release, rode no mínimo:

```bash
git status --short
git diff --stat
git diff --check
python -m pytest
git ls-files | grep -E 'reports/raw|site-audit-example.json|robots-audit-example.json|sitemap-audit-google.json|page-audit-example.json|gitleaks.*json|detect-secrets.*json|semgrep.*json|bandit.*json|pip-audit.*json|zap-report|trivy.*json|grype.*json|terraform.tfstate|site_config.json|\.env$|\.env\.|egg-info' || true
grep -RniE 'api[_-]?key|token|secret|password|passwd|credential|bearer|private[_-]?key' . --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__ || true
```

Resultados esperados:

- nenhum segredo real encontrado;
- nenhum artefato sensível rastreado;
- `.env.example` pode aparecer na varredura por conter nomes de variáveis, mas seus valores devem permanecer vazios ou sintéticos;
- falsos positivos em documentação devem ser revisados manualmente antes de publicar.
