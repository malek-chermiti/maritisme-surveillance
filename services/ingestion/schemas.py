from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

# ------------------------------------------------------------------------------
# Schémas pour les Positions des Navires (VesselPosition)
# ------------------------------------------------------------------------------
class VesselPositionSchema(BaseModel):
    mmsi: int = Field(..., description="L'identifiant unique maritime du navire")
    latitude: float = Field(..., description="Latitude de la position GPS")
    longitude: float = Field(..., description="Longitude de la position GPS")
    speed: float = Field(default=0.0, description="Vitesse du navire en nœuds")
    heading: float = Field(default=0.0, description="Cap du navire en degrés (0-360)")
    recorded_at: Optional[datetime] = Field(default=None, description="Horodatage de la position")

    class Config:
        # Permet à Pydantic de lire directement depuis les objets ORM SQLAlchemy
        from_attributes = True


# ------------------------------------------------------------------------------
# Schémas pour la Zone de Simulation (SimulationZone)
# ------------------------------------------------------------------------------
class SimulationZoneSchema(BaseModel):
    id: Optional[int] = Field(default=None, description="ID auto-généré par la base de données")
    name: Optional[str] = Field(default="Zone Personnalisée", description="Nom descriptif de la zone")
    lat_min: float = Field(..., description="Latitude minimale (Sud)")
    lat_max: float = Field(..., description="Latitude maximale (Nord)")
    lon_min: float = Field(..., description="Longitude minimale (Ouest)")
    lon_max: float = Field(..., description="Longitude maximale (Est)")

    class Config:
        # Permet à Pydantic de lire directement depuis les objets ORM SQLAlchemy
        from_attributes = True