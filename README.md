# CineReserve API

API REST para reserva de assentos e emissao de ingressos de cinema, com JWT, PostgreSQL, Redis, Celery e documentacao Swagger.

## Execucao rapida (um comando)

No diretorio do projeto, execute:

```bash
docker compose up --build
```

Pronto. A aplicacao sobe com migracoes automaticas.
As variaveis padrao ja estao em `.env.example`.

## URLs principais

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/api/docs/`
- Schema OpenAPI: `http://127.0.0.1:8000/api/schema/`
- Portal web de teste (My Portal): `http://127.0.0.1:8000/portal/`
- Flower (monitoramento Celery): `http://localhost:5555`

Tambem funciona com `http://0.0.0.0:8000`.

## O que o projeto cobre

- Cadastro e login com JWT
- Listagem paginada de filmes e sessoes
- Mapa de assentos por sessao
- Lock temporario de assento com Redis
- Checkout com geracao de ticket
- Portal `My Tickets` com filtros `active` e `history`
- Tarefas assincronas com Celery (limpeza de locks + email de confirmacao)

## Status dos requisitos tecnicos

- `TC.1 API Development`: atendido (Django + DRF, REST, Poetry no build Docker).
- `TC.2 JWT Authentication`: atendido (`register`, `login`, `refresh`, `verify`, `logout`, `profile`).
- `TC.3.1 Database`: atendido (PostgreSQL + migrations versionadas).
- `TC.3.2 Caching & Scalability`: atendido (Redis cache + lock de assento + cleanup periodico).
- `TC.4 Pagination`: atendido (paginacao obrigatoria nos endpoints de listagem via DRF).
- `TC.5 Testing`: atendido (suite automatizada de testes para auth, filmes, sessoes, reserva e tickets).
- `TC.6 Documentation`: atendido (Swagger/OpenAPI em `/api/docs/` e `/api/schema/`).
- `TC.7 Docker`: atendido (`Dockerfile` + `docker-compose.yaml` com stack completa).
- `TC.8 Git publico`: depende do repositorio remoto (nao e verificavel apenas pelo codigo local).

## Cobertura dos casos de uso no portal

O portal em `/portal/` cobre manualmente:

- `Caso 1`: cadastro e login (com refresh, verify e logout).
- `Caso 2`: listagem de filmes.
- `Caso 3`: listagem de sessoes por filme e listagem geral de sessoes.
- `Caso 4`: visualizacao de mapa de assentos por sessao.
- `Caso 5`: reserva e liberacao de assento (lock temporario).
- `Caso 6`: checkout de assento e criacao de ticket.
- `Caso 7`: consulta de "My Tickets" com filtros `active` e `history`.

Quando nao houver dados reais no banco, o portal mostra exemplos mockados para facilitar validacao visual.

## Como testar o portal web

1. Abra `http://127.0.0.1:8000/portal/`.
2. Use **Cadastro rapido** para criar usuario (se ainda nao existir).
3. Faca login e clique em **Carregar tickets** para ver `active` ou `history`.
4. Se necessario, use **Atualizar token** e **Sair**.

## Testes

Para rodar localmente (com ambiente Python configurado):

```bash
python manage.py test
```

Validacao de documentacao OpenAPI:

```bash
python manage.py spectacular --file /tmp/cinereserve-schema.yaml
```

## Postman

A colecao esta em:

- `docs/postman/CineReserve.postman_collection.json`

## CI/CD e deploy

Pipeline em `/.github/workflows/ci-cd.yml`:

- `test`: migra banco e executa testes com cobertura.
- `build`: gera imagem Docker e publica no GHCR (push em `main`/`develop`).
- `security`: roda `pip-audit` e `bandit`.
- `deploy`: somente em push na `main`, via SSH no servidor.

Secrets necessarios para deploy automatico:

- `DEPLOY_HOST`: IP ou dominio do servidor.
- `DEPLOY_USER`: usuario SSH.
- `DEPLOY_SSH_KEY`: chave privada SSH.
- `DEPLOY_PATH`: pasta no servidor com `docker-compose.yaml`.

Comandos esperados no servidor remoto (executados pelo workflow):

```bash
cd "$DEPLOY_PATH"
git fetch --all
git checkout main
git pull origin main
docker compose up -d --build --remove-orphans
```

Se os secrets nao estiverem configurados, o job de deploy e pulado com mensagem explicativa.

