from app.database.repository import Repository
from app.scrapers.youtube import YouTubeScraper

TRANSCRIPT_UNAVAILABLE_MARKER = "__UNAVAILABLE__"


def process_youtube_transcripts(limit: int | None = None) -> dict:
  """
  Process the transcripts of YouTube videos.

  Args:
    limit (Optional[int]): The maximum number of videos to process. If None, process all videos.
  """
  # initialize the scraper and repository
  scraper = YouTubeScraper()
  repo = Repository()

  # Fetch videos from the database that don't have transcripts
  videos = repo.get_youtube_videos_without_transcript(limit=limit)
  processed = 0
  unavailable = 0
  failed = 0

  for video in videos:
    try:
      transcript_result = scraper.get_transcript(video.video_id)
      if transcript_result:
        repo.update_youtube_video_transcript(video.video_id, transcript_result.text)
        processed += 1
      else:
        repo.update_youtube_video_transcript(video.video_id, TRANSCRIPT_UNAVAILABLE_MARKER)
        unavailable += 1
    except Exception as e:
      repo.update_youtube_video_transcript(video.video_id, TRANSCRIPT_UNAVAILABLE_MARKER)
      failed += 1
      print(f"Failed to process video with ID {video.video_id}: {e}")
      continue

  return {
    "total": len(videos),
    "processed": processed,
    "unavailable": unavailable,
    "failed": failed
  }
   

if __name__ == "__main__":
  result = process_youtube_transcripts()
  print(f"Total videos: {result['total']}")
  print(f"Processed: {result['processed']}")
  print(f"Unavailable: {result['unavailable']}")
  print(f"Failed: {result['failed']}")