from fastapi import APIRouter
from app.core.knowledge.db_loader import (
    LOCATIONS_DB,
    ETHNICITIES_DB,
    BLOOD_TYPES_DB,
    WORK_AREAS_DB
)

router = APIRouter(tags=["CATALOGS"])

@router.get("/all")
async def get_all_catalogs():
    """
    Retorna todos los datos maestros para alimentar los selectores
    del frontend (Provincias, Cantones, Etnias, Tipos de Sangre).
    """
    return {
        "locations": LOCATIONS_DB,
        "ethnicities": ETHNICITIES_DB,
        "blood_types": BLOOD_TYPES_DB,
        "work_areas": list(WORK_AREAS_DB.values())
    }

@router.get("/locations/{province}")
async def get_cantons_by_province(province: str):
    """Retorna solo los cantones de una provincia específica."""
    province_key = province.lower()
    return LOCATIONS_DB.get(province_key, {})

@router.get("/ethnicities/all")
async def get_ethnicities():
    return {
        "ethnicities": ETHNICITIES_DB,
    }

@router.get("/work-areas/{charge}")
async def get_charge_by_area(charge: str):
    charge_key = charge.lower()
    return WORK_AREAS_DB.get(charge_key, {})
