# MCPs configurados

| MCP | Status | Tipo | Comando/URL | Precisa token? | Variável env | Risco | Uso |
|---|---|---|---|---|---|---|---|
| filesystem_geo | ativo | local | `npx -y @modelcontextprotocol/server-filesystem /home/estevao/Projetos` | não | — | acesso a arquivos em `~/Projetos` | ler/criar docs, configs, scripts e relatórios |
| fetch | ativo | local | `uvx mcp-server-fetch` | não | — | busca conteúdo externo | ler páginas, robots, sitemap e docs |
| git_geo | ativo | local | `uvx mcp-server-git --repository /home/estevao/Projetos/geo-seo-engine` | não | — | operações Git locais | inspecionar status, log e diff |
| playwright | ativo | local | `npx -y @playwright/mcp` | não | — | navegação web automatizada | renderizar páginas e testar conteúdo JS |
| gh_grep | ativo | remoto | `https://mcp.grep.app` | não | — | consulta remota | pesquisar código público |
| github | desativado | local | `npx -y @modelcontextprotocol/server-github` | sim | `GITHUB_PERSONAL_ACCESS_TOKEN` | acesso à conta GitHub | issues, PRs, repositórios |
| brave_search | desativado | local | `npx -y @modelcontextprotocol/server-brave-search` | sim | `BRAVE_API_KEY` | pesquisa web externa | pesquisa profunda |
| postgres | desativado | local | `npx -y @modelcontextprotocol/server-postgres {env:POSTGRES_URL}` | sim | `POSTGRES_URL` | acesso a banco | consultas estruturadas |
