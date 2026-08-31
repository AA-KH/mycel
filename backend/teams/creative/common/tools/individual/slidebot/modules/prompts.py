"""
Prompt Templates Module - Stores all AI prompt templates
"""

# ============ Outline Generation Prompt Template ============

OUTLINE_PROMPT_TEMPLATE = """Please outline the core points for each page based on the overall idea of the PPT provided by the user. These points will be used later to create the ppt.

{page_constraint}

{page_instructions}

User's idea:
{user_input}

[Example Result Format]

Page 1: Core Strategy Overview
Page Title: 2026 Core Strategy: Risk Prevention + More Trading
Core Points:
Keyword 1: Risk Prevention
	Core Goal: Prevent tail risks.
	Response Measure: Systematically iterate the risk control system (shift from simple return breakdown to risk monitoring).
Keyword 2: More Trading
	Core Goal: Obtain absolute returns.
	Response Measure: Develop systematic trading signals and strategies.

Page 2: Why prevent risks? (Background and Logic)
Page Title: Market Environment Judgment: Tail Risks Looming
Core Points (List three major reasons):
Macro Narrative in Doubt: Current mainstream macro trends are crowded, with the possibility of being falsified.
Asset Valuation at High Levels: Various assets have continued to rise in the early stage, with prices at high levels.
Correlation Rising: Cross-asset correlation has significantly enhanced (low-correlation assets are fluctuating in the same direction), increasing the difficulty of diversified allocation.
Conclusion: Need to prepare for simultaneous amplification of volatility across various assets.

Please output the outline for each page in the above format. At the same time, output in JSON format for easy program parsing (The content must be in Chinese):

```json
{{
    "pages": [
        {{
            "page": 1,
            "theme": "Page theme (in Chinese)",
            "title": "Page title (in Chinese)",
            "content": "Core point content (can be multi-line text, in Chinese)"
        }}
    ]
}}
```
"""

# ============ Default Design Principles ============

DEFAULT_DESIGN_PRINCIPLES = """- Overall style: Business minimalist, financial business, white background
- Text priority, remove unnecessary English decorations, use Chinese as much as possible
- Remove overly complex graphics (e.g. scales), use simple SmartArt or block diagrams/lists, but keep information rich
- Do not use too much red color, except for risk warnings
- Avoid large blocks of solid color
- White background"""

# ============ Outline Refinement Prompt ============

REFINE_OUTLINE_PROMPT = """The user has modifications for the current PPT outline, please adjust based on the user feedback.

[Current Outline]
{current_outline}

[User Feedback]
{user_feedback}

Please output the complete modified outline, keeping the previous format. Also output JSON (Content must be in Chinese):

```json
{{
    "pages": [
        {{
            "page": 1,
            "theme": "Page theme",
            "title": "Page title", 
            "content": "Core point content"
        }}
    ]
}}
```
"""

# ============ Design Style Generation Prompt ============

STYLE_GENERATION_PROMPT = """Please help me generate detailed design plans and drawing prompts for each page based on the following PPT outline.

[Color Scheme Specification]
{color_scheme_spec}

[Typography Specification]
{font_scheme_spec}

[Design Principles]
{design_principles}

[PPT Outline]
{outline}

Please generate for each page:
1. Design concept explanation
2. Detailed image generation prompt (Prompt), for Gemini image generation API

[Note] The title of this page needs to be in the upper left corner of the page. {page_number_instruction}

Output JSON format (Keep concepts in Chinese, but image generation prompt can be English/Chinese depending on best results):
```json
{{
    "pages": [
        {{
            "page": 1,
            "theme": "Page theme",
            "design_concept": "Design concept explanation",
            "prompt": "Detailed image generation prompt, including all visual elements, colors, layout, text content, etc."
        }}
    ]
}}
```

[Partial prompt examples] Please refer to!!!

[Reference Prompt 1]: "Prompt: > PPT slide design, professional business style. Background is pure white, title text is '2026 Core Strategy Overview' 18pt, primary color ({example_primary}). Core visual element is a flat style scale graphic. The fulcrum of the scale is primary color ({example_primary}). Left side of scale: slightly heavier, decorated with a shield icon with accent color ({example_accent}) outline, text 'Risk Prevention' and 'Keywords: Steady bottom position, drawdown control', below is a bold downward arrow in accent color. Right side of scale: slightly higher, decorated with stacked coins and upward trend arrow icon in secondary color ({example_secondary}), text 'More Trading' and 'Keywords: Enhance returns, flexible response', below is a bold upward arrow in secondary color. Overall style clean, digital, clear information hierarchy."

[Reference Prompt 2]: "Prompt: PPT slide design, professional business style. Background is pure white, title is 'White Box Fixed Income+', text title 18pt, primary color ({example_primary}). Visual center is a large inverted pyramid (funnel) structure, divided horizontally into three color block areas from top to bottom: Top layer (widest): primary color ({example_primary}) block, white text. Middle layer: secondary color ({example_secondary}) block, white text. Bottom layer (narrowest): text color ({example_gray}) block, white text. Overall layout structured, high-end corporate VI tone, clean visuals."
 
"""

# ============ Default Color Scheme Description ============

DEFAULT_COLOR_SCHEME_SPEC = """• Primary Color:
  - Blue: #1C2662 —— For large titles, background color blocks, emphasis borders
  - Gold: #DAA050 —— For key data, subtitles, chart highlights
  - Red: #BC2424 —— For risk warnings, special emphasis points
• Secondary Color:
  - Gray: #666464 —— For body text, chart axes"""

# ============ Default Typography Description ============

DEFAULT_FONT_SCHEME_SPEC = """
• English/Numbers: Arial
• Size suggestion: Large title 48pt, page title 18pt, body 12-16pt, image text title 18pt, image body 12-16pt."""

# ============ Style Refinement Prompt ============

REFINE_STYLE_PROMPT = """The user has modifications for the current design plan, please adjust based on the user feedback.

[Current Design Plan]
{current_style}

[User Feedback]
{user_feedback}

Please output the complete modified design plan, keeping the JSON format:
```json
{{
    "pages": [
        {{
            "page": 1,
            "theme": "Page theme",
            "design_concept": "Design concept explanation",
            "prompt": "Modified image generation prompt"
        }}
    ]
}}
```
"""

# ============ Single Page Refine Prompt Template ============

REFINE_PAGE_PROMPT = """The user has fine-tuning feedback for page {page_num} of the PPT, please **fine-tune** this page based on user feedback.

[Important Principles]
⚠️ This is fine-tuning mode, NOT redesign! You MUST:
1. Keep the overall layout, color scheme, and font style of the current page unchanged
2. Only modify specific issues mentioned by the user
3. Keep content not mentioned by the user as is
4. Try to maintain visual consistency with the original design

[Current Page Info]
Page: Page {page_num}
Theme: {theme}
Current Design Concept: {design_concept}
Current Drawing Prompt: {current_prompt}

[User Fine-tuning Feedback]
{user_feedback}

Please output the modified design plan based on user fine-tuning feedback. Only modify parts mentioned by the user, keep others unchanged. Format as follows:

```json
{{
    "page": {page_num},
    "theme": "Page theme (keep unchanged or adjust based on request)",
    "design_concept": "Fine-tuned design concept explanation (explain what was modified)",
    "prompt": "Fine-tuned detailed image generation prompt (keep original style, only modify user requested parts)"
}}
```
"""


# ============ Helper Functions ============

def build_color_scheme_spec(color_scheme: dict) -> str:
    """Build description text based on color scheme"""
    if not color_scheme:
        return DEFAULT_COLOR_SCHEME_SPEC
    
    name = color_scheme.get('name', 'Custom Color Scheme')
    primary = color_scheme.get('primary', '#1C2662')
    secondary = color_scheme.get('secondary', '#DAA050')
    accent = color_scheme.get('accent', '#BC2424')
    gray = color_scheme.get('gray', '#666464')
    
    return f"""• Color Scheme Name: {name}
• Primary Color: {primary} —— For large titles, background blocks, emphasis borders
• Secondary Color: {secondary} —— For key data, subtitles, chart highlights
• Accent Color: {accent} —— For warnings, special emphasis
• Text Color (Gray): {gray} —— For body text, chart axes

[IMPORTANT] Please strictly use the above colors, do not use other colors!"""


def build_font_scheme_spec(font_scheme: dict) -> str:
    """Build description text based on typography scheme"""
    if not font_scheme:
        return DEFAULT_FONT_SCHEME_SPEC
    
    name = font_scheme.get('name', 'Custom Font Scheme')
    title = font_scheme.get('title', 'Microsoft YaHei')
    body = font_scheme.get('body', 'Microsoft YaHei')
    eng = font_scheme.get('eng', 'Arial')
    sizes = font_scheme.get('sizes', {})
    
    main_title_size = sizes.get('mainTitle', 48)
    page_title_size = sizes.get('pageTitle', 18)
    body_size = sizes.get('body', 14)
    
    return f"""• Font Scheme Name: {name}
• Chinese Title Font: {title}
• Chinese Body Font: {body}
• English/Numbers Font: {eng}
• Size suggestion: Large title {main_title_size}pt, page title {page_title_size}pt, body {body_size}pt

[IMPORTANT] Please strictly use the above font settings!"""
