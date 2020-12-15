# cpp-participacao-backend

![CI](https://github.com/labhackercd/cpp-participacao-backend/workflows/CI/badge.svg)
[![codecov](https://codecov.io/gh/labhackercd/cpp-participacao-backend/branch/main/graph/badge.svg?token=3WWUKZYRKG)](https://codecov.io/gh/labhackercd/cpp-participacao-backend)
[![Maintainability](https://api.codeclimate.com/v1/badges/b0ec4f8434d42480a619/maintainability)](https://codeclimate.com/github/labhackercd/cpp-participacao-backend/maintainability)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=labhackercd_cpp-participacao-backend&metric=alert_status)](https://sonarcloud.io/dashboard?id=labhackercd_cpp-participacao-backend)

## Pré-requisitos
É necessário ter intalado os seguintes softwares:
* [Docker](https://docs.docker.com/engine/install/) versão 19.03.6
* [Docker-Compose](https://docs.docker.com/compose/install/) versão 1.25.5

Caso deseje alterar as variáveis de ambiente é necessário alterar as variáveis que estão no **docker_compose.yml**. É possível alterar as
seguintes variáveis:

```bash
POSTGRES_DB:
POSTGRES_USER:
POSTGRES_PASSWORD:
PGDATA:
SECRET_KEY:
DEBUG:
ALLOWED_HOSTS:
DATABASE_ENGINE:
HOST:
PORT:
REDIS_SERVER:
LANGUAGE_CODE:
TIME_ZONE:
USE_I18N:
USE_L10N:
USE_TZ:
STATIC_URL:
GA_SCOPE:
GA_KEY_LOCATION:
GA_ID_EDEMOCRACIA:
URL_PREFIX:
EDEMOCRACIA_URL:

```

## Comandos para executar o projeto
1. Clone o projeto
```bash
git clone https://github.com/labhackercd/cpp-participacao-backend.git
```
2. Entre dentro da pasta raiz do projeto
```bash
cd cpp-participacao-backend
```

3. Execute o comando para iniciar os containers 
```bash
sudo docker-compose up
```

**A API neste momento já vai estar rodando na porta 8000 do localhost.**

## Como rodar os testes do projeto
- Com os contaires(Passo 3) já em execução rode o comando:
```bash
sudo docker-compose exec backend sh -c "flake8 src && coverage run -m pytest src && coverage report"
```


## Documentação 

Devido a arquitetura escolhida pela equipe (com front e backend desacoplados entre si), e por uma questão de organização, o desenvolvimento deste projeto utilizou a metodologia ágil Scrum, e os documentos gerados podem ser acessados na nossa <a href="https://github.com/labhackercd/cpp-participacao-backend/wiki"> Wiki </a>

<hr>