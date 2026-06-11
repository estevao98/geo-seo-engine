# Security

## Princípios

- Não commitar segredos.
- Não salvar credenciais reais no repositório.
- Não versionar exports brutos com dados sensíveis.
- Usar dados sintéticos em exemplos.
- Separar dados brutos de relatórios públicos.

## Arquivos proibidos

- `.env`
- tokens
- credentials
- service accounts
- dumps de banco
- exports privados
- relatórios raw
- `terraform.tfstate`
- `site_config.json`

## Antes de commit

```bash
git status --short
git diff --stat
git diff --check
git ls-files | grep -E 'reports/raw|gitleaks.*json|detect-secrets.*json|semgrep.*json|bandit.*json|pip-audit.*json|zap-report|trivy.*json|grype.*json|terraform.tfstate|site_config.json|\.env$|\.env\.'
```
