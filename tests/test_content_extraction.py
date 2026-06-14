from __future__ import annotations

from geo_seo_engine.crawler import extract_main_content


def test_extract_main_content_prefers_main_landmark():
    content = extract_main_content(
        """
        <html>
          <body>
            <header>Site navigation</header>
            <main id="content">
              <h1>Useful guide</h1>
              <p>This page explains practical SEO and GEO research steps.</p>
            </main>
            <footer>Legal links</footer>
          </body>
        </html>
        """
    )

    assert content.selector == "main#content"
    assert content.text == "Useful guide This page explains practical SEO and GEO research steps."
    assert content.text_length == len(content.text)
    assert content.word_count == 11


def test_extract_main_content_uses_largest_article_candidate():
    content = extract_main_content(
        """
        <article>Short teaser</article>
        <article class="post">
          <h1>Detailed post</h1>
          <p>Original content with enough context to be the primary candidate.</p>
        </article>
        """
    )

    assert content.selector == "article.post"
    assert content.text == "Detailed post Original content with enough context to be the primary candidate."


def test_extract_main_content_falls_back_to_body_without_chrome():
    content = extract_main_content(
        """
        <body>
          <nav>Products Pricing Login</nav>
          <section>Core body content remains available for extraction.</section>
          <script>window.noisy = true;</script>
        </body>
        """
    )

    assert content.selector == "body"
    assert content.text == "Core body content remains available for extraction."


def test_extract_main_content_ignores_hidden_content():
    content = extract_main_content(
        """
        <main>
          <p>Visible primary copy.</p>
          <p hidden>Hidden copy.</p>
          <p aria-hidden="true">Decorative copy.</p>
        </main>
        """
    )

    assert content.text == "Visible primary copy."
