from pathlib import Path
from bs4 import BeautifulSoup
from html import unescape
import re
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

SPEECHES = [
    ("brad-wilcox.html", "Brad Wilcox", "His Grace Is Sufficient", "https://speeches.byu.edu/talks/brad-wilcox/his-grace-is-sufficient/"),
    ("jeffrey-r-holland.html", "Jeffrey R. Holland", "Cast Not Away Therefore Your Confidence", "https://speeches.byu.edu/talks/jeffrey-r-holland/cast-not-away-therefore-your-confidence/"),
    ("dallin-h-oaks.html", "Dallin H. Oaks", "Coming Closer to Jesus Christ", "https://speeches.byu.edu/talks/dallin-h-oaks/coming-closer-to-jesus-christ/"),
    ("patrick-kearon.html", "Patrick Kearon", "Peace and Rest - Even Now", "https://speeches.byu.edu/talks/patrick-kearon/peace-and-rest-even-now/"),
    ("dallas-jenkins.html", "Dallas Jenkins", "Five Loaves and Two Fishes", "https://speeches.byu.edu/talks/dallas-jenkins/five-loaves-and-two-fishes/"),
]


def paragraphs_from_html(path):
    soup = BeautifulSoup(Path(path).read_text(encoding="utf-8", errors="replace"), "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "nav", "header", "footer"]):
        tag.decompose()
    result = []
    for p in soup.find_all("p"):
        text = " ".join(p.get_text(" ", strip=True).split())
        text = unescape(text)
        if len(text) >= 60 and re.search(r"promis|miracl", text, re.I):
            result.append(text)
    return result


def main():
    all_quotes = []
    for filename, speaker, title, url in SPEECHES:
        quotes = paragraphs_from_html(Path(__file__).parent / filename)
        all_quotes.append((speaker, title, url, quotes))
        print(f"{speaker}: {len(quotes)} quotes")

    out = Path(__file__).parent / "promises-and-miracles.pdf"
    styles = getSampleStyleSheet()
    heading = ParagraphStyle("Heading", parent=styles["Heading1"], alignment=TA_CENTER, spaceAfter=8)
    subheading = ParagraphStyle("Subheading", parent=styles["Heading2"], spaceAfter=4)
    body = ParagraphStyle("Quote", parent=styles["BodyText"], leading=14, spaceAfter=10)
    doc = SimpleDocTemplate(str(out), pagesize=LETTER, rightMargin=.7*inch, leftMargin=.7*inch, topMargin=.65*inch, bottomMargin=.65*inch)
    story = []
    for i, (speaker, title, url, quotes) in enumerate(all_quotes):
        story.append(Paragraph(speaker, heading))
        story.append(Paragraph(title, subheading))
        story.append(Paragraph(url, body))
        story.append(Spacer(1, 8))
        for q in quotes:
            story.append(Paragraph(q.replace("&", "&amp;"), body))
        if i < len(all_quotes) - 1:
            story.append(PageBreak())
    doc.build(story)
    print(f"Created {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
