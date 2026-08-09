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
Affiche l'état (healthy/unhealthy) de tous les microservices enregistrés.

## Endpoints principaux (via la gateway)

Toutes les requêtes passent par `http://localhost:8000/api/{service}/...`, avec le header `Authorization: Bearer <token>` (sauf routes publiques).

### Authentification (public)

| Méthode | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/login` | Connexion, retourne access_token + refresh_token |
| POST | `/api/auth/refresh` | Renouvelle un access_token |
| POST | `/api/users/users` | Création de compte (public) |

### Ingestion

| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/api/ingestion/vessels/{mmsi}/history` | Historique récent d'un navire |
| GET | `/api/ingestion/vessels/zone` | Zone de simulation active |
| PUT | `/api/ingestion/vessels/zone` | Met à jour la zone de simulation |

### Prédiction

| Méthode | Endpoint | Description |
|---|---|---|
| POST | `/api/prediction/predict/{mmsi}` | Lance une prédiction pour un navire |
| GET | `/api/prediction/predictions/{mmsi}` | Historique des prédictions |

### Alertes

| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/api/alert/alerts` | Toutes les alertes récentes |
| GET | `/api/alert/alerts/zone?lat=<lat>&lon=<lon>` | Alertes de la zone protégée la plus proche |
| GET | `/api/alert/alerts/{mmsi}` | Alertes pour un navire spécifique |

## Tests

Une collection Postman est utilisée pour valider chaque endpoint (login → predict → alert). Voir le dossier `docs/postman/` si exporté.

## Stack technique

- **Backend** : Python, FastAPI, SQLAlchemy 2.0, psycopg
- **ML** : Scikit-learn (Random Forest multi-output)
- **Messagerie** : Apache Kafka
- **Base de données** : PostgreSQL 17 (pattern database-per-service)
- **Auth** : JWT (python-jose), bcrypt
- **Frontend** : Angular, Leaflet + Leaflet.draw
- **Supervision** : Consul
