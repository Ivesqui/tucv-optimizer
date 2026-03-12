from app.services.analysis_service import AnalysisService as CVAnalysisService
from app.services.cv_service import CVService

def get_cv_service() -> CVService:
    return CVService()

def get_cv_analysis() -> CVAnalysisService:
    return CVAnalysisService()