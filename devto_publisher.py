"""
Publicador para Dev.to
Publica artigos automaticamente com canonical URL
"""

import yaml
import json
import time
import logging
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

DEVTO_API = "https://dev.to/api"


class DevToPublisher:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.api_key = self.config["apis"]["devto"]["api_key"]
        self.username = self.config["apis"]["devto"]["username"]
        self.headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }
        self.output_dir = Path(self.config["paths"]["output_dir"])
        self.published_file = self.output_dir / "published_devto.json"
        self.published = self._load_published()

    def _load_published(self):
        """Carrega lista de artigos ja publicados"""
        if self.published_file.exists():
            with open(self.published_file, "r") as f:
                return json.load(f)
        return {}

    def _save_published(self):
        """Salva lista de artigos publicados"""
        with open(self.published_file, "w") as f:
            json.dump(self.published, f, indent=2)

    def publish_article(self, project_key, content, canonical_url=None):
        """Publica um artigo no Dev.to"""
        project = self.config["projects"][project_key]

        # Verificar se ja foi publicado
        slug = content.get("slug", "unknown")
        if slug in self.published:
            logger.info(f"Artigo ja publicado: {slug}")
            return self.published[slug]

        # Preparar payload
        payload = {
            "article": {
                "title": content["title"],
                "body_markdown": content["body_markdown"],
                "tags": content.get("tags", project.get("tags_devto", []))[:4],
                "published": True,
                "description": content.get("description", ""),
                "canonical_url": canonical_url or f"{project['url']}/{slug}",
                "main_image": content.get("cover_image", "")
            }
        }

        if self.config["general"]["dry_run"]:
            logger.info(f"[DRY RUN] Publicaria no Dev.to: {content['title']}")
            return {"id": "dry_run", "url": "dry_run"}

        # Fazer requisicao
        try:
            response = requests.post(
                f"{DEVTO_API}/articles",
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 30))
                logger.warning(f"Rate limit Dev.to. Aguardando {retry_after}s...")
                time.sleep(retry_after)
                return self.publish_article(project_key, content, canonical_url)

            response.raise_for_status()
            result = response.json()

            # Registrar publicacao
            self.published[slug] = {
                "id": result["id"],
                "url": result["url"],
                "published_at": result.get("published_at", ""),
                "project": project_key
            }
            self._save_published()

            logger.info(f"Artigo publicado no Dev.to: {result['url']}")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao publicar no Dev.to: {e}")
            raise

    def import_from_medium(self, medium_url):
        """Importa um artigo do Medium para Dev.to"""
        # Dev.to nao tem import API direta, mas podemos usar a URL
        # O usuario precisa importar manualmente via dashboard
        logger.info(f"Para importar no Dev.to, acesse: https://dev.to/dashboard/new")
        logger.info(f"URL para importar: {medium_url}")
        return None

    def get_unpublished(self):
        """Retorna artigos nao publicados"""
        try:
            response = requests.get(
                f"{DEVTO_API}/articles/me/unpublished",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao buscar artigos nao publicados: {e}")
            return []

    def publish_from_file(self, filepath):
        """Publica um artigo a partir de um arquivo JSON"""
        with open(filepath, "r", encoding="utf-8") as f:
            content = json.load(f)

        project_key = content.get("project", "qa_overflow")
        return self.publish_article(project_key, content)


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        pub = DevToPublisher()
        pub.publish_from_file(filepath)
    else:
        print("Uso: python devto_publisher.py <caminho_para_conteudo.json>")
