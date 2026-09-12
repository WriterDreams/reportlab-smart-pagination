# ReportLab Smart Pagination

**Height-aware heading protection for ReportLab PDF generation.**

Prevents orphaned headings, text overflow, and cascade failures that ReportLab's built-in `keepWithNext` cannot handle.

Created by **Hamdy El-Shamha** — developed for [Writer's Dream AI](https://writersdream.ai), a book writing and publishing platform.

## The Problem

ReportLab's `keepWithNext=True` is a rigid boolean — it forces headings to stay with their content without checking whether they'll actually fit. This causes:

- **Text overlapping** when carried content exceeds the next page's height
- **Overflow cascades** when multiple headings chain together
- **Silent failures** — no errors, just broken PDFs

## The Solution

Smart Pagination replaces the rigid `keepWithNext` approach with **height-aware heading protection** using two percentage-based safety thresholds:

| | Built-in `keepWithNext` | Smart Pagination |
|---|---|---|
| Prevents orphaned headings | Yes | Yes |
| Prevents overflow | No | Yes — caps carry at 50% of page |
| Prevents empty pages | No | Yes — aborts if page < 15% filled |
| Handles chained headings | Breaks silently | Gracefully degrades |
| Splits large paragraphs | No | Yes — fills pages optimally |

## Installation

```bash
pip install reportlab-smart-pagination
```

## Quick Start

```python
from smart_pagination import paginate
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

styles = getSampleStyleSheet()

# Build your flowables as usual
flowables = [
    Paragraph("Chapter 1: The Beginning", styles['Heading1']),
    Paragraph("This is the first paragraph of content...", styles['Normal']),
    Paragraph("Chapter 2: The Middle", styles['Heading1']),
    Paragraph("More content follows here...", styles['Normal']),
]

# Calculate frame dimensions (letter page with 1-inch margins)
page_w, page_h = letter
frame_height = page_h - 2 * inch
frame_width = page_w - 2 * inch

# Paginate with heading protection
story = paginate(flowables, frame_height=frame_height, frame_width=frame_width)

# Build PDF
doc = SimpleDocTemplate("output.pdf", pagesize=letter)
doc.build(story)
```

## Advanced Usage

Use `SmartPaginator` for full control over thresholds:

```python
from smart_pagination import SmartPaginator

paginator = SmartPaginator(
    frame_height=720,
    frame_width=468,
    carry_max=0.5,        # Max 50% of page height can be carried
    min_page_fill=0.15,   # Page must be at least 15% filled after carry
    search_depth=10,       # Search last 10 items for orphaned headings
    split_enabled=True,    # Split large paragraphs across pages
)

story = paginator.paginate(flowables)
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `carry_max` | `0.5` | Maximum fraction of page height that can be carried to the next page. Increase for layouts with very large headings. |
| `min_page_fill` | `0.15` | Minimum fraction of page that must remain filled after carrying a heading. Decrease if you prefer heading protection over page aesthetics. |
| `search_depth` | `10` | How many flowables to search backward for an orphaned heading. |
| `split_enabled` | `True` | Whether to split large paragraphs across pages to avoid blank gaps. |
| `split_min_space` | `0.15` | Minimum available page fraction before attempting a paragraph split. |
| `safety_margin` | `10` | Extra points reserved to prevent tight-fit overflow. |

## How It Works

When a flowable would overflow the current page:

1. **Search backward** through the last few items for a heading with `keepWithNext=True`
2. **Measure the carried content** — heading + spacer + any items after it
3. **Safety check 1**: If carrying would leave the current page less than 15% filled, abort — an orphaned heading looks better than an empty page
4. **Safety check 2**: If the carried content exceeds 50% of the page height, abort — it would likely overflow the next page too
5. **If safe**, remove the heading from the current page, insert a page break, and place the heading at the top of the next page
6. **If not safe**, try splitting the overflowing paragraph across pages instead

## Origin

This algorithm was developed while building the PDF export engine for [Writer's Dream AI](https://writersdream.ai). Manuscripts with dozens of sub-headings and footnotes routinely triggered ReportLab's overflow bugs. The standard `keepWithNext` approach was the *cause* of the overlapping text, not the cure.

## License

MIT License — see [LICENSE](LICENSE) for details.
