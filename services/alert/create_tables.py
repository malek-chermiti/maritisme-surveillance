from database import engine
from models import Base, ProtectedZones, Alerts  # Importe votre Base et vos modèles

# Crée toutes les tables définies dans le modèle dans alert_db
Base.metadata.create_all(bind=engine)
print("Tables 'protected_zones' et 'alerts' créées avec succès !")
