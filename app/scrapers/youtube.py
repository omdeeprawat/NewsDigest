from pydantic import BaseModel
import feedparser
from datetime import datetime, timedelta, timezone
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from typing import Optional
class Transcript(BaseModel):
  text: str

class YouTubeScraper:
  def __init__(self):
    self.transcript_api = YouTubeTranscriptApi()

  def _get_rss_url(self, channel_id: str) -> str:
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

  def _extract_video_id(self, video_url: str) -> str:
    """
    Extracts the video ID from a YouTube URL.
    """
    if "youtube.com/watch?v=" in video_url:
      return video_url.split("watch?v=")[-1].split("&")[0]
    elif "youtu.be/" in video_url:
      return video_url.split("youtu.be/")[-1].split("?")[0]
    return video_url  

  def get_transcript(self, video_id: str) -> Optional[Transcript]:
    """
    Fetches the transcript for a given YouTube video ID.
    """

    try:
      transcript = self.transcript_api.fetch(video_id)
      text= " ".join([snippet.text for snippet in transcript.snippets])
      return Transcript(text=text)
    except(TranscriptsDisabled, NoTranscriptFound):
      return None
    except Exception as e:
      print(f"Error fetching transcript for {video_id}: {e}")
      return None


  def get_latest_videos(self, channel_id: str, hours : int =24) -> list[dict]:
    """
    Fetches the latest videos from a YouTube channel's RSS feed.
    """
    rss_url = self._get_rss_url(channel_id)
    feed = feedparser.parse(rss_url)
    print(len(feed.entries))
    if not feed.entries:
      return []
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    videos = []
    for entry in feed.entries:
      published_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
      if published_time > cutoff_time:
        video_id = self._extract_video_id(entry.link)
        videos.append({
          "title" : entry.title,
          "url" : entry.link,
          "video_id" : video_id,
          "published_at" : published_time,
          "description" : entry.get("summary", "")
        })
    return videos


  def scrape_channel(self, channel_id : str, hours:int = 150) -> list[dict]:
    """
    Scrapes the latest videos and their transcripts from a YouTube channel.
    """
    videos = self.get_latest_videos(channel_id, hours)
    for video in videos:
      transcript = self.get_transcript(video["video_id"])
      video["transcript"] = transcript
    return videos

if __name__ == "__main__":
  scraper = YouTubeScraper()
  transcript = scraper.get_transcript('jqd6_bbjhS8')
  print(transcript)