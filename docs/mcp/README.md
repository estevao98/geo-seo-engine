# MCPs do geo-seo-engine

Este diretório documenta os MCPs usados pelo projeto.

## MCPs ativos

- `filesystem_geo`: acesso restrito a `/home/estevao/Projetos`.
- `fetch`: busca páginas, HTML, robots.txt, sitemap.xml e documentação.
- `git_geo`: inspeção Git do repositório `geo-seo-engine`.
- `playwright`: navegação/renderização de páginas com browser.
- `gh_grep`: busca em código público via MCP remoto.

## MCPs desativados

- `github`: exige `GITHUB_PERSONAL_ACCESS_TOKEN`.
- `brave_search`: exige `BRAVE_API_KEY`.
- `postgres`: exige `POSTGRES_URL`.

## Regras

- Não commitar tokens.
- Não colocar chaves reais no `opencode.json`.
- Usar variáveis de ambiente.
- Não habilitar MCPs que escrevem em serviços externos sem revisão.
- Não dar acesso filesystem fora de diretórios necessários.
