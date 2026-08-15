from datetime import UTC, datetime, timedelta

import feedparser
from pydantic import BaseModel


class OpenAIArticle(BaseModel):
  title: str
  description: str
  url: str
  guid: str
  published_at: datetime
  category: str | None = None


class OpenAIScraper:
  def __init__(self):
    self.rss_url = "https://openai.com/news/rss.xml"

  def get_articles(self, hours: int = 24) -> list[OpenAIArticle]:
    """
    Fetches the latest articles from OpenAI's RSS feed.
    """
    feed = feedparser.parse(self.rss_url)
    if not feed.entries:
      return []
    cutoff_time = datetime.now(UTC) - timedelta(hours=hours)
    articles = []

    for entry in feed.entries:
      published_parsed = getattr(entry, "published_parsed", None)
      if not published_parsed:
        continue
      
      published_time = datetime(*published_parsed[:6], tzinfo=UTC)
      if published_time >= cutoff_time: 

        tags = entry.get("tags")

        articles.append(OpenAIArticle(
          title=entry.get("title", ""),
          description=entry.get("description", ""),
          url=entry.get("link", ""),
          guid=entry.get("id", entry.get("link", "")),
          published_at=published_time,
          category=tags[0]["term"] if tags else None,
        ))
    return articles

if __name__ == "__main__":
  scraper = OpenAIScraper()
  articles : list[OpenAIArticle] = scraper.get_articles(hours=24)
  print(articles)