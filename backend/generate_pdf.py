import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

PDF_OUTPUT_PATH = "../Lumio_Production_Documentation.pdf"

class NumberedCanvas(canvas.Canvas):
    """
    Custom canvas to enable dynamic page numbering (Page X of Y)
    and uniform headers/footers on all pages except the cover page.
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
            self.draw_page_number_and_headers(num_pages)
            super().showPage()
        super().save()

    def draw_page_number_and_headers(self, page_count):
        # Suppress headers & footers on the cover page
        if self._pageNumber == 1:
            return
        
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#475569")) # Slate-600
        
        # Header text & line
        self.drawString(60, 745, "LUMIO PRODUCTION MANUAL")
        self.setFont("Helvetica", 8)
        self.drawRightString(612 - 60, 745, "TECHNICAL ARCHITECTURE & AWS DEPLOYMENT")
        self.setStrokeColor(colors.HexColor("#cbd5e1")) # Slate-300
        self.setLineWidth(0.5)
        self.line(60, 737, 612 - 60, 737)
        
        # Footer text & page number
        self.line(60, 55, 612 - 60, 55)
        self.setFont("Helvetica-Bold", 7)
        self.setFillColor(colors.HexColor("#94a3b8")) # Slate-400
        self.drawString(60, 40, "CONFIDENTIAL - \u00a9 2026 RAJAN KUMAR. ALL RIGHTS RESERVED.")
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#475569"))
        self.drawRightString(612 - 60, 40, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def make_block_heading(text, style):
    """
    Wraps Heading 1 text inside a 1-cell Table with a colored left-border
    and light background to create a premium block-style heading.
    """
    p = Paragraph(text, style)
    t = Table([[p]], colWidths=[612 - 120]) # Adjust width according to document margins (60pt left/right)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")), # Slate-100
        ('LINELEFT', (0,0), (0,-1), 3.0, colors.HexColor("#4f46e5")), # Indigo left border
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    return t


def build_pdf():
    # Page dimensions: letter is 612 x 792 points. Margins: 60 pt left/right, 72 pt top/bottom
    doc = SimpleDocTemplate(
        PDF_OUTPUT_PATH,
        pagesize=letter,
        leftMargin=60,
        rightMargin=60,
        topMargin=72,
        bottomMargin=72
    )

    styles = getSampleStyleSheet()
    
    # Custom Typography Styles
    cover_logo_style = ParagraphStyle(
        'CoverLogo',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=46,
        leading=50,
        textColor=colors.HexColor("#0f172a"), # Slate-900
        alignment=1, # Center
        spaceAfter=12
    )
    
    cover_subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#4f46e5"), # Indigo-600
        alignment=1,
        spaceAfter=35
    )
    
    cover_title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=24,
        textColor=colors.HexColor("#334155"), # Slate-700
        alignment=1,
        spaceAfter=50
    )
    
    h1_text_style = ParagraphStyle(
        'H1_Text',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#0f172a"), # Slate-900
    )
    
    h2_style = ParagraphStyle(
        'H2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#0f766e"), # Teal-700
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=14,
        textColor=colors.HexColor("#334155"), # Slate-700
        spaceAfter=8,
    )
    
    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        leftIndent=20,
        firstLineIndent=-10,
        spaceAfter=5,
    )
    
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#334155")
    )
    
    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0f172a")
    )
    
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    story = []

    # ==========================================
    # COVER PAGE
    # ==========================================
    story.append(Spacer(1, 60))
    story.append(Paragraph("LUMIO", cover_logo_style))
    story.append(Paragraph("THE HIGH-PERFORMANCE WEB DOWNLOADER", cover_subtitle_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Production Deployment & Technical Documentation<br/><font size=12>FastAPI Backend & Vanilla CSS Frontend on AWS ECS Fargate</font>", cover_title_style))
    story.append(Spacer(1, 10))
    
    metadata_data = [
        [Paragraph("Lead Developer", table_cell_bold), Paragraph("<b>Rajan Kumar</b>", table_cell_bold)],
        [Paragraph("GitHub Profile", table_cell_style), Paragraph('<a href="https://github.com/RajGenStack"><font color="#4f46e5"><u>github.com/RajGenStack</u></font></a>', table_cell_style)],
        [Paragraph("LinkedIn Profile", table_cell_style), Paragraph('<a href="https://www.linkedin.com/in/rajan-kumar42/"><font color="#4f46e5"><u>linkedin.com/in/rajan-kumar42/</u></font></a>', table_cell_style)],
        [Paragraph("Instagram", table_cell_style), Paragraph('<a href="https://www.instagram.com/rajansxarma?igsh=eDh1bnk1NmVsZjcz"><font color="#4f46e5"><u>instagram.com/rajansxarma</u></font></a>', table_cell_style)],
        [Paragraph("Document Version", table_cell_style), Paragraph("1.0.1 (Stable Release)", table_cell_style)],
        [Paragraph("Target Audience", table_cell_style), Paragraph("Project Manager, AWS Security & DevOps Team", table_cell_style)],
        [Paragraph("Date of Compilation", table_cell_style), Paragraph("June 13, 2026", table_cell_style)],
        [Paragraph("Copyright Notice", table_cell_style), Paragraph("&copy; 2026 Rajan Kumar. All Rights Reserved.", table_cell_style)],
        [Paragraph("Release State", table_cell_style), Paragraph("Production-Ready", table_cell_bold)],
    ]
    meta_table = Table(metadata_data, colWidths=[130, 250])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")), # Slate-50 background
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")), # Slate-300 border
        ('LINEBELOW', (0,0), (-1,-2), 0.5, colors.HexColor("#e2e8f0")), # Inner borders
        ('PADDING', (0,0), (-1,-1), 7),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    story.append(PageBreak())

    # ==========================================
    # SECTION 1: EXECUTIVE SUMMARY & RESEARCH
    # ==========================================
    story.append(make_block_heading("1. Executive Summary & R&D Genesis", h1_text_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "<b>Lumio</b> is a lightweight, responsive, production-ready web application designed for downloading YouTube content. "
        "It supports high-speed, server-side audio extraction (MP3 format up to 320 kbps) and video compilation (MP4 formats up to 8K HDR). "
        "The system offloads heavy network and CPU processing directly to an elastic backend container, meaning client devices experience "
        "zero local computational load.", body_style))
    
    story.append(Paragraph("1.1 Core Mission & Ad-Free Philosophy", h2_style))
    story.append(Paragraph(
        "Modern online streaming media has become saturated with invasive advertisement structures, trackers, and expensive subscription barriers. "
        "This creates digital inequality, locking out users who cannot afford monthly premiums or those in areas with unstable data connections who depend on offline media. "
        "Lumio was built by <b>Rajan Kumar</b> as a fully open-source, 100% free, and completely ad-free utility. "
        "By providing a high-fidelity interface to stream and download videos without subscription walls or tracking popups, Lumio promotes open-access to media for educational, research, and personal archive use.", body_style))
    
    story.append(Paragraph("Research & Development Phase Key Decisions:", h2_style))
    story.append(Paragraph("• <b>Audio Transcoding Correction:</b> In the initial prototype, a 620 kbps 'Lossless' MP3 option was defined. R&D analysis showed that the MP3 standard supports a maximum bitrate of 320 kbps. The prototype mapped the '620k' setting to LAME VBR 0, which generated output files between 220-260 kbps (seen by the user as capping at 261 kbps). In this production release, the misleading '620k' option has been eliminated, and a true 320 kbps CBR (Constant Bitrate) option is established as the highest tier, ensuring users receive the highest compliance and actual 320 kbps quality.", bullet_style))
    story.append(Paragraph("• <b>FastAPI Event-Loop Decoupling:</b> Running command line subprocesses or blocking I/O functions inside a standard asynchronous route blocks the FastAPI event loop, causing service timeouts. The system now utilizes <code>asyncio.to_thread()</code> to defer the heavy <code>yt-dlp</code> downloads and <code>FFmpeg</code> processing to a separate thread pool. The server remains responsive to simultaneous health-checks and fetch queries.", bullet_style))
    story.append(Paragraph("• <b>Multi-Stage Docker Optimization:</b> Standard Python Docker images with compiled packages like <code>Pydantic</code> and full <code>FFmpeg</code> distributions easily exceed 1.2 GB. To minimize hosting storage and cold-start times on AWS Fargate, we implemented a multi-stage Docker build that isolates compiler tools (Stage 1) and outputs a lean, hardened runtime container (Stage 2) under 450 MB.", bullet_style))
    story.append(Spacer(1, 15))

    # ==========================================
    # SECTION 2: SYSTEM ARCHITECTURE & STACK
    # ==========================================
    story.append(make_block_heading("2. Technical Stack Specifications", h1_text_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Lumio utilizes a decoupled microservices-ready structure built on native languages and frameworks to minimize dependencies and overhead:", body_style))
    
    tech_data = [
        [Paragraph("Layer", table_header_style), Paragraph("Technology", table_header_style), Paragraph("Purpose & Version", table_header_style)],
        [Paragraph("Frontend UI", table_cell_bold), Paragraph("HTML5 & Vanilla Javascript", table_cell_style), Paragraph("Structure and interactive UI. Minimal asset size.", table_cell_style)],
        [Paragraph("Styling", table_cell_bold), Paragraph("Vanilla CSS (Modern Custom Properties)", table_cell_style), Paragraph("HARP styles, neon glassmorphism, responsive grid layouts.", table_cell_style)],
        [Paragraph("API Framework", table_cell_bold), Paragraph("Python 3.11 / FastAPI v0.111", table_cell_style), Paragraph("Asynchronous backend router with automated OpenAPI specs.", table_cell_style)],
        [Paragraph("Validation Layer", table_cell_bold), Paragraph("Pydantic v2.7", table_cell_style), Paragraph("Strict request/response validation schemas.", table_cell_style)],
        [Paragraph("Core Downloader", table_cell_bold), Paragraph("yt-dlp (Stable release)", table_cell_style), Paragraph("Handles YouTube metadata extraction and stream fetches.", table_cell_style)],
        [Paragraph("Media Transcoder", table_cell_bold), Paragraph("FFmpeg (v7.x+ build)", table_cell_style), Paragraph("Audio stream extraction and video stream stitching.", table_cell_style)],
        [Paragraph("Rate Limiter", table_cell_bold), Paragraph("SlowAPI v0.1.9 (Token Bucket)", table_cell_style), Paragraph("Prevents API abuse by limiting downloads and queries per IP.", table_cell_style)],
    ]
    tech_table = Table(tech_data, colWidths=[110, 160, 222])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")), # Slate-900 Header
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#f8fafc"), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0,0), (-1,-1), 7),
    ]))
    story.append(tech_table)
    story.append(PageBreak())

    # ==========================================
    # SECTION 3: DETAILED FRONTEND & BACKEND SPECS
    # ==========================================
    story.append(make_block_heading("3. Module and Component Breakdown", h1_text_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("3.1 Frontend Component Design", h2_style))
    story.append(Paragraph(
        "The frontend is designed as a single-page responsive client application located in the <code>/frontend</code> directory. "
        "It includes a modern dashboard utilizing a customized dark mode scheme with interactive states. "
        "The critical user interaction flow runs as follows:", body_style))
    story.append(Paragraph("1. <b>URL Extraction:</b> The user enters or pastes a YouTube URL. An event listener parses the string and extracts the 11-character video ID.", bullet_style))
    story.append(Paragraph("2. <b>Metadata Fetching:</b> The client issues a <code>POST /api/fetch-info</code>. Upon success, the UI transitions to display the video thumbnail, duration, and dynamically unlocks format select chips.", bullet_style))
    story.append(Paragraph("3. <b>Dynamic Formats:</b> For video (MP4), the frontend reads the <code>available_formats</code> array returned from the backend, dynamically hiding resolutions the original uploader did not provide. For audio (MP3), options are constrained to 70k, 128k, 160k, and 320k.", bullet_style))
    story.append(Paragraph("4. <b>Download Execution:</b> Upon selecting the quality chip, a stream fetch triggers. The frontend tracks progress stages (Connecting, Extracting, Processing, Finalizing) using a simulated progression bar before offering the final blob directly in the browser's download queue.", bullet_style))

    story.append(Paragraph("3.2 Backend Code Architecture", h2_style))
    story.append(Paragraph(
        "The backend is structured under <code>/backend/app</code> and follows standard FastAPI controller-model design patterns:", body_style))
    story.append(Paragraph("• <b><code>downloader.py</code>:</b> Contains the core wrapper around <code>yt-dlp</code> and <code>FFmpeg</code>. It maps user-selected MP3 quality levels to target bitrates (CBR) and stitches best-resolution video and audio tracks for MP4 containers.", bullet_style))
    story.append(Paragraph("• <b><code>routes.py</code>:</b> Declares HTTP controllers. Handles CORS configuration to allow cross-origin requests, intercepts validation errors, and attaches headers (e.g. <code>Content-Disposition</code>, <code>X-Lumio-Quality</code>).", bullet_style))
    story.append(Paragraph("• <b><code>schemas.py</code>:</b> Handles input sanitation. Implements regular expression checkers for standard YouTube links, live feeds, embeds, and Shorts, blocking malicious inputs.", bullet_style))
    story.append(Paragraph("• <b><code>cleanup.py</code>:</b> Temporary file sweeper. Background worker task that checks the local download directory (<code>/tmp/lumio_downloads</code>) every 5 minutes and purges any temporary files older than 5 minutes to prevent disk exhaustion.", bullet_style))
    story.append(Spacer(1, 15))

    # ==========================================
    # SECTION 4: AWS CLOUD DEPLOYMENT
    # ==========================================
    story.append(make_block_heading("4. AWS Production Deployment Architecture", h1_text_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "For a secure, scalable, and highly available production environment, we deploy the application "
        "on <b>AWS ECS Fargate</b>. This eliminates virtual machine management (EC2) and scales based on traffic.", body_style))
    
    story.append(Paragraph("Architecture Infrastructure Components:", h2_style))
    story.append(Paragraph("• <b>AWS VPC:</b> Multi-AZ layout with 2 Public subnets (housing the ALB) and 2 Private subnets (housing the ECS Fargate tasks) across 2 Availability Zones. NAT Gateways are deployed in public subnets to provide internet access to Fargate tasks for pulling YouTube content.", bullet_style))
    story.append(Paragraph("• <b>AWS Route 53 & ACM:</b> Route 53 hosts the domain DNS. AWS Certificate Manager (ACM) provisions a free SSL certificate to serve traffic over HTTPS (port 443).", bullet_style))
    story.append(Paragraph("• <b>AWS Application Load Balancer (ALB):</b> Terminates SSL and forwards HTTP requests on port 80 to target Fargate tasks in the private subnets. Path-based routing rules route traffic to `/api/*` (backend) and default `/` (frontend static assets).", bullet_style))
    story.append(Paragraph("• <b>AWS ECS Fargate:</b> Launches Docker containers in private subnets. Auto-scaling rules scale Fargate tasks dynamically when CPU exceeds 70% or target request count is high.", bullet_style))
    story.append(Paragraph("• <b>AWS ECR:</b> Private repository to store built Docker images for automated CI/CD deployments.", bullet_style))
    story.append(PageBreak())

    # ==========================================
    # SECTION 5: COST BREAKDOWN
    # ==========================================
    story.append(make_block_heading("5. AWS Monthly Cost Breakout Estimates", h1_text_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Below is a cost estimate based on standard AWS pricing in the US-East region, assuming a modest user base "
        "downloading approximately 10 TB of content per month.", body_style))
    
    cost_data = [
        [Paragraph("AWS Service", table_header_style), Paragraph("Configuration Details", table_header_style), Paragraph("Estimated Monthly Cost", table_header_style)],
        [Paragraph("ECS Fargate", table_cell_bold), Paragraph("2 Tasks active (0.5 vCPU, 1 GB RAM each) for redundancy", table_cell_style), Paragraph("$18.40", table_cell_style)],
        [Paragraph("Application Load Balancer", table_cell_bold), Paragraph("1 ALB serving traffic across 2 AZs", table_cell_style), Paragraph("$22.50", table_cell_style)],
        [Paragraph("NAT Gateway", table_cell_bold), Paragraph("1 NAT Gateway in Public Subnet (required for egress)", table_cell_style), Paragraph("$32.40 + processing fees", table_cell_style)],
        [Paragraph("Data Transfer Out (Internet)", table_cell_bold), Paragraph("~10 TB of video/audio downloads sent to users ($0.08 per GB)", table_cell_style), Paragraph("$800.00", table_cell_style)],
        [Paragraph("Route 53 & ACM", table_cell_bold), Paragraph("Hosted zone fee. SSL Certificate is free", table_cell_style), Paragraph("$0.50", table_cell_style)],
        [Paragraph("Elastic Container Registry", table_cell_bold), Paragraph("Storing 5 active image revisions (~5 GB)", table_cell_style), Paragraph("$0.50", table_cell_style)],
        [Paragraph("Total Estimated Cost", table_header_style), Paragraph("Optimized Production Standard", table_header_style), Paragraph("$874.30 / month", table_header_style)],
    ]
    cost_table = Table(cost_data, colWidths=[140, 212, 140])
    cost_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")), # Slate-900 Header
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#0f172a")), # Footer Row
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.HexColor("#f8fafc"), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0,0), (-1,-1), 7),
    ]))
    story.append(cost_table)
    story.append(Spacer(1, 10))
    story.append(Paragraph("<i>Note: Data Transfer Out is the dominant cost driver due to the bandwidth-heavy nature of downloading high-definition video. Bandwidth optimization (like preventing repeat identical downloads or restricting maximum file size) can significantly lower this cost.</i>", body_style))
    story.append(Spacer(1, 15))

    # ==========================================
    # SECTION 6: CHALLENGES & SOLUTIONS
    # ==========================================
    story.append(make_block_heading("6. Operational Challenges, Problems, & Solutions", h1_text_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Challenge 1: YouTube Rate Limiting / Bot Detection", h2_style))
    story.append(Paragraph(
        "YouTube regularly monitors request patterns and flags datacenter IP ranges (e.g. AWS Fargate), causing downloads to fail with a bot verification challenge. "
        "<b>Solution:</b> The backend implements native proxy routing via the <code>PROXY_URL</code> config setting. "
        "In production, all outbound <code>yt-dlp</code> requests are routed through a rotating residential proxy pool. "
        "This masks the AWS datacenter IPs under standard home broadband IPs, permanently preventing blocks and ensuring 100% uptime. "
        "Additionally, <code>COOKIES_FILE</code> configuration is supported to load browser session identifiers when needed.", body_style))

    story.append(Paragraph("Challenge 2: Disk Exhaustion / Ephemeral Storage Limits", h2_style))
    story.append(Paragraph(
        "Downloading multiple 4K videos simultaneously occupies significant temporary disk space. Fargate containers have "
        "20 GB of standard ephemeral storage. "
        "<b>Solution:</b> Lumio runs a persistent background cleanup worker (<code>cleanup.py</code>) that constantly purges temporary media "
        "files from `/tmp/lumio_downloads` once they are successfully streamed to the user or if they exceed 5 minutes in age. "
        "FastAPI is configured to stream files via chunked responses directly, preventing full file caching in container memory.", body_style))

    story.append(Paragraph("Challenge 3: High Latency during Transcoding", h2_style))
    story.append(Paragraph(
        "Converting high-definition video formats and merging separate video/audio tracks requires extensive FFmpeg transcoding, "
        "which can cause timeout failures. "
        "<b>Solution:</b> Backend task timeouts are increased to 10 minutes (<code>DOWNLOAD_TIMEOUT_SECONDS = 600</code>). "
        "The frontend implements an active loading state. Fargate tasks are configured with a minimum of 0.5 vCPU to ensure transcoding completes in under 45 seconds.", body_style))

    # Build the document
    doc.build(story, canvasmaker=NumberedCanvas)
    print("PDF generation completed successfully.")

if __name__ == "__main__":
    build_pdf()
