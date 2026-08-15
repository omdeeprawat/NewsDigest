import logging
from datetime import UTC, datetime, timedelta

import feedparser
import requests
import trafilatura
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class AnthropicArticle(BaseModel):
  title: str
  description: str
  url: str
  guid: str
  published_at: datetime
  category: str | None = None


class AnthropicScraper:
  def __init__(self):
    self.rss_urls = [
      "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml",
      "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_research.xml",
      "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_engineering.xml",
    ]

    self.session = requests.Session()
    self.session.headers.update(
      {
        "User-Agent": "Mozilla/5.0 (compatible; NewsDigestBot/1.0)"
      }
    )

  def get_articles(self, hours: int = 24) -> list[AnthropicArticle]:
    now = datetime.now(UTC)
    cutoff_time = now - timedelta(hours=hours)

    articles: list[AnthropicArticle] = []
    seen_guids = set()

    for rss_url in self.rss_urls:

      feed = feedparser.parse(rss_url)
      for entry in feed.entries:
        published_parsed = (
          getattr(entry, "published_parsed", None)
          or getattr(entry, "updated_parsed", None)
        )

        if not published_parsed:
          continue

        published_time = datetime(
          *published_parsed[:6],
          tzinfo=UTC,
        )

        if published_time < cutoff_time:
          continue

        guid = entry.get("id") or entry.get("link", "")

        if guid in seen_guids:
          continue

        seen_guids.add(guid)

        category = None
        if entry.get("tags"):
          category = entry.tags[0].get("term")

        articles.append(
          AnthropicArticle(
            title=entry.get("title", ""),
            description=entry.get("description", ""),
            url=entry.get("link", ""),
            guid=guid,
            published_at=published_time,
            category=category,
          )
        )

    articles.sort(key=lambda article: article.published_at, reverse=True)
    return articles

  def url_to_markdown(self, url: str) -> str | None:
    try:
      response = self.session.get(url, timeout=20)
      response.raise_for_status()

      markdown = trafilatura.extract(
        response.text,
        output_format="markdown",
        include_tables=True,
        include_comments=False,
        include_links=False,
      )

      return markdown

    except requests.RequestException:
      logger.exception("failed to fetch %s", url)
      return None

    except Exception:
      logger.exception("Failed to extract content from %s", url)
      return None


if __name__ == "__main__":
  scraper = AnthropicScraper()
  articles = scraper.get_articles(hours=60)

  print(f"\nFound {len(articles)} articles\n")

  for article in articles:
    print("=" * 80)
    print(article.title)
    print(article.published_at)
    print(article.url)
    print()

    markdown = scraper.url_to_markdown(article.url)

    if markdown:
      print(markdown[:1000])
    else:
      print("Could not extract article.")

    print()