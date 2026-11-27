"""PDF links on the native chapter Markdown path."""
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from monograph import Book
from audit import _Attributes, run as audit_page


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.anchors = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.anchors.append(dict(attrs))


class ChapterDownloads(unittest.TestCase):
    def test_no_script_paper_overview_and_external_link_policy(self):
        site = 'https://example.org/book'
        book = Book.__new__(Book)
        book.L, book.parts, book.b = {}, [], SimpleNamespace(page={'site': site})
        toc = book.contents([('programme-overview', 'Overview'), ('glossary', 'Glossary')])
        self.assertIn('<a href="#programme-overview">Overview</a>', toc)
        self.assertIn(f'<noscript><a class="mg-print-overview" href="{site}#programme-overview">Overview</a></noscript>', toc)
        self.assertIn('<a href="#glossary">Glossary</a>', toc)
        parser = _Attributes('Author', 'https://example.org/', site)
        parser.feed(toc)
        self.assertEqual(parser.outside_references, [])
        parser.feed(f'<a class="mg-print-overview" href="{site}#other">Other</a>'
                    f'<a href="{site}#programme-overview">Unmarked</a>'
                    '<a class="mg-print-overview" href="https://outside.example/">Outside</a>'
                    '<a href="https://example.org/">Author</a><a href="https://example.org/">Other</a>')
        self.assertEqual([url for url in parser.outside_references if url],
                         [site + '#other', site + '#programme-overview', 'https://outside.example/', 'https://example.org/'])

    def test_native_files_and_ordinary_citations(self):
        book = Book.__new__(Book)
        book.current = "ch14"
        book.refdefs = {}
        book.chapter_files = {}
        book.pending_refs = []
        book.local_links = []
        book.tags = {}
        book.problems = []
        parser = Links()
        files = ("celestial-current-product.pdf", "celestial-residue.pdf", "interacting-theories.pdf", "critical-points-and-sphere-insertions.pdf")
        for name in files:
            parser.feed(book.inline(f"[Download *the paper* (PDF)]({name})"))
        for name in ("unpublished.pdf", "../celestial-residue.pdf",
                     "https://example.org/celestial-residue.pdf"):
            self.assertEqual(book.inline(f"[Source]({name})"), "Source")
        self.assertEqual([a["href"] for a in parser.anchors], list(files))
        self.assertTrue(all(a.get("type") == "application/pdf" and "download" in a
                            for a in parser.anchors))
        self.assertEqual(book.pending_refs, [])

    def test_versioned_primary_page_links_keep_printed_locators(self):
        book = Book.__new__(Book)
        book.current, book.refdefs, book.chapter_files, book.tags = "ch19", {}, {}, {}
        book.pending_refs, book.local_links, book.problems = [], [], []
        root = "https://arxiv.org/pdf/2412.17168v2#page="
        audit = _Attributes()
        for page, label in [(19, "Graph grading (2.19)–(2.21)"), (62, "Two-field coefficients, Appendix B.6.2")]:
            url = root + str(page)
            markup = book.inline(f"[{label}]({url})")
            links = Links()
            links.feed(markup)
            self.assertEqual(links.anchors, [{"class": "mg-primary-page", "href": url}])
            self.assertIn(f"{label} (arXiv:2412.17168v2, PDF p. {page})</a>", markup)
            audit.feed(markup)
        self.assertEqual(audit.outside_references, [])
        later = root + "52"
        self.assertIn(f'href="{later}">Appendix B.12 (arXiv:2412.17168v2, PDF p. 52)</a>',
                      book.inline(f"[Appendix B.12]({later})"))
        other = root + "0"
        audit.feed(f'<a class="mg-primary-page" href="{other}">Other page</a>'
                   f'<img class="mg-primary-page" src="{root}19"><a href="{root}62">Unmarked</a>')
        self.assertEqual(audit.outside_references, [other, root + "19", root + "62"])

    def test_introduction_primary_page_citations(self):
        book = Book.__new__(Book)
        book.current, book.refdefs, book.chapter_files, book.tags = "expanded-introduction", {}, {}, {}
        book.pending_refs, book.local_links, book.problems = [], [], []
        audit = _Attributes()
        pages = [
            ("1605.00138", 30, "The affine reduction, §§5.2–5.3"),
            ("1605.00138", 32, "The slice, its jets and the filtered reduction, Theorems 5.7–5.8"),
            ("1605.00138", 38, "Injectivity of the Miura map, Theorem 5.17"),
            ("1605.00138", 39, "The trace-free ordered product, Corollary 5.20"),
            ("math-ph/0312042", 10, "Derivation from the Jacobi identity, Example 3.13"),
            ("1608.06255", 4, "The regular presentation and its basis, equations (3.3)–(3.5)"),
        ]
        for paper, page, label in pages:
            with self.subTest(paper=paper, page=page):
                url = f"https://arxiv.org/pdf/{paper}#page={page}"
                markup = book.inline(f"[{label}]({url})")
                links = Links()
                links.feed(markup)
                self.assertEqual(links.anchors, [{"class": "mg-primary-page", "href": url}])
                self.assertIn(f"{label} (arXiv:{paper}, PDF p. {page})</a>", markup)
                audit.feed(markup)
        self.assertEqual(audit.outside_references, [])

    def test_authored_physical_page_navigation_and_non_page_controls(self):
        book = Book.__new__(Book)
        book.current, book.refdefs, book.chapter_files, book.tags = "ch13", {}, {}, {}
        book.pending_refs, book.local_links, book.problems = [], [], []
        audit = _Attributes()
        for url in ("https://www.samraskin.net/chiralcats.pdf#page=41",
                    "https://inspirehep.net/files/65769bae9f165431f3ebb5863f596224#page=45",
                    "http://library.example/reading?series=2&year=2025#page=57"):
            with self.subTest(url=url):
                page = url.rsplit("=", 1)[1]
                label = f"The argument, PDF p. {page}"
                markup = book.inline(f"[{label}]({url})")
                parser = Links()
                parser.feed(markup)
                self.assertEqual(parser.anchors, [{"class": "mg-primary-page", "href": url}])
                self.assertEqual(markup.count("PDF p."), 1)
                audit.feed(markup)
        self.assertEqual(audit.outside_references, [])
        for fragment in ("", "#section1", "#page=0", "#page=-1", "#page=3more", "#page=3&zoom=150"):
            parser = Links()
            parser.feed(book.inline(f"[Ordinary source](https://library.example/paper.pdf{fragment})"))
            self.assertEqual(parser.anchors, [], fragment)

    def test_full_audit_distinguishes_a_publisher_file_id_from_reader_text(self):
        build = SimpleNamespace(problems=[], warnings=[], content={}, book=None,
                                all_statements=lambda content: [], page=dict(author="", home="", site=""),
                                math=SimpleNamespace(jobs=[], errors=[]),
                                term_links=SimpleNamespace(entries=[], used=set()))
        token = "65769bae9f165431f3ebb5863f596224"
        root = "https://inspirehep.net/files/"
        def check(link, label="Costello and Paquette, JHEP (7.23) (PDF p. 45)"):
            markup = f'<html><head></head><body><a class="mg-primary-page" href="{link}">{label}</a></body></html>'
            return audit_page(build, markup)["failures"]
        self.assertEqual(check(root + token + "#page=45"), [])
        self.assertEqual(check(root + token + ".pdf#page=45"), [])
        for link in [root + token + "/paper#page=45", root + "paper?id=" + token + "#page=45",
                     root + token + "#other"]:
            self.assertTrue(any("hash (in href)" in message for message in check(link)), link)
        self.assertTrue(any("hash:" in message for message in check(root + token + "#page=45", token)))


if __name__ == "__main__":
    unittest.main()
