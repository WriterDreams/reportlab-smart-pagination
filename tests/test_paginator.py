"""Tests for the smart pagination engine."""

import unittest
from reportlab.platypus import Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from smart_pagination import paginate, SmartPaginator


styles = getSampleStyleSheet()

# A heading style with keepWithNext
heading_style = ParagraphStyle(
    'TestHeading',
    parent=styles['Heading1'],
    keepWithNext=True,
    fontSize=14,
    leading=18,
)

body_style = styles['Normal']


def _make_body(text="Sample paragraph text. " * 10):
    return Paragraph(text, body_style)


def _make_heading(text="Test Heading"):
    return Paragraph(text, heading_style)


class TestBasicPagination(unittest.TestCase):
    """Test that basic pagination works without errors."""

    def test_empty_input(self):
        result = paginate([], frame_height=720, frame_width=468)
        self.assertEqual(result, [])

    def test_single_paragraph(self):
        flowables = [_make_body()]
        result = paginate(flowables, frame_height=720, frame_width=468)
        # Should contain the paragraph, no page break needed
        self.assertTrue(len(result) >= 1)
        self.assertNotIsInstance(result[-1], PageBreak)

    def test_content_fits_single_page(self):
        flowables = [
            _make_heading("Chapter 1"),
            _make_body("Short text."),
        ]
        result = paginate(flowables, frame_height=720, frame_width=468)
        # No page breaks needed if everything fits
        page_breaks = [f for f in result if isinstance(f, PageBreak)]
        self.assertEqual(len(page_breaks), 0)


class TestHeadingProtection(unittest.TestCase):
    """Test that headings are carried to the next page when orphaned."""

    def test_orphaned_heading_is_carried(self):
        # Fill a page almost completely, then add a heading + body
        flowables = []
        # Add enough body text to nearly fill a page
        for _ in range(20):
            flowables.append(_make_body())
        # Add a heading at the bottom — should be carried
        flowables.append(_make_heading("Should Be Carried"))
        flowables.append(_make_body("This follows the heading."))

        result = paginate(flowables, frame_height=400, frame_width=468)

        # There should be at least one page break
        page_breaks = [i for i, f in enumerate(result) if isinstance(f, PageBreak)]
        self.assertTrue(len(page_breaks) >= 1)

    def test_carry_aborted_if_too_large(self):
        # If the heading + content is more than 50% of page, don't carry
        paginator = SmartPaginator(
            frame_height=200,
            frame_width=468,
            carry_max=0.5,
        )
        flowables = [
            _make_body("Short."),
            _make_heading("Big Heading"),
            # This alone nearly fills a page
            _make_body("Very long content. " * 50),
        ]
        # Should not crash
        result = paginator.paginate(flowables)
        self.assertTrue(len(result) >= 1)


class TestParagraphSplitting(unittest.TestCase):
    """Test that large paragraphs are split across pages."""

    def test_large_paragraph_splits(self):
        flowables = [
            _make_body("First page content."),
            _make_body("Very long paragraph that should split. " * 100),
        ]
        result = paginate(
            flowables, frame_height=300, frame_width=468, split_enabled=True
        )
        page_breaks = [f for f in result if isinstance(f, PageBreak)]
        self.assertTrue(len(page_breaks) >= 1)

    def test_splitting_disabled(self):
        flowables = [
            _make_body("First page."),
            _make_body("Long text. " * 100),
        ]
        # With splitting disabled, should still paginate without error
        result = paginate(
            flowables, frame_height=300, frame_width=468, split_enabled=False
        )
        self.assertTrue(len(result) >= 1)


class TestSmartPaginatorConfig(unittest.TestCase):
    """Test that configuration parameters are respected."""

    def test_custom_thresholds(self):
        paginator = SmartPaginator(
            frame_height=720,
            frame_width=468,
            carry_max=0.3,
            min_page_fill=0.25,
            search_depth=5,
        )
        self.assertEqual(paginator.carry_max, 0.3)
        self.assertEqual(paginator.min_page_fill, 0.25)
        self.assertEqual(paginator.search_depth, 5)

    def test_convenience_function_kwargs(self):
        # paginate() should pass kwargs to SmartPaginator
        result = paginate(
            [_make_body()],
            frame_height=720,
            frame_width=468,
            carry_max=0.6,
            min_page_fill=0.1,
        )
        self.assertTrue(len(result) >= 1)


if __name__ == '__main__':
    unittest.main()
