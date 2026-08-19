"""
Gerador de Topicos - Sugere topics trending baseados em APIs publicas
"""

import yaml
import json
import logging
import requests
import feedparser
from pathlib import Path

logger = logging.getLogger(__name__)


class TopicGenerator:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

    def get_reddit_trending(self, subreddit, limit=10):
        """Busca posts trending no Reddit"""
        try:
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
            headers = {"User-Agent": "MarketingAutomation/1.0"}
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()

            topics = []
            for post in data.get("data", {}).get("children", []):
                p = post.get("data", {})
                topics.append({
                    "title": p.get("title", ""),
                    "score": p.get("score", 0),
                    "num_comments": p.get("num_comments", 0),
                    "url": f"https://reddit.com{p.get('permalink', '')}"
                })

            return sorted(topics, key=lambda x: x["score"], reverse=True)
        except Exception as e:
            logger.error(f"Erro ao buscar trending do Reddit: {e}")
            return []

    def get_stackoverflow_trending(self, tags=["testing", "automation", "selenium"]):
        """Busca perguntas trending no Stack Overflow"""
        try:
            tag_str = ";".join(tags)
            url = f"https://api.stackexchange.com/2.3/questions?order=desc&sort=activity&tagged={tag_str}&site=stackoverflow&filter=withbody"
            response = requests.get(url, timeout=10)
            data = response.json()

            topics = []
            for item in data.get("items", []):
                topics.append({
                    "title": item.get("title", ""),
                    "score": item.get("score", 0),
                    "view_count": item.get("view_count", 0),
                    "link": item.get("link", ""),
                    "tags": item.get("tags", [])
                })

            return sorted(topics, key=lambda x: x["score"], reverse=True)
        except Exception as e:
            logger.error(f"Erro ao buscar trending do StackOverflow: {e}")
            return []

    def get_producthunt_trending(self, limit=10):
        """Busca produtos trending no Product Hunt (via API publica)"""
        try:
            url = "https://www.producthunt.com/frontend/graphql"
            # Product Hunt requer autenticacao para API completa
            # Por enquanto, retornamos dados simulados
            return []
        except Exception as e:
            logger.error(f"Erro ao buscar trending do Product Hunt: {e}")
            return []

    def suggest_topics_for_project(self, project_key):
        """Sugere topics baseado no projeto"""
        project = self.config["projects"][project_key]

        # Buscar trending de subreddits relevantes
        subreddits = self.config["social_channels"]["reddit_subreddits"].get(project_key, [])
        trending = []

        for sub in subreddits[:2]:
            posts = self.get_reddit_trending(sub, limit=5)
            trending.extend(posts)

        # Filtrar por relevancia
        relevant = []
        keywords = project.get("tags_devto", []) + project.get("tags_reddit", [])

        for topic in trending:
            title_lower = topic["title"].lower()
            if any(kw.lower() in title_lower for kw in keywords):
                relevant.append(topic)

        return relevant[:5]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    gen = TopicGenerator()

    print("=== TOPICS TRENDING ===\n")

    print("--- Reddit r/QualityAssurance ---")
    topics = gen.get_reddit_trending("QualityAssurance", 5)
    for t in topics:
        print(f"  [{t['score']}] {t['title']}")

    print("\n--- StackOverflow (testing tags) ---")
    topics = gen.get_stackoverflow_trending(["testing", "automation"])
    for t in topics[:5]:
        print(f"  [{t['score']}] {t['title']}")
