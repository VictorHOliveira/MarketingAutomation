"""
Gerador de Imagens via Canva Connect API
Cria imagens automaticamente a partir de Brand Templates
"""

import yaml
import json
import time
import logging
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

CANVA_API_BASE = "https://api.canva.com/rest/v1"


class CanvaGenerator:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.access_token = self.config["apis"]["canva"]["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        self.output_dir = Path(self.config["paths"]["output_dir"])
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _request(self, method, endpoint, **kwargs):
        """Faz requisicao a API do Canva com retry"""
        url = f"{CANVA_API_BASE}{endpoint}"
        for attempt in range(self.config["general"]["max_retries"]):
            try:
                response = requests.request(method, url, headers=self.headers, **kwargs)
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limit atingido. Aguardando {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.error(f"Erro na requisicao (tentativa {attempt + 1}): {e}")
                if attempt < self.config["general"]["max_retries"] - 1:
                    time.sleep(self.config["general"]["retry_delay_seconds"])
        raise Exception(f"Falha apos {self.config['general']['max_retries']} tentativas")

    def create_design_from_template(self, project_key, title, subtitle=""):
        """Cria um design a partir de um Brand Template"""
        template_id = self.config["apis"]["canva"]["brand_templates"].get(project_key)
        if not template_id:
            logger.warning(f"Nenhum brand template configurado para {project_key}")
            return None

        payload = {
            "type": "brand_template",
            "brand_template": {
                "template_id": template_id
            },
            "title": title
        }

        result = self._request("POST", "/designs", json=payload)
        design_id = result.get("design", {}).get("id")
        logger.info(f"Design criado: {design_id}")

        return design_id

    def create_custom_design(self, project_key, title, width=1200, height=630):
        """Cria um design customizado"""
        payload = {
            "type": "type_and_asset",
            "design_type": {
                "type": "custom",
                "custom": {
                    "width": width,
                    "height": height
                }
            },
            "title": title
        }

        result = self._request("POST", "/designs", json=payload)
        design_id = result.get("design", {}).get("id")
        logger.info(f"Design customizado criado: {design_id}")

        return design_id

    def export_design(self, design_id, format_type="png", quality="pro"):
        """Exporta um design como imagem"""
        payload = {
            "format": {
                "type": format_type,
                "quality": quality,
                "width": 1200,
                "height": 630
            }
        }

        result = self._request("POST", f"/designs/{design_id}/export", json=payload)
        job_id = result.get("job", {}).get("id")

        # Polling ate o job completar
        for _ in range(30):  # Max 30 tentativas (60 segundos)
            time.sleep(2)
            status_result = self._request("GET", f"/exports/{job_id}")
            status = status_result.get("job", {}).get("status")

            if status == "success":
                urls = status_result.get("job", {}).get("urls", [])
                if urls:
                    return urls[0]
            elif status == "failed":
                error = status_result.get("job", {}).get("error", {})
                raise Exception(f"Falha ao exportar: {error.get('message', 'Erro desconhecido')}")

        raise Exception("Timeout aguardando exportacao do design")

    def download_image(self, url, filename):
        """Baixa uma imagem de uma URL"""
        response = requests.get(url)
        response.raise_for_status()

        filepath = self.output_dir / filename
        with open(filepath, "wb") as f:
            f.write(response.content)

        logger.info(f"Imagem baixada: {filepath}")
        return filepath

    def generate_blog_cover(self, project_key, title):
        """Gera imagem de capa para blog post"""
        logger.info(f"Gerando capa para: {title}")

        design_id = self.create_design_from_template(project_key, title)
        if not design_id:
            # Fallback: criar design customizado
            design_id = self.create_custom_design(project_key, title)

        image_url = self.export_design(design_id)
        filename = f"cover_{project_key}_{int(time.time())}.png"
        return self.download_image(image_url, filename)

    def generate_social_image(self, project_key, title, width=1080, height=1080):
        """Gera imagem para redes sociais"""
        logger.info(f"Gerando imagem social para: {title}")

        design_id = self.create_custom_design(project_key, title, width, height)
        image_url = self.export_design(design_id)
        filename = f"social_{project_key}_{int(time.time())}.png"
        return self.download_image(image_url, filename)

    def generate_all_images(self, project_key, content):
        """Gera todas as imagens necessarias para um conteudo"""
        images = {}

        # Imagem de capa do blog
        try:
            cover = self.generate_blog_cover(project_key, content["blog_post"]["title"])
            images["blog_cover"] = str(cover)
        except Exception as e:
            logger.error(f"Erro ao gerar capa do blog: {e}")

        # Imagem para LinkedIn
        try:
            linkedin_img = self.generate_social_image(
                project_key,
                content["linkedin"].get("image_prompt", content["blog_post"]["title"]),
                1200, 628
            )
            images["linkedin"] = str(linkedin_img)
        except Exception as e:
            logger.error(f"Erro ao gerar imagem LinkedIn: {e}")

        # Imagem para Reddit
        try:
            reddit_img = self.generate_social_image(
                project_key,
                content["blog_post"]["title"],
                1200, 630
            )
            images["reddit"] = str(reddit_img)
        except Exception as e:
            logger.error(f"Erro ao gerar imagem Reddit: {e}")

        return images


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    project = sys.argv[1] if len(sys.argv) > 1 else "qa_overflow"
    title = sys.argv[2] if len(sys.argv) > 2 else "Post de Teste"

    gen = CanvaGenerator()
    result = gen.generate_blog_cover(project, title)
    print(f"Imagem gerada: {result}")
