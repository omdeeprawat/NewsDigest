from pydantic import BaseModel
import feedparser
from datetime import datetime, timedelta, timezone
from youtube_transcript_api import YouTubeTranscriptApi
class Transcript(BaseModel):
  text: str

def get_rss_url(channel_id: str) -> str:
  return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

def extract_video_id(video_url: str) -> str:
  """
  Extracts the video ID from a YouTube URL.
  """
  if "youtube.com/watch?v=" in video_url:
    return video_url.split("watch?v=")[-1].split("&")[0]
  elif "youtube/" in video_url:
    return video_url.split("youtu.be/")[-1].split("?")[0]
  return video_url  

def get_latest_videos(channel_id: str, hours : int =24) -> list[dict]:
  """
  Fetches the latest videos from a YouTube channel's RSS feed.
  """
  rss_url = get_rss_url(channel_id)
  # print(rss_url)
  feed = feedparser.parse(rss_url)
  # print(feed.status)
  print(len(feed.entries))
  if not feed.entries:
    return []
  cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
  videos = []
  for entry in feed.entries:
    published_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    # print(entry.title)
    # print("Published:", published_time)
    # print("Newer:", published_time > cutoff_time)
    # print()
    if published_time > cutoff_time:
      video_id = extract_video_id(entry.link)
      videos.append({
        "title" : entry.title,
        "url" : entry.link,
        "video_id" : video_id,
        "published_at" : published_time,
        "description" : entry.get("summary", "")
      })
  return videos


def get_transcript(video_id: str) -> Transcript:
  """
  Fetches the transcript for a given YouTube video ID.
  """
  # Placeholder implementation; actual implementation would require YouTube API or scraping
  try:
    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
    return " ".join([entry['text'] for entry in transcript_list])
  except(TranscriptsDisabled, NoTranscriptFound):
    return None
  except Exception:
    return None

def scrape_channel(channel_id : str, hours:int = 150) -> list[dict]:
  """
  Scrapes the latest videos and their transcripts from a YouTube channel.
  """
  videos = get_latest_videos(channel_id, hours)
  for video in videos:
    transcript = get_transcript(video["video_id"])
    video["transcript"] = transcript
  return videos

if __name__ == "__main__":
  scraper = YouTubeScraper()
  
  videos = get_latest_videos(channel_id="UCn8ujwUInbJkBhffxqAPBVQ", hours=200)
  print(videos)