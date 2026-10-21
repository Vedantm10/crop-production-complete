"""
build_presentation_pdf.py
=========================
Generates the comprehensive, professionally styled college presentation and viva guide
for 'AgriStat India -- Crop Production Analytics Dashboard'.
Output: AgriStat_India_Project_Presentation_Guide.pdf
"""

import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether,
    PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

OUTPUT_PDF = "AgriStat_India_Project_Presentation_Guide.pdf"

# ── Color Palette ─────────────────────────────────────────────────────────────
PRIMARY = colors.HexColor("#065F46")       # Deep Emerald Green
PRIMARY_LIGHT = colors.HexColor("#ECFDF5") # Soft Emerald Tint
SECONDARY = colors.HexColor("#0F766E")     # Dark Teal
ACCENT = colors.HexColor("#0D9488")        # Bright Teal
TEXT_DARK = colors.HexColor("#1E293B")     # Slate 800 (Charcoal)
TEXT_MUTED = colors.HexColor("#64748B")    # Slate 500 (Muted)
BORDER_COLOR = colors.HexColor("#CBD5E1")  # Slate 300
BG_ALT_ROW = colors.HexColor("#F8FAFC")    # Slate 50
BG_CALLOUT = colors.HexColor("#F1F5F9")    # Slate 100
WARN_BG = colors.HexColor("#FFFBEB")       # Amber tint
WARN_BORDER = colors.HexColor("#FDE68A")   # Amber border
WARN_TEXT = colors.HexColor("#92400E")     # Amber dark text


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and print 'Page X of Y' page numbers
    and professional running headers on all pages except the cover page.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            return

        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(PRIMARY)

        # Running header
        self.drawString(54, 788, "AgriStat India - Crop Production Analytics Dashboard")
        self.setFont("Helvetica", 8)
        self.setFillColor(TEXT_MUTED)
        self.drawRightString(541, 788, "Project Presentation & Viva Comprehensive Guide")

        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.6)
        self.line(54, 780, 541, 780)

        # Running footer
        self.line(54, 45, 541, 45)
        self.setFont("Helvetica", 8)
        self.setFillColor(TEXT_MUTED)
        self.drawString(54, 32, "Confidential - Academic Project Presentation & Viva Defense Guide")
        self.drawRightString(541, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def build_pdf():
    # Page setup: A4 = 595.27 x 841.89 points. Margins: 54 pt (0.75 in)
    # Printable width: 595.27 - 108 = 487.27 pt
    usable_width = 487.27

    doc = SimpleDocTemplate(
        OUTPUT_PDF,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    base_styles = getSampleStyleSheet()

    styles = {
        "CoverTitle": ParagraphStyle(
            "CoverTitle",
            parent=base_styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=25,
            leading=31,
            textColor=PRIMARY,
            alignment=0,
            spaceAfter=7,
        ),
        "CoverSubtitle": ParagraphStyle(
            "CoverSubtitle",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=12.5,
            leading=17,
            textColor=SECONDARY,
            spaceAfter=18,
        ),
        "CoverMeta": ParagraphStyle(
            "CoverMeta",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=14.5,
            textColor=TEXT_DARK,
        ),
        "H1": ParagraphStyle(
            "H1",
            parent=base_styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=17.5,
            textColor=PRIMARY,
            spaceBefore=9,
            spaceAfter=5,
            keepWithNext=True,
        ),
        "H2": ParagraphStyle(
            "H2",
            parent=base_styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13.8,
            textColor=SECONDARY,
            spaceBefore=7,
            spaceAfter=3,
            keepWithNext=True,
        ),
        "H3": ParagraphStyle(
            "H3",
            parent=base_styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=TEXT_DARK,
            spaceBefore=5,
            spaceAfter=2,
            keepWithNext=True,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=8.4,
            leading=11.6,
            textColor=TEXT_DARK,
            spaceAfter=3.5,
        ),
        "BodyBold": ParagraphStyle(
            "BodyBold",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.4,
            leading=11.6,
            textColor=TEXT_DARK,
            spaceAfter=3.5,
        ),
        "Bullet": ParagraphStyle(
            "Bullet",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11.2,
            textColor=TEXT_DARK,
            leftIndent=10,
            firstLineIndent=-7,
            spaceAfter=1.5,
        ),
        "TableHead": ParagraphStyle(
            "TableHead",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.4,
            leading=9.5,
            textColor=colors.white,
            alignment=0,
        ),
        "TableCell": ParagraphStyle(
            "TableCell",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=7,
            leading=9.2,
            textColor=TEXT_DARK,
        ),
        "TableCellBold": ParagraphStyle(
            "TableCellBold",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=9.2,
            textColor=TEXT_DARK,
        ),
        "TableCellCode": ParagraphStyle(
            "TableCellCode",
            parent=base_styles["Normal"],
            fontName="Courier",
            fontSize=6.5,
            leading=8.5,
            textColor=PRIMARY,
        ),
        "CalloutText": ParagraphStyle(
            "CalloutText",
            parent=base_styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=7.6,
            leading=10.4,
            textColor=TEXT_DARK,
        ),
        "ScriptSpeaker": ParagraphStyle(
            "ScriptSpeaker",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11.2,
            textColor=PRIMARY,
            spaceBefore=4,
            spaceAfter=1.5,
            keepWithNext=True,
        ),
        "ScriptDialogue": ParagraphStyle(
            "ScriptDialogue",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=7.8,
            leading=11,
            textColor=TEXT_DARK,
            leftIndent=6,
            spaceAfter=4,
        ),
        "VivaQ": ParagraphStyle(
            "VivaQ",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10.6,
            textColor=PRIMARY,
            spaceBefore=3,
            spaceAfter=1,
            keepWithNext=True,
        ),
        "VivaA": ParagraphStyle(
            "VivaA",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=7.6,
            leading=10.2,
            textColor=TEXT_DARK,
            leftIndent=6,
            spaceAfter=2.5,
        ),
        "CodeBlock": ParagraphStyle(
            "CodeBlock",
            parent=base_styles["Normal"],
            fontName="Courier",
            fontSize=6.4,
            leading=8.5,
            textColor=PRIMARY,
        ),
    }

    story = []

    def make_callout(title, text, is_warning=False):
        bg = WARN_BG if is_warning else PRIMARY_LIGHT
        border = WARN_BORDER if is_warning else ACCENT
        t_color = WARN_TEXT if is_warning else PRIMARY
        
        content = [
            Paragraph(f"<b>{title}</b>", ParagraphStyle("CTitle", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=t_color)),
            Spacer(1, 1),
            Paragraph(text, styles["CalloutText"]),
        ]
        t = Table([[content]], colWidths=[usable_width])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), bg),
            ('BOX', (0,0), (-1,-1), 1, border),
            ('TOPPADDING', (0,0), (-1,-1), 3.5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        return t

    # ═══════════════════════════════════════════════════════════════════════════
    # COVER PAGE
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 15))
    story.append(Paragraph("PROJECT PRESENTATION &amp; VIVA DEFENSE GUIDE", ParagraphStyle("CoverKicker", fontName="Helvetica-Bold", fontSize=10.5, leading=13.5, textColor=ACCENT, spaceAfter=8)))
    story.append(Paragraph("AgriStat India: Crop Production Analytics Dashboard", styles["CoverTitle"]))
    story.append(Paragraph("A Full-Stack Big Data Agricultural Analytics System (1997-2025)", styles["CoverSubtitle"]))
    
    story.append(HRFlowable(width="100%", thickness=2.5, color=PRIMARY, spaceBefore=2, spaceAfter=14))

    summary_box_content = [
        Paragraph("<b>EXECUTIVE ACADEMIC SUMMARY</b>", ParagraphStyle("Hdr", fontName="Helvetica-Bold", fontSize=8.8, leading=11, textColor=PRIMARY)),
        Spacer(1, 3.5),
        Paragraph(
            "This document is a comprehensive, production-verified defense guide for the <b>AgriStat India</b> "
            "engineering project. It articulates every facet of the system: the complete technology stack "
            "(Next.js 16, React 19, FastAPI, Pandas, PySpark, MapReduce, HDFS, Plotly), the 463,847-record "
            "government dataset, all 14 backend REST API endpoints, the multi-page interactive dashboard, "
            "mathematical yield models, dual-platform cloud deployments (Vercel &amp; Render), step-by-step presentation "
            "scripts, and 36 rigorous faculty viva questions with bulletproof answers.",
            styles["Body"]
        ),
    ]
    sum_t = Table([[summary_box_content]], colWidths=[usable_width])
    sum_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_ALT_ROW),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('PADDING', (0,0), (-1,-1), 7.5),
    ]))
    story.append(sum_t)
    story.append(Spacer(1, 16))

    meta_table_data = [
        [Paragraph("<b>Domain &amp; Subject:</b>", styles["CoverMeta"]), Paragraph("Big Data Analytics &amp; Cloud Web Application Engineering", styles["CoverMeta"])],
        [Paragraph("<b>Primary Frameworks:</b>", styles["CoverMeta"]), Paragraph("Next.js 16 (React 19) Frontend · FastAPI 0.115+ (Python 3.13) REST Backend", styles["CoverMeta"])],
        [Paragraph("<b>Big Data Engines:</b>", styles["CoverMeta"]), Paragraph("Apache PySpark (Distributed SQL) · Hadoop Streaming MapReduce · HDFS", styles["CoverMeta"])],
        [Paragraph("<b>Dataset Analyzed:</b>", styles["CoverMeta"]), Paragraph("463,847 records · 34 States/UTs · 737 Districts · 115 Crops · 29 Years (1997-2025)", styles["CoverMeta"])],
        [Paragraph("<b>Live Cloud URLs:</b>", styles["CoverMeta"]), Paragraph("Frontend on Vercel · REST API on Render (agristat-india-api.onrender.com)", styles["CoverMeta"])],
        [Paragraph("<b>Test Suite Verification:</b>", styles["CoverMeta"]), Paragraph("169 / 169 automated tests passing in Pytest (100% green)", styles["CoverMeta"])],
    ]
    meta_t = Table(meta_table_data, colWidths=[130, usable_width - 130])
    meta_t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, BG_CALLOUT),
    ]))
    story.append(meta_t)

    story.append(Spacer(1, 18))
    story.append(Paragraph("<b>Table of Contents / Navigation Sitemap:</b>", styles["H3"]))
    
    toc_data = [
        [Paragraph("<b>Section 1:</b> Project Overview &amp; Motivation", styles["TableCellBold"]), Paragraph("<b>Section 7:</b> Dataset, Provenance &amp; Calculations", styles["TableCellBold"])],
        [Paragraph("<b>Section 2:</b> Verified Complete Technology Stack", styles["TableCellBold"]), Paragraph("<b>Section 8:</b> Local Setup &amp; Deployment Manual", styles["TableCellBold"])],
        [Paragraph("<b>Section 3:</b> Dashboard Features &amp; Demonstration", styles["TableCellBold"]), Paragraph("<b>Section 9:</b> Timed Presentation Scripts", styles["TableCellBold"])],
        [Paragraph("<b>Section 4:</b> End-to-End Architecture &amp; Data Flow", styles["TableCellBold"]), Paragraph("<b>Section 10:</b> 36 High-Probability Viva Q&amp;A", styles["TableCellBold"])],
        [Paragraph("<b>Section 5:</b> Source Code &amp; Key File Responsibilities", styles["TableCellBold"]), Paragraph("<b>Section 11:</b> Quick Revision Sheet &amp; Formulas", styles["TableCellBold"])],
        [Paragraph("<b>Section 6:</b> Verified API Endpoints Reference", styles["TableCellBold"]), Paragraph("<b>Summary:</b> Golden Rules for Faculty Presentation", styles["TableCellBold"])],
    ]
    toc_t = Table(toc_data, colWidths=[usable_width/2, usable_width/2])
    toc_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), PRIMARY_LIGHT),
        ('BOX', (0,0), (-1,-1), 1, ACCENT),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(toc_t)

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 1: PROJECT OVERVIEW (Target: Page 2 full)
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("1. Project Overview &amp; Foundational Motivation", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=1, spaceAfter=5))

    story.append(Paragraph(
        "<b>AgriStat India</b> is an enterprise-grade Big Data analytics and visual intelligence dashboard designed "
        "to aggregate, process, and interrogate over a quarter-century of Indian agricultural performance data. "
        "Agricultural planning in India has historically suffered from fragmented data dissemination: raw district-level "
        "statistics are released in dense tabular spreadsheets that are inaccessible to non-technical stakeholders, "
        "impractical for national cross-filtering, and prone to misinterpretation due to measurement inconsistencies.",
        styles["Body"]
    ))

    story.append(Paragraph("Core Problem Statement &amp; Academic Motivation", styles["H2"]))
    story.append(Paragraph(
        "India's agricultural economy involves over 150 million farming households, 34 States and Union Territories, "
        "and 737 administrative districts cultivating over a hundred distinct crops across six cropping seasons. "
        "Despite rich record collection by the Ministry of Agriculture &amp; Farmers Welfare, raw datasets spanning "
        "1997 to 2025 encompass nearly half a million rows (463,847 records).",
        styles["Body"]
    ))
    story.append(Paragraph("• <b>Spreadsheet Limitations:</b> Standard office tools like Microsoft Excel freeze when computing multi-dimensional pivot tables across 460,000+ rows, lacking interactive choropleth geo-mapping or real-time query caching.", styles["Bullet"]))
    story.append(Paragraph("• <b>Information Silos:</b> State planning departments lack direct visual access to cross-state comparative benchmarks, causing delays in identifying localized yield deficits.", styles["Bullet"]))
    story.append(Paragraph("• <b>Data Artifact Hazards:</b> Raw statistics contain critical nuances -- such as coconut production recorded in <i>nuts</i> rather than metric tonnes -- which naive aggregations sum together, distorting state totals.", styles["Bullet"]))
    story.append(Paragraph("• <b>Data Provenance Ambiguity:</b> Public datasets forward-fill recent years without explicit labeling, misleading researchers into treating algorithmic projections as verified facts.", styles["Bullet"]))

    story.append(Paragraph("Project Objectives", styles["H2"]))
    story.append(Paragraph("1. <b>Automated Pipeline:</b> Build a deterministic cleaning engine in Pandas handling nulls, standardizing seasons, and normalizing states.", styles["Bullet"]))
    story.append(Paragraph("2. <b>Distributed Processing:</b> Implement parallel aggregations using PySpark and MapReduce to demonstrate cluster scalability.", styles["Bullet"]))
    story.append(Paragraph("3. <b>High-Performance REST API:</b> Construct a sub-50ms FastAPI service with memory-resident caching and OpenAPI documentation.", styles["Bullet"]))
    story.append(Paragraph("4. <b>Modern Reactive Dashboard:</b> Deliver a Next.js 16 &amp; React 19 web app featuring cascading filters, choropleth maps, and explorer tables.", styles["Bullet"]))
    story.append(Paragraph("5. <b>Ethical Provenance:</b> Explicitly distinguish verified official records from synthetic projections (2024-2025).", styles["Bullet"]))

    story.append(Paragraph("Target Users &amp; Real-World Applications", styles["H2"]))
    users_data = [
        [Paragraph("<b>User Group</b>", styles["TableHead"]), Paragraph("<b>Operational Need</b>", styles["TableHead"]), Paragraph("<b>Dashboard Solution &amp; Impact</b>", styles["TableHead"])],
        [
            Paragraph("<b>Policy Planners</b>", styles["TableCellBold"]),
            Paragraph("Evaluating food grain self-sufficiency and buffer stocks.", styles["TableCell"]),
            Paragraph("Longitudinal trend lines and ranking cards isolate deficit states immediately.", styles["TableCell"])
        ],
        [
            Paragraph("<b>Insurance Underwriters</b>", styles["TableCellBold"]),
            Paragraph("Establishing baseline district yields for PMFBY insurance.", styles["TableCell"]),
            Paragraph("Explorer view filtering by district and season provides 28-year empirical yield variance.", styles["TableCell"])
        ],
        [
            Paragraph("<b>Agronomists</b>", styles["TableCellBold"]),
            Paragraph("Analyzing crop yield response to agro-climatic conditions.", styles["TableCell"]),
            Paragraph("Yield (t/ha) breakdown isolating Kharif vs. Rabi performance across 115 crops.", styles["TableCell"])
        ],
        [
            Paragraph("<b>Agri-Supply Chain</b>", styles["TableCellBold"]),
            Paragraph("Optimizing cold-storage warehousing and procurement.", styles["TableCell"]),
            Paragraph("State and district ranking tables show exact production volume distribution.", styles["TableCell"])
        ],
    ]
    u_t = Table(users_data, colWidths=[95, 175, usable_width - 270])
    u_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_ALT_ROW]),
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
        ('LEFTPADDING', (0,0), (-1,-1), 2.5),
        ('RIGHTPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(u_t)

    story.append(Spacer(1, 4))
    story.append(make_callout(
        "Spoken Elevator Pitch (Verbatim Script - 30 Seconds)",
        '"Good morning, esteemed faculty members. Today I present AgriStat India, a full-stack Big Data analytics '
        'platform that transforms 29 years of Indian agricultural records -- covering 463,847 official government entries -- into '
        'actionable visual intelligence. Combining an asynchronous FastAPI backend and a reactive Next.js 16 frontend with '
        'distributed PySpark processing, AgriStat enables agronomists and policymakers to cross-filter national crop yields, '
        'cultivated areas, and seasonal trends in under 50 milliseconds, while maintaining rigorous data provenance '
        'transparency over synthetic projections and measurement anomalies."'
    ))
    story.append(Spacer(1, 3))
    story.append(Paragraph(
        "<b>1-Minute Conceptual Walkthrough:</b> <i>\"AgriStat India addresses agricultural data fragmentation. While government ministries gather rich records, "
        "spreadsheets of 463,000 rows fail in standard office software. Our reproducible pipeline cleans whitespace, standardizes seasons, and flags anomalies. "
        "Dual engines -- PySpark for distributed clusters and in-memory FastAPI/Pandas for REST queries -- power a Next.js 16 dashboard with choropleth maps, "
        "donut crop mix, and cascading filters, verified by 169 automated Pytest cases across Vercel and Render.\"</i>",
        styles["Body"]
    ))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 2: COMPLETE TECHNOLOGY STACK (Target: Page 3 full)
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("2. Complete Verified Technology Stack", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=1, spaceAfter=5))

    story.append(Paragraph(
        "Every technology in the table below was directly verified against repository configuration files "
        "(<code>frontend/package.json</code>, <code>backend/requirements.txt</code>, and root environment manifests). "
        "No unused, speculative, or unverified packages have been included.",
        styles["Body"]
    ))

    tech_table_data = [
        [Paragraph("<b>Technology</b>", styles["TableHead"]), Paragraph("<b>Verified Version</b>", styles["TableHead"]), Paragraph("<b>Layer / Purpose</b>", styles["TableHead"]), Paragraph("<b>Why Chosen &amp; Key Advantage</b>", styles["TableHead"]), Paragraph("<b>Source Files</b>", styles["TableHead"])],
        [
            Paragraph("<b>Next.js</b>", styles["TableCellBold"]),
            Paragraph("16.4.0 (Canary/16)", styles["TableCellCode"]),
            Paragraph("Frontend Web Framework (App Router)", styles["TableCell"]),
            Paragraph("Enables hybrid server/client rendering, automatic code splitting, and zero-config Vercel edge deployment.", styles["TableCell"]),
            Paragraph("frontend/app/*<br/>next.config.mjs", styles["TableCellCode"])
        ],
        [
            Paragraph("<b>React</b>", styles["TableCellBold"]),
            Paragraph("19.0.0", styles["TableCellCode"]),
            Paragraph("Declarative UI Engine", styles["TableCell"]),
            Paragraph("React 19 compiler optimizations, concurrent rendering, and hooks (<code>useDeferredValue</code> for search).", styles["TableCell"]),
            Paragraph("frontend/components/*", styles["TableCellCode"])
        ],
        [
            Paragraph("<b>TypeScript</b>", styles["TableCellBold"]),
            Paragraph("5.7.3", styles["TableCellCode"]),
            Paragraph("Static Typing &amp; Contracts", styles["TableCell"]),
            Paragraph("Guarantees strict API data contracts (<code>Filters</code>, <code>KpiSummary</code>, <code>CropRecord</code>).", styles["TableCell"]),
            Paragraph("frontend/lib/data/types.ts", styles["TableCellCode"])
        ],
        [
            Paragraph("<b>Tailwind CSS</b>", styles["TableCellBold"]),
            Paragraph("4.3.3 (@tailwindcss/postcss)", styles["TableCellCode"]),
            Paragraph("Design System &amp; Styling", styles["TableCell"]),
            Paragraph("Tailwind v4 CSS-first engine provides sub-millisecond build times, modern flex/grid, and theme variables.", styles["TableCell"]),
            Paragraph("frontend/app/globals.css", styles["TableCellCode"])
        ],
        [
            Paragraph("<b>Plotly.js</b>", styles["TableCellBold"]),
            Paragraph("4.1.2 (dist-min)", styles["TableCellCode"]),
            Paragraph("Interactive Visualizations", styles["TableCell"]),
            Paragraph("Hardware-accelerated SVG/WebGL charting for choropleths, multi-line trends, and dual-axis plots.", styles["TableCell"]),
            Paragraph("frontend/components/charts/*", styles["TableCellCode"])
        ],
        [
            Paragraph("<b>SWR</b>", styles["TableCellBold"]),
            Paragraph("2.5.1", styles["TableCellCode"]),
            Paragraph("Client State &amp; Data Fetching", styles["TableCell"]),
            Paragraph("Implements Stale-While-Revalidate caching, in-flight request deduplication, and error revalidation.", styles["TableCell"]),
            Paragraph("frontend/hooks/use-analytics.ts", styles["TableCellCode"])
        ],
        [
            Paragraph("<b>FastAPI</b>", styles["TableCellBold"]),
            Paragraph("0.115.0 / 0.151.0", styles["TableCellCode"]),
            Paragraph("Backend Asynchronous REST API", styles["TableCell"]),
            Paragraph("High throughput ASGI framework with native OpenAPI schema generation and Pydantic validation.", styles["TableCell"]),
            Paragraph("backend/api.py<br/>api.py (root)", styles["TableCellCode"])
        ],
        [
            Paragraph("<b>Uvicorn</b>", styles["TableCellBold"]),
            Paragraph("0.29.0 / 0.54.0", styles["TableCellCode"]),
            Paragraph("ASGI Production Server", styles["TableCell"]),
            Paragraph("Lightning-fast async HTTP/1.1 and WebSocket server built on uvloop and httptools.", styles["TableCell"]),
            Paragraph("requirements.txt", styles["TableCellCode"])
        ],
        [
            Paragraph("<b>Pandas</b>", styles["TableCellBold"]),
            Paragraph("2.0.0+ (3.0.6)", styles["TableCellCode"]),
            Paragraph("In-Memory Data Engineering", styles["TableCell"]),
            Paragraph("Vectorized boolean filtering, GroupBy aggregations, and resilient missing data imputation.", styles["TableCell"]),
            Paragraph("backend/src/pandas_analysis.py<br/>backend/src/data_cleaning.py", styles["TableCellCode"])
        ],
        [
            Paragraph("<b>NumPy</b>", styles["TableCellBold"]),
            Paragraph("1.24.0+ (2.5.4)", styles["TableCellCode"]),
            Paragraph("Numerical Operations", styles["TableCell"]),
            Paragraph("Vectorized conditional calculations via <code>np.where</code> for zero-guarded yield division.", styles["TableCell"]),
            Paragraph("backend/src/pandas_analysis.py", styles["TableCellCode"])
        ],
        [
            Paragraph("<b>Apache PySpark</b>", styles["TableCellBold"]),
            Paragraph("3.4.0+ (4.2.0)", styles["TableCellCode"]),
            Paragraph("Distributed Big Data Engine", styles["TableCell"]),
            Paragraph("Executes multi-threaded DataFrame SQL aggregations and exports columnar Parquet files.", styles["TableCell"]),
            Paragraph("backend/src/pyspark_analysis.py", styles["TableCellCode"])
        ],
        [
            Paragraph("<b>Hadoop MapReduce</b>", styles["TableCellBold"]),
            Paragraph("Python Streaming Interface", styles["TableCellCode"]),
            Paragraph("Batch Big Data MapReduce", styles["TableCell"]),
            Paragraph("Implements standard UNIX-pipe mapper and reducer scripts for key-value production summing.", styles["TableCell"]),
            Paragraph("backend/src/mapreduce/*<br/>bigdata/scripts/*", styles["TableCellCode"])
        ],
        [
            Paragraph("<b>Apache HDFS Utils</b>", styles["TableCellBold"]),
            Paragraph("Custom Subprocess Wrapper", styles["TableCellCode"]),
            Paragraph("Distributed File Management", styles["TableCell"]),
            Paragraph("Manages HDFS namespaces (<code>/user/crop_project</code>) with automated fallback to local storage.", styles["TableCell"]),
            Paragraph("backend/src/hdfs_utils.py", styles["TableCellCode"])
        ],
        [
            Paragraph("<b>Streamlit</b>", styles["TableCellBold"]),
            Paragraph("1.35.0+ (1.66.0)", styles["TableCellCode"]),
            Paragraph("Alternative Python UI", styles["TableCell"]),
            Paragraph("Provides a rapid 7-page standalone Python exploration interface for local data scientists.", styles["TableCell"]),
            Paragraph("backend/app.py", styles["TableCellCode"])
        ],
        [
            Paragraph("<b>Pytest &amp; HTTPX</b>", styles["TableCellBold"]),
            Paragraph("pytest 9.1.1, httpx 0.28.1", styles["TableCellCode"]),
            Paragraph("Automated Testing Suite", styles["TableCell"]),
            Paragraph("In-process ASGI testing via TestClient; 169 automated test cases covering all edge cases.", styles["TableCell"]),
            Paragraph("backend/tests/test_api.py<br/>backend/tests/test_pipeline.py", styles["TableCellCode"])
        ],
        [
            Paragraph("<b>Vercel</b>", styles["TableCellBold"]),
            Paragraph("Global Edge Network", styles["TableCellCode"]),
            Paragraph("Frontend Cloud Hosting", styles["TableCell"]),
            Paragraph("Provides global CDN distribution, automatic SSL, and continuous deployment from GitHub.", styles["TableCell"]),
            Paragraph(".env.example", styles["TableCellCode"])
        ],
        [
            Paragraph("<b>Render</b>", styles["TableCellBold"]),
            Paragraph("Cloud Linux Container", styles["TableCellCode"]),
            Paragraph("Backend API Hosting", styles["TableCell"]),
            Paragraph("Hosts FastAPI ASGI container with automatic Git webhooks and port environment binding.", styles["TableCell"]),
            Paragraph("api.py (root proxy)", styles["TableCellCode"])
        ],
    ]

    tech_t = Table(tech_table_data, colWidths=[65, 75, 105, usable_width - 345, 100])
    tech_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_ALT_ROW]),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 1.6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.6),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(tech_t)

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 3: DASHBOARD FEATURES AND FUNCTIONALITY (Target: Page 4 full)
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("3. Dashboard Features &amp; User Interface Architecture", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=1, spaceAfter=5))

    story.append(Paragraph(
        "The AgriStat India frontend consists of seven core analytics routes, designed with a clean, cohesive "
        "aesthetic adhering to modern information architecture standards. Every view is powered by universal "
        "filter reconciliation, meaning any filter applied on one view persists and updates all visualizations.",
        styles["Body"]
    ))

    feat_table_data = [
        [Paragraph("<b>Component / Feature</b>", styles["TableHead"]), Paragraph("<b>What it Displays</b>", styles["TableHead"]), Paragraph("<b>Calculation Logic / Source</b>", styles["TableHead"]), Paragraph("<b>API &amp; Service Layer</b>", styles["TableHead"]), Paragraph("<b>User Interaction</b>", styles["TableHead"])],
        [
            Paragraph("<b>Total Production KPI</b>", styles["TableCellBold"]),
            Paragraph("Aggregated production in M/K tonnes plus YoY %.", styles["TableCell"]),
            Paragraph("<code>sum(Production)</code> excluding nulls. YoY: <code>((Prod_t - Prod_t-1)/Prod_t-1)*100</code>.", styles["TableCell"]),
            Paragraph("<code>/api/kpis</code><br/>(fallback: <code>/api/yearwise</code>)", styles["TableCellCode"]),
            Paragraph("Updates on any dimension change.", styles["TableCell"])
        ],
        [
            Paragraph("<b>Cultivated Area KPI</b>", styles["TableCellBold"]),
            Paragraph("Total land cultivated in M/K hectares plus YoY %.", styles["TableCell"]),
            Paragraph("<code>sum(Area)</code> across filtered rows. Scaled dynamically.", styles["TableCell"]),
            Paragraph("<code>/api/kpis</code><br/>(fallback: <code>/api/yearwise</code>)", styles["TableCellCode"]),
            Paragraph("Shows land utilization expansion.", styles["TableCell"])
        ],
        [
            Paragraph("<b>Active Crops KPI</b>", styles["TableCellBold"]),
            Paragraph("Distinct crop varieties meeting active filters.", styles["TableCell"]),
            Paragraph("<code>df['Crop'].nunique()</code>. Caption displays record count.", styles["TableCell"]),
            Paragraph("<code>/api/kpis</code><br/>(fallback: <code>/api/cropwise</code>)", styles["TableCellCode"]),
            Paragraph("Shows crop biodiversity under filters.", styles["TableCell"])
        ],
        [
            Paragraph("<b>Geographic Entities KPI</b>", styles["TableCellBold"]),
            Paragraph("Active state count and total districts represented.", styles["TableCell"]),
            Paragraph("State count: <code>nunique()</code>; District count: unique districts.", styles["TableCell"]),
            Paragraph("<code>/api/kpis</code><br/>(fallback: <code>/api/statewise</code>)", styles["TableCellCode"]),
            Paragraph("Caption confirms data validity.", styles["TableCell"])
        ],
        [
            Paragraph("<b>India Choropleth Map</b>", styles["TableCellBold"]),
            Paragraph("Color-shaded map representing state-level metrics.", styles["TableCell"]),
            Paragraph("Values matched by GeoJSON ID. Non-reporting shaded grey.", styles["TableCell"]),
            Paragraph("<code>/api/statewise</code> + GeoJSON", styles["TableCellCode"]),
            Paragraph("Clicking state drills down; re-click clears.", styles["TableCell"])
        ],
        [
            Paragraph("<b>Top States Bar Chart</b>", styles["TableCellBold"]),
            Paragraph("Ranked horizontal bar chart of top 10/20 states.", styles["TableCell"]),
            Paragraph("Descending sort of aggregated metric values.", styles["TableCell"]),
            Paragraph("<code>/api/statewise</code>", styles["TableCellCode"]),
            Paragraph("Hover shows values; click sets state.", styles["TableCell"])
        ],
        [
            Paragraph("<b>Trend Line Chart</b>", styles["TableCellBold"]),
            Paragraph("Historical movement 1997-2025 with dual encoding.", styles["TableCell"]),
            Paragraph("1997-2023 solid line; 2024-2025 dashed + shaded band.", styles["TableCell"]),
            Paragraph("<code>/api/yearwise</code> or <code>/api/crop-trend</code>", styles["TableCellCode"]),
            Paragraph("Conveys observed vs synthetic data.", styles["TableCell"])
        ],
        [
            Paragraph("<b>Crop Mix Donut</b>", styles["TableCellBold"]),
            Paragraph("Percentage share of top 6 crops + 'Other'.", styles["TableCell"]),
            Paragraph("<code>(Crop_Prod / Total_Prod) * 100</code>.", styles["TableCell"]),
            Paragraph("<code>/api/cropwise?n=115</code>", styles["TableCellCode"]),
            Paragraph("Clicking slice sets crop filter.", styles["TableCell"])
        ],
        [
            Paragraph("<b>Cropping Season Bar</b>", styles["TableCellBold"]),
            Paragraph("Output comparison across 6 cropping seasons.", styles["TableCell"]),
            Paragraph("Sum of metric grouped by <code>Season</code> column.", styles["TableCell"]),
            Paragraph("<code>/api/seasonal</code>", styles["TableCellCode"]),
            Paragraph("Clicking bar toggles season filter.", styles["TableCell"])
        ],
        [
            Paragraph("<b>Data Explorer Grid</b>", styles["TableCellBold"]),
            Paragraph("Paginated, searchable table of raw records.", styles["TableCell"]),
            Paragraph("Slicing (25 rows/page) with multi-column sorting.", styles["TableCell"]),
            Paragraph("<code>/api/records</code>", styles["TableCellCode"]),
            Paragraph("Debounced search, page sort toggles.", styles["TableCell"])
        ],
        [
            Paragraph("<b>Data Quality View</b>", styles["TableCellBold"]),
            Paragraph("Audit page showing raw/clean rows, null counts.", styles["TableCell"]),
            Paragraph("Aggregates missing values, zero counts, and GeoJSON diffs.", styles["TableCell"]),
            Paragraph("<code>/api/quality</code>", styles["TableCellCode"]),
            Paragraph("Explains yield calculation exclusions.", styles["TableCell"])
        ],
        [
            Paragraph("<b>Big Data Status View</b>", styles["TableCellBold"]),
            Paragraph("Real-time telemetry of pipeline components.", styles["TableCell"]),
            Paragraph("Reports execution state, input/output paths, and cluster mode.", styles["TableCell"]),
            Paragraph("<code>getProcessingStatus()</code>", styles["TableCellCode"]),
            Paragraph("Confirms cluster vs REST mode.", styles["TableCell"])
        ],
    ]

    f_t = Table(feat_table_data, colWidths=[85, 105, 110, 85, usable_width - 385])
    f_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_ALT_ROW]),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
        ('LEFTPADDING', (0,0), (-1,-1), 2.5),
        ('RIGHTPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(f_t)

    story.append(Spacer(1, 4))
    story.append(Paragraph("Live Demonstration Protocol (Faculty Walkthrough Script)", styles["H2"]))
    story.append(Paragraph("1. <b>Initial Overview:</b> Open <code>/</code>; point out 4 KPI cards and scale suffixes ('M' for Million, 'K' for Thousand).", styles["Bullet"]))
    story.append(Paragraph("2. <b>Choropleth Drill-Down:</b> Click Maharashtra on map -- observe Top States convert to district bars and KPIs re-aggregate.", styles["Bullet"]))
    story.append(Paragraph("3. <b>Dependent Filters:</b> Open Filter Bar; note district dropdown is now restricted exclusively to Maharashtra's districts.", styles["Bullet"]))
    story.append(Paragraph("4. <b>Synthetic Shading:</b> Navigate to <code>/trends</code>; point to dashed lines and shaded bands for projected years 2024-2025.", styles["Bullet"]))
    story.append(Paragraph("5. <b>Unit Integrity:</b> On <code>/crops</code>, highlight why coconut nuts and grain tonnes cannot be mixed into all-crop yield.", styles["Bullet"]))
    story.append(Paragraph("6. <b>Data Explorer &amp; Export:</b> On <code>/explorer</code>, search 'Wheat', sort by Production, and click 'Export Filtered CSV'.", styles["Bullet"]))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 4: ARCHITECTURE AND DATA FLOW (Target: Page 5 full)
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("4. End-to-End Architecture &amp; Data Flow", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=1, spaceAfter=5))

    story.append(Paragraph(
        "AgriStat India operates on a decoupled client-server architecture with an asynchronous REST API bridge. "
        "The diagram below outlines the journey of data from raw government CSV files to the client's screen.",
        styles["Body"]
    ))

    arch_diagram_text = (
        "+-----------------------------------------------------------------------------------------+\n"
        "|                             DATA SOURCES & BIG DATA ENGINES                             |\n"
        "|  crop_production_1997_2025.csv (463,847 rows, 27.6 MB)  --> HDFS (/user/crop_project)   |\n"
        "+-----------------------------------------------------------------------------------------+\n"
        "                |                                              |\n"
        "                v                                              v\n"
        "+-------------------------------+             +----------------------------------+\n"
        "|      PYTHON / PANDAS PIPELINE |             |     APACHE PYSPARK & MAPREDUCE   |\n"
        "| data_cleaning.clean()         |             | pyspark_analysis.py (local[*])   |\n"
        "| - Whitespace stripping        |             | - Column casting & Schema check  |\n"
        "| - Season title-casing         |             | - Distributed GroupBy state/crop |\n"
        "| - Zero-guarded yield (t/ha)   |             | - Parquet & CSV Output Storage   |\n"
        "| - Provenance classification   |             | Hadoop Streaming (mapper/reducer)|\n"
        "+-------------------------------+             +----------------------------------+\n"
        "                |\n"
        "                v\n"
        "+-----------------------------------------------------------------------------------------+\n"
        "|                       FASTAPI REST BACKEND (backend/api.py)                             |\n"
        "| - Pre-loaded in-memory DataFrame (_DF) via async lifespan context manager               |\n"
        "| - In-memory LRU Query Cache (_CACHE, 512 entries) for sub-50ms repeat queries           |\n"
        "| - JSON Sentinel Sanitizer (_safe): converts NaN/Inf/pd.NA -> null native types          |\n"
        "| - CORS Middleware: whitelists Vercel production domains & localhost:3000                |\n"
        "| - Deployed on Render (Linux Container) at: https://agristat-india-api.onrender.com     |\n"
        "+-----------------------------------------------------------------------------------------+\n"
        "                ^                                              |\n"
        "  HTTP Request  | (GET /api/kpis?years=2015,2016&states=Punjab)| JSON Response (Gzip)\n"
        "                |                                              v\n"
        "+-----------------------------------------------------------------------------------------+\n"
        "|                      FRONTEND DATA SERVICE (frontend/lib/data/service.ts)               |\n"
        "| - Dual-Mode Resolver: createApiService() if API URL set, else demoService fallback     |\n"
        "| - In-Flight Deduplication: inFlightRequests map prevents duplicate parallel HTTP calls   |\n"
        "| - Client Response Cache: responseCache map (30s TTL) for instant back-navigation        |\n"
        "| - Auto Cold-Start Retry: Exponential backoff (2s, 3s, 5s) handles Render server wakeup  |\n"
        "+-----------------------------------------------------------------------------------------+\n"
        "                |\n"
        "                v\n"
        "+-----------------------------------------------------------------------------------------+\n"
        "|                      REACTIVE UI LAYER (Next.js 16 + React 19)                         |\n"
        "| - FiltersContext (filters-context.tsx): Cascading state reconciliation                  |\n"
        "| - SWR Hooks (use-analytics.ts): Stale-While-Revalidate caching & revalidation           |\n"
        "| - Visual Components: Plotly Charts, India Map Choropleth, KPI Cards, Data Explorer     |\n"
        "| - Deployed on Vercel Edge at: https://crop-production-complete.vercel.app              |\n"
        "+-----------------------------------------------------------------------------------------+"
    )
    story.append(Paragraph(f"<pre>{arch_diagram_text}</pre>", styles["CodeBlock"]))
    story.append(Spacer(1, 4))

    story.append(Paragraph("Code Tracing: Feature 1 -- KPI Summary Calculation", styles["H2"]))
    story.append(Paragraph("1. <b>User Action:</b> User selects year range (e.g. 2015-2020) and state 'Punjab' on the filter bar.", styles["Bullet"]))
    story.append(Paragraph("2. <b>FiltersContext Reconciliation:</b> <code>filters-context.tsx</code> reconciles state, verifies 'Punjab' in metadata, and triggers SWR hook <code>useKpis(filters)</code>.", styles["Bullet"]))
    story.append(Paragraph("3. <b>HTTP Request:</b> <code>service.ts</code> dispatches <code>GET /api/kpis?years=2015,2016,2017,2018,2019,2020&amp;states=Punjab</code>.", styles["Bullet"]))
    story.append(Paragraph("4. <b>FastAPI Query Processing:</b> In <code>backend/api.py</code>, the route executes <code>_apply_filters()</code> and computes total production, total area, crop count, district count, and YoY percentage changes.", styles["Bullet"]))
    story.append(Paragraph("5. <b>Sanitization &amp; Serialization:</b> <code>_safe()</code> converts NaN/Inf to null native types, serializing into clean JSON.", styles["Bullet"]))
    story.append(Paragraph("6. <b>UI Formatting &amp; Scaling:</b> The frontend runs <code>scaled(totalProduction)</code> formatting <code>284,500,000</code> into <code>'284.5 M tonnes'</code> with upward/downward percentage badges.", styles["Bullet"]))

    story.append(Spacer(1, 3))
    story.append(Paragraph("Code Tracing: Feature 2 -- State-Wise Choropleth Map", styles["H2"]))
    story.append(Paragraph("1. <b>Frontend Call:</b> <code>overview-view.tsx</code> invokes <code>useBreakdown(allStates, 'state')</code> with <code>state: 'all'</code> for national spatial context.", styles["Bullet"]))
    story.append(Paragraph("2. <b>Backend Execution:</b> The request hits <code>/api/statewise</code>. <code>pandas_analysis.py</code> groups by <code>State_Name</code>, summing production and area.", styles["Bullet"]))
    story.append(Paragraph("3. <b>GeoJSON Name Reconciliation:</b> In <code>india-map.tsx</code>, CSV state names are reconciled against GeoJSON properties (e.g. CSV 'Odisha' -> GeoJSON 'Orissa').", styles["Bullet"]))
    story.append(Paragraph("4. <b>Plotly Rendering:</b> Plotly builds a <code>choroplethmapbox</code> trace applying an emerald color scale normalized across state outputs.", styles["Bullet"]))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 5: IMPORTANT FILES AND CODE EXPLANATION (Target: Page 6 full)
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("5. Source Code &amp; Key File Responsibilities", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=1, spaceAfter=5))

    story.append(Paragraph(
        "The repository is organized into distinct backend and frontend packages. The table below outlines "
        "every critical file, its exact structural responsibility, and the key functions or components it exports.",
        styles["Body"]
    ))

    files_table_data = [
        [Paragraph("<b>File Path</b>", styles["TableHead"]), Paragraph("<b>Module Role</b>", styles["TableHead"]), Paragraph("<b>Key Functions / Components</b>", styles["TableHead"]), Paragraph("<b>Implementation Details &amp; Logic</b>", styles["TableHead"])],
        [
            Paragraph("<b>api.py</b> (root)", styles["TableCellBold"]),
            Paragraph("ASGI Entrypoint Proxy", styles["TableCell"]),
            Paragraph("<code>app</code> (delegated)", styles["TableCellCode"]),
            Paragraph("Ensures smooth execution on Render and local uvicorn by dynamically adding <code>backend/</code> and <code>backend/src/</code> to <code>sys.path</code>.", styles["TableCell"])
        ],
        [
            Paragraph("<b>backend/api.py</b>", styles["TableCellBold"]),
            Paragraph("Primary FastAPI REST Backend", styles["TableCell"]),
            Paragraph("<code>lifespan()</code>, <code>get_df()</code>, <code>_apply_filters()</code>, <code>_safe()</code>", styles["TableCellCode"]),
            Paragraph("Exposes 14 REST routes; maintains in-memory DataFrame <code>_DF</code> and 512-entry query cache <code>_CACHE</code>; implements CORS for Vercel.", styles["TableCell"])
        ],
        [
            Paragraph("<b>backend/src/<br/>data_cleaning.py</b>", styles["TableCellBold"]),
            Paragraph("Data Pipeline &amp; Validation", styles["TableCell"]),
            Paragraph("<code>load_raw()</code>, <code>clean()</code>, <code>quality_report()</code>", styles["TableCellCode"]),
            Paragraph("Strips string whitespace, title-cases seasons, coerces numeric types, adds <code>Yield_t_per_ha</code> and <code>Data_Provenance</code> columns.", styles["TableCell"])
        ],
        [
            Paragraph("<b>backend/src/<br/>pandas_analysis.py</b>", styles["TableCellBold"]),
            Paragraph("Core Analytical Aggregations", styles["TableCell"]),
            Paragraph("<code>statewise_production()</code>, <code>yearwise_production()</code>, <code>cropwise_production()</code>, <code>district_production()</code>", styles["TableCellCode"]),
            Paragraph("Executes zero-guarded GroupBy aggregations, calculating sums, record counts, unique entities, and yields for all dashboard dimensions.", styles["TableCell"])
        ],
        [
            Paragraph("<b>backend/src/<br/>pyspark_analysis.py</b>", styles["TableCellBold"]),
            Paragraph("Distributed Big Data Pipeline", styles["TableCell"]),
            Paragraph("<code>run_spark_pipeline()</code>", styles["TableCellCode"]),
            Paragraph("Initializes local SparkSession, casts DataFrame schemas, performs parallelized group-by aggregations, and writes Parquet outputs.", styles["TableCell"])
        ],
        [
            Paragraph("<b>backend/src/<br/>mapreduce/mapper.py<br/>reducer.py</b>", styles["TableCellBold"]),
            Paragraph("Hadoop Streaming MapReduce", styles["TableCell"]),
            Paragraph("UNIX Standard I/O streaming", styles["TableCellCode"]),
            Paragraph("Mapper extracts <code>State_Name\\tProduction</code>; Reducer aggregates key-value pairs across partition boundaries.", styles["TableCell"])
        ],
        [
            Paragraph("<b>backend/src/<br/>hdfs_utils.py</b>", styles["TableCellBold"]),
            Paragraph("Hadoop HDFS Bridge", styles["TableCell"]),
            Paragraph("<code>check_hdfs_available()</code>, <code>setup_hdfs_directories()</code>", styles["TableCellCode"]),
            Paragraph("Subprocess wrapper executing HDFS DFS commands with non-blocking graceful fallback when Hadoop is inactive.", styles["TableCell"])
        ],
        [
            Paragraph("<b>frontend/lib/data/<br/>service.ts</b>", styles["TableCellBold"]),
            Paragraph("Frontend Data Access Layer", styles["TableCell"]),
            Paragraph("<code>createApiService()</code>, <code>demoService</code>, <code>fetchJson()</code>", styles["TableCellCode"]),
            Paragraph("Manages API fetching, request deduplication (<code>inFlightRequests</code>), 30s response caching, and exponential backoff cold-start retries.", styles["TableCell"])
        ],
        [
            Paragraph("<b>frontend/lib/<br/>filters-context.tsx</b>", styles["TableCellBold"]),
            Paragraph("Global Filter State Manager", styles["TableCell"]),
            Paragraph("<code>FiltersProvider</code>, <code>useFilters()</code>, <code>reconcile()</code>", styles["TableCellCode"]),
            Paragraph("React Context maintaining active filter state; enforces cascading dependency rules (e.g. resetting district if state changes).", styles["TableCell"])
        ],
        [
            Paragraph("<b>frontend/components/<br/>views/overview-view.tsx</b>", styles["TableCellBold"]),
            Paragraph("Main Dashboard View", styles["TableCell"]),
            Paragraph("<code>OverviewView</code>", styles["TableCellCode"]),
            Paragraph("Orchestrates 4 KPI cards, India choropleth map, Top 10 ranking bar chart, multi-line trend chart, crop mix donut, and season bar chart.", styles["TableCell"])
        ],
        [
            Paragraph("<b>frontend/components/<br/>charts/india-map.tsx</b>", styles["TableCellBold"]),
            Paragraph("Interactive Choropleth Component", styles["TableCell"]),
            Paragraph("<code>IndiaMap</code>", styles["TableCellCode"]),
            Paragraph("Loads GeoJSON state boundaries, handles name normalization mapping, renders choroplethmapbox trace, and emits click selection events.", styles["TableCell"])
        ],
        [
            Paragraph("<b>frontend/components/<br/>views/quality-view.tsx</b>", styles["TableCellBold"]),
            Paragraph("Data Integrity &amp; Provenance", styles["TableCell"]),
            Paragraph("<code>QualityView</code>", styles["TableCellCode"]),
            Paragraph("Renders comprehensive audit summary: raw vs clean rows, null counts, exclusions, provenance bar charts, and data quality warnings.", styles["TableCell"])
        ],
    ]

    files_t = Table(files_table_data, colWidths=[95, 85, 120, usable_width - 300])
    files_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_ALT_ROW]),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 1.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.8),
        ('LEFTPADDING', (0,0), (-1,-1), 2.5),
        ('RIGHTPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(files_t)

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 6: API ENDPOINTS (Target: Page 7 full)
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("6. Verified REST API Endpoints Specification", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=1, spaceAfter=5))

    story.append(Paragraph(
        "The FastAPI backend serves 14 verified endpoints. Every endpoint was verified against <code>backend/api.py</code> "
        "and integration tested in <code>backend/tests/test_api.py</code>.",
        styles["Body"]
    ))

    api_table_data = [
        [Paragraph("<b>Endpoint &amp; Method</b>", styles["TableHead"]), Paragraph("<b>Purpose &amp; Operation</b>", styles["TableHead"]), Paragraph("<b>Query Parameters</b>", styles["TableHead"]), Paragraph("<b>Response Schema</b>", styles["TableHead"]), Paragraph("<b>Frontend Caller &amp; Status</b>", styles["TableHead"])],
        [
            Paragraph("<b>GET /api/health</b>", styles["TableCellBold"]),
            Paragraph("Server liveness &amp; dataset status.", styles["TableCell"]),
            Paragraph("None", styles["TableCellCode"]),
            Paragraph("<code>{status, records, year_min, year_max}</code>", styles["TableCellCode"]),
            Paragraph("DevOps / Render uptime monitoring. Not called directly by UI.", styles["TableCell"])
        ],
        [
            Paragraph("<b>GET /api/metadata</b>", styles["TableCellBold"]),
            Paragraph("Returns filter bounds and mapping trees.", styles["TableCell"]),
            Paragraph("None", styles["TableCellCode"]),
            Paragraph("<code>{years, states, crops, seasons, districts_by_state...}</code>", styles["TableCellCode"]),
            Paragraph("Called by <code>useMeta()</code> during initial application bootstrap.", styles["TableCell"])
        ],
        [
            Paragraph("<b>GET /api/quality</b>", styles["TableCellBold"]),
            Paragraph("Comprehensive data quality report.", styles["TableCell"]),
            Paragraph("None", styles["TableCellCode"]),
            Paragraph("<code>{total_records, missing_production, zero_production...}</code>", styles["TableCellCode"]),
            Paragraph("Called by <code>useQuality()</code> on Data Quality page (<code>/quality</code>).", styles["TableCell"])
        ],
        [
            Paragraph("<b>GET /api/kpis</b>", styles["TableCellBold"]),
            Paragraph("Single-roundtrip summary for KPI cards.", styles["TableCell"]),
            Paragraph("<code>years, states, district, crops, seasons, data_type</code>", styles["TableCellCode"]),
            Paragraph("<code>{totalProduction, totalArea, cropCount, stateCount...}</code>", styles["TableCellCode"]),
            Paragraph("Called by <code>useKpis()</code> on Overview, Regions, and Map views.", styles["TableCell"])
        ],
        [
            Paragraph("<b>GET /api/statewise</b>", styles["TableCellBold"]),
            Paragraph("State-level aggregation of metrics and yield.", styles["TableCell"]),
            Paragraph("All dimension filters", styles["TableCellCode"]),
            Paragraph("<code>{data: [{State_Name, Total_Production, Total_Area...}]}</code>", styles["TableCellCode"]),
            Paragraph("Called by <code>useBreakdown(filters, 'state')</code>; powers Map &amp; Bars.", styles["TableCell"])
        ],
        [
            Paragraph("<b>GET /api/yearwise</b>", styles["TableCellBold"]),
            Paragraph("Yearly national aggregate time-series.", styles["TableCell"]),
            Paragraph("All dimension filters", styles["TableCellCode"]),
            Paragraph("<code>{data: [{Crop_Year, Total_Production, Total_Area...}]}</code>", styles["TableCellCode"]),
            Paragraph("Called by <code>useTimeSeries()</code>; powers Trend chart &amp; KPI fallback.", styles["TableCell"])
        ],
        [
            Paragraph("<b>GET /api/cropwise</b>", styles["TableCellBold"]),
            Paragraph("Top N crops ranked by total production.", styles["TableCell"]),
            Paragraph("Dimension filters + <code>n</code> (default 15)", styles["TableCellCode"]),
            Paragraph("<code>{data: [{Crop, Production, Area, Yield_t_per_ha...}]}</code>", styles["TableCellCode"]),
            Paragraph("Called by <code>useBreakdown(filters, 'crop')</code>; powers Donut &amp; Crops view.", styles["TableCell"])
        ],
        [
            Paragraph("<b>GET /api/seasonal</b>", styles["TableCellBold"]),
            Paragraph("Production distribution across 6 seasons.", styles["TableCell"]),
            Paragraph("All dimension filters", styles["TableCellCode"]),
            Paragraph("<code>{data: [{Season, Total_Production, Total_Area...}]}</code>", styles["TableCellCode"]),
            Paragraph("Called by <code>useBreakdown(filters, 'season')</code>; powers Season bar chart.", styles["TableCell"])
        ],
        [
            Paragraph("<b>GET /api/mapdata</b>", styles["TableCellBold"]),
            Paragraph("GeoJSON-mapped choropleth table.", styles["TableCell"]),
            Paragraph("Dimension filters + <code>metric</code>", styles["TableCellCode"]),
            Paragraph("<code>{data: [{state, geo_name, value, unit, records...}]}</code>", styles["TableCellCode"]),
            Paragraph("Alternate backend map endpoint. Next.js maps client-side via <code>/api/statewise</code>.", styles["TableCell"])
        ],
        [
            Paragraph("<b>GET /api/crop-trend</b>", styles["TableCellBold"]),
            Paragraph("Longitudinal trend for a specific crop.", styles["TableCell"]),
            Paragraph("Dimension filters + <code>crop</code>", styles["TableCellCode"]),
            Paragraph("<code>{data: [{Crop_Year, Total_Production, Total_Area...}]}</code>", styles["TableCellCode"]),
            Paragraph("Called by <code>getTimeSeries()</code> when crop filter is active.", styles["TableCell"])
        ],
        [
            Paragraph("<b>GET /api/state-trend</b>", styles["TableCellBold"]),
            Paragraph("Longitudinal trend for a specific state.", styles["TableCell"]),
            Paragraph("Dimension filters + <code>state</code>", styles["TableCellCode"]),
            Paragraph("<code>{data: [{Crop_Year, Total_Production, Total_Area...}]}</code>", styles["TableCellCode"]),
            Paragraph("Called by <code>getTimeSeries()</code> when state filter is active.", styles["TableCell"])
        ],
        [
            Paragraph("<b>GET /api/districts</b>", styles["TableCellBold"]),
            Paragraph("District-level breakdown filtered by state.", styles["TableCell"]),
            Paragraph("Dimension filters + <code>state, n</code>", styles["TableCellCode"]),
            Paragraph("<code>{data: [{State_Name, District_Name, Production...}]}</code>", styles["TableCellCode"]),
            Paragraph("Called by <code>useBreakdown(filters, 'district')</code> on Regions view.", styles["TableCell"])
        ],
        [
            Paragraph("<b>GET /api/records</b>", styles["TableCellBold"]),
            Paragraph("Paginated record grid query.", styles["TableCell"]),
            Paragraph("Filters + <code>search, sort_by, sort_order, page, page_size</code>", styles["TableCellCode"]),
            Paragraph("<code>{records: [...], total, page, page_size, total_pages}</code>", styles["TableCellCode"]),
            Paragraph("Called by <code>useRecords()</code> on Data Explorer page (<code>/explorer</code>).", styles["TableCell"])
        ],
        [
            Paragraph("<b>GET /api/export/records</b>", styles["TableCellBold"]),
            Paragraph("Direct streaming CSV file download.", styles["TableCell"]),
            Paragraph("All dimension filters", styles["TableCellCode"]),
            Paragraph("<code>StreamingResponse</code> with <code>text/csv</code> header", styles["TableCellCode"]),
            Paragraph("Called by <code>ExportButtons</code> component on every page.", styles["TableCell"])
        ],
    ]

    api_t = Table(api_table_data, colWidths=[90, 95, 95, 105, usable_width - 385])
    api_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_ALT_ROW]),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
        ('LEFTPADDING', (0,0), (-1,-1), 2.5),
        ('RIGHTPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(api_t)

    story.append(Spacer(1, 3.5))
    story.append(Paragraph("KPI Implementation &amp; Resilient Fallback Strategy", styles["H2"]))
    story.append(Paragraph(
        "A key architectural feature of <code>frontend/lib/data/service.ts</code> is its dual-tier KPI strategy. "
        "The frontend first attempts to query <code>GET /api/kpis</code>, which executes in a single high-performance "
        "Pandas aggregation pass on the backend. If <code>/api/kpis</code> is unavailable or blocked, the client's "
        "<code>try/catch</code> block automatically executes <code>Promise.all()</code> across <code>/api/statewise</code>, "
        "<code>/api/yearwise</code>, and <code>/api/cropwise</code>, reducing these row arrays client-side to calculate "
        "total production, total area, and YoY percentages without crashing.",
        styles["Body"]
    ))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 7: DATASET AND CALCULATIONS (Target: Page 8 full)
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("7. Dataset Provenance, Cleaning &amp; Mathematical Formulations", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=1, spaceAfter=5))

    story.append(Paragraph(
        "All calculations in AgriStat India are derived from the official government crop production dataset. "
        "The table below documents the verified physical dataset attributes, followed by data cleaning rules "
        "and mathematical formulas.",
        styles["Body"]
    ))

    data_meta_data = [
        [Paragraph("<b>Dataset Property</b>", styles["TableCellBold"]), Paragraph("<b>Empirically Verified Value</b>", styles["TableCell"]), Paragraph("<b>Technical Note / Implication</b>", styles["TableCell"])],
        [Paragraph("Source File &amp; Size", styles["TableCellBold"]), Paragraph("<code>data/crop_production_1997_2025.csv</code> (27.6 MB)", styles["TableCellCode"]), Paragraph("Never mutated in-place; all transformations occur in memory.", styles["TableCell"])],
        [Paragraph("Total Row &amp; Column Count", styles["TableCellBold"]), Paragraph("463,847 records · 8 columns", styles["TableCellCode"]), Paragraph("High volume district-level agricultural observation records.", styles["TableCell"])],
        [Paragraph("Temporal Coverage", styles["TableCellBold"]), Paragraph("1997 to 2025 (29 Crop Years)", styles["TableCellCode"]), Paragraph("Spans modern agricultural reform periods and monsoon cycles.", styles["TableCell"])],
        [Paragraph("Geographical Breadth", styles["TableCellBold"]), Paragraph("34 States/UTs · 737 Districts", styles["TableCellCode"]), Paragraph("Comprehensive national coverage across all Indian states.", styles["TableCell"])],
        [Paragraph("Crop Varieties", styles["TableCellBold"]), Paragraph("115 distinct crop categories", styles["TableCellCode"]), Paragraph("Encompasses food grains, pulses, oilseeds, commercial &amp; cash crops.", styles["TableCell"])],
        [Paragraph("Cropping Seasons", styles["TableCellBold"]), Paragraph("6 seasons (Kharif, Rabi, Whole Year, Summer, Winter, Autumn)", styles["TableCellCode"]), Paragraph("Captures monsoon (Kharif) and winter (Rabi) harvest rhythms.", styles["TableCell"])],
        [Paragraph("Missing Values", styles["TableCellBold"]), Paragraph("4,973 rows (1.07%) missing Production; 0 missing Area", styles["TableCellCode"]), Paragraph("Excluded from production sums; never filled arbitrarily with zero.", styles["TableCell"])],
        [Paragraph("Zero Values", styles["TableCellBold"]), Paragraph("7,280 zero Production; 3,223 zero Area", styles["TableCellCode"]), Paragraph("Reflects crop abandonment, total drought loss, or reporting gaps.", styles["TableCell"])],
        [Paragraph("Duplicate Records", styles["TableCellBold"]), Paragraph("0 full duplicates · 0 key collision duplicates", styles["TableCellCode"]), Paragraph("High baseline integrity across State-District-Year-Season-Crop keys.", styles["TableCell"])],
    ]
    dm_t = Table(data_meta_data, colWidths=[120, 160, usable_width - 280])
    dm_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY_LIGHT),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('PADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(dm_t)

    story.append(Spacer(1, 4))
    story.append(Paragraph("Data Cleaning Pipeline (<code>backend/src/data_cleaning.py</code>)", styles["H2"]))
    story.append(Paragraph("1. <b>Whitespace Trimming:</b> Strips leading and trailing whitespace from string columns (<code>State_Name</code>, <code>District_Name</code>, <code>Season</code>, <code>Crop</code>).", styles["Bullet"]))
    story.append(Paragraph("2. <b>Season Standardisation:</b> Capitalises season values into Title Case (e.g. 'Kharif', 'Rabi') resolving capitalization discrepancies.", styles["Bullet"]))
    story.append(Paragraph("3. <b>Defensive Area Null Stripping:</b> Filters rows where Area is null (none exist in raw data, but defensive against corrupt records).", styles["Bullet"]))
    story.append(Paragraph("4. <b>Numeric Coercion:</b> Coerces <code>Area</code> and <code>Production</code> to <code>float64</code> via <code>pd.to_numeric(..., errors='coerce')</code>.", styles["Bullet"]))
    story.append(Paragraph("5. <b>Yield Calculation:</b> Computes <code>Yield_t_per_ha</code> strictly guarded by <code>(Area > 0) &amp; Production.notna()</code>.", styles["Bullet"]))
    story.append(Paragraph("6. <b>Provenance Annotation:</b> Flags years 2024 and 2025 with <code>Data_Provenance = 'Potentially Extended'</code>.", styles["Bullet"]))

    story.append(Spacer(1, 3.5))
    story.append(Paragraph("Mathematical Formulas &amp; Derived Metrics", styles["H2"]))
    story.append(Paragraph("• <b>Agricultural Yield Formulation:</b> <code>Yield (t/ha) = Production (t) / Area (ha)</code>. Guarded: If <code>Area == 0</code> or <code>Production is NaN</code>, Yield returns <code>NaN</code> (null in JSON).", styles["Body"]))
    story.append(Paragraph("• <b>Year-over-Year (YoY) Growth:</b> <code>Change % = ((Value_current - Value_previous) / Value_previous) * 100</code>. Guarded: If <code>Value_previous == 0</code> or null, returns null ('needs 2+ years').", styles["Body"]))

    story.append(Spacer(1, 3.5))
    story.append(Paragraph("Critical Data Quality Nuances &amp; Limitations", styles["H2"]))
    story.append(make_callout(
        "Crucial Anomaly 1: The Coconut Unit Mismatch",
        "In Indian government statistics, coconut production is recorded in NUMBER OF NUTS (often millions of nuts), "
        "whereas all other crops (rice, wheat, pulses) are measured in METRIC TONNES. In the raw CSV, both are stored "
        "under the same 'Production' column without unit flags. Naively summing all crops together causes Kerala, Tamil Nadu, "
        "and Karnataka to appear massively inflated in total production volume. AgriStat resolves this by explicitly restricting "
        "yield calculations to single crops only, and documenting the caveat transparently across the dashboard.",
        is_warning=True
    ))
    story.append(Spacer(1, 2.5))
    story.append(make_callout(
        "Crucial Anomaly 2: Forward-Filled Years (2024-2025)",
        "In the source dataset, years 2024 and 2025 are labelled 'Actual'. However, empirical analysis reveals they contain "
        "exactly 18,844 records each -- identical to 2023 -- with minor sequential increments. They are algorithmically "
        "projected or forward-filled, not official verified census returns. AgriStat transparently flags them as 'Synthetic / "
        "Potentially Extended' with dashed chart lines, adhering to strict academic integrity.",
        is_warning=True
    ))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 8: LOCAL SETUP AND DEPLOYMENT (Target: Page 9 full)
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("8. Local Setup &amp; Cloud Deployment Manual", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=1, spaceAfter=5))

    story.append(Paragraph(
        "Follow these exact Windows PowerShell instructions to set up, execute, and verify the project locally. "
        "All commands reflect the actual repository structure.",
        styles["Body"]
    ))

    story.append(Paragraph("Backend Setup &amp; Execution (Windows PowerShell)", styles["H2"]))
    backend_cmd_text = (
        "# 1. Navigate to project root\n"
        "cd \"c:\\Users\\vedant more\\OneDrive\\Desktop\\crop-production-complete\"\n\n"
        "# 2. Activate Python virtual environment (Python 3.13)\n"
        ".\\backend\\.venv\\Scripts\\Activate.ps1\n\n"
        "# 3. Verify installed dependencies or install from backend/requirements.txt\n"
        "python -m pip install -r backend/requirements.txt\n\n"
        "# 4. Launch FastAPI REST Server via Uvicorn on Port 8000\n"
        "python -m uvicorn api:app --reload --host 127.0.0.1 --port 8000\n\n"
        "# 5. Verify backend health in a separate terminal\n"
        "curl http://127.0.0.1:8000/api/health\n"
        "# Interactive Swagger UI Documentation: http://127.0.0.1:8000/docs"
    )
    story.append(Paragraph(f"<pre>{backend_cmd_text}</pre>", styles["CodeBlock"]))

    story.append(Spacer(1, 4))
    story.append(Paragraph("Frontend Setup &amp; Execution (Next.js 16 + React 19)", styles["H2"]))
    frontend_cmd_text = (
        "# 1. Open a new PowerShell terminal and navigate to frontend folder\n"
        "cd \"c:\\Users\\vedant more\\OneDrive\\Desktop\\crop-production-complete\\frontend\"\n\n"
        "# 2. Create or verify .env.local configuration\n"
        "# Point to local FastAPI backend:\n"
        "Set-Content -Path .env.local -Value \"NEXT_PUBLIC_ANALYTICS_API_URL=http://127.0.0.1:8000\"\n\n"
        "# 3. Install Node.js dependencies via pnpm or npm\n"
        "pnpm install    # (or: npm install --legacy-peer-deps)\n\n"
        "# 4. Start Next.js Development Server on Port 3000\n"
        "pnpm dev        # (or: npm run dev)\n\n"
        "# 5. Open Dashboard in Browser: http://localhost:3000"
    )
    story.append(Paragraph(f"<pre>{frontend_cmd_text}</pre>", styles["CodeBlock"]))

    story.append(Spacer(1, 4))
    story.append(Paragraph("Alternative: Standalone Streamlit Dashboard", styles["H2"]))
    streamlit_cmd_text = (
        "# From project root with virtual environment activated:\n"
        "streamlit run backend/app.py --server.port 8501"
    )
    story.append(Paragraph(f"<pre>{streamlit_cmd_text}</pre>", styles["CodeBlock"]))

    story.append(Spacer(1, 4))
    story.append(Paragraph("Production Cloud Deployment Architecture", styles["H2"]))
    story.append(Paragraph("• <b>Frontend on Vercel:</b> Deployed from GitHub repository root with Root Directory set to <code>frontend</code>. Environment variable <code>NEXT_PUBLIC_ANALYTICS_API_URL</code> is set to <code>https://agristat-india-api.onrender.com</code>. Builds edge-cached HTML and bundles static assets automatically.", styles["Bullet"]))
    story.append(Paragraph("• <b>Backend on Render:</b> Deployed as a Python Web Service pointing to repository root. Build command: <code>pip install -r backend/requirements.txt</code>. Start command: <code>uvicorn api:app --host 0.0.0.0 --port $PORT</code>. Render binds port dynamically via <code>$PORT</code>.", styles["Bullet"]))

    story.append(Spacer(1, 4))
    story.append(Paragraph("Troubleshooting &amp; Operational Failure Modes", styles["H2"]))
    trouble_data = [
        [Paragraph("<b>Failure Symptom</b>", styles["TableHead"]), Paragraph("<b>Root Cause</b>", styles["TableHead"]), Paragraph("<b>Resolution Procedure</b>", styles["TableHead"])],
        [
            Paragraph("<b>Render Cold Start Delay (50-90s)</b>", styles["TableCellBold"]),
            Paragraph("Render free-tier instances spin down to 0 after 15 min of inactivity.", styles["TableCell"]),
            Paragraph("<code>service.ts</code> implements automatic exponential retry (2s, 3s, 5s). Wait 60s or ping <code>/api/health</code> to wake up container.", styles["TableCell"])
        ],
        [
            Paragraph("<b>Blank KPI Cards or '—'</b>", styles["TableCellBold"]),
            Paragraph("Backend unreachable or CORS origin rejected by FastAPI.", styles["TableCell"]),
            Paragraph("Verify FastAPI console for requests; confirm Vercel domain is listed in <code>DEFAULT_ALLOWED_ORIGINS</code> in <code>backend/api.py</code>.", styles["TableCell"])
        ],
        [
            Paragraph("<b>Fallback to Demo Mode</b>", styles["TableCellBold"]),
            Paragraph("<code>NEXT_PUBLIC_ANALYTICS_API_URL</code> environment variable is missing.", styles["TableCell"]),
            Paragraph("Ensure <code>frontend/.env.local</code> exists with valid URL; rebuild frontend (<code>pnpm build</code>) to bake variable into static output.", styles["TableCell"])
        ],
        [
            Paragraph("<b>Port 8000 Already in Use</b>", styles["TableCellBold"]),
            Paragraph("A previous uvicorn or python process is still bound to port 8000.", styles["TableCell"]),
            Paragraph("Run <code>Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process</code> to terminate stale process.", styles["TableCell"])
        ],
    ]
    tr_t = Table(trouble_data, colWidths=[120, 150, usable_width - 270])
    tr_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_ALT_ROW]),
        ('PADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(tr_t)

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 9: PRESENTATION SCRIPT (Target: Page 10 full)
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("9. Timed Presentation Scripts &amp; Speaking Guide", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=1, spaceAfter=5))

    story.append(Paragraph(
        "These presentation scripts are formatted in natural, confident spoken English. Practice them aloud "
        "to deliver a polished defense before your examination committee.",
        styles["Body"]
    ))

    story.append(Paragraph("Complete 2.5-Minute Formal Presentation Speech", styles["H2"]))
    
    speech_blocks = [
        ("Slide 1: Title & Introduction (0:00 - 0:30)",
         "\"Respected professors and external examiners, good afternoon. Today, I am proud to present AgriStat India, "
         "an advanced Big Data analytics and visual intelligence platform designed to explore 29 years of Indian agricultural "
         "performance from 1997 through 2025.\n\n"
         "Agriculture is the backbone of the Indian economy, engaging over half our workforce. However, the official data "
         "collected by the Ministry of Agriculture is published as massive, disjointed spreadsheets. Analyzing 463,000 records "
         "in Excel leads to software crashes, zero visual geospatial insight, and severe misinterpretations due to measurement "
         "inconsistencies. Our project solves this by delivering an end-to-end, high-performance web platform.\""),
        
        ("Slide 2: System Architecture & Dual Engines (0:30 - 1:00)",
         "\"To handle both large-scale batch processing and sub-50ms web queries, we engineered a dual-layer architecture. "
         "For Big Data processing, we implemented Apache PySpark and Hadoop Streaming MapReduce, running distributed group-by "
         "aggregations and writing partitioned Parquet files into HDFS. For our web API, we built a Python FastAPI backend that "
         "pre-loads the cleaned dataset into memory and utilizes a 512-entry query cache. This guarantees sub-second response times "
         "across all 14 REST endpoints, communicating with our Next.js 16 and React 19 frontend hosted on Vercel.\""),
        
        ("Slide 3: Data Cleaning & Integrity Nuances (1:00 - 1:35)",
         "\"Our engineering rigor is reflected in our data pipeline. In `backend/src/data_cleaning.py`, we clean whitespace, standardise "
         "season definitions, and compute derived yield figures in metric tonnes per hectare. Crucially, we resolved two major "
         "industry data quality issues: First, coconut production in government datasets is recorded in 'nuts' rather than 'tonnes' -- "
         "we prevent misleading aggregations by isolating yield strictly to single crops. Second, we discovered that years 2024 and 2025 "
         "are forward-filled projections; rather than falsely claiming them as historical facts, our dashboard explicitly flags "
         "them with dashed trend lines and synthetic shaded bands.\""),

        ("Slide 4: Live Feature Demonstration (1:35 - 2:15)",
         "\"As you can see on the live dashboard, the national overview provides four instant KPI cards. When I click on Maharashtra "
         "on our interactive India choropleth map, the entire dashboard cross-filters dynamically. The Top States chart transitions "
         "into a district-level ranking, the crop mix isolates sugarcane and cotton, and the multi-line trend displays historical "
         "yield resilience. If we navigate to the Data Explorer, users can search 463,000 rows with server-side pagination, "
         "or download filtered CSV exports for policy analysis.\""),

        ("Slide 5: Conclusion & Future Scope (2:15 - 2:45)",
         "\"In conclusion, AgriStat India successfully bridges the gap between Big Data engineering and practical agricultural "
         "policy. The entire system is live on Vercel and Render, backed by 169 passing automated test cases. In the future, we plan "
         "to integrate weather satellite APIs and train machine learning yield prediction models. Thank you, and I look forward to your questions.\"")
    ]

    for title, text in speech_blocks:
        story.append(Paragraph(title, styles["ScriptSpeaker"]))
        story.append(Paragraph(text.replace("\n\n", "<br/><br/>"), styles["ScriptDialogue"]))

    story.append(Spacer(1, 4))
    story.append(Paragraph("5-Minute Slide-by-Slide Presentation Structure", styles["H2"]))
    slide_data = [
        [Paragraph("<b>Slide # &amp; Title</b>", styles["TableHead"]), Paragraph("<b>Visual Content on Slide</b>", styles["TableHead"]), Paragraph("<b>Core Spoken Message</b>", styles["TableHead"]), Paragraph("<b>Target Time</b>", styles["TableHead"])],
        [
            Paragraph("<b>Slide 1: Title</b>", styles["TableCellBold"]),
            Paragraph("Project name, student details, roll number, supervisor.", styles["TableCell"]),
            Paragraph("Introduce yourself, project title, and core motivation: modernizing Indian agricultural data.", styles["TableCell"]),
            Paragraph("30 sec", styles["TableCellCode"])
        ],
        [
            Paragraph("<b>Slide 2: Problem</b>", styles["TableCellBold"]),
            Paragraph("Spreadsheet crash illustration, data fragmentation, 463,847 rows stat.", styles["TableCell"]),
            Paragraph("Explain why Excel fails on large datasets and how information silos hurt farmers.", styles["TableCell"]),
            Paragraph("45 sec", styles["TableCellCode"])
        ],
        [
            Paragraph("<b>Slide 3: Architecture</b>", styles["TableCellBold"]),
            Paragraph("System block diagram: CSV -> PySpark/FastAPI -> Vercel/Render -> Next.js.", styles["TableCell"]),
            Paragraph("Explain the dual-engine approach: PySpark for big batch, FastAPI for sub-50ms REST queries.", styles["TableCell"]),
            Paragraph("60 sec", styles["TableCellCode"])
        ],
        [
            Paragraph("<b>Slide 4: Dataset Nuances</b>", styles["TableCellBold"]),
            Paragraph("Data attributes table, Coconut unit caveat callout, Synthetic years badge.", styles["TableCell"]),
            Paragraph("Highlight intellectual honesty: separating observed history from projected 2024-2025.", styles["TableCell"]),
            Paragraph("60 sec", styles["TableCellCode"])
        ],
        [
            Paragraph("<b>Slide 5: Live Demo</b>", styles["TableCellBold"]),
            Paragraph("Live browser window showing Next.js dashboard, choropleth map, filter drilldown.", styles["TableCell"]),
            Paragraph("Demonstrate state click, district cascading filter, and instant CSV export.", styles["TableCell"]),
            Paragraph("60 sec", styles["TableCellCode"])
        ],
        [
            Paragraph("<b>Slide 6: Conclusion</b>", styles["TableCellBold"]),
            Paragraph("169/169 Pytest pass console screenshot, future scope (ML yield prediction).", styles["TableCell"]),
            Paragraph("Summarize impact, confirm test coverage, and express readiness for viva examination.", styles["TableCell"]),
            Paragraph("45 sec", styles["TableCellCode"])
        ],
    ]
    sl_t = Table(slide_data, colWidths=[90, 130, usable_width - 270, 50])
    sl_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_ALT_ROW]),
        ('PADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(sl_t)

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 10: VIVA QUESTIONS AND ANSWERS (Target: Pages 11, 12, 13 full)
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("10. Comprehensive Faculty Viva Questions &amp; Answers", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=1, spaceAfter=5))

    story.append(Paragraph(
        "This section compiles 36 high-probability viva questions divided across 5 core competency areas. "
        "Every answer is technically precise and directly reflects the repository's code implementation.",
        styles["Body"]
    ))

    viva_groups = [
        ("Group A: Project Objectives, Real-World Impact & Architecture", [
            ("Q1: What is the main objective of AgriStat India, and why is it needed?",
             "AgriStat India aggregates 29 years of district-level Indian agricultural data (463,847 records) into an interactive, sub-50ms analytics dashboard. It eliminates spreadsheet limitations, provides spatial choropleth mapping, resolves unit inconsistencies (like coconut nuts vs grain tonnes), and transparently identifies synthetic projections."),
            ("Q2: Why did you choose a decoupled architecture (Next.js frontend + FastAPI backend) instead of a monolithic framework like Django or Streamlit?",
             "Decoupling separates user interface performance from backend analytical computing. Next.js 16 provides edge-cached, static HTML rendering on Vercel with zero cold start for UI assets, while FastAPI on Render handles memory-heavy Pandas filtering. If we used Streamlit alone, multi-user concurrency would bottleneck on Python's GIL. If we used Django, we would carry unnecessary ORM overhead when our analytical workload is entirely columnar vector processing."),
            ("Q3: How do the frontend and backend communicate in production?",
             "They communicate over HTTPS using RESTful JSON APIs. The frontend data layer (`service.ts`) issues `fetch()` requests to `https://agristat-india-api.onrender.com`. FastAPI receives requests, checks an in-memory cache, executes vector filtering, sanitizes nulls via `_safe()`, and returns gzipped JSON."),
            ("Q4: Does your project predict future crop production using machine learning?",
             "No, and this is an important distinction. AgriStat is a descriptive and diagnostic Big Data analytics platform. It computes empirical historical aggregations and visualizes trends. While the dataset contains forward-filled records for 2024-2025, we explicitly flag them as synthetic estimates rather than claiming them as predictive ML models."),
            ("Q5: What are the primary user personas for this dashboard?",
             "Agricultural policy planners evaluating food security buffer stocks, crop insurance underwriters (PMFBY) calculating district baseline yield variances, agronomists analyzing seasonal crop performance, and agribusiness supply chain operators planning procurement."),
            ("Q6: How does the system handle concurrent users requesting different filters?",
             "FastAPI is an asynchronous ASGI framework running on Uvicorn. Data filtering in Pandas releases the Python GIL during heavy NumPy underlying operations, allowing Uvicorn's event loop to handle hundreds of concurrent requests. Furthermore, our 512-entry in-memory cache returns pre-calculated responses in under 5 milliseconds for duplicate filter requests."),
            ("Q7: What is the dual-mode architecture in the frontend?",
             "In `frontend/lib/data/service.ts`, the frontend inspects `process.env.NEXT_PUBLIC_ANALYTICS_API_URL`. If present, it initializes `createApiService` calling the live backend. If absent, it gracefully falls back to `demoService`, which generates synthetic records and aggregates them entirely in-browser. This ensures the frontend never shows a fatal crash if the backend is offline."),
        ]),

        ("Group B: Frontend Engineering, React 19 & Next.js 16", [
            ("Q8: Why did you choose Next.js 16 and React 19?",
             "Next.js 16 provides the App Router with hybrid server and client component boundaries, automatic asset pre-fetching, and instant deployment to Vercel's global edge network. React 19 provides concurrent rendering, smooth state transitions, and hooks like `useDeferredValue` for stutter-free search bar debouncing across thousands of records."),
            ("Q9: What is SWR and why is it better than a standard `useEffect` + `fetch`?",
             "SWR (Stale-While-Revalidate) is a client-side data-fetching library. Unlike standard `useEffect`, SWR automatically caches API responses, deduplicates simultaneous identical requests across different UI components, revalidates on window focus, and provides optimistic UI updates with automatic retries."),
            ("Q10: How does your filter reconciliation logic prevent invalid user selections?",
             "In `frontend/lib/filters-context.tsx`, the `reconcile()` function runs whenever a filter changes. If a user selects 'Punjab', the function cross-references `meta.districtsByState` and automatically resets any previously selected district (e.g. 'Pune') back to 'all'. It also ensures that selecting 'yield' without a specific crop reverts to 'production' to prevent cross-crop unit errors."),
            ("Q11: How is the India Choropleth map implemented without crashing the browser?",
             "We use Plotly.js (`plotly.js-dist-min`) with a TopoJSON/GeoJSON boundary file (`india_states.geojson`). Instead of rendering individual district polygons (which would require tens of thousands of complex SVG nodes), the map groups data at the state level (34 features) and reconciles naming differences (e.g., 'Odisha' vs 'Orissa') client-side."),
            ("Q12: How do you format numbers for readability on mobile and desktop?",
             "In `frontend/lib/format.ts`, the `scaled()` helper checks absolute values. If greater than 1,000,000, it divides by 1e6 and appends 'M'; if greater than 1,000, it appends 'K'. This prevents huge numbers like `284,529,102 tonnes` from breaking card layouts, rendering as `284.53 M tonnes`."),
            ("Q13: How does the Data Explorer page maintain high performance when displaying records?",
             "The Data Explorer (`explorer-view.tsx`) uses server-side pagination with a fixed limit of 25 records per page (`PAGE_SIZE = 25`). Sorting and filtering parameters (`page`, `sort_by`, `search`) are transmitted as query parameters to `/api/records`, ensuring the browser DOM never renders more than 25 table rows at a time."),
            ("Q14: How did you implement responsive design across mobile and desktop?",
             "We used Tailwind CSS v4's mobile-first responsive utility classes (`grid-cols-1 sm:grid-cols-2 xl:grid-cols-4`). Chart containers utilize fixed height breakpoints (`h-[460px] md:h-[680px]`) with flexbox wrappers, ensuring all visual cards scale cleanly on mobile devices and 4K displays."),
        ]),

        ("Group C: Backend Engineering, FastAPI & REST Endpoints", [
            ("Q15: Why did you choose FastAPI over Flask?",
             "FastAPI is substantially faster because it runs on ASGI (Asynchronous Server Gateway Interface) via Uvicorn, rather than WSGI. It provides native type hinting, automatic Pydantic input validation, and auto-generates interactive Swagger documentation at `/docs` with zero extra code."),
            ("Q16: How does the backend avoid reloading the 27.6 MB CSV file on every request?",
             "We implement FastAPI's async `lifespan` context manager in `backend/api.py`. When Uvicorn starts, the dataset is loaded once into a global variable `_DF` via `get_df()`. All subsequent HTTP requests read from this in-memory DataFrame in RAM, achieving sub-50ms execution times."),
            ("Q17: How do you serialize Pandas NaN and Infinite float values to JSON without errors?",
             "Standard JSON does not support `NaN`, `Infinity`, or Pandas `pd.NA`. Naive `json.dumps()` will crash. In `backend/api.py`, we created a recursive sanitizer function `_safe()` and `_df_to_records()` that inspects every value: `np.floating` with `math.isnan()` is converted to `None`, which safely serializes to standard `null` in JSON."),
            ("Q18: What is the purpose of the `/api/health` endpoint if the UI does not call it?",
             "The `/api/health` endpoint is an industry-standard DevOps pattern. It is used by cloud monitoring services (such as Render health checks, Docker health probes, and uptime pingers) to verify container readiness and ensure the 463,847 records are loaded in memory before routing user traffic."),
            ("Q19: What is the purpose of `/api/mapdata` versus `/api/statewise`?",
             "Both return state-level aggregations. However, `/api/mapdata` explicitly merges GeoJSON name mappings on the server, designed for third-party or mobile map clients. The Next.js frontend calls `/api/statewise` directly and handles mapping in `india-map.tsx`, keeping map rendering completely decoupled from server schemas."),
            ("Q20: How does `/api/export/records` stream CSV data efficiently?",
             "Instead of building a massive string in memory, `/api/export/records` uses FastAPI's `StreamingResponse` with `io.StringIO()`. It applies active filters to the in-memory DataFrame and streams CSV rows chunk-by-chunk with a `Content-Disposition: attachment` header, preventing server memory spikes."),
            ("Q21: How is CORS configured, and why is it essential?",
             "Cross-Origin Resource Sharing (CORS) is enforced by browsers to prevent unauthorized cross-domain API access. In `backend/api.py`, `CORSMiddleware` whitelists Vercel production domains (`crop-production-complete.vercel.app`) and `localhost:3000`, allowing HTTP GET requests while blocking untrusted origins."),
        ]),

        ("Group D: Big Data Processing, PySpark, MapReduce & Dataset", [
            ("Q22: Why include Apache PySpark and MapReduce if the dataset fits in 27.6 MB of RAM?",
             "In academic and production data engineering, demonstrating distributed computing principles is essential. While 463,847 rows fit comfortably in RAM today, agricultural IoT sensor networks, satellite imagery, and soil telemetry expand datasets into gigabytes and terabytes. Implementing PySpark (`pyspark_analysis.py`) and MapReduce proved that our aggregation logic scales across a multi-node cluster without architectural refactoring."),
            ("Q23: How does your PySpark pipeline work?",
             "In `backend/src/pyspark_analysis.py`, we initialize a `SparkSession` with master `local[*]`. It reads the raw CSV, casts `Area` and `Production` to `DoubleType`, applies null filtering, and runs distributed `.groupBy('State_Name').agg(F.sum('Production'), ...)` queries, saving outputs as snappy-compressed Parquet files."),
            ("Q24: How does your Hadoop MapReduce implementation work?",
             "In `backend/src/mapreduce/`, we use Hadoop Streaming. `mapper.py` reads CSV rows from standard input, parses columns, and emits tab-delimited `<State_Name>\t<Production>` key-value pairs. Hadoop's shuffle-and-sort phase groups identical states together, and `reducer.py` reads sorted streams to output cumulative totals per state."),
            ("Q25: What is the exact formula for agricultural yield in your code?",
             "`Yield_t_per_ha = Production / Area`. It is calculated only when `Area > 0` and `Production.notna()`. If `Area == 0`, it returns `np.nan` (rendered as `null` in JSON and '—' on the UI), completely preventing divide-by-zero crashes."),
            ("Q26: Why are 4,973 production values missing in the dataset, and how do you handle them?",
             "Missing values (1.07% of the dataset) occur due to reporting lapses in remote districts or crop failures before harvest. In `data_cleaning.py`, we defensively keep these rows so cultivated area statistics remain accurate, but exclude them from production sums via `.dropna(subset=['Production'])`. We never fill missing production with zero, as that would falsely drag down district yield averages."),
            ("Q27: Explain the Coconut Unit Anomaly in detail.",
             "In Indian agricultural reporting, coconuts are harvested and counted in individual nuts, whereas grains, oilseeds, and pulses are weighed in metric tonnes. In the government CSV, both use the 'Production' column. A single district in Kerala producing 500 million coconuts would appear to produce 500 million tonnes if summed naively! AgriStat resolves this by enforcing crop-specific yield metrics and warning users prominently."),
            ("Q28: What is your evidence that years 2024 and 2025 are synthetic?",
             "When analyzing record counts per year, 1997-2022 vary naturally according to agricultural reporting cycles. However, 2024 and 2025 each contain exactly 18,844 rows -- identical to 2023. The state-district-crop combinations replicate 2022/2023 with small synthetic increments, indicating forward-filled estimations rather than empirical census surveys."),
            ("Q29: How did state reorganizations affect your analysis?",
             "Over the 29-year timeline, Indian internal boundaries changed: Telangana was carved from Andhra Pradesh in 2014, and Ladakh was separated from Jammu & Kashmir in 2019. In `map_utils.py`, we document that historical comparisons for Andhra Pradesh show a drop after 2014 because Telangana records branched into a separate entity. For mapping, Ladakh is mapped to J&K geometry because standard India GeoJSONs predate 2019."),
        ]),

        ("Group E: Deployment, Testing, Cold Starts & Security", [
            ("Q30: How many automated tests exist, and how are they structured?",
             "We have 169 automated tests in `backend/tests/` (100% passing). `test_api.py` contains integration tests for all 14 endpoints using FastAPI's in-process `TestClient` (powered by HTTPX), verifying HTTP status codes, parameter filtering, and JSON schemas. `test_pipeline.py` verifies data cleaning, column addition, and non-negative constraints."),
            ("Q31: What is a Render 'Cold Start' and how did you engineer around it?",
             "Render's free tier spins down inactive web services after 15 minutes. When a user visits the dashboard after inactivity, the first API call may take 50-90 seconds while the container boots and loads the 463,000 records. In `service.ts`, we implemented an automatic retry loop with exponential delays (2s, 3s, 5s, 7s, 10s) and logged user notifications, preventing the frontend from failing prematurely."),
            ("Q32: How did you verify that no secret keys or passwords were leaked in this project?",
             "The project operates on public government data. All environment variables in `.env.example` specify public URLs (`NEXT_PUBLIC_ANALYTICS_API_URL`) or internal paths. Git history contains zero credential commits, and all cloud resources operate on anonymous read-only access."),
            ("Q33: How does the client-side caching mechanism work?",
             "In `service.ts`, we maintain two caching structures: `responseCache` (storing API responses with a 30-second TTL for instant back-navigation) and `inFlightRequests` (a Map storing active Promises that deduplicates simultaneous parallel requests for identical URLs)."),
            ("Q34: If the university wanted to scale this to 100 million records, what changes would you make?",
             "We would transition from an in-memory Pandas DataFrame to an analytical columnar database like ClickHouse or DuckDB, or maintain pre-aggregated cube tables in PostgreSQL. The frontend and FastAPI REST contracts would remain completely unchanged, preserving the UI layer."),
            ("Q35: What would happen if a user types a SQL injection payload into the search bar?",
             "The search bar queries the in-memory Pandas DataFrame via vector string matching (`df['Crop'].str.contains(...)`) or client-side filtering. Because there is no raw SQL database execution, standard SQL injection attacks have zero attack surface on this architecture."),
            ("Q36: What is the single most important lesson learned during this project?",
             "The critical importance of data provenance and domain knowledge. Writing code is easy, but discovering that coconuts were counted in nuts and recent years were synthetic forward-fills taught us that data engineers must always rigorously audit raw data before presenting charts to decision-makers."),
        ]),
    ]

    for group_title, qas in viva_groups:
        story.append(Paragraph(group_title, styles["H2"]))
        for q, a in qas:
            story.append(Paragraph(f"<b>{q}</b>", styles["VivaQ"]))
            story.append(Paragraph(a, styles["VivaA"]))
        story.append(Spacer(1, 1.5))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 11: QUICK REVISION SHEET (Target: Page 14 full)
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("11. Quick Revision Sheet &amp; Technical Glossary", styles["H1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=1, spaceAfter=5))

    story.append(Paragraph(
        "Review this high-density cheat sheet 10 minutes before entering your presentation room. "
        "It summarizes all key facts, definitions, and equations in concise language.",
        styles["Body"]
    ))

    story.append(Paragraph("One-Line Technology Explanations", styles["H2"]))
    one_liners = [
        ("Next.js 16", "React framework providing App Router, server-side pre-rendering, and global Vercel edge deployment."),
        ("React 19", "Modern UI library utilizing concurrent rendering and hooks (`useDeferredValue`, `useMemo`) for reactive state."),
        ("FastAPI", "High-performance Python ASGI REST framework providing Pydantic validation and auto-generated Swagger docs."),
        ("Pandas 3.0", "In-memory columnar data engine executing sub-50ms GroupBy aggregations and boolean filtering."),
        ("Apache PySpark", "Distributed cluster computing engine running parallelized SQL transformations and saving Parquet files."),
        ("Hadoop MapReduce", "UNIX Streaming mapper and reducer scripts implementing batch key-value aggregation across nodes."),
        ("Plotly.js", "Hardware-accelerated charting library rendering interactive choropleth maps, trend lines, and donut charts."),
        ("SWR 2.5", "Client state manager providing Stale-While-Revalidate caching, request deduplication, and error recovery."),
    ]
    for tech, desc in one_liners:
        story.append(Paragraph(f"• <b>{tech}:</b> {desc}", styles["Bullet"]))

    story.append(Spacer(1, 3))
    story.append(Paragraph("Core Mathematical Formulas", styles["H2"]))
    story.append(Paragraph("1. <b>Yield:</b> <code>Yield (t/ha) = Production (t) / Area (ha)</code> [Guarded: <code>Area > 0</code> and <code>Production != null</code>]", styles["Bullet"]))
    story.append(Paragraph("2. <b>YoY Growth:</b> <code>Change % = ((Prod_t - Prod_t-1) / Prod_t-1) * 100</code> [Guarded: <code>Prod_t-1 > 0</code>]", styles["Bullet"]))
    story.append(Paragraph("3. <b>Crop Share:</b> <code>Share % = (Production_crop / Total_Production_filtered) * 100</code>", styles["Bullet"]))

    story.append(Spacer(1, 3))
    story.append(Paragraph("Technical Glossary", styles["H2"]))
    glossary = [
        ("Kharif Season", "Autumn harvest cropping season sown with southwest monsoons (June-October); includes Rice, Maize, Cotton."),
        ("Rabi Season", "Spring harvest cropping season sown in winter (October-March); includes Wheat, Barley, Mustard, Gram."),
        ("Choropleth Map", "A thematic map where administrative areas are shaded in proportion to an aggregated statistical variable."),
        ("In-Flight Deduplication", "Coalescing concurrent identical network requests into a single shared Promise to prevent duplicate server hits."),
        ("Parquet", "An open-source columnar storage file format providing efficient data compression and encoding schemes."),
        ("Cold Start", "The latency delay (50-90s) incurred when a serverless container spins up from an idle zero-instance state."),
    ]
    for term, defn in glossary:
        story.append(Paragraph(f"• <b>{term}:</b> {defn}", styles["Bullet"]))

    story.append(Spacer(1, 3.5))
    story.append(Paragraph("Ten Golden Rules for Presentation Day", styles["H2"]))
    golden_rules = [
        "1. Start with confidence: state the 463,847 row count and 29-year span immediately to establish project scale.",
        "2. Never claim you predicted future yields: emphasize that 2024-2025 are synthetic forward-fills and you flagged them transparently.",
        "3. Emphasize the coconut anomaly: faculty love when students spot real-world data collection flaws like 'nuts' vs 'tonnes'.",
        "4. Explain the dual-engine purpose: PySpark for big batch cluster scalability, FastAPI/Pandas for sub-50ms web queries.",
        "5. Explain the dual-mode frontend: if the API sleeps, the demoService ensures the dashboard never displays a fatal crash.",
        "6. Highlight 169 automated tests: passing 169 unit and integration tests proves industrial code quality and robustness.",
        "7. Point out cascading filter reconciliation: selecting a state dynamically restricts the district dropdown to valid children.",
        "8. Demonstrate interactive map drill-down: clicking Maharashtra to update the entire dashboard wows evaluators.",
        "9. Maintain composure during cold starts: if Render wakes up slowly, explain that free-tier instances sleep after 15 min.",
        "10. Conclude with realistic future scope: integrate real-time satellite vegetation index (NDVI) and weather forecast APIs."
    ]
    for rule in golden_rules:
        story.append(Paragraph(f"<b>{rule}</b>", styles["Bullet"]))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated {OUTPUT_PDF}")


if __name__ == "__main__":
    build_pdf()
