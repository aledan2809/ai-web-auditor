"""
Translations for AI Web Auditor
Supports: Romanian (ro), English (en)
Note: Romanian uses ASCII-only characters (no diacritics) for PDF compatibility
"""

TRANSLATIONS = {
    "ro": {
        # Report titles
        "report_title": "RAPORT DE AUDIT WEB",
        "audit_date": "Data auditului",
        "overall_score": "SCOR GENERAL",
        "category_scores": "Scor pe Categorii",
        "issues_identified": "Probleme Identificate",
        "issue_details": "Detalii Probleme",
        "generated_by": "Raport generat de AI Web Auditor",

        # Categories
        "category": "Categorie",
        "score": "Scor",
        "status": "Status",
        "severity": "Severitate",
        "count": "Numar",

        # Severity levels
        "critical": "Critice",
        "high": "Importante",
        "medium": "Medii",
        "low": "Minore",
        "info": "Informatii",

        # Score labels
        "excellent": "Excelent",
        "very_good": "Foarte Bun",
        "good": "Bun",
        "satisfactory": "Satisfacator",
        "needs_improvement": "Necesita Imbunatatiri",
        "significant_issues": "Probleme Semnificative",

        # Status icons
        "status_good": "Bun",
        "status_satisfactory": "Satisfacator",
        "status_needs_attention": "Necesita atentie",

        # Common terms
        "recommendation": "Recomandare",
        "estimated_time": "Timp estimat",
        "complexity": "Complexitate",
        "simple": "simplu",
        "medium_complexity": "mediu",
        "complex": "complex",

        # SEO Issues
        "seo_no_title": "Lipseste tag-ul title",
        "seo_no_title_desc": "Pagina nu are un tag <title> definit.",
        "seo_no_title_rec": "Adaugati un title unic si descriptiv de 50-60 caractere care include cuvantul cheie principal.",

        "seo_short_title": "Title prea scurt",
        "seo_short_title_desc": "Title-ul are {0} caractere. Recomandat: {1}-{2}",
        "seo_short_title_rec": "Extindeti title-ul pentru a include mai multe cuvinte cheie relevante.",

        "seo_long_title": "Title prea lung",
        "seo_long_title_desc": "Title-ul are {0} caractere si va fi trunchiat in SERP.",
        "seo_long_title_rec": "Scurtati title-ul la maxim 60 caractere.",

        "seo_no_meta": "Lipseste meta description",
        "seo_no_meta_desc": "Pagina nu are meta description definit.",
        "seo_no_meta_rec": "Adaugati o meta description de 150-160 caractere care descrie continutul paginii.",

        "seo_no_h1": "Lipseste tag-ul H1",
        "seo_no_h1_desc": "Pagina nu are un heading H1.",
        "seo_no_h1_rec": "Adaugati un singur H1 care contine cuvantul cheie principal.",

        "seo_multiple_h1": "Multiple tag-uri H1",
        "seo_multiple_h1_desc": "Pagina are {0} tag-uri H1. Recomandat: doar unul.",
        "seo_multiple_h1_rec": "Pastrati un singur H1 si convertiti restul in H2 sau H3.",

        "seo_no_robots": "Lipseste robots.txt",
        "seo_no_robots_desc": "Site-ul nu are fisier robots.txt.",
        "seo_no_robots_rec": "Creati un fisier robots.txt pentru a ghida crawlerele.",

        "seo_no_sitemap": "Lipseste sitemap.xml",
        "seo_no_sitemap_desc": "Site-ul nu are sitemap XML.",
        "seo_no_sitemap_rec": "Generati si publicati un sitemap.xml pentru indexare optima.",

        "seo_broken_links": "{0} link-uri broken gasite",
        "seo_broken_links_desc": "Link-uri cu eroare: {0}...",
        "seo_broken_links_rec": "Corectati sau eliminati link-urile care returneaza erori 4xx/5xx.",

        "seo_missing_alt": "{0} imagini fara atribut alt",
        "seo_missing_alt_desc": "Imaginile fara alt text afecteaza SEO si accesibilitatea.",
        "seo_missing_alt_rec": "Adaugati text alt descriptiv pentru toate imaginile.",

        # Performance Issues
        "perf_lcp_slow": "Largest Contentful Paint (LCP) prea mare",
        "perf_lcp_slow_desc": "LCP actual: {0}s. Recomandat: sub 2.5s",
        "perf_lcp_slow_rec": "Optimizati imaginile hero, folositi lazy loading, CDN, si preload pentru resurse critice.",

        "perf_fid_slow": "First Input Delay (FID) prea mare",
        "perf_fid_slow_desc": "FID actual: {0}ms. Recomandat: sub 100ms",
        "perf_fid_slow_rec": "Reduceti JavaScript-ul care blocheaza thread-ul principal, folositi code splitting.",

        "perf_cls_high": "Cumulative Layout Shift (CLS) mare",
        "perf_cls_high_desc": "CLS actual: {0}. Recomandat: sub 0.1",
        "perf_cls_high_rec": "Specificati dimensiuni pentru imagini si iframe-uri, evitati inserarea dinamica de continut.",

        "perf_ttfb_slow": "Time to First Byte (TTFB) prea mare",
        "perf_ttfb_slow_desc": "TTFB actual: {0}ms. Recomandat: sub 800ms",
        "perf_ttfb_slow_rec": "Optimizati server-side rendering, folositi caching, CDN, si baza de date optimizata.",

        "perf_fcp_slow": "First Contentful Paint (FCP) lent",
        "perf_fcp_slow_desc": "FCP actual: {0}s. Recomandat: sub 1.8s",
        "perf_fcp_slow_rec": "Eliminati resursele care blocheaza randarea, minimizati CSS critic, si folositi font-display: swap.",

        "perf_speed_index_slow": "Speed Index ridicat",
        "perf_speed_index_slow_desc": "Speed Index actual: {0}s. Recomandat: sub 3.4s",
        "perf_speed_index_slow_rec": "Prioritizati incarcarea continutului vizibil, folositi lazy loading pentru restul.",

        # Security Issues
        "sec_no_https": "Site-ul nu foloseste HTTPS",
        "sec_no_https_desc": "Conexiunea nu este securizata cu SSL/TLS.",
        "sec_no_https_rec": "Instalati un certificat SSL si redirectionati tot traficul catre HTTPS.",

        "sec_no_hsts": "Lipseste header-ul HSTS",
        "sec_no_hsts_desc": "Strict-Transport-Security nu este configurat.",
        "sec_no_hsts_rec": "Adaugati header-ul HSTS pentru a forta conexiuni HTTPS.",

        "sec_no_csp": "Lipseste Content Security Policy",
        "sec_no_csp_desc": "Header-ul CSP nu este configurat.",
        "sec_no_csp_rec": "Implementati CSP pentru a preveni atacuri XSS si injection.",

        "sec_no_xframe": "Lipseste X-Frame-Options",
        "sec_no_xframe_desc": "Site-ul poate fi incarcat intr-un iframe (risc clickjacking).",
        "sec_no_xframe_rec": "Adaugati header-ul X-Frame-Options: DENY sau SAMEORIGIN.",

        "sec_no_xcontent": "Lipseste X-Content-Type-Options",
        "sec_no_xcontent_desc": "Browser-ul poate interpreta gresit tipul de continut.",
        "sec_no_xcontent_rec": "Adaugati header-ul X-Content-Type-Options: nosniff.",

        "sec_cookies_insecure": "Cookie-uri nesecurizate",
        "sec_cookies_insecure_desc": "Cookie-urile nu au flag-urile Secure si HttpOnly.",
        "sec_cookies_insecure_rec": "Configurati cookie-urile cu Secure, HttpOnly si SameSite.",

        # GDPR Issues
        "gdpr_no_privacy": "Lipseste politica de confidentialitate",
        "gdpr_no_privacy_desc": "Site-ul nu are o politica de confidentialitate vizibila.",
        "gdpr_no_privacy_rec": "Creati o pagina de Privacy Policy accesibila din footer.",

        "gdpr_no_cookie": "Lipseste politica de cookie-uri",
        "gdpr_no_cookie_desc": "Site-ul nu are o politica de cookie-uri.",
        "gdpr_no_cookie_rec": "Creati o pagina Cookie Policy si un banner de consimtamant.",

        "gdpr_no_consent": "Lipseste bannerul de consimtamant cookie",
        "gdpr_no_consent_desc": "Site-ul nu solicita consimtamantul pentru cookie-uri.",
        "gdpr_no_consent_rec": "Implementati un banner de cookie cu optiuni granulare.",

        "gdpr_analytics": "Tracking fara consimtamant",
        "gdpr_analytics_desc": "Script-uri de analytics sunt incarcate fara consimtamant.",
        "gdpr_analytics_rec": "Incarcati script-urile de tracking doar dupa obtinerea consimtamantului.",

        # Accessibility Issues
        "a11y_no_lang": "Lipseste atributul lang",
        "a11y_no_lang_desc": "Tag-ul <html> nu are atributul lang definit.",
        "a11y_no_lang_rec": "Adaugati lang='ro' sau limba corespunzatoare pe tag-ul <html>.",

        "a11y_missing_alt": "Imagini fara text alternativ",
        "a11y_missing_alt_desc": "{0} imagini nu au atributul alt.",
        "a11y_missing_alt_rec": "Adaugati text alt descriptiv pentru toate imaginile.",

        "a11y_low_contrast": "Contrast scazut",
        "a11y_low_contrast_desc": "Unele elemente au contrast insuficient.",
        "a11y_low_contrast_rec": "Asigurati un ratio de contrast minim de 4.5:1 pentru text.",

        "a11y_no_skip_link": "Lipseste link-ul 'Skip to content'",
        "a11y_no_skip_link_desc": "Nu exista un link pentru a sari peste navigatie.",
        "a11y_no_skip_link_rec": "Adaugati un link ascuns 'Skip to main content' la inceputul paginii.",

        "a11y_missing_labels": "Formulare fara etichete",
        "a11y_missing_labels_desc": "{0} campuri de formular nu au etichete asociate.",
        "a11y_missing_labels_rec": "Adaugati tag-uri <label> pentru toate campurile de input.",
    },

    "en": {
        # Report titles
        "report_title": "WEB AUDIT REPORT",
        "audit_date": "Audit date",
        "overall_score": "OVERALL SCORE",
        "category_scores": "Category Scores",
        "issues_identified": "Issues Identified",
        "issue_details": "Issue Details",
        "generated_by": "Report generated by AI Web Auditor",

        # Categories
        "category": "Category",
        "score": "Score",
        "status": "Status",
        "severity": "Severity",
        "count": "Count",

        # Severity levels
        "critical": "Critical",
        "high": "High",
        "medium": "Medium",
        "low": "Low",
        "info": "Info",

        # Score labels
        "excellent": "Excellent",
        "very_good": "Very Good",
        "good": "Good",
        "satisfactory": "Satisfactory",
        "needs_improvement": "Needs Improvement",
        "significant_issues": "Significant Issues",

        # Status icons
        "status_good": "Good",
        "status_satisfactory": "Satisfactory",
        "status_needs_attention": "Needs attention",

        # Common terms
        "recommendation": "Recommendation",
        "estimated_time": "Estimated time",
        "complexity": "Complexity",
        "simple": "simple",
        "medium_complexity": "medium",
        "complex": "complex",

        # SEO Issues
        "seo_no_title": "Missing title tag",
        "seo_no_title_desc": "The page does not have a <title> tag defined.",
        "seo_no_title_rec": "Add a unique and descriptive title of 50-60 characters that includes the main keyword.",

        "seo_short_title": "Title too short",
        "seo_short_title_desc": "Title has {0} characters. Recommended: {1}-{2}",
        "seo_short_title_rec": "Expand the title to include more relevant keywords.",

        "seo_long_title": "Title too long",
        "seo_long_title_desc": "Title has {0} characters and will be truncated in SERP.",
        "seo_long_title_rec": "Shorten the title to a maximum of 60 characters.",

        "seo_no_meta": "Missing meta description",
        "seo_no_meta_desc": "The page does not have a meta description defined.",
        "seo_no_meta_rec": "Add a meta description of 150-160 characters that describes the page content.",

        "seo_no_h1": "Missing H1 tag",
        "seo_no_h1_desc": "The page does not have an H1 heading.",
        "seo_no_h1_rec": "Add a single H1 that contains the main keyword.",

        "seo_multiple_h1": "Multiple H1 tags",
        "seo_multiple_h1_desc": "The page has {0} H1 tags. Recommended: only one.",
        "seo_multiple_h1_rec": "Keep a single H1 and convert the rest to H2 or H3.",

        "seo_no_robots": "Missing robots.txt",
        "seo_no_robots_desc": "The site does not have a robots.txt file.",
        "seo_no_robots_rec": "Create a robots.txt file to guide crawlers.",

        "seo_no_sitemap": "Missing sitemap.xml",
        "seo_no_sitemap_desc": "The site does not have an XML sitemap.",
        "seo_no_sitemap_rec": "Generate and publish a sitemap.xml for optimal indexing.",

        "seo_broken_links": "{0} broken links found",
        "seo_broken_links_desc": "Links with errors: {0}...",
        "seo_broken_links_rec": "Fix or remove links that return 4xx/5xx errors.",

        "seo_missing_alt": "{0} images without alt attribute",
        "seo_missing_alt_desc": "Images without alt text affect SEO and accessibility.",
        "seo_missing_alt_rec": "Add descriptive alt text for all images.",

        # Performance Issues
        "perf_lcp_slow": "Largest Contentful Paint (LCP) too high",
        "perf_lcp_slow_desc": "Actual LCP: {0}s. Recommended: under 2.5s",
        "perf_lcp_slow_rec": "Optimize hero images, use lazy loading, CDN, and preload for critical resources.",

        "perf_fid_slow": "First Input Delay (FID) too high",
        "perf_fid_slow_desc": "Actual FID: {0}ms. Recommended: under 100ms",
        "perf_fid_slow_rec": "Reduce JavaScript that blocks the main thread, use code splitting.",

        "perf_cls_high": "Cumulative Layout Shift (CLS) high",
        "perf_cls_high_desc": "Actual CLS: {0}. Recommended: under 0.1",
        "perf_cls_high_rec": "Specify dimensions for images and iframes, avoid dynamic content insertion.",

        "perf_ttfb_slow": "Time to First Byte (TTFB) too high",
        "perf_ttfb_slow_desc": "Actual TTFB: {0}ms. Recommended: under 800ms",
        "perf_ttfb_slow_rec": "Optimize server-side rendering, use caching, CDN, and optimized database.",

        "perf_fcp_slow": "First Contentful Paint (FCP) slow",
        "perf_fcp_slow_desc": "Actual FCP: {0}s. Recommended: under 1.8s",
        "perf_fcp_slow_rec": "Remove render-blocking resources, minimize critical CSS, use font-display: swap.",

        "perf_speed_index_slow": "Speed Index high",
        "perf_speed_index_slow_desc": "Actual Speed Index: {0}s. Recommended: under 3.4s",
        "perf_speed_index_slow_rec": "Prioritize loading of visible content, use lazy loading for the rest.",

        # Security Issues
        "sec_no_https": "Site not using HTTPS",
        "sec_no_https_desc": "Connection is not secured with SSL/TLS.",
        "sec_no_https_rec": "Install an SSL certificate and redirect all traffic to HTTPS.",

        "sec_no_hsts": "Missing HSTS header",
        "sec_no_hsts_desc": "Strict-Transport-Security is not configured.",
        "sec_no_hsts_rec": "Add HSTS header to force HTTPS connections.",

        "sec_no_csp": "Missing Content Security Policy",
        "sec_no_csp_desc": "CSP header is not configured.",
        "sec_no_csp_rec": "Implement CSP to prevent XSS and injection attacks.",

        "sec_no_xframe": "Missing X-Frame-Options",
        "sec_no_xframe_desc": "Site can be loaded in an iframe (clickjacking risk).",
        "sec_no_xframe_rec": "Add X-Frame-Options: DENY or SAMEORIGIN header.",

        "sec_no_xcontent": "Missing X-Content-Type-Options",
        "sec_no_xcontent_desc": "Browser may misinterpret content type.",
        "sec_no_xcontent_rec": "Add X-Content-Type-Options: nosniff header.",

        "sec_cookies_insecure": "Insecure cookies",
        "sec_cookies_insecure_desc": "Cookies do not have Secure and HttpOnly flags.",
        "sec_cookies_insecure_rec": "Configure cookies with Secure, HttpOnly and SameSite.",

        # GDPR Issues
        "gdpr_no_privacy": "Missing privacy policy",
        "gdpr_no_privacy_desc": "The site does not have a visible privacy policy.",
        "gdpr_no_privacy_rec": "Create a Privacy Policy page accessible from the footer.",

        "gdpr_no_cookie": "Missing cookie policy",
        "gdpr_no_cookie_desc": "The site does not have a cookie policy.",
        "gdpr_no_cookie_rec": "Create a Cookie Policy page and consent banner.",

        "gdpr_no_consent": "Missing cookie consent banner",
        "gdpr_no_consent_desc": "The site does not request consent for cookies.",
        "gdpr_no_consent_rec": "Implement a cookie banner with granular options.",

        "gdpr_analytics": "Tracking without consent",
        "gdpr_analytics_desc": "Analytics scripts are loaded without consent.",
        "gdpr_analytics_rec": "Load tracking scripts only after obtaining consent.",

        # Accessibility Issues
        "a11y_no_lang": "Missing lang attribute",
        "a11y_no_lang_desc": "The <html> tag does not have the lang attribute defined.",
        "a11y_no_lang_rec": "Add lang='en' or the corresponding language to the <html> tag.",

        "a11y_missing_alt": "Images without alternative text",
        "a11y_missing_alt_desc": "{0} images do not have the alt attribute.",
        "a11y_missing_alt_rec": "Add descriptive alt text for all images.",

        "a11y_low_contrast": "Low contrast",
        "a11y_low_contrast_desc": "Some elements have insufficient contrast.",
        "a11y_low_contrast_rec": "Ensure a minimum contrast ratio of 4.5:1 for text.",

        "a11y_no_skip_link": "Missing 'Skip to content' link",
        "a11y_no_skip_link_desc": "There is no link to skip navigation.",
        "a11y_no_skip_link_rec": "Add a hidden 'Skip to main content' link at the beginning of the page.",

        "a11y_missing_labels": "Forms without labels",
        "a11y_missing_labels_desc": "{0} form fields do not have associated labels.",
        "a11y_missing_labels_rec": "Add <label> tags for all input fields.",
    }
}


def get_translation(key: str, lang: str = "ro", *args) -> str:
    """Get translated string with optional format arguments"""
    translations = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    text = translations.get(key, key)

    if args:
        try:
            return text.format(*args)
        except (IndexError, KeyError):
            return text
    return text


def t(key: str, lang: str = "ro", *args) -> str:
    """Shorthand for get_translation"""
    return get_translation(key, lang, *args)
