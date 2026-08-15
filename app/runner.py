from .scrapers.anthropic import AnthropicScraper
from .scrapers.openai import OpenAIScraper
from .scrapers.youtube import YouTubeScraper, ChannelVideo
from .config import YOUTUBE_CHANNELS

def run_scrapers(hours: int=24) -> dict:
  """
  Run all scrapers and return a dictionary with the results.

  Args:
      hours (int): The number of hours to look back for new data. Default is 24.  
  """
  youtube_scraper = YouTubeScraper()
  openai_scraper = OpenAIScraper()
  anthropic_scraper = AnthropicScraper()

  youtube_videos = []
  video_dicts = []
  
  for channel_id in YOUTUBE_CHANNELS:
    videos