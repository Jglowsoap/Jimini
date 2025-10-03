"""
Phase 6A - Intelligence API Endpoints
REST API endpoints for AI-powered regulatory analysis and rule generation
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
import tempfile
import json
from pathlib import Path
from datetime import datetime
import asyncio

from app.intelligence.regulatory_parser import (
    RegulatoryTextParser, RegulationType, RequirementType,
    PolicyRequirement, GeneratedRule
)
from app.intelligence.config import load_intelligence_config, validate_intelligence_setup
from app.models import BaseResponse
from app.util import get_logger

logger = get_logger(__name__)

# Initialize router
intelligence_router = APIRouter(prefix="/v1/intelligence", tags=["intelligence"])

# Global parser instance
parser_instance: Optional[RegulatoryTextParser] = None


class DocumentType(str, Enum):
    """Supported document types."""
    PDF = "pdf"
    HTML = "html"
    TEXT = "text"
    DOCX = "docx"


class ProcessingStatus(str, Enum):
    """Processing status values."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalyzeDocumentRequest(BaseModel):
    """Request model for document analysis."""
    regulation_type: RegulationType
    document_type: DocumentType
    confidence_threshold: Optional[float] = Field(default=0.4, ge=0.0, le=1.0)
    max_rules: Optional[int] = Field(default=50, ge=1, le=200)
    auto_approve_high_confidence: Optional[bool] = Field(default=False)


class RequirementResponse(BaseModel):
    """Response model for extracted requirements."""
    id: str
    regulation_type: str
    requirement_type: str
    title: str
    description: str
    regulatory_section: str
    severity: str
    confidence_score: float
    suggested_action: str
    data_types: List[str]
    applicable_contexts: List[str]


class GeneratedRuleResponse(BaseModel):
    """Response model for generated rules."""
    rule_id: str
    name: str
    description: str
    pattern: Optional[str]
    llm_prompt: Optional[str]
    action: str
    confidence_score: float
    applies_to: List[str]
    endpoints: List[str]
    yaml_content: str
    requires_approval: bool
    approved_by: Optional[str]
    approved_at: Optional[datetime]


class AnalyzeDocumentResponse(BaseResponse):
    """Response model for document analysis."""
    processing_id: str
    requirements: List[RequirementResponse]
    generated_rules: List[GeneratedRuleResponse]
    total_requirements: int
    total_rules: int
    processing_time_seconds: float
    intelligence_status: Dict[str, Any]


class ProcessingJob(BaseModel):
    """Background processing job."""
    id: str
    status: ProcessingStatus
    regulation_type: RegulationType
    document_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    requirements: Optional[List[RequirementResponse]] = None
    rules: Optional[List[GeneratedRuleResponse]] = None
    error_message: Optional[str] = None


class ApproveRuleRequest(BaseModel):
    """Request to approve a generated rule."""
    rule_id: str
    approved_by: str
    notes: Optional[str] = None


class BatchAnalysisRequest(BaseModel):
    """Request for batch analysis of multiple documents."""
    regulation_type: RegulationType
    confidence_threshold: Optional[float] = Field(default=0.4, ge=0.0, le=1.0)
    max_rules_per_document: Optional[int] = Field(default=50, ge=1, le=100)


# In-memory storage for processing jobs (in production, use Redis or database)
processing_jobs: Dict[str, ProcessingJob] = {}
approved_rules: Dict[str, Dict[str, Any]] = {}


def get_parser() -> RegulatoryTextParser:
    """Get or create parser instance."""
    global parser_instance
    if parser_instance is None:
        parser_instance = RegulatoryTextParser()
    return parser_instance


def convert_requirement_to_response(req: PolicyRequirement) -> RequirementResponse:
    """Convert PolicyRequirement to response model."""
    return RequirementResponse(
        id=req.id,
        regulation_type=req.regulation_type.value,
        requirement_type=req.requirement_type.value,
        title=req.title,
        description=req.description,
        regulatory_section=req.regulatory_section,
        severity=req.severity,
        confidence_score=req.confidence_score,
        suggested_action=req.suggested_action,
        data_types=req.data_types,
        applicable_contexts=req.applicable_contexts
    )


def convert_rule_to_response(rule: GeneratedRule) -> GeneratedRuleResponse:
    """Convert GeneratedRule to response model."""
    return GeneratedRuleResponse(
        rule_id=rule.rule_id,
        name=rule.name,
        description=rule.description,
        pattern=rule.pattern,
        llm_prompt=rule.llm_prompt,
        action=rule.action,
        confidence_score=rule.confidence_score,
        applies_to=rule.applies_to,
        endpoints=rule.endpoints,
        yaml_content=rule.yaml_content,
        requires_approval=rule.requires_approval,
        approved_by=rule.approved_by,
        approved_at=rule.approved_at
    )


@intelligence_router.get("/status")
async def get_intelligence_status() -> JSONResponse:
    """Get intelligence system status and capabilities."""
    try:
        config = load_intelligence_config()
        setup_status = validate_intelligence_setup()
        
        return JSONResponse({
            "status": "ok",
            "phase": "6A - Intelligence Expansion",
            "capabilities": {
                "regulatory_parsing": True,
                "ai_rule_generation": True,
                "nlp_analysis": setup_status.get("spacy_available", False),
                "advanced_classification": setup_status.get("transformers_available", False),
                "pdf_processing": setup_status.get("pdf_processing_available", False),
                "html_processing": setup_status.get("html_processing_available", False)
            },
            "supported_regulations": [reg.value for reg in RegulationType],
            "supported_formats": config.supported_formats,
            "configuration": {
                "min_confidence_threshold": config.min_confidence_threshold,
                "auto_approval_threshold": config.auto_approval_threshold,
                "max_rules_per_document": config.max_rules_per_document,
                "auto_approval_enabled": config.enable_auto_approval,
                "human_review_required": config.require_human_review
            },
            "setup_status": setup_status
        })
        
    except Exception as e:
        logger.error(f"Failed to get intelligence status: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@intelligence_router.post("/analyze-document")
async def analyze_document(
    file: UploadFile = File(...),
    regulation_type: RegulationType = Form(...),
    confidence_threshold: float = Form(0.4),
    max_rules: int = Form(50),
    auto_approve: bool = Form(False),
    background_tasks: BackgroundTasks = BackgroundTasks()
) -> AnalyzeDocumentResponse:
    """Analyze regulatory document and generate policy rules."""
    
    start_time = datetime.now()
    processing_id = f"proc_{int(start_time.timestamp())}"
    
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file size (max 10MB)
        config = load_intelligence_config()
        if file.size and file.size > config.max_document_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {config.max_document_size_mb}MB"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()
            
            # Process document
            parser = get_parser()
            requirements, rules = parser.parse_regulation_document(
                temp_file.name, regulation_type
            )
            
            # Filter by confidence threshold
            filtered_requirements = [
                req for req in requirements 
                if req.confidence_score >= confidence_threshold
            ]
            
            filtered_rules = [
                rule for rule in rules 
                if rule.confidence_score >= confidence_threshold
            ][:max_rules]
            
            # Auto-approve high-confidence rules if enabled
            if auto_approve:
                for rule in filtered_rules:
                    if rule.confidence_score >= config.auto_approval_threshold:
                        rule.requires_approval = False
                        rule.approved_by = "system"
                        rule.approved_at = datetime.now()
            
            # Clean up temp file
            Path(temp_file.name).unlink()
        
        # Convert to response models
        req_responses = [convert_requirement_to_response(req) for req in filtered_requirements]
        rule_responses = [convert_rule_to_response(rule) for rule in filtered_rules]
        
        # Calculate processing time
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Store processing job
        job = ProcessingJob(
            id=processing_id,
            status=ProcessingStatus.COMPLETED,
            regulation_type=regulation_type,
            document_name=file.filename,
            started_at=start_time,
            completed_at=end_time,
            requirements=req_responses,
            rules=rule_responses
        )
        processing_jobs[processing_id] = job
        
        logger.info(
            f"Document analysis completed: {len(filtered_requirements)} requirements, "
            f"{len(filtered_rules)} rules generated in {processing_time:.2f}s"
        )
        
        return AnalyzeDocumentResponse(
            success=True,
            message="Document analysis completed successfully",
            processing_id=processing_id,
            requirements=req_responses,
            generated_rules=rule_responses,
            total_requirements=len(req_responses),
            total_rules=len(rule_responses),
            processing_time_seconds=processing_time,
            intelligence_status=validate_intelligence_setup()
        )
        
    except Exception as e:
        logger.error(f"Document analysis failed: {e}")
        
        # Store failed job
        job = ProcessingJob(
            id=processing_id,
            status=ProcessingStatus.FAILED,
            regulation_type=regulation_type,
            document_name=file.filename if file.filename else "unknown",
            started_at=start_time,
            error_message=str(e)
        )
        processing_jobs[processing_id] = job
        
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@intelligence_router.get("/processing-jobs")
async def list_processing_jobs() -> JSONResponse:
    """List all processing jobs."""
    jobs = [job.dict() for job in processing_jobs.values()]
    jobs.sort(key=lambda x: x["started_at"], reverse=True)
    
    return JSONResponse({
        "jobs": jobs,
        "total_jobs": len(jobs),
        "active_jobs": len([j for j in jobs if j["status"] == ProcessingStatus.PROCESSING.value])
    })


@intelligence_router.get("/processing-jobs/{processing_id}")
async def get_processing_job(processing_id: str) -> JSONResponse:
    """Get specific processing job details."""
    if processing_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Processing job not found")
    
    job = processing_jobs[processing_id]
    return JSONResponse(job.dict())


@intelligence_router.post("/approve-rule")
async def approve_rule(request: ApproveRuleRequest) -> BaseResponse:
    """Approve a generated rule for deployment."""
    try:
        # Find the rule in processing jobs
        rule_found = False
        for job in processing_jobs.values():
            if job.rules:
                for rule in job.rules:
                    if rule.rule_id == request.rule_id:
                        rule.requires_approval = False
                        rule.approved_by = request.approved_by
                        rule.approved_at = datetime.now()
                        rule_found = True
                        
                        # Store in approved rules
                        approved_rules[request.rule_id] = {
                            "rule": rule.dict(),
                            "approved_by": request.approved_by,
                            "approved_at": datetime.now().isoformat(),
                            "notes": request.notes
                        }
                        break
            if rule_found:
                break
        
        if not rule_found:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        logger.info(f"Rule {request.rule_id} approved by {request.approved_by}")
        
        return BaseResponse(
            success=True,
            message=f"Rule {request.rule_id} approved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rule approval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Approval failed: {str(e)}")


@intelligence_router.get("/approved-rules")
async def list_approved_rules() -> JSONResponse:
    """List all approved rules."""
    return JSONResponse({
        "approved_rules": list(approved_rules.values()),
        "total_approved": len(approved_rules)
    })


@intelligence_router.get("/export-rules/{processing_id}")
async def export_rules(processing_id: str, approved_only: bool = False) -> FileResponse:
    """Export generated rules as YAML file."""
    if processing_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Processing job not found")
    
    job = processing_jobs[processing_id]
    if not job.rules:
        raise HTTPException(status_code=400, detail="No rules found in processing job")
    
    # Filter rules if requested
    rules_to_export = job.rules
    if approved_only:
        rules_to_export = [rule for rule in job.rules if not rule.requires_approval]
    
    if not rules_to_export:
        raise HTTPException(status_code=400, detail="No rules available for export")
    
    # Generate combined YAML content
    yaml_content = "# Generated Policy Rules\n"
    yaml_content += f"# Generated from: {job.document_name}\n"
    yaml_content += f"# Regulation: {job.regulation_type}\n"
    yaml_content += f"# Generated at: {datetime.now().isoformat()}\n\n"
    
    for rule in rules_to_export:
        yaml_content += f"# Rule: {rule.name}\n"
        yaml_content += f"# Confidence: {rule.confidence_score:.2f}\n"
        yaml_content += rule.yaml_content
        yaml_content += "\n"
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
        temp_file.write(yaml_content)
        temp_file.flush()
        
        filename = f"rules_{job.regulation_type}_{processing_id}.yaml"
        
        return FileResponse(
            path=temp_file.name,
            filename=filename,
            media_type="application/x-yaml"
        )


@intelligence_router.delete("/processing-jobs/{processing_id}")
async def delete_processing_job(processing_id: str) -> BaseResponse:
    """Delete a processing job and its results."""
    if processing_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Processing job not found")
    
    # Remove any approved rules from this job
    job = processing_jobs[processing_id]
    if job.rules:
        for rule in job.rules:
            if rule.rule_id in approved_rules:
                del approved_rules[rule.rule_id]
    
    # Remove the job
    del processing_jobs[processing_id]
    
    logger.info(f"Processing job {processing_id} deleted")
    
    return BaseResponse(
        success=True,
        message=f"Processing job {processing_id} deleted successfully"
    )


@intelligence_router.post("/demo")
async def run_intelligence_demo() -> JSONResponse:
    """Run intelligence system demonstration."""
    try:
        from app.intelligence.regulatory_parser import demo_regulatory_parser
        
        # Run demo
        requirements, rules = demo_regulatory_parser()
        
        # Convert to response format
        req_responses = [convert_requirement_to_response(req) for req in requirements]
        rule_responses = [convert_rule_to_response(rule) for rule in rules]
        
        return JSONResponse({
            "demo_completed": True,
            "message": "Intelligence system demonstration completed successfully",
            "sample_requirements": req_responses[:3],  # First 3 requirements
            "sample_rules": rule_responses[:2],  # First 2 rules
            "total_requirements": len(req_responses),
            "total_rules": len(rule_responses),
            "intelligence_status": validate_intelligence_setup()
        })
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise HTTPException(status_code=500, detail=f"Demo failed: {str(e)}")


# Add intelligence router to main app
def add_intelligence_routes(app):
    """Add intelligence routes to FastAPI app."""
    app.include_router(intelligence_router)
    
    # Phase 6C & 6D - Policy Recommendations and Predictive Intelligence
    try:
        from .policy_recommendations_api import create_policy_recommendations_router
        from .predictive_intelligence_api import router as predictive_router
        
        app.include_router(create_policy_recommendations_router())
        app.include_router(predictive_router)
        print("✅ Policy recommendations and predictive intelligence routes added")
    except ImportError as e:
        print(f"ℹ️ Advanced intelligence features not available: {e}")
    
    # Phase 7 - Reinforcement Learning Framework
    try:
        from .reinforcement_learning_api import rl_router
        app.include_router(rl_router)
        print("✅ Reinforcement learning routes added")
    except ImportError as e:
        print(f"ℹ️ Reinforcement learning features not available: {e}")