from __future__ import annotations

from geo_seo_engine.content import extract_main_content_from_html, summarize_content_extraction
from geo_seo_engine.crawler import extract_main_content


def test_extract_main_content_from_html_prefers_main_landmark():
    content = extract_main_content_from_html(
        """
        <html>
          <head><title>Useful page</title></head>
          <body>
            <header>Site navigation</header>
            <main id="content">
              <h1>Useful guide</h1>
              <p>This page explains practical SEO and GEO research steps.</p>
            </main>
            <footer>Legal links</footer>
          </body>
        </html>
        """,
        "https://example.com/guide",
    )

    assert content.extraction_method == "main_element"
    assert content.main_selector == "main#content"
    assert content.title == "Useful page"
    assert content.plain_text == "Useful guide This page explains practical SEO and GEO research steps."
    assert content.word_count == 11
    assert content.character_count == len(content.plain_text)
    assert content.boilerplate_removed is True


def test_extract_main_content_from_html_uses_role_main():
    content = extract_main_content_from_html(
        """
        <div role="main">
          <h1>Role landmark</h1>
          <p>Primary content inside a role main landmark.</p>
        </div>
        """,
        "https://example.com/role",
    )

    assert content.extraction_method == "role_main"
    assert content.main_selector == "div[role='main']"
    assert "Primary content" in content.plain_text


def test_extract_main_content_from_html_uses_article_fallback():
    content = extract_main_content_from_html(
        """
        <article>Short teaser</article>
        <article class="post">
          <h1>Detailed post</h1>
          <p>Original content with enough context to be the primary candidate.</p>
        </article>
        """,
        "https://example.com/post",
    )

    assert content.extraction_method == "article_like"
    assert content.main_selector == "article.post"
    assert content.plain_text == "Detailed post Original content with enough context to be the primary candidate."


def test_extract_main_content_from_html_uses_heuristic_fallback():
    content = extract_main_content_from_html(
        """
        <body>
          <div class="sidebar">Products Pricing Login Search</div>
          <section id="content">
            <h2>Documentation</h2>
            <p>Core body content remains available for extraction.</p>
            <p>Additional detail helps identify this section as the page body.</p>
          </section>
        </body>
        """,
        "https://example.com/docs",
    )

    assert content.extraction_method == "scored_candidate"
    assert content.main_selector == "section#content"
    assert "Products Pricing Login" not in content.plain_text
    assert "Core body content" in content.plain_text


def test_extract_main_content_from_html_excludes_boilerplate_hidden_and_search():
    content = extract_main_content_from_html(
        """
        <body>
          <nav>Products Pricing Login</nav>
          <header>Header copy</header>
          <footer>Footer copy</footer>
          <aside class="sidebar">Sidebar copy</aside>
          <div class="cookie-banner">Cookie notice</div>
          <form role="search">Search box</form>
          <main>
            <p>Visible primary copy.</p>
            <p hidden>Hidden copy.</p>
            <p aria-hidden="true">Decorative copy.</p>
          </main>
        </body>
        """,
        "https://example.com/clean",
    )

    assert content.plain_text == "Visible primary copy."
    assert content.paragraph_count == 1


def test_extract_main_content_from_html_extracts_headings_text_links_images_and_metadata():
    content = extract_main_content_from_html(
        """
        <html>
          <head>
            <title>Content title</title>
            <meta name="description" content="Content description.">
            <link rel="canonical" href="/canonical">
          </head>
          <body>
            <main>
              <h1>Main heading</h1>
              <h2>Second heading</h2>
              <h3>Third heading</h3>
              <p>First paragraph with useful words.</p>
              <blockquote>Quoted supporting text.</blockquote>
              <a href="/internal">Internal link</a>
              <a href="https://other.example/page">External link</a>
              <img src="/image.jpg" alt="Descriptive image alt">
            </main>
          </body>
        </html>
        """,
        "https://example.com/page",
    )

    assert content.title == "Content title"
    assert content.meta_description == "Content description."
    assert content.canonical_url == "https://example.com/canonical"
    assert [(heading.level, heading.text, heading.order) for heading in content.headings] == [
        (1, "Main heading", 0),
        (2, "Second heading", 1),
        (3, "Third heading", 2),
    ]
    assert [(block.tag, block.text, block.order) for block in content.text_blocks] == [
        ("p", "First paragraph with useful words.", 0),
        ("blockquote", "Quoted supporting text.", 1),
    ]
    assert content.links[0].url == "https://example.com/internal"
    assert content.links[0].anchor_text == "Internal link"
    assert content.links[0].is_internal is True
    assert content.links[1].url == "https://other.example/page"
    assert content.links[1].is_internal is False
    assert content.image_alt_texts == ["Descriptive image alt"]
    assert content.heading_count == 3
    assert content.link_count == 2
    assert content.internal_link_count == 1
    assert content.external_link_count == 1


def test_extract_main_content_from_html_handles_empty_script_heavy_html():
    content = extract_main_content_from_html(
        """
        <html><head><script>window.app = true;</script></head><body><script>render()</script></body></html>
        """,
        "https://example.com/app",
    )

    assert content.extraction_method == "empty_html"
    assert content.main_selector is None
    assert content.plain_text == ""
    assert content.word_count == 0


def test_summarize_content_extraction_counts_pages_and_methods():
    first = extract_main_content_from_html("<main><p>Short page.</p></main>", "https://example.com/a")
    second = extract_main_content_from_html("<html><script>render()</script></html>", "https://example.com/b")

    result = summarize_content_extraction([first, second], start_url="https://example.com/")

    assert result.start_url == "https://example.com/"
    assert result.summary.total_pages == 2
    assert result.summary.pages_with_main_content == 1
    assert result.summary.pages_missing_main_content == 1
    assert result.summary.extraction_methods == {"main_element": 1, "empty_html": 1}
    assert result.summary.low_word_count_pages == ["https://example.com/a", "https://example.com/b"]


def test_crawler_main_content_summary_reuses_content_extractor():
    content = extract_main_content(
        """
        <body>
          <nav>Products Pricing Login</nav>
          <main><h1>Primary heading</h1><p>Useful page copy.</p></main>
        </body>
        """
    )

    assert content.selector == "main"
    assert content.text == "Primary heading Useful page copy."
    assert content.text_length == len(content.text)
    assert content.word_count == 5
