from app.services.cv_service import CVService


def get_cv_service() -> CVService:
    """
    Devuelve una instancia de CVService para inyección de dependencias en FastAPI
    """
    return CVService()
