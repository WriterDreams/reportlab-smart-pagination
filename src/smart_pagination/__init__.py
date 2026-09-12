"""
ReportLab Smart Pagination
~~~~~~~~~~~~~~~~~~~~~~~~~~

Height-aware heading protection for ReportLab PDF generation.
Prevents orphaned headings and overflow cascades that ReportLab's
built-in keepWithNext cannot handle.

Created by Hamdy Elshamy for Writer's Dream AI (https://writersdream.ai)

Basic usage::

    from smart_pagination import paginate
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    styles = getSampleStyleSheet()
    flowables = [
        Paragraph("Chapter 1", styles['Heading1']),
        Paragraph("Body text here...", styles['Normal']),
    ]

    doc = SimpleDocTemplate("output.pdf")
    story = paginate(flowables, frame_height=720, frame_width=468)
    doc.build(story)
"""

from .paginator import paginate, SmartPaginator

__version__ = "1.0.2"
__author__ = "Hamdy Elshamy"
__all__ = ["paginate", "SmartPaginator"]
