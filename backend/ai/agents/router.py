"""
AI Agents API Endpoints
Contract generation and sales chat
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from database.models import User, Audit, Lead
from auth.dependencies import get_current_user, get_current_user_optional
from sqlalchemy import select

from .contract_agent import ContractAgent, ContractProposal
from .sales_agent import SalesAgent, SalesResponse


router = APIRouter(prefix="/api/ai", tags=["ai-agents"])

# Initialize agents
contract_agent = ContractAgent()
sales_agent = SalesAgent()


# ============== SCHEMAS ==============

class GenerateProposalRequest(BaseModel):
    audit_id: str
    client_name: str
    client_email: str
    hourly_rate: float = 75.0
    currency: str = "EUR"
    discount_percent: float = 0
    language: str = "en"


class ChatRequest(BaseModel):
    session_id: str
    message: str
    audit_id: Optional[str] = None
    language: str = "en"


# ============== CONTRACT AGENT ENDPOINTS ==============

@router.post("/contract/generate", response_model=ContractProposal)
async def generate_contract_proposal(
    request: GenerateProposalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a contract proposal from audit results"""

    # Get audit
    result = await db.execute(
        select(Audit).where(Audit.id == request.audit_id)
    )
    audit = result.scalar_one_or_none()

    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    # Build audit result dict
    audit_result = {
        "id": audit.id,
        "url": audit.url,
        "overall_score": audit.overall_score,
        "performance_score": audit.performance_score,
        "seo_score": audit.seo_score,
        "security_score": audit.security_score,
        "gdpr_score": audit.gdpr_score,
        "accessibility_score": audit.accessibility_score,
        "issues": [
            {
                "category": issue.category,
                "severity": issue.severity,
                "title": issue.title,
                "description": issue.description,
                "estimated_hours": issue.estimated_hours,
                "complexity": issue.complexity
            }
            for issue in audit.issues
        ]
    }

    proposal = await contract_agent.generate_proposal(
        audit_result=audit_result,
        client_name=request.client_name,
        client_email=request.client_email,
        hourly_rate=request.hourly_rate,
        currency=request.currency,
        discount_percent=request.discount_percent,
        language=request.language
    )

    return proposal


@router.post("/contract/pdf")
async def generate_contract_pdf(
    proposal: ContractProposal,
    current_user: User = Depends(get_current_user)
):
    """Generate a PDF from a contract proposal"""
    pdf_path = await contract_agent.generate_contract_pdf(proposal)
    return {"pdf_url": pdf_path}


# ============== SALES AGENT ENDPOINTS ==============

@router.post("/chat", response_model=SalesResponse)
async def chat_with_sales_agent(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Chat with the AI sales agent"""

    # Build context if audit is available
    context = None
    if request.audit_id:
        result = await db.execute(
            select(Audit).where(Audit.id == request.audit_id)
        )
        audit = result.scalar_one_or_none()

        if audit:
            context = {
                "audit_result": {
                    "url": audit.url,
                    "overall_score": audit.overall_score,
                    "performance_score": audit.performance_score,
                    "seo_score": audit.seo_score,
                    "security_score": audit.security_score,
                    "gdpr_score": audit.gdpr_score,
                    "accessibility_score": audit.accessibility_score,
                    "issues": [
                        {
                            "category": issue.category,
                            "severity": issue.severity,
                            "title": issue.title
                        }
                        for issue in audit.issues[:10]  # Limit to 10 issues
                    ]
                }
            }

    response = await sales_agent.chat(
        session_id=request.session_id,
        user_message=request.message,
        context=context,
        language=request.language
    )

    return response


@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    history = sales_agent.get_conversation_history(session_id)
    return {"messages": [msg.model_dump() for msg in history]}


@router.delete("/chat/{session_id}")
async def clear_chat_history(session_id: str):
    """Clear chat history for a session"""
    sales_agent.clear_conversation(session_id)
    return {"success": True}


# ============== LEAD QUALIFICATION ENDPOINT ==============

@router.get("/qualify/{session_id}")
async def get_lead_qualification(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get lead qualification for a chat session"""
    qualification = await sales_agent._qualify_lead(session_id, None)

    if not qualification:
        return {"qualified": False, "message": "Not enough conversation data"}

    return {
        "qualified": True,
        "qualification": qualification.model_dump()
    }
