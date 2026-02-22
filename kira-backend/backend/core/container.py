from functools import lru_cache

from backend.core.analyze import RegulatoryImpactAnalyzer
from backend.core.cache import RedisCache
from backend.core.llm_client import LlmClient
from backend.core.rag_pipeline import RegulatoryRAGPipeline
from backend.core.vector_store import VectorStoreClient
from backend.services.analysis_service import AnalysisService
from backend.services.assistant_service import AssistantService
from backend.services.dashboard_service import DashboardService
from backend.services.pdfAnalyzer import PdfAnalyzerService
from backend.services.policyQA import PolicyQAService


@lru_cache(maxsize=1)
def get_cache() -> RedisCache:
    return RedisCache()


@lru_cache(maxsize=1)
def get_llm_client() -> LlmClient:
    return LlmClient()


@lru_cache(maxsize=1)
def get_vector_store() -> VectorStoreClient:
    return VectorStoreClient()


@lru_cache(maxsize=1)
def get_rag_pipeline() -> RegulatoryRAGPipeline:
    return RegulatoryRAGPipeline(get_llm_client(), get_vector_store())


@lru_cache(maxsize=1)
def get_analyzer() -> RegulatoryImpactAnalyzer:
    return RegulatoryImpactAnalyzer(get_llm_client())


@lru_cache(maxsize=1)
def get_analysis_service() -> AnalysisService:
    return AnalysisService(get_rag_pipeline(), get_analyzer(), get_cache())


@lru_cache(maxsize=1)
def get_assistant_service() -> AssistantService:
    return AssistantService(get_rag_pipeline(), get_llm_client(), get_cache())


@lru_cache(maxsize=1)
def get_dashboard_service() -> DashboardService:
    return DashboardService(get_vector_store(), get_cache())


@lru_cache(maxsize=1)
def get_pdf_analyzer_service() -> PdfAnalyzerService:
    return PdfAnalyzerService(get_llm_client())


@lru_cache(maxsize=1)
def get_policy_qa_service() -> PolicyQAService:
    return PolicyQAService(get_llm_client(), get_pdf_analyzer_service())
