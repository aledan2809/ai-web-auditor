"""
Audit repository for database operations
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from database.models import (
    Audit, AuditIssue, PerformanceMetric, SEOMetric,
    SecurityMetric, GDPRMetric, AccessibilityMetric
)


class AuditRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        url: str,
        audit_types: List[str],
        user_id: Optional[str] = None
    ) -> Audit:
        """Create a new audit"""
        audit = Audit(
            url=url,
            audit_types=audit_types,
            user_id=user_id,
            status="pending"
        )
        self.db.add(audit)
        await self.db.flush()
        await self.db.refresh(audit)
        return audit

    async def get_by_id(self, audit_id: str, include_relations: bool = True) -> Optional[Audit]:
        """Get audit by ID with optional relations"""
        query = select(Audit).where(Audit.id == audit_id)

        if include_relations:
            query = query.options(
                selectinload(Audit.issues),
                selectinload(Audit.performance_metrics),
                selectinload(Audit.seo_metrics),
                selectinload(Audit.security_metrics),
                selectinload(Audit.gdpr_metrics),
                selectinload(Audit.accessibility_metrics)
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_audits(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        url_search: Optional[str] = None,
        min_score: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """Get user's audits with filters and pagination"""

        # Base query
        query = select(Audit).where(Audit.user_id == user_id)

        # Apply filters
        conditions = []

        if status:
            conditions.append(Audit.status == status)

        if url_search:
            conditions.append(Audit.url.ilike(f"%{url_search}%"))

        if min_score is not None:
            conditions.append(Audit.overall_score >= min_score)

        if date_from:
            conditions.append(Audit.created_at >= date_from)

        if date_to:
            conditions.append(Audit.created_at <= date_to)

        if conditions:
            query = query.where(and_(*conditions))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply sorting
        sort_column = getattr(Audit, sort_by, Audit.created_at)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        # Load relations
        query = query.options(selectinload(Audit.issues))

        result = await self.db.execute(query)
        audits = list(result.scalars().all())

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
            "audits": audits
        }

    async def get_all(
        self,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get all audits (admin view)"""
        query = select(Audit)

        if status:
            query = query.where(Audit.status == status)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Paginate
        offset = (page - 1) * limit
        query = query.order_by(Audit.created_at.desc()).offset(offset).limit(limit)
        query = query.options(selectinload(Audit.issues))

        result = await self.db.execute(query)
        audits = list(result.scalars().all())

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
            "audits": audits
        }

    async def update_status(
        self,
        audit_id: str,
        status: str,
        completed_at: Optional[datetime] = None
    ) -> Optional[Audit]:
        """Update audit status"""
        audit = await self.get_by_id(audit_id, include_relations=False)
        if not audit:
            return None

        audit.status = status
        if completed_at:
            audit.completed_at = completed_at

        await self.db.flush()
        return audit

    async def update_scores(
        self,
        audit_id: str,
        overall_score: int,
        performance_score: Optional[int] = None,
        seo_score: Optional[int] = None,
        security_score: Optional[int] = None,
        gdpr_score: Optional[int] = None,
        accessibility_score: Optional[int] = None
    ) -> Optional[Audit]:
        """Update audit scores"""
        audit = await self.get_by_id(audit_id, include_relations=False)
        if not audit:
            return None

        audit.overall_score = overall_score
        if performance_score is not None:
            audit.performance_score = performance_score
        if seo_score is not None:
            audit.seo_score = seo_score
        if security_score is not None:
            audit.security_score = security_score
        if gdpr_score is not None:
            audit.gdpr_score = gdpr_score
        if accessibility_score is not None:
            audit.accessibility_score = accessibility_score

        await self.db.flush()
        return audit

    async def update_screenshots(
        self,
        audit_id: str,
        desktop: Optional[str] = None,
        mobile: Optional[str] = None
    ) -> Optional[Audit]:
        """Update audit screenshots"""
        audit = await self.get_by_id(audit_id, include_relations=False)
        if not audit:
            return None

        if desktop:
            audit.desktop_screenshot = desktop
        if mobile:
            audit.mobile_screenshot = mobile

        await self.db.flush()
        return audit

    async def add_issue(
        self,
        audit_id: str,
        category: str,
        severity: str,
        title: str,
        description: str,
        recommendation: str,
        affected_element: Optional[str] = None,
        estimated_hours: float = 1.0,
        complexity: str = "medium"
    ) -> AuditIssue:
        """Add issue to audit"""
        issue = AuditIssue(
            audit_id=audit_id,
            category=category,
            severity=severity,
            title=title,
            description=description,
            recommendation=recommendation,
            affected_element=affected_element,
            estimated_hours=estimated_hours,
            complexity=complexity
        )
        self.db.add(issue)
        await self.db.flush()
        return issue

    async def add_issues_bulk(self, audit_id: str, issues: List[Dict]) -> List[AuditIssue]:
        """Add multiple issues to audit"""
        issue_objects = []
        for issue_data in issues:
            issue = AuditIssue(
                audit_id=audit_id,
                category=issue_data.get("category", "general"),
                severity=issue_data.get("severity", "medium"),
                title=issue_data.get("title", ""),
                description=issue_data.get("description", ""),
                recommendation=issue_data.get("recommendation", ""),
                affected_element=issue_data.get("affected_element"),
                estimated_hours=issue_data.get("estimated_hours", 1.0),
                complexity=issue_data.get("complexity", "medium")
            )
            self.db.add(issue)
            issue_objects.append(issue)

        await self.db.flush()
        return issue_objects

    async def add_performance_metrics(self, audit_id: str, metrics: Dict) -> PerformanceMetric:
        """Add performance metrics"""
        metric = PerformanceMetric(
            audit_id=audit_id,
            score=metrics.get("score", 0),
            lcp=metrics.get("lcp"),
            fid=metrics.get("fid"),
            cls=metrics.get("cls"),
            ttfb=metrics.get("ttfb"),
            speed_index=metrics.get("speed_index"),
            total_blocking_time=metrics.get("total_blocking_time"),
            first_contentful_paint=metrics.get("first_contentful_paint")
        )
        self.db.add(metric)
        await self.db.flush()
        return metric

    async def add_seo_metrics(self, audit_id: str, metrics: Dict) -> SEOMetric:
        """Add SEO metrics"""
        metric = SEOMetric(
            audit_id=audit_id,
            score=metrics.get("score", 0),
            title=metrics.get("title"),
            title_length=metrics.get("title_length", 0),
            meta_description=metrics.get("meta_description"),
            meta_description_length=metrics.get("meta_description_length", 0),
            h1_count=metrics.get("h1_count", 0),
            h1_texts=metrics.get("h1_texts", []),
            canonical_url=metrics.get("canonical_url"),
            robots_txt_exists=metrics.get("robots_txt_exists", False),
            sitemap_exists=metrics.get("sitemap_exists", False),
            structured_data=metrics.get("structured_data", []),
            broken_links=metrics.get("broken_links", []),
            image_alt_missing=metrics.get("image_alt_missing", 0)
        )
        self.db.add(metric)
        await self.db.flush()
        return metric

    async def add_security_metrics(self, audit_id: str, metrics: Dict) -> SecurityMetric:
        """Add security metrics"""
        metric = SecurityMetric(
            audit_id=audit_id,
            score=metrics.get("score", 0),
            https_enabled=metrics.get("https_enabled", False),
            ssl_valid=metrics.get("ssl_valid", False),
            ssl_expiry_days=metrics.get("ssl_expiry_days"),
            hsts_enabled=metrics.get("hsts_enabled", False),
            csp_enabled=metrics.get("csp_enabled", False),
            x_frame_options=metrics.get("x_frame_options", False),
            x_content_type_options=metrics.get("x_content_type_options", False),
            cookies_secure=metrics.get("cookies_secure", False),
            cookies_httponly=metrics.get("cookies_httponly", False),
            exposed_emails=metrics.get("exposed_emails", []),
            exposed_api_keys=metrics.get("exposed_api_keys", False)
        )
        self.db.add(metric)
        await self.db.flush()
        return metric

    async def add_gdpr_metrics(self, audit_id: str, metrics: Dict) -> GDPRMetric:
        """Add GDPR metrics"""
        metric = GDPRMetric(
            audit_id=audit_id,
            score=metrics.get("score", 0),
            cookie_banner_present=metrics.get("cookie_banner_present", False),
            privacy_policy_link=metrics.get("privacy_policy_link", False),
            cookie_categories_explained=metrics.get("cookie_categories_explained", False),
            opt_out_option=metrics.get("opt_out_option", False),
            third_party_trackers=metrics.get("third_party_trackers", []),
            google_analytics=metrics.get("google_analytics", False),
            facebook_pixel=metrics.get("facebook_pixel", False),
            data_retention_info=metrics.get("data_retention_info", False)
        )
        self.db.add(metric)
        await self.db.flush()
        return metric

    async def add_accessibility_metrics(self, audit_id: str, metrics: Dict) -> AccessibilityMetric:
        """Add accessibility metrics"""
        metric = AccessibilityMetric(
            audit_id=audit_id,
            score=metrics.get("score", 0),
            wcag_level=metrics.get("wcag_level", "A"),
            color_contrast_issues=metrics.get("color_contrast_issues", 0),
            missing_alt_texts=metrics.get("missing_alt_texts", 0),
            missing_form_labels=metrics.get("missing_form_labels", 0),
            keyboard_navigation=metrics.get("keyboard_navigation", False),
            aria_usage=metrics.get("aria_usage", 0),
            heading_hierarchy_valid=metrics.get("heading_hierarchy_valid", False)
        )
        self.db.add(metric)
        await self.db.flush()
        return metric

    async def delete(self, audit_id: str) -> bool:
        """Delete audit and all related data"""
        audit = await self.get_by_id(audit_id, include_relations=False)
        if not audit:
            return False

        await self.db.delete(audit)
        await self.db.flush()
        return True

    async def get_stats(self) -> Dict[str, Any]:
        """Get audit statistics for admin dashboard"""
        # Total audits
        total_result = await self.db.execute(select(func.count(Audit.id)))
        total = total_result.scalar() or 0

        # By status
        status_result = await self.db.execute(
            select(Audit.status, func.count(Audit.id))
            .group_by(Audit.status)
        )
        by_status = dict(status_result.all())

        # Average score
        avg_result = await self.db.execute(
            select(func.avg(Audit.overall_score))
            .where(Audit.status == "completed")
        )
        avg_score = avg_result.scalar() or 0

        # Top issues
        top_issues_result = await self.db.execute(
            select(AuditIssue.title, func.count(AuditIssue.id).label("count"))
            .group_by(AuditIssue.title)
            .order_by(func.count(AuditIssue.id).desc())
            .limit(10)
        )
        top_issues = [{"title": row[0], "count": row[1]} for row in top_issues_result.all()]

        return {
            "total": total,
            "by_status": by_status,
            "avg_score": round(float(avg_score), 1),
            "top_issues": top_issues
        }
