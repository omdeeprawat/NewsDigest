from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
Base = declarative_base()

class YouTubeVideo(Base):
  __tablename__ = "youtube_videos"

  video_id = Column(String(255), primary_key=True)
  title = Column(String(255), nullable=False)
  url = Column(String(255), nullable=False)
  channel_id = Column(String(255), nullable=False)
  published_at = Column(DateTime, nullable=False)
  description = Column(Text)
  transcript = Column(Text, nullable=True)
  created_at = Column(DateTime, default=datetime.utcnow)

class OpenAIArticle(Base):
  __tablename__ = "openai_articles"

  guid = Column(String(255), primary_key=True)
  title = Column(String(255), nullable=False)
  url = Column(String(255), nullable=False)
  description = Column(Text)
  published_at = Column(DateTime, nullable=False)
  category = Column(String, nullable=True)
  created_at = Column(DateTime, default=datetime.utcnow)  

class AnthropicArticle(Base):
  __tablename__ = "anthropic_articles"

  guid = Column(String(255), primary_key=True)
  title = Column(String(255), nullable=False)
  url = Column(String(255), nullable=False)
  description = Column(Text)
  published_at = Column(DateTime, nullable=False)
  category = Column(String, nullable=True)
  markdown = Column(Text, nullable=True)
  created_at = Column(DateTime, default=datetime.utcnow)

