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

## Prédiction et détection des intrusions

La détection d'intrusion est effectuée par le **service d'alertes** (`services/alert`), et non par le modèle de prédiction. Le modèle estime une position future du navire et un score d'anomalie ; le service d'alertes utilise ensuite ces résultats pour décider s'il faut créer une alerte.

1. Le frontend récupère les navires présents dans la zone dessinée sur la carte et demande une prédiction pour chacun.
2. Le service de prédiction récupère les trois positions les plus récentes du navire depuis le service d'ingestion : latitude, longitude, vitesse et cap.
3. Le modèle Random Forest prédit la latitude et la longitude futures ainsi qu'un score d'anomalie entre 0 et 1. Il est entraîné sur le jeu de données synthétique de `services/prediction/training`.
4. Le service de prédiction enregistre le résultat et l'envoie au service d'alertes.
5. Le service d'alertes vérifie si la position prédite est une intrusion :
   - Si une zone de simulation active est disponible, il vérifie si la position prédite se trouve dans son rectangle. Si elle est à l'extérieur, l'évaluation s'arrête et aucune alerte n'est créée.
   - Sinon, il recherche la zone protégée la plus proche et compare la distance entre cette zone et la position prédite à son rayon.
6. Le service considère qu'il y a une anomalie lorsque le score est supérieur ou égal à `0.5`. Il crée une alerte pour une intrusion, une anomalie, ou les deux ; sinon, aucune alerte n'est enregistrée. Les alertes enregistrées sont ensuite chargées et affichées dans le panneau latéral de la carte.

| Résultat de l'évaluation | Raison | Niveau renvoyé par le service |
|---|---|---|
| Intrusion et anomalie | `LES_DEUX` | `CRITICAL` |
| Intrusion seule | `INTRUSION` | `MEDIUM` |
| Anomalie seule | `DEGAZAGE` | `MEDIUM` |
| Aucun critère détecté | Aucune alerte créée | `LOW` |

**À garder en tête :** le score d'anomalie est produit par un modèle entraîné sur des trajectoires synthétiques ; il ne représente pas nécessairement une probabilité validée sur des données réelles. Par ailleurs, le service renvoie le niveau `MEDIUM` pour une intrusion ou une anomalie isolée, alors que la contrainte définie dans le modèle de base de données autorise `NORMAL`, `WARNING` et `CRITICAL`. Vérifiez la contrainte de la base utilisée si ces alertes ne sont pas enregistrées.

## Prompt pour générer une image de l'architecture

Copiez ce prompt dans Claude :

```text
Crée une image claire et professionnelle qui représente l'architecture de l'application « Maritime Surveillance », une application de surveillance maritime. Fais un diagramme d'architecture horizontal au format 16:9, avec des blocs distincts, des flèches directionnelles, des libellés lisibles en français et un style moderne sobre (fond clair, bleu marine et turquoise). N'ajoute aucun composant qui n'est pas décrit ci-dessous.

Composants et flux à représenter :

- Utilisateur → Frontend Angular + Leaflet (port 4200) : affichage de la carte, dessin d'une zone rectangulaire et consultation des alertes.
- Frontend → API Gateway FastAPI (port 8000) : point d'entrée de l'API, validation des JWT et routage des requêtes vers les microservices.
- Frontend → Service d'ingestion FastAPI (port 8001), via la Gateway : récupération de l'historique et des navires dans la zone ; configuration de la zone de simulation.
- Simulateur (données AIS simulées ou réelles) → Kafka, topic « vessel-gps » → Service d'ingestion : ingestion et enregistrement des positions des navires.
- Service d'ingestion → Base PostgreSQL ingestion : positions AIS, historique des navires et zone de simulation.
- Frontend → Service de prédiction FastAPI (port 8002), via la Gateway : demande de prédiction pour un MMSI.
- Service de prédiction → Service d'ingestion : lecture des trois positions les plus récentes du navire.
- Service de prédiction contient un modèle scikit-learn Random Forest entraîné sur des trajectoires synthétiques ; il prédit la position future et un score d'anomalie.
- Service de prédiction → Base PostgreSQL prediction : journal des prédictions.
- Service de prédiction → Service d'alertes FastAPI (port 8003) : transmission du MMSI, de la position prédite et du score d'anomalie.
- Service d'alertes vérifie l'intrusion dans la zone de simulation active ; si aucune zone active n'est disponible, il compare la position prédite aux zones protégées et à leurs rayons. Le seuil d'anomalie est 0,5.
- Service d'alertes → Base PostgreSQL alert : alertes et zones protégées.
- Frontend → Service d'alertes, via la Gateway : consultation des alertes affichées dans le panneau de la carte.
- Service d'authentification FastAPI (port 8004) : émission et validation des JWT ; la Gateway l'interroge pour valider les requêtes protégées.
- Service utilisateurs FastAPI (port 8005) → Base PostgreSQL users : gestion des comptes.

Montre les bases PostgreSQL comme bases séparées par service, Kafka uniquement entre le simulateur et l'ingestion, et distingue visuellement le flux de données AIS du flux de prédiction/alertes. Indique les ports des services. Organise le diagramme pour que le parcours principal soit facile à suivre :
AIS → Kafka → Ingestion → Prédiction → Alertes → Frontend.
Ne représente pas le modèle comme celui qui décide lui-même de l'intrusion : cette décision appartient au service d'alertes.
```

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
