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

## Padrões

* Markdown claro.
* JSON/YAML válido.
* Sem segredos.
* Sem dados reais.
* Sem promessas não verificáveis.
