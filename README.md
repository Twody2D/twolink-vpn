# TwoLink VPN

Инфраструктура для продажи прокси/VPN-доступа (VLESS+Reality и Hysteria2 —
два независимых протокола на выбор клиента, Shadowsocks в резерве) через
Telegram-бота — **multi-node с одним центром управления**.

## Архитектура

- **Главный сервер** (2 vCPU / 2GB RAM) — единственный. PostgreSQL, FastAPI-бэкенд,
  Telegram-бот и **первая нода** (`is_local = true`) с Xray и Hysteria2.
  Локальная нода общается с бэкендом напрямую по внутренней docker-сети
  (Xray — gRPC push; Hysteria2 — live HTTP auth callback), без выхода наружу.
- **Удалённые pico-ноды** (1 vCPU / 1GB RAM каждая, добавляются по мере роста) —
  Xray + Hysteria2 + лёгкий `node-agent`. Никакой БД, никакого бэкенда. node-agent
  принимает REST-команды от главного сервера по HTTPS с авторизацией по
  API-ключу конкретной ноды.
- Xray и Hysteria2 устроены принципиально по-разному, поэтому у каждого —
  свой интерфейс:
  - `XrayClientInterface` (`backend/app/services/xray_client/`) — push-модель:
    `LocalXrayClient` (gRPC к Xray напрямую) и `RemoteXrayClient` (HTTPS к
    node-agent) кладут клиента в Xray заранее.
  - `HysteriaClientInterface` (`backend/app/services/hysteria_client/`) —
    Hysteria2 сам спрашивает бэкенд на каждое подключение (`auth.type: http`),
    поэтому `add_client`/`remove_client` не проталкивают ничего в сам
    Hysteria2-процесс, а лишь готовят место, где будет найден правильный
    ответ: `LocalHysteriaClient` — no-op (ответ и так живёт в БД бэкенда,
    её проверяет `POST /internal/hysteria/authenticate`), `RemoteHysteriaClient`
    пушит пароль в кэш node-agent'а, а Hysteria2 той же ноды спрашивает
    `node-agent`, а не бэкенд напрямую — так удалённая нода не бьёт по
    бэкенду на каждое подключение и не требует открывать бэкенд наружу.
  - Обе абстракции неразличимы для бизнес-логики — конкретная реализация
    подставляется по `node.is_local`.
- При создании подписки без явного `node_id` бэкенд сам выбирает активную
  ноду с наименьшим числом активных подписок (`app/services/node_selection.py`).
- `GET /sub/{token}` отдаёт для каждой активной ноды пользователя и
  `vless://`-, и `hysteria2://`-ссылку (если у ноды заполнены Hysteria2-поля) —
  клиент сам решает, каким протоколом пользоваться и переключается при блокировках.

## Стек

- **Xray-core** — VLESS+Reality (основной протокол) + Shadowsocks (резерв)
- **Hysteria2** — второй независимый протокол (QUIC/UDP, Brutal congestion
  control, Salamander-обфускация) — на случай если VLESS+Reality начнут
  блокировать по трафику, а не только по домену
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
│   ├── docker-compose.yml            # главный сервер: postgres, backend, bot, xray+hysteria (нода 1)
│   ├── docker-compose.node.yml       # удалённая нода: xray + hysteria + node-agent
│   ├── docker-compose.prod.yml       # override для прода (hardening, лимиты CPU)
│   └── docker-compose.monitoring.yml # опциональный профиль (не реализован)
├── xray/
│   ├── Dockerfile
│   └── config/                       # шаблоны, реальный config.json генерируется
├── hysteria/
│   ├── Dockerfile                    # бинарь скачивается и проверяется по SHA-256 при сборке
│   └── config/                       # шаблон; TLS-сертификат persisted на именованном volume
├── node-agent/                       # лёгкий FastAPI-сервис для удалённых нод
│   └── app/
│       └── services/
│           ├── xray.py               # gRPC к локальному Xray этой ноды
│           └── hysteria.py           # in-memory кэш паролей для локального Hysteria2 этой ноды
├── backend/                          # центральный FastAPI
│   ├── Dockerfile
│   ├── app/
│   │   └── services/
│   │       ├── xray_client/          # абстракция: local_client.py, remote_client.py
│   │       ├── hysteria_client/      # абстракция: local_client.py (no-op), remote_client.py
│   │       ├── node_agent_auth.py    # общий поиск API-ключа node-agent'а по node_id
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
- Hysteria2 — другой случай: он несёт реальный пользовательский трафик, а не
  только служебные вызовы node-agent'а, поэтому доверять самоподписанному
  сертификату вслепую (`insecure=1`) нельзя — MITM-риск реален. Вместо этого
  клиентские ссылки пиннят SHA-256 отпечаток сертификата (`pinSHA256`),
  который контейнер печатает один раз при первом старте
  (`hysteria/entrypoint.sh`) и который затем сохраняется на именованном
  volume (`hysteria-tls`) — сертификат не перегенерируется на каждом
  рестарте, иначе все выданные ссылки сломались бы разом.
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
   - `HYSTERIA_OBFS_PASSWORD` — сгенерировать заново
   - `HYSTERIA_CERT_FINGERPRINT` — оставить пустым на первый запуск (см. шаг 3)
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
   Контейнер `hysteria` при первом старте печатает в лог
   `Certificate SHA-256 fingerprint (pinSHA256): ...` — скопировать это
   значение в `.env` как `HYSTERIA_CERT_FINGERPRINT` и повторить
   `python -m app.seed`, иначе `hysteria2://`-ссылки не будут строиться
   (см. раздел безопасности — сертификат генерируется один раз и не
   перевыпускается сам).
4. Настроить обратный прокси (nginx/Caddy) с TLS (Let's Encrypt) перед
   `/sub/*`, если backend должен быть достижим извне для выдачи подписок —
   сам backend по-прежнему не публикует порт на хост.
5. Пройти чек-лист безопасности ОС ниже.

## Добавление новой pico-ноды

На **самой ноде**:

1. Установить Docker, склонировать репозиторий (нужны только `xray/`,
   `hysteria/`, `node-agent/`, `docker/docker-compose.node.yml`).
2. `cp node.env.example node.env`, заполнить:
   - `REALITY_PRIVATE_KEY`, `REALITY_SHORT_ID` — сгенерировать на этой ноде
     (`docker run --rm ghcr.io/xtls/xray-core:latest x25519`, `openssl rand -hex 4`)
   - `SHADOWSOCKS_PASSWORD` — сгенерировать
   - `HYSTERIA_OBFS_PASSWORD` — сгенерировать
   - `NODE_API_KEY` — сгенерировать (`openssl rand -base64 32`), это единственный
     раз, когда ключ существует в открытом виде вне `node.env` — передать
     оператору главного сервера по защищённому каналу (не в чат/тикет открытым текстом)
   - `ALLOWED_BACKEND_IPS` — публичный IP главного сервера
   - `NODE_AGENT_PORT` — порт, который увидит главный сервер снаружи
3. `cd docker && docker compose -p twolink-node --env-file ../node.env -f docker-compose.node.yml up -d --build`
4. Прочитать в логе `hysteria`-контейнера строку
   `Certificate SHA-256 fingerprint (pinSHA256): ...` — понадобится оператору
   главного сервера на шаге 6.
5. Настроить `ufw`, ограничив порт node-agent только IP главного сервера (см. чек-лист ниже).

На **главном сервере**:

6. Добавить ключ в `.env`: `NODE_AGENT_API_KEYS=<node_id>:<плейнтекст-ключ>,...` (дописать через запятую к существующим).
7. Зарегистрировать ноду в БД (пока без отдельного эндпоинта — прямой SQL,
   `api_key_hash` считается как `sha256(<ключ>)`):
   ```bash
   docker compose --env-file ../.env exec postgres psql -U twolink -d twolink -c "
   INSERT INTO nodes (node_id, name, host, vless_port, ss_port, xray_api_host, xray_api_port,
     reality_public_key, reality_short_id, reality_server_name,
     hysteria_port, hysteria_cert_fingerprint, hysteria_obfs_password,
     is_local, api_key_hash, agent_host, agent_port, status, is_active, created_at)
   VALUES ('node-2', 'pico-2', '<публичный IP ноды>', 443, 8388, 'unused', 0,
     '<REALITY_PUBLIC_KEY ноды>', '<REALITY_SHORT_ID ноды>', '<REALITY_SERVER_NAMES ноды>',
     <HYSTERIA_PORT ноды>, '<fingerprint из шага 4>', '<HYSTERIA_OBFS_PASSWORD ноды>',
     false, '<sha256 хэш ключа>', '<публичный IP ноды>', <NODE_AGENT_PORT>,
     'online', true, now());"
   ```
8. Перезапустить backend, чтобы подхватить новый `NODE_AGENT_API_KEYS`:
   `docker compose --env-file ../.env up -d backend`.

## Чек-лист безопасности ОС

Для **главного сервера** и **каждой ноды** отдельно:

- сменить порт SSH с 22 на нестандартный;
- отключить вход по паролю (только по ключу): `PasswordAuthentication no`;
- отключить root-логин по SSH: `PermitRootLogin no`;
- установить и настроить `fail2ban` для sshd;
- `ufw`:
  - главный сервер: разрешить SSH (свой порт), `XRAY_VLESS_PORT`,
    `XRAY_SS_PORT`, `HYSTERIA_PORT/udp`, порт HTTP/HTTPS если используется
    обратный прокси/ACME;
  - нода: разрешить SSH (свой порт), `XRAY_VLESS_PORT`, `XRAY_SS_PORT`,
    `HYSTERIA_PORT/udp`, и `NODE_AGENT_PORT` **только** с IP главного сервера:
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
13. ✅ Hysteria2 на локальной ноде — Docker-сервис, TLS-сертификат persisted
    через именованный volume
14. ✅ Схема БД + `HysteriaClientInterface` (`LocalHysteriaClient`/`RemoteHysteriaClient`)
15. ✅ `POST /internal/hysteria/authenticate` — live-проверка для локальной ноды
16. ✅ `GET /sub/{token}` отдаёт `hysteria2://`-ссылки с `pinSHA256` наравне с `vless://`
17. ✅ node-agent: `/hysteria/users` (push от бэкенда) + собственный
    `/hysteria/authenticate` для Hysteria2 удалённой ноды; `RemoteHysteriaClient`
18. ✅ README: раздел Hysteria2 (архитектура, `pinSHA256`, деплой)
