# TwoLink VPN

Инфраструктура для продажи прокси/VPN-доступа (VLESS+Reality, Shadowsocks в
резерве) через Telegram-бота — **multi-node с одним центром управления**.

## Архитектура

- **Главный сервер** (2 vCPU / 2GB RAM) — единственный. PostgreSQL, FastAPI-бэкенд,
  Telegram-бот и **первая Xray-нода** (`is_local = true`). Локальная нода
  общается с бэкендом напрямую по внутренней docker-сети (gRPC), без выхода наружу.
- **Удалённые pico-ноды** (1 vCPU / 1GB RAM каждая, добавляются по мере роста) —
  только Xray + лёгкий `node-agent`. Никакой БД, никакого бэкенда. node-agent
  принимает REST-команды от главного сервера по HTTPS с авторизацией по
  API-ключу конкретной ноды.
- Бэкенд обращается к любой ноде через единый интерфейс `XrayClientInterface`
  (`backend/app/services/xray_client/`) — `LocalXrayClient` (gRPC к Xray
  напрямую) и `RemoteXrayClient` (HTTPS к node-agent) неразличимы для
  бизнес-логики.
- При создании подписки без явного `node_id` бэкенд сам выбирает активную
  ноду с наименьшим числом активных подписок (`app/services/node_selection.py`).

## Стек

- **Xray-core** — VLESS+Reality (основной протокол) + Shadowsocks (резерв)
- **node-agent** — лёгкий FastAPI-сервис на каждой удалённой ноде
- **FastAPI** — центральный бэкенд: пользователи/ноды, subscription-ссылки
- **PostgreSQL** — пользователи, подписки, ноды, лимиты трафика
- **aiogram** — Telegram-бот
- **Docker Compose** — оркестрация; отдельный compose для главного сервера
  и минимальный — для нод
- **Prometheus + Grafana** — мониторинг (опциональный профиль, не реализован)

## Окружения

| | Локальная разработка | Прод (главный сервер) |
|---|---|---|
| Хост | Ubuntu VM (VMware Workstation) | Ubuntu VPS (2 vCPU / 2GB RAM / 60GB SSD) |
| Конфигурация | `docker-compose.yml` | `docker-compose.yml` + `docker-compose.prod.yml` |
| Отличия | через `.env` | через `.env` |

Перенос с VM на VPS не требует изменений кода — только `.env`.

## Структура репозитория

```text
twolink/
├── docker/
│   ├── docker-compose.yml            # главный сервер: postgres, backend, bot, xray (нода 1)
│   ├── docker-compose.node.yml       # удалённая нода: xray + node-agent
│   ├── docker-compose.prod.yml       # override для прода (hardening, лимиты CPU)
│   └── docker-compose.monitoring.yml # опциональный профиль (не реализован)
├── xray/
│   ├── Dockerfile
│   └── config/                       # шаблоны, реальный config.json генерируется
├── node-agent/                       # лёгкий FastAPI-сервис для удалённых нод
├── backend/                          # центральный FastAPI
│   ├── Dockerfile
│   ├── app/
│   │   └── services/
│   │       ├── xray_client/          # абстракция: local_client.py, remote_client.py
│   │       └── node_selection.py     # выбор наименее загруженной ноды
│   └── alembic/                      # миграции БД
├── bot/                               # aiogram
│   ├── Dockerfile
│   └── app/
├── .env.example                       # для главного сервера
├── node.env.example                   # для удалённых нод
├── .gitignore
└── README.md
```

## Быстрый старт (локальная разработка, главный сервер)

```bash
cp .env.example .env
# заполнить .env реальными значениями для локальной разработки
cd docker
docker compose up -d
docker compose exec backend python -m app.seed   # регистрирует локальную ноду
```

## Безопасность — обязательные принципы

- Секреты только в `.env` (не в git, не в коде). В репозиторий коммитится
  только `.env.example`/`node.env.example` с плейсхолдерами.
- Все контейнеры работают от непривилегированного пользователя; в проде
  (`docker-compose.prod.yml`) — ещё и `read_only` корневая ФС + `no-new-privileges`.
- На главном сервере наружу смотрят только: Xray-порт, порт бота (если
  вебхук), порт для Let's Encrypt. PostgreSQL и FastAPI-бэкенд — только во
  внутренней docker-сети.
- На удалённых нодах наружу смотрят только Xray-порт и порт node-agent;
  node-agent проверяет IP-адрес источника (allowlist) и API-ключ ноды —
  двойная защита.
- API-ключ каждой ноды уникален; в БД хранится только его SHA-256 хэш
  (`api_key_hash`). Сам ключ живёт только в `.env` главного сервера
  (`NODE_AGENT_API_KEYS`) и в `node.env` самой ноды — никогда в БД, никогда в git.
- node-agent на текущем этапе обслуживает HTTPS с самоподписанным
  сертификатом, генерируемым при старте контейнера (`verify=False` на
  клиенте). **Для прода это нужно заменить** на нормальный сертификат
  (например, через внутренний CA) или mTLS — самоподписанный сертификат
  допустим только для старта/тестирования.
- Reality-ключи генерируются локально (`xray x25519`) для каждой ноды
  отдельно, никогда не хардкодятся и не коммитятся.
- Внутренний API-ключ разделяет бота и бэкенд; бэкенд не публикуется в
  интернет напрямую в проде.
- Токены подписок — криптографически случайные (`secrets.token_urlsafe`),
  не последовательные ID; rate-limit на `/sub/{token}` (20 req/min).

## Масштабируемость

- Таблица `nodes`: `node_id`, `is_local`, `api_key_hash`, `agent_host`,
  `agent_port`, `status`, `max_users` — с самого начала рассчитана на
  произвольное число нод.
- Подписки ссылаются на `node_id` — привязка пользователя к конкретной ноде.
- Бэкенд обращается к Xray через `XrayClientInterface`, не хардкодит
  `localhost` — конкретная реализация (локальная/удалённая) подставляется
  по `node.is_local`.
- Subscription-эндпоинт отдаёт конфиги для всех активных нод пользователя,
  а не для одной захардкоженной.

---

## Перенос главного сервера на прод VPS

1. На VPS: установить Docker (`curl -fsSL https://get.docker.com | sudo sh`),
   клонировать репозиторий.
2. `cp .env.example .env`, заполнить реальными значениями:
   - `ENVIRONMENT=production`
   - `POSTGRES_PASSWORD` — сгенерировать (`openssl rand -base64 32`)
   - `BACKEND_INTERNAL_API_KEY` — сгенерировать
   - `BOT_TOKEN` — от @BotFather
   - `NODE_HOST` — публичный IP/домен VPS
   - `REALITY_*` — сгенерировать заново на VPS (`docker run --rm ghcr.io/xtls/xray-core:latest x25519`),
     **не переносить с dev-окружения**
   - `SHADOWSOCKS_PASSWORD` — сгенерировать заново
   - `PUBLIC_BASE_URL` — публичный домен, под которым будет отвечать `/sub/*`
   - `NODE_AGENT_API_KEYS` — пусто, пока нет удалённых нод
3. Запуск прод-профиля:
   ```bash
   cd docker
   docker compose --env-file ../.env -f docker-compose.yml -f docker-compose.prod.yml up -d --build
   docker compose --env-file ../.env -f docker-compose.yml -f docker-compose.prod.yml \
     run --rm --no-deps backend alembic upgrade head
   docker compose --env-file ../.env -f docker-compose.yml -f docker-compose.prod.yml \
     exec backend python -m app.seed
   ```
4. Настроить обратный прокси (nginx/Caddy) с TLS (Let's Encrypt) перед
   `/sub/*`, если backend должен быть достижим извне для выдачи подписок —
   сам backend по-прежнему не публикует порт на хост.
5. Пройти чек-лист безопасности ОС ниже.

## Добавление новой pico-ноды

На **самой ноде**:

1. Установить Docker, склонировать репозиторий (нужны только `xray/`,
   `node-agent/`, `docker/docker-compose.node.yml`).
2. `cp node.env.example node.env`, заполнить:
   - `REALITY_PRIVATE_KEY`, `REALITY_SHORT_ID` — сгенерировать на этой ноде
     (`docker run --rm ghcr.io/xtls/xray-core:latest x25519`, `openssl rand -hex 4`)
   - `SHADOWSOCKS_PASSWORD` — сгенерировать
   - `NODE_API_KEY` — сгенерировать (`openssl rand -base64 32`), это единственный
     раз, когда ключ существует в открытом виде вне `node.env` — передать
     оператору главного сервера по защищённому каналу (не в чат/тикет открытым текстом)
   - `ALLOWED_BACKEND_IPS` — публичный IP главного сервера
   - `NODE_AGENT_PORT` — порт, который увидит главный сервер снаружи
3. `cd docker && docker compose -p twolink-node --env-file ../node.env -f docker-compose.node.yml up -d --build`
4. Настроить `ufw`, ограничив порт node-agent только IP главного сервера (см. чек-лист ниже).

На **главном сервере**:

5. Добавить ключ в `.env`: `NODE_AGENT_API_KEYS=<node_id>:<плейнтекст-ключ>,...` (дописать через запятую к существующим).
6. Зарегистрировать ноду в БД (пока без отдельного эндпоинта — прямой SQL,
   `api_key_hash` считается как `sha256(<ключ>)`):
   ```bash
   docker compose --env-file ../.env exec postgres psql -U twolink -d twolink -c "
   INSERT INTO nodes (node_id, name, host, vless_port, ss_port, xray_api_host, xray_api_port,
     reality_public_key, reality_short_id, reality_server_name,
     is_local, api_key_hash, agent_host, agent_port, status, is_active, created_at)
   VALUES ('node-2', 'pico-2', '<публичный IP ноды>', 443, 8388, 'unused', 0,
     '<REALITY_PUBLIC_KEY ноды>', '<REALITY_SHORT_ID ноды>', '<REALITY_SERVER_NAMES ноды>',
     false, '<sha256 хэш ключа>', '<публичный IP ноды>', <NODE_AGENT_PORT>,
     'online', true, now());"
   ```
7. Перезапустить backend, чтобы подхватить новый `NODE_AGENT_API_KEYS`:
   `docker compose --env-file ../.env up -d backend`.

## Чек-лист безопасности ОС

Для **главного сервера** и **каждой ноды** отдельно:

- сменить порт SSH с 22 на нестандартный;
- отключить вход по паролю (только по ключу): `PasswordAuthentication no`;
- отключить root-логин по SSH: `PermitRootLogin no`;
- установить и настроить `fail2ban` для sshd;
- `ufw`:
  - главный сервер: разрешить SSH (свой порт), `XRAY_VLESS_PORT`,
    `XRAY_SS_PORT`, порт HTTP/HTTPS если используется обратный прокси/ACME;
  - нода: разрешить SSH (свой порт), `XRAY_VLESS_PORT`, `XRAY_SS_PORT`, и
    `NODE_AGENT_PORT` **только** с IP главного сервера:
    ```bash
    ufw allow from <IP главного сервера> to any port <NODE_AGENT_PORT> proto tcp
    ```
- автоматические обновления безопасности ОС (`unattended-upgrades`);
- регулярный бэкап `postgres-data` (главный сервер) — вне зоны ответственности
  этой инфраструктуры на данном этапе, но обязателен перед реальным запуском.

## Roadmap

1. ✅ Инициализация репозитория
2. ✅ Docker-сеть и PostgreSQL
3. ✅ Xray-core (Reality) + генерация ключей
4. ✅ FastAPI: модели, миграции, health-check
5. ✅ Управление Xray-пользователями через `XrayClientInterface`
6. ✅ Subscription-эндпоинт (rate-limited, под список нод)
7. ✅ Telegram-бот (базовый каркас, заглушка оплаты)
8. ✅ Интеграция бота с бэкендом через внутренний API-ключ
9. ✅ node-agent: приём команд по HTTPS с проверкой API-ключа и IP, метрики
10. ✅ `RemoteXrayClient` (HTTPS к node-agent) + выбор наименее загруженной ноды
11. ✅ `docker-compose.prod.yml` — hardening для прода главного сервера
12. ✅ README: перенос на прод, добавление pico-ноды, чек-лист безопасности ОС
