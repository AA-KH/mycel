import os
import re
import uuid
import logging
import httpx
import json
from typing import Dict, Any, Optional
from pydantic import BaseModel
from core.groq_engine import groq_engine

logger = logging.getLogger(__name__)

BUILDER_WRITE_API = "https://builder.io/api/v1/write/page"
BUILDER_HTML_API = "https://cdn.builder.io/api/v1/html/page"

class WebsiteGenerationRequest(BaseModel):
    company_name: str
    industry: str
    target_audience: str
    business_model: str
    value_proposition: str
    brand_identity: str
    growth_strategy: str
    website_type: str = "GENERAL_COMPANY_WEBSITE"
    pages: list[str] = ["Home"]


class BuilderWebsiteProvider:
    """
    Full Builder.io integration for website generation.
    
    Flow:
    1. Use LLM to generate structured Builder.io page content (blocks)
    2. POST to Builder.io Write API to create the page
    3. GET rendered HTML from Builder.io CDN HTML API
    4. Return the HTML for iframe preview
    
    Falls back to direct HTML/CSS/JS generation if Builder.io API fails.
    """

    def __init__(self):
        self.public_key = os.getenv("BUILDER_IO_PUBLIC_KEY", "")
        self.private_key = os.getenv("BUILDER_IO_PRIVATE_KEY", "")
        self.is_enabled = os.getenv("BUILDER_PROVIDER_ENABLED", "true").lower() == "true"

    async def generate_website(self, request: WebsiteGenerationRequest) -> Dict[str, Any]:
        if not self.is_enabled:
            return {"status": "GENERATION_FAILED", "reason": "Builder.io provider is disabled."}

        # As per user request: "just use html and css", we bypass the flaky Builder.io JSON blocks API
        # and strictly rely on the pure HTML/CSS generation fallback.
        logger.info("Bypassing Builder.io API and strictly using pure HTML/CSS generation.")
        return await self._generate_html_fallback(request)

    # ─────────────────────────────────────────────────
    # BUILDER.IO FULL INTEGRATION
    # ─────────────────────────────────────────────────

    async def _generate_via_builder_api(self, request: WebsiteGenerationRequest) -> Dict[str, Any]:
        """
        1. Generate Builder.io blocks using LLM
        2. Create page via Write API
        3. Fetch rendered HTML via HTML API
        """
        try:
            # Step 1: Generate page blocks using LLM
            blocks = await self._generate_builder_blocks(request)

            # Step 2: Create page in Builder.io
            page_url = f"/{request.company_name.lower().replace(' ', '-')}-{str(uuid.uuid4())[:8]}"
            page_id = await self._create_builder_page(request, blocks, page_url)

            if not page_id:
                logger.warning("Builder.io page creation failed, falling back to HTML generation.")
                return await self._generate_html_fallback(request)

            # Step 3: Fetch rendered HTML
            html = await self._fetch_builder_html(page_url)

            if not html:
                logger.warning("Builder.io HTML fetch returned empty, falling back.")
                return await self._generate_html_fallback(request)

            # Wrap in full HTML document
            full_html = self._wrap_builder_html(html, request.company_name)

            return {
                "status": "SUCCESS",
                "artifact": {
                    "format": "html",
                    "content": full_html,
                    "stack": ["Builder.io", "HTML", "CSS"],
                    "builder_page_id": page_id,
                    "builder_page_url": page_url,
                }
            }

        except Exception as e:
            logger.error(f"Builder.io generation failed: {e}. Falling back.")
            return await self._generate_html_fallback(request)

    async def _generate_builder_blocks(self, request: WebsiteGenerationRequest) -> list:
        """Use LLM to generate Builder.io block structure for the landing page."""
        system_prompt = (
            "You are a Builder.io page structure expert. "
            "Generate a JSON array of Builder.io blocks for a landing page. "
            "Use ONLY standard Builder.io components: Text, Image, Columns, Box, Button. "
            "Output ONLY a valid JSON array. No explanation, no markdown."
        )
        user_prompt = f"""Create Builder.io blocks for a landing page for '{request.company_name}'.
Value: {request.value_proposition}
Brand: {request.brand_identity}

Include: Hero section (big heading + subheading + CTA button), 3 feature boxes, contact/footer.
Output JSON array of Builder.io block objects only."""

        try:
            from core.gemini_engine import engine_manager as gemini_manager
            
            response = await gemini_manager.chat_completion(
                model="gemini-1.5-pro",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            raw = response.choices[0].message.content or "[]"
            # Extract JSON array
            match = re.search(r'\[[\s\S]*\]', raw)
            if match:
                return json.loads(match.group())
        except Exception as e:
            logger.warning(f"LLM block generation failed: {e}")

        # Minimal fallback blocks if LLM fails
        return [
            {
                "@type": "@builder.io/sdk:Element",
                "component": {
                    "name": "Text",
                    "options": {"text": f"<h1>{request.company_name}</h1><p>{request.value_proposition}</p>"}
                }
            },
            {
                "@type": "@builder.io/sdk:Element",
                "component": {
                    "name": "Text",
                    "options": {"text": f"<p>{request.brand_identity}</p>"}
                }
            }
        ]

    async def _create_builder_page(self, request: WebsiteGenerationRequest, blocks: list, page_url: str) -> Optional[str]:
        """POST to Builder.io Write API to create the page."""
        payload = {
            "name": f"{request.company_name} Landing Page",
            "published": "published",
            "query": [
                {
                    "@type": "@builder.io/core:Query",
                    "property": "urlPath",
                    "operator": "is",
                    "value": page_url
                }
            ],
            "data": {
                "title": f"{request.company_name} — {request.value_proposition[:60]}",
                "blocks": blocks
            }
        }

        headers = {
            "Authorization": f"Bearer {self.private_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(BUILDER_WRITE_API, json=payload, headers=headers)
            if resp.status_code in (200, 201):
                data = resp.json()
                page_id = data.get("id") or data.get("data", {}).get("id")
                logger.info(f"Builder.io page created: id={page_id}, url={page_url}")
                return page_id
            else:
                logger.error(f"Builder.io Write API error {resp.status_code}: {resp.text[:300]}")
                return None

    async def _fetch_builder_html(self, page_url: str) -> Optional[str]:
        """Fetch rendered HTML from Builder.io CDN HTML API."""
        import asyncio
        await asyncio.sleep(2)  # Give Builder.io a moment to index the page

        params = {
            "apiKey": self.public_key,
            "url": page_url,
            "cacheSeconds": "0"
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(BUILDER_HTML_API, params=params)
            if resp.status_code == 200:
                data = resp.json()
                html = data.get("data", {}).get("html") or data.get("html", "")
                if html:
                    logger.info(f"Builder.io HTML fetched successfully ({len(html)} chars)")
                    return html
            logger.warning(f"Builder.io HTML API returned {resp.status_code}: {resp.text[:200]}")
            return None

    def _wrap_builder_html(self, body_html: str, company_name: str) -> str:
        """Wrap Builder.io rendered HTML in a full HTML document."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{company_name}</title>
  <link rel="stylesheet" href="https://cdn.builder.io/css/v1/styles.css">
  <style>
    body {{ margin: 0; font-family: Inter, sans-serif; }}
    * {{ box-sizing: border-box; }}
  </style>
</head>
<body>
{body_html}
</body>
</html>"""

    # ─────────────────────────────────────────────────
    # LLM HTML FALLBACK (pure HTML/CSS/JS)
    # ─────────────────────────────────────────────────

    async def _generate_html_fallback(self, request: WebsiteGenerationRequest) -> Dict[str, Any]:
        """Pure HTML/CSS/JS generation using LLM as fallback."""
        system_prompt = (
            "You are a world-class UI/UX designer and senior frontend engineer specializing in stunning, award-winning landing pages. "
            "Your websites look like they were designed by top agencies for Fortune 500 companies. "
            "OUTPUT RULES (strictly follow ALL of them): "
            "(1) Output ONLY raw HTML starting with <!DOCTYPE html>. NO markdown, NO backticks, NO explanations. "
            "(2) Include Tailwind CSS CDN: <script src=\"https://cdn.tailwindcss.com\"></script> "
            "(3) Use a <style> block with CSS custom properties and advanced animations (keyframes, transitions). "
            "(4) Include smooth JavaScript interactions (scroll animations, hover effects, counter animations, typed effects). "
            "(5) MUST include ALL of these sections: sticky nav, hero (with animated gradient text), stats bar, features grid, "
            "how-it-works, testimonials, pricing/CTA section, footer. "
            "(6) Use Google Fonts (Inter or Plus Jakarta Sans) via @import. "
            "(7) Make it fully responsive (mobile-first). "
            "(8) Use glassmorphism, gradient borders, subtle glow effects, animated gradient backgrounds. "
            "(9) Color palette must be dark premium: deep navy/black backgrounds with vibrant purple/cyan/emerald accents. "
            "(10) Every section must have scroll-triggered fade-in animations using IntersectionObserver. "
            "The HTML must be complete, self-contained, and render perfectly in a browser iframe."
        )
        
        company = request.company_name or "Acme Corp"
        value = request.value_proposition or "Transforming the future with cutting-edge AI solutions"
        brand = request.brand_identity or "Modern, innovative, trustworthy"
        
        user_prompt = f"""Create an absolutely STUNNING, premium-quality landing page for:

Company: {company}
Value Proposition: {value}
Brand Identity: {brand}

Requirements:
- Animated gradient hero with a bold headline, subtext, and two CTA buttons (primary gradient + ghost)
- Animated stat counters (e.g., "10K+ Users", "99.9% Uptime", "500+ Integrations")  
- 6-card features grid with hover glow effects and icon emojis
- "How It Works" 3-step section with connecting lines
- 3 testimonial cards with star ratings and avatar initials
- Pricing section with 3 tiers (highlight the middle one)
- Email capture CTA section with gradient background
- Footer with links grid and social icons
- Smooth scroll-triggered reveal animations on all sections
- Mobile hamburger menu

Make it look like it costs $50,000 to build. Every pixel must be intentional and beautiful.
Output ONLY the raw HTML. Start with <!DOCTYPE html> immediately."""

        try:
            from core.gemini_engine import engine_manager as gemini_manager
            
            # Use the best available model for high-quality website generation
            response = await gemini_manager.chat_completion(
                model="gemini-flash-latest",  # Better than lite for quality
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=8192
            )
            raw_code = response.choices[0].message.content or ""

            
            # Robustly extract HTML from markdown code blocks
            html_match = re.search(r'```(?:html|htm)\s*(.*?)\s*```', raw_code, re.DOTALL | re.IGNORECASE)
            if html_match:
                raw_code = html_match.group(1)
            else:
                generic_match = re.search(r'```\s*(.*?)\s*```', raw_code, re.DOTALL)
                if generic_match:
                    raw_code = generic_match.group(1)
                    
            raw_code = raw_code.strip()

            if not raw_code.lower().startswith("<!doctype") and "<html" not in raw_code.lower():
                raw_code = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{request.company_name}</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-white">
{raw_code}
</body>
</html>"""
            else:
                # Reliably inject Tailwind if missing
                if "cdn.tailwindcss.com" not in raw_code and "tailwind.min.css" not in raw_code:
                    raw_code = raw_code.replace("</head>", "  <script src=\"https://cdn.tailwindcss.com\"></script>\n</head>")
                    # If there's no </head> tag for some reason, inject before body or just at the top
                    if "</head>" not in raw_code:
                        raw_code = raw_code.replace("<body", "<script src=\"https://cdn.tailwindcss.com\"></script>\n<body")

            return {
                "status": "SUCCESS",
                "artifact": {
                    "format": "html",
                    "content": raw_code,
                    "stack": ["HTML", "CSS", "JavaScript", "TailwindCSS"]
                }
            }
        except Exception as e:
            logger.error(f"HTML fallback generation failed: {e}")
            return {"status": "GENERATION_FAILED", "reason": str(e)}
