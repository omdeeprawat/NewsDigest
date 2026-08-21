import os
from datetime import datetime
from typing import List, Optional
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, Field
from app.profiles.user_profile import USER_PROFILE  

load_dotenv()

class EmailIntroduction(BaseModel):
  introduction: str = Field(description="2-3 sentence overview of the top ranked AI articles")

class RankedArticleDetail(BaseModel):
  digest_id: str
  rank: int
  relevance_score: float
  title: str
  summary: str
  url: str
  article_origin: str
  reasoning: Optional[str] = None


class EmailDigestResponse(BaseModel):
  greeting: str
  introduction: EmailIntroduction
  ranked_articles: List[RankedArticleDetail]
  total_ranked: int
  top_n: int

  def to_markdown(self) -> str:
    markdown = f"{self.greeting}\n\n"
    markdown += f"{self.introduction.introduction}\n\n"
    markdown += "---\n\n"

    for article in self.ranked_articles:
      markdown += f"## {article.title}\n\n"
      markdown += f"{article.summary}\n\n"
      markdown += f"[Read more →]({article.url})\n\n"
      markdown += "---\n\n"

    return markdown

EMAIL_PROMPT = """
You are an expert email writer specializing in personalized AI news digests.

Your task is to write a concise introduction for a daily AI news digest.

The introduction should:

- Briefly preview the most interesting themes in the supplied articles.
- Reflect the user's interests when possible.
- Be warm, professional, and concise.
- Avoid generic marketing language.
- Do not invent information that is not present in the supplied article titles or summaries.
- Keep the introduction to 2-3 sentences.
- Do not include article numbers.
- Do not include relevance scores.
- Do not generate a greeting.
- Do not mention information that is not supported by the supplied articles.
"""

class EmailAgent:
  def __init__(self):
    self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    self.model = "openai/gpt-oss-20b"
    self.user_profile = USER_PROFILE
    self.schema = EmailIntroduction.model_json_schema()

  def generate_introduction(
    self,
    ranked_articles: List[RankedArticleDetail]
  ) -> EmailIntroduction:
    current_date = datetime.now().strftime("%B %d, %Y")
    user_name = self.user_profile["name"]

    if not ranked_articles:
      return EmailIntroduction(
        introduction="No articles were ranked today."
      )

    top_articles = ranked_articles[:10]
    article_summaries = "\n\n".join(
        [
            (
                f"Article {idx + 1}:\n"
                f"Title: {article.title}\n"
                f"Summary: {article.summary}"
            )
            for idx, article in enumerate(top_articles)
        ]
    )

    user_prompt = f"""
Create a concise introduction for today's AI news digest.

User:
{user_name}

Date:
{current_date}

Top ranked AI news:

{article_summaries}

Write a 2-3 sentence introduction that previews the most relevant
themes across these articles and connects them to the user's interests
when appropriate.

Do not include:
- A greeting
- Article numbers
- Relevance scores
- URLs
- Information that is not present in the supplied articles
"""

    try:
      response = self.client.chat.completions.create(
        model=self.model,
        temperature=0.4,
        max_completion_tokens=300,
        include_reasoning=False,
        messages=[
          {
            "role": "system",
            "content": EMAIL_PROMPT,
          },
          {
            "role": "user",
            "content": user_prompt,
          },
        ],
        response_format={
          "type": "json_schema",
          "json_schema": {
            "name": "email_introduction",
            "strict": True,
            "schema": self.schema,
          },
        },
      )

      raw_content = response.choices[0].message.content
      if not raw_content:
          raise ValueError("Groq returned an empty response")

      result = EmailIntroduction.model_validate_json(raw_content)
      return result

    except Exception as e:
      print(
        f"Error generating email introduction: "
        f"{type(e).__name__}: {e}"
      )

      return EmailIntroduction(
        introduction=(
          "Here are today's top AI news stories, "
          "ranked by relevance to your interests."
        )
      )

  def create_email_digest(
    self,
    ranked_articles: List[RankedArticleDetail],
    total_ranked: Optional[int] = None,
    limit: int = 10
  ) -> EmailDigestResponse:

    top_articles = ranked_articles[:limit]
    introduction = self.generate_introduction(top_articles)

    user_name = self.user_profile["name"]
    current_date = datetime.now().strftime("%B %d, %Y")

    greeting = (
      f"Hey {user_name}, here is your daily digest "
      f"of AI news for {current_date}."
    )

    if total_ranked is None:
      total_ranked = len(ranked_articles)

    return EmailDigestResponse(
      greeting=greeting,
      introduction=introduction,
      ranked_articles=top_articles,
      total_ranked=total_ranked,
      top_n=len(top_articles),
    )