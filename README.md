# Maritime Surveillance

Surveillance maritime en temps réel : ingestion AIS → Kafka → Prediction ML → Détection d'anomalies → Alertes

## Architecture

| Service | Port | Rôle |
|---|---|---|
| gateway | 8000 | Entry point, JWT validation, routing |
| ingestion | 8001 | Kafka consumer, vessel history |
| prediction | 8002 | ML trajectory & anomaly score |
| alert | 8003 | Intrusion/degassing detection |
| auth | 8004 | JWT tokens |
| users | 8005 | User CRUD |
| simulator | — | Mock/real AIS data generator |
| frontend | 4200 | Angular UI |

## Setup

**Requirements:** Python 3.13, Node.js 18+, Docker, PostgreSQL 17

```bash
# 1. Infrastructure
docker compose up -d

# 2. Python environment
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt

# 3. .env (root dir)
# INTERNAL_SECRET=dev-secret
# JWT_SECRET=dev-secret
# INGESTION_DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5433/ingestion_db
# PREDICTION_DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5433/prediction_db
# ALERT_DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5433/alert_db
# USERS_DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5433/users_db
# KAFKA_BOOTSTRAP_SERVERS=localhost:9092
# KAFKA_TOPIC=vessel-gps
# AISSTREAM_API_KEY=your-key

# 4. Create databases
psql -h localhost -p 5433 -U postgres -c "CREATE DATABASE ingestion_db; CREATE DATABASE prediction_db; CREATE DATABASE alert_db; CREATE DATABASE users_db;"

# 5. Enable extensions (alert_db)
psql -h localhost -p 5433 -U postgres -d alert_db -c "CREATE EXTENSION IF NOT EXISTS cube; CREATE EXTENSION IF NOT EXISTS earthdistance;"

# 6. Frontend
cd frontend && npm install

## Run

Activate venv then run each in separate terminal:

```bash
# Backend (6 terminals)
cd services/gateway && uvicorn main:app --reload --port 8000
cd services/ingestion && uvicorn main:app --reload --port 8001
cd services/prediction && uvicorn main:app --reload --port 8002
cd services/alert && uvicorn main:app --reload --port 8003
cd services/auth && uvicorn main:app --reload --port 8004
cd services/users && uvicorn main:app --reload --port 8005

# Simulator (optional)
cd services/simulator && python main_mock.py

# Frontend
cd frontend && ng serve
```

**Access:** http://localhost:4200

## API Endpoints

**Base URL:** `http://localhost:8000/api` (via Gateway)  
**Auth:** `Authorization: Bearer <token>` (except public routes)

| Method | Endpoint | Public | Description |
|---|---|---|---|
| POST | `/auth/login` |Get access_token + refresh_token |
| POST | `/auth/refresh` | Refresh expired token |
| POST | `/users/users` | Create account |
| GET | `/ingestion/vessels/{mmsi}/history` | Vessel position history |
| GET/PUT | `/ingestion/vessels/zone` |  Get/set simulation zone |
| POST | `/prediction/predict/{mmsi}` |  Run ML prediction |
| GET | `/alert/alerts` |  All alerts |
| GET | `/alert/alerts/{mmsi}` | Alerts for vessel |

**Swagger docs:** `http://localhost:PORT/docs`

## Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy 2.0
- **Database:** PostgreSQL 17 (database-per-service pattern)
- **ML:** Scikit-learn (Random Forest)
- **Messaging:** Apache Kafka
- **Auth:** JWT (python-jose), bcrypt
- **Frontend:** Angular, Leaflet
- **Orchestration:** Consul (optional)
