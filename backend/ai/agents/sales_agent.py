"""
AI Sales Agent
Handles customer inquiries, qualifies leads, and provides recommendations
"""

import os
from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel
from enum import Enum
import json

# Try to import anthropic, fall back to mock if not available
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class LeadScore(str, Enum):
    HOT = "hot"       # Ready to buy
    WARM = "warm"     # Interested, needs nurturing
    COLD = "cold"     # Just browsing


class CustomerIntent(str, Enum):
    PURCHASE = "purchase"
    INFORMATION = "information"
    SUPPORT = "support"
    PRICING = "pricing"
    DEMO = "demo"
    COMPARISON = "comparison"


class ConversationMessage(BaseModel):
    role: str  # user or assistant
    content: str
    timestamp: str


class LeadQualification(BaseModel):
    lead_score: LeadScore
    intent: CustomerIntent
    budget_indication: Optional[str]
    timeline: Optional[str]
    pain_points: List[str]
    recommended_package: str
    follow_up_actions: List[str]
    confidence: float  # 0-1


class SalesResponse(BaseModel):
    message: str
    suggested_actions: List[str]
    qualification: Optional[LeadQualification]
    show_pricing: bool
    show_demo: bool
    escalate_to_human: bool


class SalesAgent:
    """AI Sales Agent for customer engagement"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if ANTHROPIC_AVAILABLE and self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None

        # Conversation context
        self.conversations: Dict[str, List[ConversationMessage]] = {}

        # Product knowledge
        self.packages = {
            "starter": {
                "name": "Starter",
                "price": 0,
                "currency": "EUR",
                "features": ["2 audit types", "Basic score overview", "Social share required"],
                "best_for": "Small websites, initial testing"
            },
            "pro": {
                "name": "Pro",
                "price": 1.99,
                "currency": "EUR",
                "features": ["4 audit types", "Detailed issue breakdown", "Basic PDF report", "Email delivery"],
                "best_for": "Growing businesses, regular monitoring"
            },
            "full": {
                "name": "Full",
                "price": 4.99,
                "currency": "EUR",
                "features": ["All 6 audit types", "Full issue details", "Professional PDF", "Priority support", "AI recommendations"],
                "best_for": "Enterprises, agencies, comprehensive audits"
            }
        }

    async def chat(
        self,
        session_id: str,
        user_message: str,
        context: Optional[dict] = None,
        language: str = "en"
    ) -> SalesResponse:
        """Handle a chat message from a potential customer"""

        # Initialize conversation if new
        if session_id not in self.conversations:
            self.conversations[session_id] = []

        # Add user message to history
        self.conversations[session_id].append(ConversationMessage(
            role="user",
            content=user_message,
            timestamp=datetime.utcnow().isoformat()
        ))

        # Generate response
        if self.client:
            response = await self._generate_ai_response(session_id, context, language)
        else:
            response = self._generate_rule_based_response(user_message, context, language)

        # Add assistant message to history
        self.conversations[session_id].append(ConversationMessage(
            role="assistant",
            content=response.message,
            timestamp=datetime.utcnow().isoformat()
        ))

        return response

    async def _generate_ai_response(
        self,
        session_id: str,
        context: Optional[dict],
        language: str
    ) -> SalesResponse:
        """Generate AI-powered response"""

        # Build conversation history for Claude
        history = self.conversations.get(session_id, [])
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in history
        ]

        # Context about audit if available
        audit_context = ""
        if context and context.get("audit_result"):
            audit = context["audit_result"]
            audit_context = f"""
Current website audit context:
- URL: {audit.get('url')}
- Overall Score: {audit.get('overall_score')}/100
- Issues found: {len(audit.get('issues', []))}
- Performance: {audit.get('performance_score')}
- SEO: {audit.get('seo_score')}
- Security: {audit.get('security_score')}
"""

        lang_instruction = "Respond in Romanian." if language == "ro" else "Respond in English."

        system_prompt = f"""You are a friendly and helpful AI sales assistant for AI Web Auditor,
a website auditing platform that helps businesses improve their websites.

Your goals:
1. Understand the customer's needs
2. Qualify leads (identify budget, timeline, pain points)
3. Recommend the appropriate package
4. Answer questions about the service
5. Move customers toward a purchase decision

Available packages:
- Starter (Free): Basic 2-audit scan, requires social share
- Pro (€1.99): 4 audit types, detailed breakdown, PDF report
- Full (€4.99): All 6 audits, professional PDF, priority support, AI recommendations

{audit_context}

Be conversational, helpful, and professional. Don't be pushy.
{lang_instruction}

Based on the conversation, also determine:
- Lead score (hot/warm/cold)
- Customer intent
- Recommended package
- Whether to show pricing or offer a demo
- Whether to escalate to a human"""

        try:
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                system=system_prompt,
                messages=messages
            )

            response_text = message.content[0].text

            # Analyze the conversation for qualification
            qualification = await self._qualify_lead(session_id, context)

            return SalesResponse(
                message=response_text,
                suggested_actions=self._get_suggested_actions(qualification),
                qualification=qualification,
                show_pricing=qualification.intent in [CustomerIntent.PRICING, CustomerIntent.PURCHASE] if qualification else False,
                show_demo=qualification.intent == CustomerIntent.DEMO if qualification else False,
                escalate_to_human=self._should_escalate(session_id)
            )

        except Exception as e:
            print(f"AI chat error: {e}")
            return self._generate_rule_based_response(
                self.conversations[session_id][-1].content if self.conversations[session_id] else "",
                context,
                language
            )

    def _generate_rule_based_response(
        self,
        user_message: str,
        context: Optional[dict],
        language: str
    ) -> SalesResponse:
        """Generate rule-based response when AI is not available"""

        message_lower = user_message.lower()

        # Detect intent
        if any(word in message_lower for word in ["price", "cost", "how much", "pricing", "pret", "cat costa"]):
            intent = CustomerIntent.PRICING
            if language == "ro":
                response = """Avem 3 pachete disponibile:

🆓 **Starter** (Gratuit) - 2 tipuri de audit, necesită distribuire pe social media
💼 **Pro** (€1.99) - 4 tipuri de audit, raport PDF, livrare email
🏆 **Full** (€4.99) - Toate cele 6 audituri, PDF profesional, suport prioritar, recomandări AI

Care pachet v-ar interesa?"""
            else:
                response = """We have 3 packages available:

🆓 **Starter** (Free) - 2 audit types, requires social share
💼 **Pro** (€1.99) - 4 audit types, PDF report, email delivery
🏆 **Full** (€4.99) - All 6 audits, professional PDF, priority support, AI recommendations

Which package would interest you?"""

        elif any(word in message_lower for word in ["demo", "try", "test", "incearca"]):
            intent = CustomerIntent.DEMO
            if language == "ro":
                response = "Puteți încerca gratuit! Introduceți URL-ul site-ului dvs. în câmpul de sus pentru a primi un audit instantaneu cu scorurile pentru performanță, SEO, securitate și altele."
            else:
                response = "You can try it for free! Enter your website URL in the field above to get an instant audit with scores for performance, SEO, security, and more."

        elif any(word in message_lower for word in ["help", "support", "problem", "issue", "ajutor", "problema"]):
            intent = CustomerIntent.SUPPORT
            if language == "ro":
                response = "Sunt aici să vă ajut! Ce problemă întâmpinați? Dacă este o problemă tehnică, puteți contacta support@aiwebauditor.com."
            else:
                response = "I'm here to help! What issue are you experiencing? For technical problems, you can reach support@aiwebauditor.com."

        elif any(word in message_lower for word in ["compare", "vs", "difference", "better", "diferenta", "comparatie"]):
            intent = CustomerIntent.COMPARISON
            if language == "ro":
                response = """Iată diferențele principale:

| Caracteristică | Starter | Pro | Full |
|----------------|---------|-----|------|
| Tipuri audit | 2 | 4 | 6 |
| Raport PDF | ❌ | Bazic | Profesional |
| Suport | Standard | Email | Prioritar |
| Recomandări AI | ❌ | ❌ | ✅ |

Recomand Pro pentru majoritatea afacerilor - oferă cel mai bun raport calitate/preț."""
            else:
                response = """Here are the main differences:

| Feature | Starter | Pro | Full |
|---------|---------|-----|------|
| Audit types | 2 | 4 | 6 |
| PDF Report | ❌ | Basic | Professional |
| Support | Standard | Email | Priority |
| AI Recommendations | ❌ | ❌ | ✅ |

I recommend Pro for most businesses - it offers the best value for money."""

        else:
            intent = CustomerIntent.INFORMATION
            if language == "ro":
                response = "AI Web Auditor analizează site-ul dvs. pentru performanță, SEO, securitate, conformitate GDPR și accesibilitate. Doriți să știți mai multe despre un anumit aspect?"
            else:
                response = "AI Web Auditor analyzes your website for performance, SEO, security, GDPR compliance, and accessibility. Would you like to know more about a specific aspect?"

        qualification = LeadQualification(
            lead_score=LeadScore.WARM,
            intent=intent,
            budget_indication=None,
            timeline=None,
            pain_points=[],
            recommended_package="pro",
            follow_up_actions=["Send pricing info", "Offer free trial"],
            confidence=0.6
        )

        return SalesResponse(
            message=response,
            suggested_actions=["View Packages", "Start Free Audit"],
            qualification=qualification,
            show_pricing=intent == CustomerIntent.PRICING,
            show_demo=intent == CustomerIntent.DEMO,
            escalate_to_human=False
        )

    async def _qualify_lead(
        self,
        session_id: str,
        context: Optional[dict]
    ) -> Optional[LeadQualification]:
        """Qualify a lead based on conversation history"""

        history = self.conversations.get(session_id, [])
        if len(history) < 2:
            return None

        # Simple rule-based qualification
        all_messages = " ".join([m.content.lower() for m in history if m.role == "user"])

        # Detect intent
        if any(word in all_messages for word in ["buy", "purchase", "pay", "cumpar", "achit"]):
            intent = CustomerIntent.PURCHASE
            lead_score = LeadScore.HOT
        elif any(word in all_messages for word in ["price", "cost", "pret", "cat costa"]):
            intent = CustomerIntent.PRICING
            lead_score = LeadScore.WARM
        elif any(word in all_messages for word in ["demo", "try", "test"]):
            intent = CustomerIntent.DEMO
            lead_score = LeadScore.WARM
        else:
            intent = CustomerIntent.INFORMATION
            lead_score = LeadScore.COLD

        # Detect pain points
        pain_points = []
        if any(word in all_messages for word in ["slow", "lent", "performance"]):
            pain_points.append("slow website performance")
        if any(word in all_messages for word in ["seo", "google", "search"]):
            pain_points.append("poor search visibility")
        if any(word in all_messages for word in ["security", "hack", "secure", "securitate"]):
            pain_points.append("security concerns")
        if any(word in all_messages for word in ["gdpr", "privacy", "cookie"]):
            pain_points.append("GDPR compliance")

        # Recommend package
        if lead_score == LeadScore.HOT or len(pain_points) > 2:
            recommended = "full"
        elif len(pain_points) > 0:
            recommended = "pro"
        else:
            recommended = "starter"

        return LeadQualification(
            lead_score=lead_score,
            intent=intent,
            budget_indication=None,
            timeline=None,
            pain_points=pain_points,
            recommended_package=recommended,
            follow_up_actions=self._get_follow_up_actions(lead_score, intent),
            confidence=0.7 if len(history) > 4 else 0.5
        )

    def _get_suggested_actions(self, qualification: Optional[LeadQualification]) -> List[str]:
        """Get suggested actions based on qualification"""
        if not qualification:
            return ["Start Free Audit", "View Packages"]

        if qualification.lead_score == LeadScore.HOT:
            return ["Complete Purchase", "Talk to Sales"]
        elif qualification.intent == CustomerIntent.DEMO:
            return ["Start Free Audit", "View Demo Video"]
        elif qualification.intent == CustomerIntent.PRICING:
            return ["View Packages", "Get Custom Quote"]
        else:
            return ["Learn More", "Start Free Audit"]

    def _get_follow_up_actions(self, lead_score: LeadScore, intent: CustomerIntent) -> List[str]:
        """Get follow-up actions for CRM"""
        actions = []

        if lead_score == LeadScore.HOT:
            actions.append("Priority follow-up call")
            actions.append("Send personalized offer")
        elif lead_score == LeadScore.WARM:
            actions.append("Send nurture email sequence")
            actions.append("Schedule follow-up in 3 days")
        else:
            actions.append("Add to newsletter")
            actions.append("Send educational content")

        return actions

    def _should_escalate(self, session_id: str) -> bool:
        """Determine if conversation should be escalated to human"""
        history = self.conversations.get(session_id, [])

        # Escalate after many messages
        if len(history) > 10:
            return True

        # Check for escalation keywords
        all_messages = " ".join([m.content.lower() for m in history if m.role == "user"])
        escalation_keywords = ["speak to human", "real person", "manager", "complaint", "refund", "cancel"]

        return any(keyword in all_messages for keyword in escalation_keywords)

    def get_conversation_history(self, session_id: str) -> List[ConversationMessage]:
        """Get conversation history for a session"""
        return self.conversations.get(session_id, [])

    def clear_conversation(self, session_id: str):
        """Clear conversation history for a session"""
        if session_id in self.conversations:
            del self.conversations[session_id]
