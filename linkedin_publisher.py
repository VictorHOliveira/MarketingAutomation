"""
Publicador para LinkedIn
Publica posts profissionais com imagens
"""

import yaml
import json
import time
import logging
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

LINKEDIN_API = "https://api.linkedin.com/rest"
LINKEDIN_VERSION = "202607"


class LinkedInPublisher:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.access_token = self.config["apis"]["linkedin"]["access_token"]
        self.person_urn = self.config["apis"]["linkedin"]["person_urn"]
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Linkedin-Version": LINKEDIN_VERSION,
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json"
        }
        self.output_dir = Path(self.config["paths"]["output_dir"])
        self.published_file = self.output_dir / "published_linkedin.json"
        self.published = self._load_published()

    def _load_published(self):
        if self.published_file.exists():
            with open(self.published_file, "r") as f:
                return json.load(f)
        return {}

    def _save_published(self):
        with open(self.published_file, "w") as f:
            json.dump(self.published, f, indent=2)

    def upload_image(self, image_path):
        """Upload de imagem para LinkedIn (precisa de image upload separado)"""
        # LinkedIn requer upload via Images API
        # Por enquanto, retornamos None e usamos posts de texto
        logger.info("Upload de imagem no LinkedIn requer Images API (implementar se necessario)")
        return None

    def publish_post(self, project_key, content, image_path=None):
        """Publica um post no LinkedIn"""
        project = self.config["projects"][project_key]

        # Verificar se ja foi publicado
        text_hash = hash(content["text"][:100])
        if str(text_hash) in self.published:
            logger.info("Post ja publicado no LinkedIn")
            return self.published[str(text_hash)]

        # Preparar payload - Post de texto com artigo
        payload = {
            "author": self.person_urn,
            "commentary": content["text"],
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False
        }

        # Se tiver URL do projeto, adicionar como artigo
        if project.get("url"):
            payload["content"] = {
                "article": {
                    "source": project["url"],
                    "title": project["name"],
                    "description": project["description"]
                }
            }

        if self.config["general"]["dry_run"]:
            logger.info(f"[DRY RUN] Publicaria no LinkedIn: {content['text'][:100]}...")
            return {"id": "dry_run"}

        try:
            response = requests.post(
                f"{LINKEDIN_API}/posts",
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning(f"Rate limit LinkedIn. Aguardando {retry_after}s...")
                time.sleep(retry_after)
                return self.publish_post(project_key, content, image_path)

            response.raise_for_status()

            # Pegar ID do header
            post_id = response.headers.get("x-restli-id", "unknown")

            # Registrar
            self.published[str(text_hash)] = {
                "id": post_id,
                "project": project_key,
                "text_preview": content["text"][:200]
            }
            self._save_published()

            logger.info(f"Post publicado no LinkedIn: {post_id}")
            return {"id": post_id}

        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao publicar no LinkedIn: {e}")
            raise

    def publish_linkedin_post(self, project_key, linkedin_content, image_path=None):
        """Wrapper para publicar post gerado pelo content_generator"""
        return self.publish_post(project_key, linkedin_content, image_path)


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1:
        project = sys.argv[1]
        content = {
            "text": "Post de teste da automacao de marketing. #QA #TestesAutomatizados"
        }
        pub = LinkedInPublisher()
        pub.publish_post(project, content)
    else:
        print("Uso: python linkedin_publisher.py <projeto>")
