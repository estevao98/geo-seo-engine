# Política de segurança para MCPs

## Proibido

- Commitar `.env`.
- Commitar tokens.
- Commitar service accounts.
- Commitar exports reais de Search Console, Analytics ou dados de clientes.
- Habilitar MCPs com permissão de escrita em serviços externos sem revisão.
- Usar filesystem fora de diretórios necessários.
- Rodar comandos destrutivos via agente.

## Permitido

- Usar placeholders em `.env.example`.
- Usar dados sintéticos.
- Usar relatórios sem dados pessoais.
- Usar MCPs de leitura para pesquisa e auditoria.

## Revisão obrigatória

Antes de commit:

```bash
git status --short
git diff --stat
git diff --check
git ls-files | grep -E 'reports/raw|gitleaks.*json|detect-secrets.*json|semgrep.*json|bandit.*json|pip-audit.*json|zap-report|trivy.*json|grype.*json|terraform.tfstate|site_config.json|\.env'
```
