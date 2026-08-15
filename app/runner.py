from .config import YOUTUBE_CHANNELS
from .database.repository import Repository
from .scrapers.anthropic import AnthropicScraper
from .scrapers.openai import OpenAIScraper
from .scrapers.youtube import YouTubeScraper
def run_scrapers(hours: int=24) -> dict:
  """
  Run all scrapers and return a dictionary with the results.

  Args:
      hours (int): The number of hours to look back for new data. Default is 24.  
  """
  youtube_scraper = YouTubeScraper()
  openai_scraper = OpenAIScraper()
  anthropic_scraper = AnthropicScraper()
  repo = Repository()  

  youtube_videos = []
  video_dicts = []
  
  for channel_id in YOUTUBE_CHANNELS:
    videos = youtube_scraper.get_latest_videos(channel_id, hours=hours)
    youtube_videos.extend(videos)
    video_dicts.extend([{
      "video_id": video.video_id,
      "title": video.title,
      "url": video.url,
      "channel_id": channel_id,
      "published_at": video.published_at,
      "description": video.description,
      "transcript": video.transcript
      } for video in videos])

  openai_articles = openai_scraper.get_articles(hours=hours)
  anthropic_articles = anthropic_scraper.get_articles(hours=hours)

  if video_dicts: 
    repo.bulk_create_youtube_videos(video_dicts)

  if openai_articles:
    article_dicts = [{
      "guid": article.guid,
      "title": article.title,
      "url": article.url, 
      "published_at": article.published_at,
      "description": article.description,
      "category": article.category
    } for article in openai_articles]
    repo.bulk_create_openai_articles(article_dicts)

  if anthropic_articles:
    article_dicts = [{
      "guid": article.guid,
      "title": article.title,
      "url": article.url,
      "description": article.description,
      "published_at": article.published_at,
      "category": article.category
    } for article in anthropic_articles]
    repo.bulk_create_anthropic_articles(article_dicts)

  return {
    "youtube": youtube_videos,
    "openai": openai_articles,
    "anthropic": anthropic_articles
  }

  if __name__ == "__main__":
    results = run_scrapers(hours=24)
    print(f"youtube videos : {len(results['youtube'])}")
    print(f"openai articles : {len(results['openai'])}")
    print(f"anthropic articles : {len(results['anthropic'])}")


if __name__ == "__main__":
    print("__main__ BLOCK STARTED")
    main()