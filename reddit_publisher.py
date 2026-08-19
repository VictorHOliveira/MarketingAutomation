"""
Publicador para Reddit
Publica posts em subreddits relevantes
"""

import yaml
import json
import time
import logging
import praw
from pathlib import Path

logger = logging.getLogger(__name__)


class RedditPublisher:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        reddit_config = self.config["apis"]["reddit"]
        self.reddit = praw.Reddit(
            client_id=reddit_config["client_id"],
            client_secret=reddit_config["client_secret"],
            username=reddit_config["username"],
            password=reddit_config["password"],
            user_agent=reddit_config["user_agent"]
        )

        self.output_dir = Path(self.config["paths"]["output_dir"])
        self.published_file = self.output_dir / "published_reddit.json"
        self.published = self._load_published()

    def _load_published(self):
        if self.published_file.exists():
            with open(self.published_file, "r") as f:
                return json.load(f)
        return {}

    def _save_published(self):
        with open(self.published_file, "w") as f:
            json.dump(self.published, f, indent=2)

    def publish_link_post(self, project_key, subreddit_name, title, url, flair=None):
        """Publica um link post no Reddit"""
        project = self.config["projects"][project_key]

        # Verificar se ja foi publicado
        post_key = f"{subreddit_name}:{url}"
        if post_key in self.published:
            logger.info(f"Link ja publicado em r/{subreddit_name}")
            return self.published[post_key]

        if self.config["general"]["dry_run"]:
            logger.info(f"[DRY RUN] Publicaria em r/{subreddit_name}: {title}")
            return {"id": "dry_run"}

        try:
            subreddit = self.reddit.subreddit(subreddit_name)

            # Submeter link post
            submission = subreddit.submit(
                title=title,
                url=url,
                flair_text=flair,
                send_replies=True
            )

            # Registrar
            self.published[post_key] = {
                "id": submission.id,
                "url": f"https://reddit.com{submission.permalink}",
                "subreddit": subreddit_name,
                "project": project_key
            }
            self._save_published()

            logger.info(f"Link publicado em r/{subreddit_name}: {submission.permalink}")
            return {"id": submission.id, "url": submission.permalink}

        except Exception as e:
            logger.error(f"Erro ao publicar no Reddit: {e}")
            raise

    def publish_text_post(self, project_key, subreddit_name, title, body, flair=None):
        """Publica um text post no Reddit"""
        project = self.config["projects"][project_key]

        # Verificar se ja foi publicado
        post_key = f"{subreddit_name}:text:{hash(title)}"
        if post_key in self.published:
            logger.info(f"Text ja publicado em r/{subreddit_name}")
            return self.published[post_key]

        if self.config["general"]["dry_run"]:
            logger.info(f"[DRY RUN] Publicaria text em r/{subreddit_name}: {title}")
            return {"id": "dry_run"}

        try:
            subreddit = self.reddit.subreddit(subreddit_name)

            # Submeter text post
            submission = subreddit.submit(
                title=title,
                selftext=body,
                flair_text=flair,
                send_replies=True
            )

            # Registrar
            self.published[post_key] = {
                "id": submission.id,
                "url": f"https://reddit.com{submission.permalink}",
                "subreddit": subreddit_name,
                "project": project_key
            }
            self._save_published()

            logger.info(f"Text publicado em r/{subreddit_name}: {submission.permalink}")
            return {"id": submission.id, "url": submission.permalink}

        except Exception as e:
            logger.error(f"Erro ao publicar text no Reddit: {e}")
            raise

    def publish_reddit_content(self, project_key, reddit_content):
        """Wrapper para publicar conteudo gerado pelo content_generator"""
        subreddit = reddit_content.get("subreddit", "QualityAssurance")
        title = reddit_content.get("title", "Post de teste")
        body = reddit_content.get("body", "")

        # Decidir se e link ou text post
        project = self.config["projects"][project_key]
        if project.get("url") and len(body) < 500:
            return self.publish_link_post(
                project_key, subreddit, title, project["url"]
            )
        else:
            return self.publish_text_post(
                project_key, subreddit, title, body
            )

    def get_subreddit_rules(self, subreddit_name):
        """Retorna as regras de um subreddit"""
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            rules = subreddit.rules
            return [rule.short_name for rule in rules]
        except Exception as e:
            logger.error(f"Erro ao buscar regras de r/{subreddit_name}: {e}")
            return []


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 2:
        project = sys.argv[1]
        subreddit = sys.argv[2]
        pub = RedditPublisher()
        rules = pub.get_subreddit_rules(subreddit)
        print(f"Regras de r/{subreddit}: {rules}")
    else:
        print("Uso: python reddit_publisher.py <projeto> <subreddit>")
