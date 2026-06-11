# schema_validator_server

Status: planned

## Objetivo

MCP customizado planejado para o geo-seo-engine.

## Ferramentas previstas

* A definir no schema correspondente em `mcp/schemas/`.

## Permissões

* Leitura por padrão.
* Escrita apenas se explicitamente necessária.
* Nenhuma credencial real deve ser salva no repositório.

## Variáveis de ambiente

A definir conforme a integração.

## Riscos

* Vazamento de dados.
* Uso excessivo de API.
* Exposição de relatórios privados.
* Escrita acidental em serviço externo.

## Próximos passos

1. Definir input schema.
2. Definir output schema.
3. Criar implementação mínima.
4. Criar testes.
5. Adicionar logs seguros.
6. Documentar limites e rate limits.
