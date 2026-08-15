from datetime import UTC, datetime, timedelta

import feedparser
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled


class Transcript(BaseModel):
  text: str

class ChannelVideo(BaseModel):
  title: str
  url: str
  video_id: str
  published_at: datetime
  description: str
  transcript: str | None = None


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
    if "youtube.com/shorts/" in video_url:
      return video_url.split("shorts/")[-1].split("?")[0]
    if "youtu.be/" in video_url:
      return video_url.split("youtu.be/")[-1].split("?")[0]
    return video_url  


  def get_transcript(self, video_id: str) -> Transcript | None:
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


  def get_latest_videos(self, channel_id: str, hours : int =24) -> list[ChannelVideo]:
    """
    Fetches the latest videos from a YouTube channel's RSS feed.
    """
    rss_url = self._get_rss_url(channel_id)
    feed = feedparser.parse(rss_url)
    if not feed.entries:
      return []
    cutoff_time = datetime.now(UTC) - timedelta(hours=hours)
    videos = []
    for entry in feed.entries:
      if "/shorts/" in entry.link:
        continue 
      published_time = datetime(*entry.published_parsed[:6], tzinfo=UTC)
      if published_time > cutoff_time:
        video_id = self._extract_video_id(entry.link)
        videos.append(ChannelVideo(
          title=entry.title,
          url=entry.link,
          video_id=video_id,
          published_at=published_time,
          description=entry.get("summary", "")
        ))
    return videos


  def scrape_channel(self, channel_id : str, hours:int = 150) -> list[ChannelVideo]:
    """
    Scrapes the latest videos and their transcripts from a YouTube channel.
    """
    videos = self.get_latest_videos(channel_id, hours)
    result = []
    for video in videos:
      transcript = self.get_transcript(video.video_id)
      result.append(video.model_copy(update={"transcript": transcript.text if transcript else None}))
    return result

if __name__ == "__main__":
  scraper = YouTubeScraper()
  transcript: Transcript = scraper.get_transcript('jqd6_bbjhS8')
  print(transcript.text)
  channel_videos : List[ChannelVideo] = scraper.scrape_channel('UCn8ujwUInbJkBhffxqAPBVQ', hours=24)