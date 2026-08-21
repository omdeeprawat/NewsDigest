import os
import json
from typing import List

from groq import Groq
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class RankedArticle(BaseModel):
  digest_id: str = Field(
    description="The ID of the digest (article_origin:article_id)"
  )
  relevance_score: float = Field(
    description="Relevance score from 0.0 to 10.0",
    ge=0.0,
    le=10.0
  )
  rank: int = Field(
    description="Rank position, where 1 is most relevant",
    ge=1
  )
  reasoning: str = Field(
    description="Brief explanation of why this article is ranked here"
  )


class RankedDigestList(BaseModel):
  articles: List[RankedArticle]


CURATOR_PROMPT = """You are an expert AI news curator specializing in personalized content ranking for AI professionals.

Your task is to analyze and rank AI-related news articles, research papers, and video content based on the user's specific profile, interests, background, expertise, and preferences.

The goal is NOT to determine which article is objectively the most important.

The goal is to determine which content is most valuable and relevant to THIS USER.

Ranking Criteria:
1. Relevance to the user's stated interests and background
2. Technical depth and practical value
3. Novelty and significance
4. Alignment with the user's expertise level
5. Actionability and real-world applicability

Scoring Guidelines:
- 9.0-10.0: Highly relevant, directly aligns with user interests, significant value
- 7.0-8.9: Very relevant, strong alignment with interests, good value
- 5.0-6.9: Moderately relevant, some alignment, decent value
- 3.0-4.9: Somewhat relevant, limited alignment, lower value
- 0.0-2.9: Low relevance, minimal alignment, little value

Ranking Rules:
- Evaluate every supplied digest.
- Return exactly one result for every supplied digest.
- Do not invent or modify digest IDs.
- Rank articles from most relevant to least relevant.
- Rank 1 must be the most relevant article.
- Use every rank exactly once.
- Ranks must be consecutive from 1 through N.
- The article with the highest relevance score should receive rank 1.
- Higher relevance should generally result in a better rank.
- Do not favor content simply because it comes from a major AI company.
- Do not favor articles over videos or videos over articles.
- Evaluate the substance and value of the content for this specific user.
- Consider the user's expertise level when evaluating technical depth.
- Prefer practical insights, technical substance, novelty, and actionable information over marketing language.
- Do not invent information that is not present in the supplied digest.
- Keep reasoning brief and specific.
"""


class CuratorAgent:

  def __init__(self, user_profile: dict):
    self.client = Groq(
      api_key=os.getenv("GROQ_API_KEY")
    )
    self.model = "openai/gpt-oss-20b"
    self.user_profile = user_profile
    self.system_prompt = self._build_system_prompt()
    self.schema = RankedDigestList.model_json_schema()

  def _build_system_prompt(self) -> str:
    interests = "\n".join(
      f"- {interest}"
      for interest in self.user_profile["interests"]
    )

    preferences = self.user_profile["preferences"]
    pref_text = "\n".join(
      f"- {key}: {value}"
      for key, value in preferences.items()
    )
    return f"""{CURATOR_PROMPT}

User Profile:

Background:
{self.user_profile["background"]}

Expertise Level:
{self.user_profile["expertise_level"]}

Interests:
{interests}

Preferences:
{pref_text}
"""

  def rank_digests(
    self,
    digests: List[dict]
  ) -> List[RankedArticle]:

    if not digests:
      return []

    digest_list = "\n\n".join(
        [
            f"""ID: {d['id']}
Title: {d['title']}
Summary: {d['summary']}
Source: {d.get('article_origin', 'unknown')}
Type: {d.get('article_type', 'unknown')}"""
            for d in digests
        ]
    )

    user_prompt = f"""Rank these {len(digests)} AI news digests according to the user profile.

{digest_list}

Return exactly one ranking result for every digest.

Use ranks 1 through {len(digests)} exactly once.
Rank 1 must be the most relevant digest.
"""
    try:
      response = self.client.chat.completions.create(
        model=self.model,
        temperature=0.3,
        max_completion_tokens=1500,
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
            "name": "ranked_digest_list",
            "strict": True,
            "schema": self.schema,
          },
        },
      )

      raw_content = response.choices[0].message.content
      if not raw_content:
        print("Groq returned an empty curator response")
        return []

      result = json.loads(raw_content)
      ranked_result = RankedDigestList.model_validate(result)

      return self._validate_ranking(
        ranked_result.articles,
        digests
      )

    except Exception as e:
      print(
        f"Error ranking digests: "
        f"{type(e).__name__}: {e}"
      )
      return []


  def _validate_ranking(
    self,
    ranked_articles: List[RankedArticle],
    digests: List[dict]
  ) -> List[RankedArticle]:
    expected_ids = {
      digest["id"]
      for digest in digests
    }

    returned_ids = {
      article.digest_id
      for article in ranked_articles
    }

    if returned_ids != expected_ids:
      raise ValueError(
        f"Digest ID mismatch. "
        f"Expected {len(expected_ids)} digests, "
        f"received {len(returned_ids)}."
      )

    ranks = [
      article.rank
      for article in ranked_articles
    ]

    expected_ranks = list(
      range(1, len(digests) + 1)
    )

    if sorted(ranks) != expected_ranks:
      raise ValueError(
        f"Invalid ranking positions: {ranks}. "
        f"Expected {expected_ranks}."
      )

    # rank 1 should have highest score
    sorted_by_score = sorted(
      ranked_articles,
      key=lambda article: article.relevance_score,
      reverse=True
    )

    sorted_by_rank = sorted(
      ranked_articles,
      key=lambda article: article.rank
    )

    score_order = [
      article.digest_id
      for article in sorted_by_score
    ]

    rank_order = [
      article.digest_id
      for article in sorted_by_rank
    ]

    if score_order != rank_order:
      raise ValueError(
        "Ranking order does not match relevance scores."
      )

    return sorted_by_rank