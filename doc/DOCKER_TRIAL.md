# Docker Trial Run

這份文件提供最短路徑，讓你直接用 Docker 啟動 `Fixture-M Lite Web + API + migration bootstrap + MySQL`。

## 1. 前置條件

- 已安裝 Docker Desktop
- 在專案根目錄執行指令（目前目錄有 `docker-compose.yml`）

## 2. 啟動方式

1. 複製環境檔：

```powershell
Copy-Item .env.example .env
```

2. 啟動容器：

```powershell
docker compose up --build -d
```

3. 檢查狀態：

```powershell
docker compose ps
```

4. 查看 API log：

```powershell
docker compose logs -f api
```

5. 查看前端/Nginx log：

```powershell
docker compose logs -f web
```

## 3. 服務位址

- Web App (Vue + Nginx): `http://localhost:${WEB_HOST_PORT}`（預設 `8080`）
- API Health (direct): `http://localhost:${API_HOST_PORT}/health`（預設 `8010`）
- Swagger (direct): `http://localhost:${API_HOST_PORT}/docs`（預設 `8010`）
- API via Nginx: `http://localhost:${WEB_HOST_PORT}/api/v2/*`（預設 `8080`）
- MySQL Host: `localhost:${DB_HOST_PORT}`（預設 `3309`）

## 4. 資料庫連線資訊

連線值由 `.env` 提供；`.env.example` 的資料庫名稱與帳號範例為：

- DB: `fixture_m_lite`
- User: `fixture_user`
- Password: 必須在 `MYSQL_PASSWORD` 設定，沒有可直接使用的提交預設值
- Root Password: 必須在 `MYSQL_ROOT_PASSWORD` 設定，沒有可直接使用的提交預設值

SQLAlchemy 連線字串：

```text
mysql+pymysql://fixture_user:replace-app-password@db:3306/fixture_m_lite?charset=utf8mb4
```

從你的電腦連 MySQL（例如 DBeaver / DataGrip）：

- Host: `127.0.0.1`
- Port: `3309`（或你在 `.env` 設定的 `DB_HOST_PORT`）
- User: `fixture_user`
- Password: 你在 `.env` 的 `MYSQL_PASSWORD` 設定值
- Database: `fixture_m_lite`

## 5. 環境變數說明

`backend/app/core/config.py` 會依序使用：

1. `DATABASE_URL`（最高優先）
2. `DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME`
3. 若都沒給，退回 SQLite：`sqlite:///./fixture_m_lite.db`

API launcher 另支援：

- `UVICORN_RELOAD`：Docker 範例預設 `0`；只有本機開發需要檔案監看時才設為 `1`
- `UVICORN_WORKERS`：reload 關閉時的 worker 數，預設 `1`；調高前需依主機 CPU、記憶體與資料庫連線上限評估

## 6. 停止與清理

停止：

```powershell
docker compose down
```

連同資料庫資料卷一起刪除：

```powershell
docker compose down -v
```

## 7. 常見問題

- API 起不來：先看 `docker compose logs -f api` 是否為 DB 連線字串錯誤。
- DB 密碼改了：請同步更新 `.env` 的 `DATABASE_URL`（或 DB_* 變數）與 `docker-compose.yml` 的 MySQL 使用者設定。
- API `8010` host port 衝突：把 `.env` 的 `API_HOST_PORT` 改成其他值（例如 `8011`）後重啟；容器內仍使用 `8000`。
- Web `8080` port 衝突：把 `.env` 的 `WEB_HOST_PORT` 改成其他值（例如 `8080`、`8081`）後重啟。
- DB `3306`/`3307`/`3308` 衝突：把 `.env` 的 `DB_HOST_PORT` 改成其他值（例如 `3309`、`3310`）後重啟。
