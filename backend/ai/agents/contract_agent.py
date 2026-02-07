"""
AI Contract Agent
Generates professional contract proposals based on audit results
"""

import os
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from pydantic import BaseModel
import json

# Try to import anthropic, fall back to mock if not available
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class ContractItem(BaseModel):
    category: str
    title: str
    description: str
    estimated_hours: float
    hourly_rate: float
    total: float
    priority: str  # high, medium, low
    complexity: str


class ContractProposal(BaseModel):
    proposal_id: str
    client_name: str
    client_email: str
    website_url: str
    audit_id: str

    # Pricing
    items: List[ContractItem]
    subtotal: float
    discount_percent: float
    discount_amount: float
    total: float
    currency: str

    # Terms
    validity_days: int
    payment_terms: str
    estimated_duration: str
    warranty_period: str

    # AI-generated content
    executive_summary: str
    scope_of_work: str
    deliverables: List[str]
    exclusions: List[str]
    recommended_approach: str

    created_at: str


class ContractAgent:
    """AI Agent for generating contract proposals"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if ANTHROPIC_AVAILABLE and self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None

    async def generate_proposal(
        self,
        audit_result: dict,
        client_name: str,
        client_email: str,
        hourly_rate: float = 75.0,
        currency: str = "EUR",
        discount_percent: float = 0,
        language: str = "en"
    ) -> ContractProposal:
        """Generate a contract proposal from audit results"""

        # Extract issues and calculate pricing
        issues = audit_result.get("issues", [])
        items = []
        total_hours = 0

        for issue in issues:
            hours = issue.get("estimated_hours", 1.0)
            total_hours += hours
            items.append(ContractItem(
                category=issue.get("category", "general"),
                title=issue.get("title", ""),
                description=issue.get("description", ""),
                estimated_hours=hours,
                hourly_rate=hourly_rate,
                total=hours * hourly_rate,
                priority=self._get_priority(issue.get("severity", "medium")),
                complexity=issue.get("complexity", "medium")
            ))

        # Calculate totals
        subtotal = sum(item.total for item in items)
        discount_amount = subtotal * (discount_percent / 100)
        total = subtotal - discount_amount

        # Generate AI content
        ai_content = await self._generate_ai_content(
            audit_result,
            items,
            language
        )

        # Estimate duration
        duration = self._estimate_duration(total_hours)

        # Generate proposal ID
        import secrets
        proposal_id = f"PROP-{datetime.utcnow().strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"

        return ContractProposal(
            proposal_id=proposal_id,
            client_name=client_name,
            client_email=client_email,
            website_url=audit_result.get("url", ""),
            audit_id=audit_result.get("id", ""),

            items=items,
            subtotal=subtotal,
            discount_percent=discount_percent,
            discount_amount=discount_amount,
            total=total,
            currency=currency,

            validity_days=30,
            payment_terms="50% upfront, 50% on completion",
            estimated_duration=duration,
            warranty_period="90 days",

            executive_summary=ai_content.get("executive_summary", ""),
            scope_of_work=ai_content.get("scope_of_work", ""),
            deliverables=ai_content.get("deliverables", []),
            exclusions=ai_content.get("exclusions", []),
            recommended_approach=ai_content.get("recommended_approach", ""),

            created_at=datetime.utcnow().isoformat()
        )

    async def _generate_ai_content(
        self,
        audit_result: dict,
        items: List[ContractItem],
        language: str
    ) -> dict:
        """Generate AI content for the proposal"""

        if not self.client:
            # Return mock content if no API key
            return self._get_mock_content(audit_result, items, language)

        # Prepare context for Claude
        issues_summary = "\n".join([
            f"- {item.title} ({item.category}, {item.priority} priority): {item.estimated_hours}h"
            for item in items[:20]  # Limit to 20 items
        ])

        scores = {
            "overall": audit_result.get("overall_score", 0),
            "performance": audit_result.get("performance_score"),
            "seo": audit_result.get("seo_score"),
            "security": audit_result.get("security_score"),
            "gdpr": audit_result.get("gdpr_score"),
            "accessibility": audit_result.get("accessibility_score")
        }

        lang_instruction = "Respond in Romanian." if language == "ro" else "Respond in English."

        prompt = f"""You are an expert web development consultant creating a professional contract proposal.

Website: {audit_result.get("url", "")}
Current Scores: {json.dumps(scores)}

Issues to address:
{issues_summary}

Total estimated hours: {sum(item.estimated_hours for item in items)}

{lang_instruction}

Generate a professional contract proposal with:
1. An executive summary (2-3 paragraphs)
2. Scope of work description
3. List of 5-7 key deliverables
4. List of 3-4 exclusions
5. Recommended implementation approach

Format your response as JSON with these keys:
- executive_summary: string
- scope_of_work: string
- deliverables: array of strings
- exclusions: array of strings
- recommended_approach: string"""

        try:
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse response
            content = message.content[0].text

            # Try to extract JSON
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content

            return json.loads(json_str)

        except Exception as e:
            print(f"AI content generation error: {e}")
            return self._get_mock_content(audit_result, items, language)

    def _get_mock_content(self, audit_result: dict, items: List[ContractItem], language: str) -> dict:
        """Return mock content when AI is not available"""
        url = audit_result.get("url", "the website")
        score = audit_result.get("overall_score", 0)
        issue_count = len(items)

        if language == "ro":
            return {
                "executive_summary": f"Acest raport prezintă o analiză completă a site-ului {url}, "
                    f"care a obținut un scor general de {score}/100. Am identificat {issue_count} probleme "
                    "care necesită atenție pentru a îmbunătăți performanța, securitatea și experiența utilizatorilor.",
                "scope_of_work": "Lucrările vor include optimizarea performanței, îmbunătățirea SEO, "
                    "consolidarea securității și asigurarea conformității GDPR.",
                "deliverables": [
                    "Raport tehnic detaliat",
                    "Implementarea optimizărilor de performanță",
                    "Configurarea securității",
                    "Implementare cookie banner GDPR",
                    "Testare și documentație finală"
                ],
                "exclusions": [
                    "Creare conținut nou",
                    "Redesign complet",
                    "Mentenanță pe termen lung"
                ],
                "recommended_approach": "Recomandăm o abordare în faze, începând cu problemele critice "
                    "de securitate, urmate de optimizările de performanță și apoi îmbunătățirile SEO."
            }
        else:
            return {
                "executive_summary": f"This report presents a comprehensive analysis of {url}, "
                    f"which achieved an overall score of {score}/100. We have identified {issue_count} issues "
                    "that require attention to improve performance, security, and user experience.",
                "scope_of_work": "The work will include performance optimization, SEO improvements, "
                    "security hardening, and GDPR compliance implementation.",
                "deliverables": [
                    "Detailed technical report",
                    "Performance optimization implementation",
                    "Security configuration",
                    "GDPR cookie banner implementation",
                    "Testing and final documentation"
                ],
                "exclusions": [
                    "New content creation",
                    "Complete redesign",
                    "Long-term maintenance"
                ],
                "recommended_approach": "We recommend a phased approach, starting with critical security "
                    "issues, followed by performance optimizations, and then SEO improvements."
            }

    def _get_priority(self, severity: str) -> str:
        """Convert severity to priority"""
        mapping = {
            "critical": "high",
            "high": "high",
            "medium": "medium",
            "low": "low",
            "info": "low"
        }
        return mapping.get(severity, "medium")

    def _estimate_duration(self, total_hours: float) -> str:
        """Estimate project duration based on total hours"""
        if total_hours <= 8:
            return "1-2 days"
        elif total_hours <= 24:
            return "3-5 days"
        elif total_hours <= 40:
            return "1-2 weeks"
        elif total_hours <= 80:
            return "2-4 weeks"
        else:
            return "1-2 months"

    async def generate_contract_pdf(self, proposal: ContractProposal) -> str:
        """Generate a PDF contract from the proposal"""
        # This would use a PDF generator like ReportLab or WeasyPrint
        # For now, return a placeholder
        return f"/tmp/contract_{proposal.proposal_id}.pdf"
