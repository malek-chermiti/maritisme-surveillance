# Maritime Surveillance

Système de surveillance maritime basé sur une architecture microservices (Python/FastAPI) avec ingestion temps réel via Kafka, prédiction ML des trajectoires, détection d'anomalies (intrusion/dégazage), et interface Angular.

## Architecture
### Services

| Service | Port | Rôle |
|---|---|---|
| `gateway` | 8000 | Point d'entrée unique, validation JWT, routage |
| `ingestion` | 8001 | Ingestion des positions AIS via Kafka, gestion de la zone de simulation |
| `prediction` | 8002 | Prédiction de trajectoire (Random Forest) et score d'anomalie |
| `alert` | 8003 | Évaluation des prédictions, détection intrusion/dégazage |
| `auth` | 8004 | Login, validation et rafraîchissement des tokens JWT |
| `users` | 8005 | CRUD des utilisateurs |
| `simulator` | — | Scripts standalone (mock + réel) publiant sur Kafka |
| `frontend` | 4200 | Interface Angular (carte, dessin de zone, alertes) |

## Prérequis

- Python 3.13
- Node.js + npm
- Angular CLI (`npm install -g @angular/cli`)
- PostgreSQL 17
- Apache Kafka + Zookeeper (via Docker Compose)
- Consul (optionnel, supervision des services)
- Docker Desktop

## Installation

### 1. Infrastructure (Kafka, Zookeeper, Consul)

```bash
docker compose up -d
```

### 2. Environnement Python

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### 3. Variables d'environnement

Crée un fichier `.env` à la racine du projet :

```env
INTERNAL_SECRET=<secret partagé entre tous les services>
JWT_SECRET=<secret de signature JWT>

INGESTION_DATABASE_URL=postgresql+psycopg://postgres:<password>@localhost:5433/ingestion_db
PREDICTION_DATABASE_URL=postgresql+psycopg://postgres:<password>@localhost:5433/prediction_db
ALERT_DATABASE_URL=postgresql+psycopg://postgres:<password>@localhost:5433/alert_db
USERS_DATABASE_URL=postgresql+psycopg://postgres:<password>@localhost:5433/users_db

KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=vessel-gps

INGESTION_SERVICE_URL=http://localhost:8001
ALERT_SERVICE_URL=http://localhost:8003
USERS_SERVICE_URL=http://localhost:8005

AISSTREAM_API_KEY=<clé API AISStream.io>
```

### 4. Bases de données

Crée les 4 bases PostgreSQL (`ingestion_db`, `prediction_db`, `alert_db`, `users_db`) et exécute les scripts SQL de création de tables (voir `docs/schema.sql` si présent, sinon se référer au diagramme de classe du projet).

Active les extensions PostgreSQL requises sur `alert_db` :

```sql
CREATE EXTENSION IF NOT EXISTS cube;
CREATE EXTENSION IF NOT EXISTS earthdistance;
```

### 5. Frontend

```bash
cd frontend
npm install
```

## Démarrage

Chaque service tourne dans son propre terminal, avec le même environnement virtuel activé.

### Backend

```bash
# Terminal 1 — gateway
cd services/gateway
uvicorn main:app --reload --port 8000

# Terminal 2 — ingestion
cd services/ingestion
uvicorn main:app --reload --port 8001

# Terminal 3 — prediction
cd services/prediction
uvicorn main:app --reload --port 8002

# Terminal 4 — alert
cd services/alert
uvicorn main:app --reload --port 8003

# Terminal 5 — auth
cd services/auth
uvicorn main:app --reload --port 8004

# Terminal 6 — users
cd services/users
uvicorn main:app --reload --port 8005
```

### Simulateur (données de test)

```bash
# Données synthétiques (mock)
cd services/simulator
python main_mock.py

# OU données AIS réelles (AISStream.io)
python main_real.py
```

### Frontend

```bash
cd frontend
ng serve
```

Accès : `http://localhost:4200`

## Supervision (Consul)
