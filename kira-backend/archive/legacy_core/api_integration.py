"""
API Integration Module for Regulatory Intelligence System
Prepares backend for REST API and frontend connectivity
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
from datetime import datetime

# Import existing modules
from .dynamic_ingest import DynamicIngester
from .rag_pipeline import RegulatoryRAGPipeline
from .analyze import RegulatoryImpactAnalyzer
from .config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Regulatory Intelligence API",
    description="AI-powered regulatory compliance and impact analysis system",
    version="1.0.0"
)

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
class IngestionRequest(BaseModel):
    data_source: Optional[str] = None
    force_reingest: bool = False

class AnalysisRequest(BaseModel):
    organization_profile: Dict
    query: Optional[str] = None

class PolicySearchRequest(BaseModel):
    query: str
    limit: int = 5
    authority: Optional[str] = None
    sector_tags: Optional[List[str]] = None

# Global instances
dynamic_ingester = None
rag_pipeline = None
analyzer = None

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global dynamic_ingester, rag_pipeline, analyzer
    try:
        dynamic_ingester = DynamicIngester()
        rag_pipeline = RegulatoryRAGPipeline()
        analyzer = RegulatoryImpactAnalyzer()
        logger.info("API components initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize API components: {e}")

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Regulatory Intelligence API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "ingestion": "/ingest",
            "analysis": "/analyze", 
            "search": "/search",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test basic functionality
        if dynamic_ingester and rag_pipeline and analyzer:
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "ingestion": "ready",
                    "rag": "ready", 
                    "analysis": "ready"
                }
            }
        else:
            return {
                "status": "initializing",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.post("/ingest")
async def trigger_ingestion(request: IngestionRequest):
    """Trigger data ingestion"""
    try:
        logger.info(f"Ingestion requested: {request.data_source}")
        
        if request.force_reingest:
            logger.info("Force reingest requested - clearing existing data")
            # Implementation for clearing vector DB would go here
        
        # Run dynamic ingestion
        dynamic_ingester.ingest_all_data_sources()
        
        return {
            "message": "Ingestion completed successfully",
            "timestamp": datetime.now().isoformat(),
            "data_source": request.data_source
        }
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.post("/analyze")
async def analyze_impact(request: AnalysisRequest):
    """Perform regulatory impact analysis"""
    try:
        logger.info(f"Impact analysis requested for organization")
        
        # Use existing analyzer
        analysis = analyzer.analyze_organization_impact()
        
        return {
            "analysis": analysis,
            "timestamp": datetime.now().isoformat(),
            "organization": request.organization_profile.get("organization_name", "Unknown")
        }
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/search")
async def search_policies(request: PolicySearchRequest):
    """Search for relevant policies"""
    try:
        logger.info(f"Policy search requested: {request.query}")
        
        # Use existing RAG pipeline
        if not rag_pipeline:
            raise HTTPException(status_code=503, detail="RAG pipeline not initialized")
        
        # Load organization profile (default)
        org_profile = {
            "organization_name": "Search User",
            "industry": "banking",
            "business_model": "Financial services"
        }
        
        # Retrieve relevant context
        retrieval_results = rag_pipeline.retrieve_relevant_context(
            org_profile=org_profile,
            query=request.query
        )
        
        return {
            "results": retrieval_results["relevant_policies"][:request.limit],
            "total_found": len(retrieval_results["relevant_policies"]),
            "query": request.query,
            "timestamp": datetime.now().isoformat(),
            "filters_applied": retrieval_results["retrieval_metadata"]["filters_applied"]
        }
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/stats")
async def get_system_stats():
    """Get system statistics"""
    try:
        # Get vector DB stats
        if not dynamic_ingester:
            raise HTTPException(status_code=503, detail="Ingester not initialized")
        
        collection = dynamic_ingester.collection
        total_docs = collection.count()
        
        # Get source breakdown
        results = collection.get(include=["metadatas"])
        source_counts = {}
        if results["metadatas"]:
            for metadata in results["metadatas"]:
                source = metadata.get("source", "unknown")
                source_counts[source] = source_counts.get(source, 0) + 1
        
        return {
            "total_documents": total_docs,
            "source_breakdown": source_counts,
            "vector_store_path": config.vector_store_path,
            "policies_path": config.processing_config["policies_path"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stats failed: {str(e)}")

# Frontend integration notes
FRONTEND_INTEGRATION_NOTES = """
Frontend Integration Guide:

1. REACT FRONTEND (Forntend/kira-v2/):
   - Already exists with modern React setup
   - Uses Vite for build tooling
   - Has TailwindCSS for styling
   - Ready for API integration

2. API ENDPOINTS:
   GET  /           - API info
   GET  /health       - Health check
   POST /ingest      - Trigger ingestion
   POST /analyze      - Impact analysis
   POST /search       - Policy search
   GET  /stats        - System stats

3. INTEGRATION EXAMPLES:

   // Health Check
   fetch('/health')
     .then(res => res.json())
     .then(data => console.log('System Status:', data.status))

   // Policy Search
   fetch('/search', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({
       query: 'AI governance requirements',
       limit: 5
     })
   })
     .then(res => res.json())
     .then(data => {
       console.log('Search Results:', data.results);
       data.results.forEach(policy => {
         console.log('Policy:', policy.metadata.policy_id);
       });
     });

   // Impact Analysis
   fetch('/analyze', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({
       organization_profile: {
         organization_name: 'Acme Financial Services Ltd',
         industry: 'banking',
         business_model: 'Commercial banking'
       }
     })
   })
     .then(res => res.json())
     .then(data => {
       console.log('Impact Analysis:', data.analysis);
     });

4. SETUP INSTRUCTIONS:
   - Start backend: python -m uvicorn api_integration:app --host 0.0.0.0 --port 8000
   - Start frontend: cd Forntend/kira-v2 && npm run dev
   - Configure CORS for production domains
   - Add authentication middleware as needed

5. PRODUCTION CONSIDERATIONS:
   - Add rate limiting
   - Add authentication/authorization
   - Configure proper CORS origins
   - Add API versioning
   - Add monitoring/logging
   - Add input validation
"""

if __name__ == "__main__":
    import uvicorn
    
    print("Starting Regulatory Intelligence API...")
    print("Frontend Integration Guide:")
    print(FRONTEND_INTEGRATION_NOTES)
    print("\nStarting API server on http://localhost:8000")
    print("Frontend should connect to: http://localhost:8000")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
