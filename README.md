# Arrematex

Sistema web para gestao de leiloes pecuarios, com frontend em React/Vite e backend em Django.

## Tecnologias

- React 18 + Vite
- TypeScript
- Tailwind CSS
- Zustand
- Django 5
- Django REST Framework
- PostgreSQL
- Redis
- Celery
- Docker Compose

## Estrutura

```text
backend/              API Django, apps, migrations e configuracoes
frontend/             Aplicacao React/Vite
infra/nginx/          Configuracao Nginx
docker-compose.yml    Ambiente de producao/container
docker-compose.dev.yml Ambiente de desenvolvimento
```

## Rodando o frontend

```powershell
cd frontend
npm install
npm run dev
```

Por padrao o Vite usa a porta definida em `frontend/vite.config.ts`. Se a porta estiver ocupada, ele escolhe a proxima disponivel.

## Rodando o projeto completo com Docker

Crie um arquivo `.env` na raiz do projeto com as variaveis necessarias. O arquivo `.env` local nao e versionado.

Depois execute:

```powershell
docker compose -f docker-compose.dev.yml up --build
```

Acessos esperados:

- Frontend: `http://localhost:3000` ou porta indicada pelo Vite
- Backend: `http://localhost:8000`

## Preparando o backend

Com os containers rodando:

```powershell
docker compose -f docker-compose.dev.yml exec backend python manage.py migrate_schemas --shared
docker compose -f docker-compose.dev.yml exec backend python manage.py setup_dev
docker compose -f docker-compose.dev.yml exec backend python manage.py createsuperuser
```

Depois use o email e senha criados no `createsuperuser` para acessar o sistema.

## Login demo

Enquanto o backend nao estiver rodando, o frontend possui um login local de demonstracao:

```text
E-mail: admin@arrematex.com.br
Senha: Admin12345
```

Esse login libera o painel no navegador, mas dados reais dependem da API Django, PostgreSQL e Redis.

## Build do frontend

```powershell
cd frontend
npm run build
```

## Observacoes

- `.env`, `node_modules`, `dist`, logs e caches ficam fora do Git pelo `.gitignore`.
- O backend foi preparado para rodar com Docker, PostgreSQL e Redis.
- Para login real em producao ou homologacao, crie usuarios pelo backend/Django.
