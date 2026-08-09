# Maritisme Surveillance

## Description

Projet de surveillance maritime composé de microservices Python/FastAPI et d'une application frontend Angular.

### Services
- `services/gateway` : API gateway
- `services/ingestion` : ingestion des positions navires via Kafka
- `services/alert` : gestion des alertes
- `services/auth` : authentification
- `services/prediction` : prédiction des anomalies
- `services/simulator` : simulateur Kafka de positions navires
- `frontend` : interface utilisateur Angular

## Prérequis

- Python 3.x
- Node.js + npm
- PostgreSQL
- Kafka
- Consul (facultatif selon le déploiement)
- `docker-compose` si tu utilises les conteneurs

## Installation

1. Installer les dépendances Python pour chaque service :
   ```bash
   pip install -r services/<service>/requirements.txt
   ```

2. Installer le frontend Angular :
   ```bash
   cd frontend
   npm install
   ```

## Démarrage

### Services backend

Démarre chaque service dans son dossier :

- Gateway : `uvicorn main:app --port 8000`
- Ingestion : `uvicorn main:app --port 8001`
- Alert : `uvicorn main:app --port 8002` (ou port configuré)
- Auth : `uvicorn main:app --port 8003` (ou port configuré)
- Prediction : `uvicorn main:app --port 8004` (ou port configuré)

### Frontend

```bash
cd frontend
ng serve
```

## Endpoints utiles

### Gateway
- `http://localhost:8000/api/alert/alerts/zone?lat=<lat>&lon=<lon>&limit=<limit>`

### Ingestion
- `http://localhost:8001` (service ingestion)

### Auth
- `http://localhost:8000/api/auth/login` (via gateway)

## Notes

- `alerts/zone` est un endpoint `GET`; les paramètres `lat`, `lon`, `limit` doivent être envoyés en query string.
- Si tu veux un endpoint `POST` avec body JSON, il faudra modifier le contrôleur correspondant.

## Test Postman

Exemple :

```text
GET http://localhost:8000/api/alert/alerts/zone?lat=35.3&lon=10.4&limit=20
```

Aucun body n'est nécessaire.
