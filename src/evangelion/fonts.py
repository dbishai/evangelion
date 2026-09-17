"""Crimson Text font registration for the PDF body text, with a Times
fallback if the TTFs are somehow missing. Crimson Text is a Garamond-revival
book serif (SIL Open Font License; see fonts/OFL.txt), shipped as real
static Regular/Bold/Italic/BoldItalic instances -- deliberately chosen over
newer Google Fonts families (Lora included) that have moved to
variable-font-only releases, which reportlab cannot instance into a true
bold weight.
"""

import os

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

_FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

try:
    pdfmetrics.registerFont(
        TTFont("Crimson", os.path.join(_FONT_DIR, "CrimsonText-Regular.ttf"))
    )
    pdfmetrics.registerFont(
        TTFont("Crimson-Bold", os.path.join(_FONT_DIR, "CrimsonText-Bold.ttf"))
    )
    pdfmetrics.registerFont(
        TTFont("Crimson-Italic", os.path.join(_FONT_DIR, "CrimsonText-Italic.ttf"))
    )
    pdfmetrics.registerFont(
        TTFont(
            "Crimson-BoldItalic", os.path.join(_FONT_DIR, "CrimsonText-BoldItalic.ttf")
        )
    )
    pdfmetrics.registerFontFamily(
        "Crimson",
        normal="Crimson",
        bold="Crimson-Bold",
        italic="Crimson-Italic",
        boldItalic="Crimson-BoldItalic",
    )
    BODY_FONT, BODY_BOLD, BODY_ITALIC = "Crimson", "Crimson-Bold", "Crimson-Italic"
except Exception:
    BODY_FONT, BODY_BOLD, BODY_ITALIC = "Times-Roman", "Times-Bold", "Times-Italic"
