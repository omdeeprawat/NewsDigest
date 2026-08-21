import os
from typing import Optional
from groq import Groq
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

load_dotenv()

class DigestOutput(BaseModel):
  title: str
  summary: str


SYSTEM_PROMPT = """You are an expert AI news analyst specializing in artificial intelligence.

You analyze content from multiple sources, including:
- AI company blogs and announcements
- Technical articles and research
- YouTube videos and transcripts
- Product and model announcements

Your role is to create concise, informative digests that help readers quickly understand the key points and significance of AI-related content.

Guidelines:
- Create a compelling title of 5-10 words
- Write a concise 2-3 sentence summary
- Highlight the main development and why it matters
- Focus on actionable insights and implications
- Use clear, accessible language while maintaining technical accuracy
- Avoid marketing fluff
- Do not invent information
- Only use information present in the supplied content
- Preserve important technical details, model names, product names,
  benchmarks, numbers, and dates when relevant
"""


class DigestAgent:
  def __init__(self):
    self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    self.model = "openai/gpt-oss-20b"
    self.system_prompt = SYSTEM_PROMPT
    self.schema = DigestOutput.model_json_schema()
    self.schema["additionalProperties"] = False

  def generate_digest(
    self,
    title: str,
    content: str,
    article_origin: str,
  ) -> Optional[DigestOutput]:

    if not content or not content.strip():
      print(
        f"Cannot generate digest: empty content "
        f"for {article_origin}:{title}"
      )
      return None

    user_prompt = f"""Create a digest for this {article_origin} content.

Original title:
{title}

Content:
{content[:16000]}
"""
    try:
      response = self.client.chat.completions.create(
        model=self.model,
        temperature=0.3,
        max_completion_tokens=500,
        include_reasoning=False,
        messages=[
          {
            "role": "system",
            "content": self.system_prompt,
          },
          {
            "role": "user",
            "content": user_prompt,
          },
        ],
        response_format={
          "type": "json_schema",
          "json_schema": {
            "name": "digest_output",
            "strict": True,
            "schema": self.schema,
          },
        },
      )

      content = response.choices[0].message.content

      if not content:
        print(
          f"Empty response from Groq for "
          f"{article_origin}:{title}"
        )
        return None

      return DigestOutput.model_validate_json(content)

    except Exception as e:
      print(
        f"Error generating digest for "
        f"{article_origin}:{title}: "
        f"{type(e).__name__}: {e}"
      )
      return None


