# Creative Designer Role — Mycel

## Role Overview

The **Graphic Designer** is a specialist position in the Creative Team responsible for the full visual design production lifecycle — from understanding a client brief through concept development, AI-assisted asset generation, iterative review, and final artifact delivery.

---

## Capability Model

The Designer's effective capability is calculated as a layered inheritance:

```
Creative Team Common
        +
Graphic Designer Position
        +
Individual Skills
        +
Individual Tools
        +
Active Upskills
        =
Effective Designer Capability
```

Subject to: Authorization Policy, Security Gateway, Team Boundaries, Tool Permissions.

---

## Creative Team Common Skills

Inherited by all Creative Team members:

| Skill | Category | Description |
|---|---|---|
| `visual_design` | CREATIVE | Creating aesthetic and functional visual assets |
| `visual_communication` | COMMUNICATION | Conveying ideas through visual mediums |
| `storytelling` | CREATIVE | Crafting compelling narratives |
| `composition` | CREATIVE | Arranging visual elements effectively |
| `media_production` | CREATIVE | Creating and editing multimedia content |
| `creative_direction` | CREATIVE | Guiding the overall creative vision |
| `creative_review` | QUALITY | Reviewing and providing feedback on creative work |

---

## Graphic Designer Position Skills

Required baseline for the `graphic_designer` position:

| Skill | Min. Proficiency | Required |
|---|---|---|
| `visual_design` | 70 | ✅ |
| `composition` | 65 | ✅ |
| `typography` | 65 | ✅ |
| `color_theory` | 65 | ✅ |
| `branding` | 60 | ✅ |
| `design_review` | 60 | ✅ |
| `storyboarding` | 50 | Preferred |
| `ai_image_generation` | 50 | Preferred |
| `illustration` | 55 | Preferred |

---

## Riya Sharma — Individual Specialization

**Employee ID:** `emp_riya_sharma`  
**Position:** Graphic Designer  
**Specialization:** Visual & Brand Designer

Individual skills (extending position defaults):

| Skill | Proficiency | Experience |
|---|---|---|
| `video_editing` | 96 | Extensive |
| `storytelling` | 94 | Extensive |
| `branding` | 92 | Extensive |
| `social_media_design` | 91 | Extensive |
| `visual_design` | 90 | Extensive |
| `design_review` | 89 | Advanced |
| `ai_image_generation` | 88 | Advanced |
| `composition` | 88 | Advanced |
| `typography` | 87 | Advanced |
| `color_theory` | 86 | Advanced |
| `storyboarding` | 84 | Advanced |
| `marketing_content` | 82 | Advanced |

---

## Designer Tools

All tool execution passes through the Security Gateway. Designers do NOT call implementations directly.

```
Designer Agent
     ↓
Tool Request (intent + metadata)
     ↓
Security Gateway
     ↓
Intent Check → Policy Check → Risk Check → ArmorIQ
     ↓
Authorization
     ↓
Tool Registry
     ↓
Tool Implementation
```

### Available Tools (Riya)

| Tool ID | Description | Status |
|---|---|---|
| `image.generate` | AI image generation (Local ComfyUI) | Active |
| `image.variation` | Iterative design variant generation (Local ComfyUI) | Active |
| `design.canvas` | Layout & brand asset creation (Penpot API) | Stub (requires `PENPOT_ACCESS_TOKEN`) |
| `video.generate` | AI video generation | Active |
| `audio.generate` | AI audio/narration generation | Active |
| `ffmpeg` | Media processing | Active |
| `cloudinary.upload` | Asset storage | Active |

---

## Design Asset Creation Pipeline

A 7-stage pipeline for visual design tasks:

```
Brief Intake
     ↓
Creative Concept (2-3 directions)
     ↓
Visual Direction (lock one, set style dials)
     ↓
Storyboard / Layout (plan before generation)
     ↓
Asset Generation (max 3 iteration rounds)
     ↓
Design Review (quality gate)
     ↓
Final Delivery (Cloudinary + Artifact)
```

---

## Quality Gates

Design Review stage enforces:
- **Composition** — Visual hierarchy and balance
- **Typography** — Readability and hierarchy
- **Brand Consistency** — Colour, logo usage, tone
- **Readability** — Contrast ratios, text sizing
- **Asset Completeness** — All required formats present
- **Format Validity** — Correct dimensions and file formats

---

## Artifact Types

| Artifact Type | Description |
|---|---|
| `design_asset` | General purpose visual design file |
| `social_media_asset` | Platform-optimised social media image |
| `brand_asset` | Brand identity material |
| `thumbnail` | Video or article thumbnail |
| `marketing_image` | Marketing campaign visual |

Storage: All artifacts route through Cloudinary. No files stored in the repository.

---

## Talent Market Discovery

The Talent Market can discover Riya for tasks requiring:
- `branding`, `visual_design`, `social_media_design`, `composition`, `creative_direction`

Example query: `"Create a branded Instagram campaign"` → Riya discovered via capability match on `branding + social_media_design + visual_design`.

---

## Security

- Designer tools are intercepted by the **SecurityGateway** (Phase 17).
- Riya **cannot** access Legal, Finance, or Operations team restricted tools.
- The ArmorIQ boundary is preserved for all tool executions.
- No designer can grant itself new skills or elevated permissions at runtime.
