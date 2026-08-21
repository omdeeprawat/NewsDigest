import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.agent.digest_agent import DigestAgent
from app.database.repository import Repository

def process_digest(limit: int | None = None) -> dict:
  """
  Process the digests for articles from various sources.

  Args:
    limit :int | None = None :: The maximum number of articles to process. If None, process all articles.
  """
  repo = Repository()
  agent = DigestAgent()

  # Fetch articles that don't have digests
  articles = repo.get_articles_without_digest(limit=limit)
  total = len(articles)
  processed = 0
  failed = 0

  for idx, article in enumerate(articles,1):
    article_origin = article["origin"]
    article_id = article["id"]
    article_title = article["title"][:60] + "..." if len(article["title"]) > 60 else article["title"]
    
    try:
      digest_result = agent.generate_digest(
        title=article["title"],
        content=article["content"],
        article_origin=article_origin
      )
      if digest_result:
        repo.create_digest(
          article_origin=article["origin"],
          article_id=article["id"],
          url=article["url"],
          title=digest_result.title,
          summary=digest_result.summary,
          published_at=article.get("published_at")
        )
        processed += 1
      else:
        failed += 1
    except Exception as e:
      failed += 1
      print(f"Failed to process digest for article with ID {article.id}: {e}")
      continue

  return {
    "total": len(articles),
    "processed": processed,
    "failed": failed
  }

if __name__ == "__main__":
  result = process_digest()
  print(f"Total articles: {result['total']}")
  print(f"Processed: {result['processed']}")
  print(f"Failed: {result['failed']}")

