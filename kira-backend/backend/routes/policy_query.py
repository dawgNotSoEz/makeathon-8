from fastapi import APIRouter, Depends, Query

from backend.core.container import get_pdf_analyzer_service, get_policy_qa_service
from backend.schemas.policy_query import PolicyAnalysisItem, PolicyQueryRequest, PolicyQueryResponse
from backend.services.pdfAnalyzer import PdfAnalyzerService
from backend.services.policyQA import NOT_FOUND_MESSAGE, PolicyQAService


router = APIRouter()


@router.get("/policy-analyses", response_model=list[PolicyAnalysisItem])
async def list_policy_analyses(
    limit: int = Query(default=8, ge=1, le=20),
    analyzer: PdfAnalyzerService = Depends(get_pdf_analyzer_service),
) -> list[PolicyAnalysisItem]:
    results = await analyzer.analyze_all(limit=limit)
    return [PolicyAnalysisItem.model_validate(item) for item in results]


@router.post("/policy-query", response_model=PolicyQueryResponse)
async def query_policy(
    request: PolicyQueryRequest,
    service: PolicyQAService = Depends(get_policy_qa_service),
) -> PolicyQueryResponse:
    result = await service.ask(request.question, request.gazette_id)
    if result.get("error"):
        return PolicyQueryResponse(error=str(result.get("error")), sources=result.get("sources") or [])
    answer = str(result.get("answer") or NOT_FOUND_MESSAGE)
    return PolicyQueryResponse(answer=answer, sources=result.get("sources") or [])
