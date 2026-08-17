import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.database.repository import Repository
from app.scrapers.anthropic import AnthropicScraper


def process_anthropic_markdown(limit: int | None = None) -> dict:
  """
  Process the markdown content of articles from the Anthropics website.

  Args:
  limit (Optional[int]): The maximum number of articles to process. If None, process all articles.
  """
  # initialize the scraper and repository
  scraper = AnthropicScraper()
  repo = Repository()

  # Fetch articles from the Anthropics website
  articles = repo.get_anthropic_articles_without_markdown(limit=limit)
  processed = 0
  failed = 0

  for article in articles:
    markdown = scraper.url_to_markdown(article.url)
    try:
      if markdown:
        repo.update_anthropic_article_markdown(article.guid, markdown)
        processed +=1
      else:
        failed +=1
    except Exception as e:
      failed += 1
      print(f"Failed to process article with GUID {article.guid}: {e}")
      continue
  
  return{
    "processed": processed,
    "failed": failed,
    "total": len(articles)
  }

if __name__ == "__main__":
  result = process_anthropic_markdown()
  print(f"total articles: {result['total']}")
  print(f"processed articles: {result['processed']}") 
  print(f"failed articles: {result['failed']}")