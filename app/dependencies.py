from app.services.cv_service import CVService


def get_cv_service() -> CVService:
    return CVService()
