"""
Smart Pagination Engine
~~~~~~~~~~~~~~~~~~~~~~~

Replaces ReportLab's rigid keepWithNext with height-aware heading
protection that prevents orphaned headings, overflow cascades, and
empty pages.

The core insight: instead of blindly forcing headings to stay with
their content (which causes silent overflow when content is too tall),
measure heights and only carry headings forward when it's safe.

Two threshold checks prevent the most common failures:

1. Don't carry more than 50% of a page — prevents overflow on next page
2. Don't leave a page less than 15% filled — prevents ugly empty pages

Created by Hamdy El-Shamha for Writer's Dream AI.
"""

from reportlab.platypus import (
    PageBreak,
    Spacer,
    Flowable,
)


def _measure_flowable(flowable, frame_width):
    """Measure the height a flowable will occupy at the given width."""
    if isinstance(flowable, Spacer):
        return flowable.height if hasattr(flowable, 'height') else flowable._height
    if isinstance(flowable, PageBreak):
        return 0
    try:
        w, h = flowable.wrap(frame_width, 999999)
        return h
    except Exception:
        return 0


class SmartPaginator:
    """
    Height-aware paginator that protects headings from being orphaned
    at the bottom of pages without causing overflow cascades.

    Parameters
    ----------
    frame_height : float
        The usable height of each page frame in points.
    frame_width : float
        The usable width of each page frame in points.
    carry_max : float, optional
        Maximum fraction of page height that can be carried to the next
        page (default 0.5). Increase for layouts with very large headings.
    min_page_fill : float, optional
        Minimum fraction of page that must remain filled after carrying
        a heading (default 0.15). Decrease if you prefer heading protection
        over page fill.
    search_depth : int, optional
        How many items to search backward for an orphaned heading
        (default 10).
    safety_margin : float, optional
        Extra points reserved to prevent tight-fit overflow (default 10).
    split_enabled : bool, optional
        Whether to split large paragraphs across pages instead of
        leaving blank gaps (default True).
    split_min_space : float, optional
        Minimum fraction of page that must be available before attempting
        a paragraph split (default 0.15).

    Example
    -------
    >>> from smart_pagination import SmartPaginator
    >>> paginator = SmartPaginator(frame_height=720, frame_width=468)
    >>> story = paginator.paginate(flowables)
    """

    def __init__(
        self,
        frame_height,
        frame_width,
        carry_max=0.5,
        min_page_fill=0.15,
        search_depth=10,
        safety_margin=10,
        split_enabled=True,
        split_min_space=0.15,
    ):
        self.frame_height = frame_height
        self.frame_width = frame_width
        self.carry_max = carry_max
        self.min_page_fill = min_page_fill
        self.search_depth = search_depth
        self.safety_margin = safety_margin
        self.split_enabled = split_enabled
        self.split_min_space = split_min_space

    def paginate(self, flowables):
        """
        Process a list of flowables and return a new list with intelligent
        page breaks inserted.

        Parameters
        ----------
        flowables : list[Flowable]
            ReportLab flowables to paginate.

        Returns
        -------
        list[Flowable]
            New list with PageBreak flowables inserted at optimal positions.
        """
        story_out = []
        page_body = []
        page_body_h = 0.0

        def flush_page(force_break=True):
            nonlocal page_body, page_body_h
            if not page_body:
                return
            story_out.extend(page_body)
            if force_break:
                story_out.append(PageBreak())
            page_body = []
            page_body_h = 0.0

        for flowable in flowables:
            # Skip existing page breaks — we manage breaks ourselves
            if isinstance(flowable, PageBreak):
                flush_page()
                continue

            f_h = _measure_flowable(flowable, self.frame_width)

            # Check if adding this flowable would overflow the page
            if page_body_h + f_h + self.safety_margin > self.frame_height and page_body:
                carried = self._find_carry(page_body, page_body_h)

                if carried:
                    # Remove carried items from current page
                    carried_h = sum(
                        _measure_flowable(f, self.frame_width) for f in carried
                    )
                    page_body = page_body[: len(page_body) - len(carried)]
                    page_body_h -= carried_h
                else:
                    carried = []

                # Try splitting large paragraphs across pages
                if not carried and self.split_enabled:
                    split_result = self._try_split(
                        flowable, f_h, page_body_h
                    )
                    if split_result:
                        first_part, second_part = split_result
                        page_body.append(first_part)
                        page_body_h += _measure_flowable(
                            first_part, self.frame_width
                        )
                        flush_page()
                        # Continue with second part
                        flowable = second_part
                        f_h = _measure_flowable(flowable, self.frame_width)
                        page_body.append(flowable)
                        page_body_h += f_h
                        continue

                flush_page()

                # Re-add carried heading to the new page
                for cf in carried:
                    page_body.append(cf)
                    page_body_h += _measure_flowable(cf, self.frame_width)

            page_body.append(flowable)
            page_body_h += f_h

        # Flush the final page without a trailing PageBreak
        flush_page(force_break=False)

        return story_out

    def _find_carry(self, page_body, page_body_h):
        """
        Search backward through the current page for an orphaned heading
        (one with keepWithNext=True) and determine if it's safe to carry
        it to the next page.

        Returns the list of flowables to carry, or empty list if unsafe.
        """
        search_limit = min(len(page_body), self.search_depth)
        kwn_pos = None

        # Search backward for a keepWithNext heading
        for i in range(1, search_limit + 1):
            item = page_body[-i]
            if hasattr(item, 'style') and getattr(
                item.style, 'keepWithNext', False
            ):
                kwn_pos = len(page_body) - i
                break

        if kwn_pos is None:
            return []

        # Also grab the spacer before the heading (visual spacing)
        if kwn_pos > 0 and isinstance(page_body[kwn_pos - 1], Spacer):
            kwn_pos -= 1

        carried = page_body[kwn_pos:]
        carried_h = sum(
            _measure_flowable(f, self.frame_width) for f in carried
        )
        remaining_h = page_body_h - carried_h

        # SAFETY CHECK 1: Don't leave a nearly-empty page
        if remaining_h < self.frame_height * self.min_page_fill:
            return []

        # SAFETY CHECK 2: Don't carry more than allowed fraction
        if carried_h > self.frame_height * self.carry_max:
            return []

        return carried

    def _try_split(self, flowable, f_h, page_body_h):
        """
        Try to split a large flowable across pages to avoid blank gaps.

        Returns (first_part, second_part) tuple, or None if split failed.
        """
        avail = (
            self.frame_height
            - page_body_h
            - self.safety_margin
        )

        if avail <= self.frame_height * self.split_min_space:
            return None

        if not hasattr(flowable, 'split'):
            return None

        parts = flowable.split(self.frame_width, avail)
        if parts and len(parts) == 2:
            return (parts[0], parts[1])

        return None


def paginate(flowables, frame_height, frame_width, **kwargs):
    """
    Convenience function for one-shot pagination.

    Parameters
    ----------
    flowables : list[Flowable]
        ReportLab flowables to paginate.
    frame_height : float
        Usable page height in points.
    frame_width : float
        Usable page width in points.
    **kwargs
        Additional arguments passed to SmartPaginator.

    Returns
    -------
    list[Flowable]
        Paginated flowables with intelligent page breaks.

    Example
    -------
    >>> from smart_pagination import paginate
    >>> story = paginate(my_flowables, frame_height=720, frame_width=468)
    """
    p = SmartPaginator(frame_height, frame_width, **kwargs)
    return p.paginate(flowables)
