"""Free Systems standard figure footer (canonical implementation).

Canonical source: ~/.claude/skills/fs-figure-footer/assets/fs_footer.py
Vendored into this repo so the figure scripts run standalone. If you change the
footer here, push the change back to the skill copy too.

The footer is one horizontal band at the bottom of the figure:

    Source: ...
    ------------------------------------------------------------------------------
    [logo lockup]                    Stanford GSB & Hoover · freesystems.substack.com

The source/credit line sits ABOVE the rule so it can never collide with the logo,
which owns the bottom-left corner.

Use `add_footer(fig)` after all axes are laid out, then reserve room for it with
`fig.subplots_adjust(bottom=FOOTER_BOTTOM)`.
"""
import os
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager

# --- brand assets ------------------------------------------------------------
# Named by the background they belong on, because the upstream ~/Logos filenames
# use "light"/"dark" inconsistently between the circle and lockup variants.
LOGOS = Path(os.environ.get("FS_LOGO_DIR", str(Path.home() / "Logos")))
LOCKUP_LIGHT_BG = LOGOS / "lockup-for-light-bg.png"   # dark ink
LOCKUP_DARK_BG = LOGOS / "lockup-for-dark-bg.png"     # white ink
LOCKUP_ASPECT = 3.598  # trimmed width/height; hard-coded so a missing file
                       # never silently changes the layout

AFFILIATION = "Stanford GSB & Hoover"
SUBSTACK = "freesystems.substack.com"

# Real typeface, in preference order. DejaVu Sans (matplotlib's default) is the
# single biggest reason a chart reads as amateurish — never leave it in place.
# Arial sits ahead of DejaVu because it is the best fallback that ships real
# separate weight files (see ensure_fonts).
FONT_STACK = ["Helvetica Neue", "Arial", "DejaVu Sans"]

# macOS ships Helvetica Neue as a .ttc *collection*. matplotlib registers only
# face 0 (Regular) from a collection, so every fontweight silently resolves to
# Regular — bold titles come out light and nothing warns you. We extract the
# individual faces once into a cache and register them properly.
_FONT_CACHE = Path(os.environ.get(
    "FS_FONT_CACHE", str(Path.home() / ".cache/fs-figures/fonts")))
_HELVETICA_TTC = Path("/System/Library/Fonts/HelveticaNeue.ttc")
_WANTED_FACES = {0: "Regular", 10: "Medium", 1: "Bold"}


def ensure_fonts():
    """Extract & register real Helvetica Neue weights. Idempotent; safe to call
    repeatedly. Returns True if the family is usable with real weights."""
    if any(f.name == "Helvetica Neue" and f.weight == 700
           for f in font_manager.fontManager.ttflist):
        return True
    if not _HELVETICA_TTC.exists():
        return False
    try:
        from fontTools.ttLib import TTCollection
    except ImportError:
        return False  # fall back to Arial, which has real weight files

    _FONT_CACHE.mkdir(parents=True, exist_ok=True)
    try:
        coll = None
        for idx, label in _WANTED_FACES.items():
            out = _FONT_CACHE / f"HelveticaNeue-{label}.ttf"
            if not out.exists():
                if coll is None:
                    coll = TTCollection(str(_HELVETICA_TTC))
                coll.fonts[idx].save(str(out))
            font_manager.fontManager.addfont(str(out))
    except Exception:
        return False
    return any(f.name == "Helvetica Neue" and f.weight == 700
               for f in font_manager.fontManager.ttflist)

# --- palette (Anthropic dataviz guidance, light surface) ----------------------
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASE = "#c3c2b7"
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
RECESSIVE = "#d6d5cf"

# Vertical budget the footer needs, as a fraction of figure height. Pass this to
# fig.subplots_adjust(bottom=FOOTER_BOTTOM) at minimum, or axis tick labels will
# overlap the source line.
FOOTER_BOTTOM = 0.185


def apply_style():
    """Set the standard rcParams for a Free Systems light-surface figure."""
    ensure_fonts()
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": FONT_STACK,
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "savefig.dpi": 220,
        "xtick.color": MUTED,
        "ytick.color": INK2,
        "text.color": INK,
    })


def _draw_tracked(fig, x_right, y, text, tracking=0.0024, **kw):
    """Draw letterspaced text, right-aligned at x_right. Returns its left edge.

    Matplotlib has no tracking property, and Helvetica Neue carries no thin-space
    glyph to fake it with (only U+0020 and NBSP), so tracking is done properly:
    each glyph is measured and placed with an added advance. Tracked caps are
    what make a short institutional line read as a mark rather than body copy.
    """
    widths = []
    for ch in text:
        probe = fig.text(0, -1, ch, **kw)   # measured offscreen, then discarded
        widths.append(_text_width(fig, probe))
        probe.remove()

    total = sum(widths) + tracking * (len(text) - 1)
    x = x_right - total
    for ch, w in zip(text, widths):
        fig.text(x, y, ch, ha="left", **kw)
        x += w + tracking
    return x_right - total


def _text_width(fig, artist):
    """Width of a drawn text artist as a fraction of figure width."""
    fig.canvas.draw()
    bb = artist.get_window_extent(fig.canvas.get_renderer())
    return bb.width / (fig.get_size_inches()[0] * fig.dpi)


def _draw_right_block(fig, right, baseline, ink, ink2, muted):
    """Right side of the footer: tracked institutional caps | hairline | URL.

    Laid out right-to-left from `right` using measured text widths, so the
    hairline divider always lands in the optical gap regardless of typeface
    metrics or figure width.
    """
    # The URL is the call to action — it gets the larger, darker treatment.
    url = fig.text(right, baseline, SUBSTACK, fontsize=10, color=ink,
                   ha="right", va="center", fontweight="medium")
    url_w = _text_width(fig, url)

    gap = 0.011
    div_x = right - url_w - gap
    # Hairline divider, set shorter than the cap height so it reads as a
    # separator rather than a border.
    fig.add_artist(plt.Line2D([div_x, div_x],
                              [baseline - 0.016, baseline + 0.016],
                              color=BASE, linewidth=0.9))

    # Affiliation as tracked caps: smaller and lighter than the URL, so the two
    # read as a hierarchy instead of one flat run of text.
    _draw_tracked(fig, div_x - gap, baseline, AFFILIATION.upper(),
                  fontsize=8.2, color=muted, va="center", fontweight="bold")


def add_footer(fig, source=None, dark=False, require_logo=True,
               logo_height=0.058, left=0.015, right=0.985, rule_y=0.088,
               baseline=0.044, source_y=0.108):
    """Draw the standard footer on `fig`.

    source : optional source/credit line printed below the rule.
    dark   : True to use the white-ink lockup for a dark surface.
    require_logo : default True — raise if the brand asset is missing, so a
        figure is never written with the fallback wordmark by accident. Set
        False only for throwaway/internal plots.
    logo_height : lockup height as a fraction of figure height. Width is derived
        from LOCKUP_ASPECT and the figure's own aspect so the logo never stretches.

    Returns True if the logo image was drawn, False if it fell back to a
    typographic wordmark (only reachable when require_logo=False).
    """
    lockup = LOCKUP_DARK_BG if dark else LOCKUP_LIGHT_BG
    if require_logo and not lockup.exists():
        raise FileNotFoundError(
            f"Free Systems lockup not found: {lockup}\n"
            "Expected it in ~/Logos (override with $FS_LOGO_DIR). See the "
            "fs-figure-footer skill; pass require_logo=False for a draft."
        )
    ink = "#fcfcfb" if dark else INK
    ink2 = "#c3c2b7" if dark else INK2
    muted = "#898781"

    fig.add_artist(plt.Line2D([left, right], [rule_y, rule_y], color=GRID,
                              linewidth=1))

    drew_logo = False
    if lockup.exists():
        # Convert the desired height fraction into a width fraction, correcting
        # for the figure's aspect ratio, so the axes box matches the image.
        fw, fh = fig.get_size_inches()
        width = logo_height * LOCKUP_ASPECT * (fh / fw)
        ax = fig.add_axes([left, baseline - logo_height / 2, width, logo_height])
        ax.imshow(plt.imread(lockup))
        ax.axis("off")
        ax.grid(False)
        drew_logo = True
    else:
        # Fallback wordmark so a figure still builds without the brand assets.
        fig.text(left, baseline - 0.004, "FREE", fontsize=13.5,
                 fontweight="bold", color=ink)
        fig.text(left + 0.0525, baseline - 0.004, "SYSTEMS", fontsize=13.5,
                 fontweight="bold", color=BLUE)

    _draw_right_block(fig, right, baseline, ink, ink2, muted)

    if source:
        fig.text(left, source_y, source, fontsize=8.5, color=muted, va="center")

    return drew_logo
