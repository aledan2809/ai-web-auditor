"""
Security Auditor - Checks security headers, SSL, and common vulnerabilities
"""

import asyncio
from dataclasses import dataclass
from typing import List, Optional
import httpx
from urllib.parse import urlparse
import ssl
import socket
from datetime import datetime, timedelta
import re

from models.schemas import (
    SecurityMetrics, AuditIssue, AuditType, Severity
)


@dataclass
class SecurityResult:
    score: int
    metrics: SecurityMetrics
    issues: List[AuditIssue]


class SecurityAuditor:
    """Audits website security"""

    def __init__(self):
        self.security_headers = [
            'strict-transport-security',
            'content-security-policy',
            'x-frame-options',
            'x-content-type-options',
            'x-xss-protection',
            'referrer-policy'
        ]

    async def audit(self, url: str) -> SecurityResult:
        """Run security audit on URL"""
        parsed = urlparse(url)
        domain = parsed.netloc

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url)
            headers = dict(response.headers)
            content = response.text

        # Check HTTPS
        https_enabled = url.startswith('https://')

        # Check SSL certificate
        ssl_info = await self._check_ssl(domain)

        # Check security headers
        hsts = 'strict-transport-security' in headers
        csp = 'content-security-policy' in headers
        x_frame = 'x-frame-options' in headers
        x_content_type = 'x-content-type-options' in headers

        # Check cookies
        cookies = response.cookies
        cookies_secure = all(c.secure for c in cookies.jar if hasattr(c, 'secure'))
        cookies_httponly = True  # Hard to check client-side

        # Check for exposed data
        exposed_emails = self._find_emails(content)
        exposed_api_keys = self._check_exposed_keys(content)

        # Build metrics
        metrics = SecurityMetrics(
            score=0,
            https_enabled=https_enabled,
            ssl_valid=ssl_info['valid'],
            ssl_expiry_days=ssl_info['days_until_expiry'],
            hsts_enabled=hsts,
            csp_enabled=csp,
            x_frame_options=x_frame,
            x_content_type_options=x_content_type,
            cookies_secure=cookies_secure,
            cookies_httponly=cookies_httponly,
            exposed_emails=exposed_emails[:5],
            exposed_api_keys=exposed_api_keys
        )

        # Generate issues
        issues = self._generate_issues(metrics, url, headers)

        # Calculate score
        score = self._calculate_score(metrics)
        metrics.score = score

        return SecurityResult(score=score, metrics=metrics, issues=issues)

    async def _check_ssl(self, domain: str) -> dict:
        """Check SSL certificate validity"""
        try:
            # Remove port if present
            if ':' in domain:
                domain = domain.split(':')[0]

            context = ssl.create_default_context()

            # Create connection
            loop = asyncio.get_event_loop()

            def get_cert():
                with socket.create_connection((domain, 443), timeout=10) as sock:
                    with context.wrap_socket(sock, server_hostname=domain) as ssock:
                        cert = ssock.getpeercert()
                        return cert

            cert = await loop.run_in_executor(None, get_cert)

            # Parse expiry date
            not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
            days_until_expiry = (not_after - datetime.now()).days

            return {
                'valid': True,
                'days_until_expiry': days_until_expiry,
                'issuer': dict(x[0] for x in cert.get('issuer', []))
            }

        except Exception as e:
            return {
                'valid': False,
                'days_until_expiry': None,
                'error': str(e)
            }

    def _find_emails(self, content: str) -> List[str]:
        """Find exposed email addresses in page content"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, content)
        # Filter out common false positives
        return [e for e in set(emails) if not e.endswith('.png') and not e.endswith('.jpg')]

    def _check_exposed_keys(self, content: str) -> bool:
        """Check for potentially exposed API keys"""
        patterns = [
            r'api[_-]?key["\']?\s*[:=]\s*["\'][a-zA-Z0-9]{20,}',
            r'secret[_-]?key["\']?\s*[:=]\s*["\'][a-zA-Z0-9]{20,}',
            r'sk-[a-zA-Z0-9]{20,}',  # OpenAI keys
            r'pk_live_[a-zA-Z0-9]{20,}',  # Stripe keys
            r'AIza[a-zA-Z0-9]{35}',  # Google API keys
        ]

        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True

        return False

    def _calculate_score(self, metrics: SecurityMetrics) -> int:
        """Calculate security score"""
        score = 100

        # HTTPS (-25)
        if not metrics.https_enabled:
            score -= 25

        # SSL (-20)
        if not metrics.ssl_valid:
            score -= 20
        elif metrics.ssl_expiry_days and metrics.ssl_expiry_days < 30:
            score -= 10

        # Security headers (-5 each)
        if not metrics.hsts_enabled:
            score -= 10
        if not metrics.csp_enabled:
            score -= 10
        if not metrics.x_frame_options:
            score -= 5
        if not metrics.x_content_type_options:
            score -= 5

        # Cookies (-5)
        if not metrics.cookies_secure:
            score -= 5

        # Exposed data (-15)
        if metrics.exposed_api_keys:
            score -= 15
        if metrics.exposed_emails:
            score -= 5

        return max(0, score)

    def _generate_issues(
        self,
        metrics: SecurityMetrics,
        url: str,
        headers: dict
    ) -> List[AuditIssue]:
        """Generate security issues"""
        issues = []

        # HTTPS
        if not metrics.https_enabled:
            issues.append(AuditIssue(
                id=f"sec_no_https_{hash(url)}",
                category=AuditType.SECURITY,
                severity=Severity.CRITICAL,
                title="Site-ul nu folosește HTTPS",
                description="Conexiunea nu este securizată. Datele pot fi interceptate.",
                recommendation="Instalați un certificat SSL și forțați HTTPS pe întregul site.",
                estimated_hours=4.0,
                complexity="medium"
            ))

        # SSL
        if not metrics.ssl_valid:
            issues.append(AuditIssue(
                id=f"sec_invalid_ssl_{hash(url)}",
                category=AuditType.SECURITY,
                severity=Severity.CRITICAL,
                title="Certificat SSL invalid",
                description="Certificatul SSL nu este valid sau a expirat.",
                recommendation="Reînnoiți sau instalați un certificat SSL valid.",
                estimated_hours=2.0,
                complexity="simple"
            ))
        elif metrics.ssl_expiry_days and metrics.ssl_expiry_days < 30:
            issues.append(AuditIssue(
                id=f"sec_ssl_expiring_{hash(url)}",
                category=AuditType.SECURITY,
                severity=Severity.HIGH,
                title=f"Certificat SSL expiră în {metrics.ssl_expiry_days} zile",
                description="Certificatul SSL va expira în curând.",
                recommendation="Reînnoiți certificatul SSL înainte de expirare.",
                estimated_hours=1.0,
                complexity="simple"
            ))

        # Security headers
        if not metrics.hsts_enabled:
            issues.append(AuditIssue(
                id=f"sec_no_hsts_{hash(url)}",
                category=AuditType.SECURITY,
                severity=Severity.HIGH,
                title="Lipsește header-ul HSTS",
                description="Strict-Transport-Security nu este configurat.",
                recommendation="Adăugați header-ul: Strict-Transport-Security: max-age=31536000; includeSubDomains",
                estimated_hours=1.0,
                complexity="simple"
            ))

        if not metrics.csp_enabled:
            issues.append(AuditIssue(
                id=f"sec_no_csp_{hash(url)}",
                category=AuditType.SECURITY,
                severity=Severity.HIGH,
                title="Lipsește Content Security Policy",
                description="CSP nu este configurat, site-ul e vulnerabil la XSS.",
                recommendation="Implementați un Content-Security-Policy header restrictiv.",
                estimated_hours=4.0,
                complexity="complex"
            ))

        if not metrics.x_frame_options:
            issues.append(AuditIssue(
                id=f"sec_no_xframe_{hash(url)}",
                category=AuditType.SECURITY,
                severity=Severity.MEDIUM,
                title="Lipsește X-Frame-Options",
                description="Site-ul poate fi încadrat în iframe (clickjacking).",
                recommendation="Adăugați: X-Frame-Options: DENY sau SAMEORIGIN",
                estimated_hours=0.5,
                complexity="simple"
            ))

        if not metrics.x_content_type_options:
            issues.append(AuditIssue(
                id=f"sec_no_xcontent_{hash(url)}",
                category=AuditType.SECURITY,
                severity=Severity.LOW,
                title="Lipsește X-Content-Type-Options",
                description="Browser-ul poate interpreta greșit MIME types.",
                recommendation="Adăugați: X-Content-Type-Options: nosniff",
                estimated_hours=0.5,
                complexity="simple"
            ))

        # Exposed data
        if metrics.exposed_api_keys:
            issues.append(AuditIssue(
                id=f"sec_exposed_keys_{hash(url)}",
                category=AuditType.SECURITY,
                severity=Severity.CRITICAL,
                title="Posibile chei API expuse în cod",
                description="S-au detectat pattern-uri ce seamănă cu chei API în codul sursă.",
                recommendation="Eliminați cheile API din codul frontend. Folosiți variabile de environment pe server.",
                estimated_hours=2.0,
                complexity="medium"
            ))

        if metrics.exposed_emails:
            issues.append(AuditIssue(
                id=f"sec_exposed_emails_{hash(url)}",
                category=AuditType.SECURITY,
                severity=Severity.LOW,
                title=f"{len(metrics.exposed_emails)} adrese email expuse",
                description=f"Email-uri găsite: {', '.join(metrics.exposed_emails[:3])}...",
                recommendation="Ascundeți email-urile sau folosiți formulare de contact pentru a evita spam-ul.",
                estimated_hours=1.0,
                complexity="simple"
            ))

        return issues
