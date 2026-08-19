"""
Publicador para Twitter/X
Publica threads com suporte a imagens
"""

import yaml
import json
import time
import logging
import tweepy
from pathlib import Path

logger = logging.getLogger(__name__)


class TwitterPublisher:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        twitter_config = self.config["apis"]["twitter"]

        # OAuth 1.0a para media upload + posts
        auth = tweepy.OAuth1UserHandler(
            twitter_config["api_key"],
            twitter_config["api_secret"],
            twitter_config["access_token"],
            twitter_config["access_token_secret"]
        )
        self.api = tweepy.API(auth)

        # OAuth 2.0 para posts v2
        self.client = tweepy.Client(
            bearer_token=twitter_config["bearer_token"],
            consumer_key=twitter_config["api_key"],
            consumer_secret=twitter_config["api_secret"],
            access_token=twitter_config["access_token"],
            access_token_secret=twitter_config["access_token_secret"]
        )

        self.output_dir = Path(self.config["paths"]["output_dir"])
        self.published_file = self.output_dir / "published_twitter.json"
        self.published = self._load_published()

    def _load_published(self):
        if self.published_file.exists():
            with open(self.published_file, "r") as f:
                return json.load(f)
        return {}

    def _save_published(self):
        with open(self.published_file, "w") as f:
            json.dump(self.published, f, indent=2)

    def upload_media(self, image_path):
        """Upload de midia para Twitter"""
        try:
            media = self.api.media_upload(filename=str(image_path))
            logger.info(f"Media uploaded: {media.media_id_string}")
            return media.media_id_string
        except Exception as e:
            logger.error(f"Erro ao upload media: {e}")
            return None

    def post_tweet(self, text, media_ids=None):
        """Posta um tweet simples"""
        if self.config["general"]["dry_run"]:
            logger.info(f"[DRY RUN] Tweetaria: {text[:100]}...")
            return {"id": "dry_run"}

        try:
            kwargs = {"text": text}
            if media_ids:
                kwargs["media_ids"] = media_ids

            response = self.client.create_tweet(**kwargs)
            tweet_id = response.data["id"]
            logger.info(f"Tweet publicado: https://x.com/i/status/{tweet_id}")
            return {"id": tweet_id, "url": f"https://x.com/i/status/{tweet_id}"}

        except Exception as e:
            logger.error(f"Erro ao publicar tweet: {e}")
            raise

    def post_thread(self, tweets, media_ids=None):
        """Posta uma thread (sequencia de tweets)"""
        if self.config["general"]["dry_run"]:
            logger.info(f"[DRY RUN] Threadaria {len(tweets)} tweets")
            return [{"id": "dry_run"} for _ in tweets]

        results = []
        previous_tweet_id = None

        for i, tweet_text in enumerate(tweets):
            try:
                kwargs = {"text": tweet_text}

                # Adicionar media apenas no primeiro tweet
                if i == 0 and media_ids:
                    kwargs["media_ids"] = media_ids

                # Se nao e o primeiro tweet, adicionar reply
                if previous_tweet_id:
                    kwargs["in_reply_to_tweet_id"] = previous_tweet_id

                response = self.client.create_tweet(**kwargs)
                tweet_id = response.data["id"]
                previous_tweet_id = tweet_id

                results.append({
                    "id": tweet_id,
                    "url": f"https://x.com/i/status/{tweet_id}",
                    "text": tweet_text
                })

                logger.info(f"Tweet {i + 1}/{len(tweets)}: {tweet_id}")

                # Delay entre tweets da thread
                if i < len(tweets) - 1:
                    time.sleep(2)

            except Exception as e:
                logger.error(f"Erro ao publicar tweet {i + 1}: {e}")
                break

        return results

    def publish_twitter_content(self, project_key, twitter_content, image_path=None):
        """Wrapper para publicar conteudo gerado pelo content_generator"""
        tweets = twitter_content.get("tweets", [])

        if not tweets:
            logger.warning("Nenhum tweet para publicar")
            return []

        # Upload de imagem se fornecida
        media_ids = None
        if image_path:
            media_id = self.upload_media(image_path)
            if media_id:
                media_ids = [media_id]

        # Publicar thread
        return self.post_thread(tweets, media_ids)


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1:
        project = sys.argv[1]
        pub = TwitterPublisher()
        result = pub.post_tweet("Teste de automacao de marketing #QA #TestesAutomatizados")
        print(f"Resultado: {result}")
    else:
        print("Uso: python twitter_publisher.py <projeto>")
