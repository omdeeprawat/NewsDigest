from typing import Optional, List
from sqlalchemy.orm import Session
from .connection import get_session
from datetime import datetime
from .models import YouTubeVideo, OpenAIArticle, AnthropicArticle

class Repository:
  def __init__(self,session: Optional[Session] = None):
    self.session = session or get_session()

  def create_youtube_video(self, video_id: str, title: str, url: str, channel_id: str, published_at: datetime, description: str = "",transcript: Optional[str] = None)-> Optional[YouTubeVideo]:

    existing = self.session.query(YouTubeVideo).filter_by(video_id=video_id).first()
    if existing:
      return None
  
    video = YouTubeVideo(
      video_id=video_id,
      title=title,
      url=url,
      channel_id=channel_id,
      published_at=published_at,
      description=description,
      transcript=transcript
    )
    self.session.add(video)
    self.session.commit()
    return video

  def create_openai_article(self, guid: str, title: str, url: str, description: str, published_at: datetime, category: Optional[str] = None) -> Optional[OpenAIArticle]:

    existing = self.session.query(OpenAIArticle).filter_by(guid=guid).first()
    if existing:
      return None

    article = OpenAIArticle(
      guid=guid,
      title=title,
      url=url,
      published_at=published_at,
      description=description,
      category=category
    )
    self.session.add(article)
    self.session.commit()
    return article

  def create_anthropic_article(self, guid: str, title: str, url: str, description: str, published_at: datetime, category: Optional[str] = None) -> Optional[AnthropicArticle]:
      existing = self.session.query(AnthropicArticle).filter_by(guid=guid).first()
      if existing:
        return None

      article = AnthropicArticle(
        guid=guid,
        title=title,
        url=url,
        published_at=published_at,
        description=description,
        category=category,
      )
      self.session.add(article)
      self.session.commit()
      return article
      

  def bulk_create_youtube_videos(self, videos: List[dict]) -> int:
    new_videos = []
    for v in videos:
      existing = self.session.query(YouTubeVideo).filter_by(video_id=v["video_id"]).first()
      if not existing:
        new_videos.append(YouTubeVideo(
          video_id=v["video_id"],
          title=v["title"],
          url=v["url"],
          channel_id=v["channel_id"],
          published_at=v["published_at"],
          description=v.get("description", ""),
          transcript=v.get("transcript")
        ))

    if new_videos:
      self.session.bulk_save_objects(new_videos)
      self.session.commit()
    return len(new_videos)

  def bulk_create_openai_articles(self, articles: List[dict]) -> int:
    new_articles = []
    for a in articles:
      existing = self.session.query(OpenAIArticle).filter_by(guid=a["guid"]).first()
      if not existing:
        new_articles.append(OpenAIArticle(
          guid=a["guid"],
          title=a["title"],
          url=a["url"],
          published_at=a["published_at"],
          description=a.get("description", ""),
          category=a.get("category")
        ))

    if new_articles:
      self.session.bulk_save_objects(new_articles)
      self.session.commit()
    return len(new_articles)

  def bulk_create_anthropic_articles(self, articles: List[dict]) -> int:  
    new_articles = []
    for a in articles:
      existing = self.session.query(AnthropicArticle).filter_by(guid=a["guid"]).first()
      if not existing:
        new_articles.append(AnthropicArticle(
          guid=a["guid"],
          title=a["title"],
          url=a["url"],
          published_at=a["published_at"],
          description=a.get("description", ""),
          category=a.get("category")
        ))

    if new_articles:
      self.session.bulk_save_objects(new_articles)
      self.session.commit()
    return len(new_articles)

  

