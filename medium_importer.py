"""
Importador para Medium
Importa artigos do Dev.to para Medium via URL
"""

import yaml
import json
import logging
import requests
from pathlib import Path

logger = logging.getLogger(__name__)


class MediumImporter:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.output_dir = Path(self.config["paths"]["output_dir"])
        self.published_file = self.output_dir / "published_medium.json"
        self.published = self._load_published()

    def _load_published(self):
        if self.published_file.exists():
            with open(self.published_file, "r") as f:
                return json.load(f)
        return {}

    def _save_published(self):
        with open(self.published_file, "w") as f:
            json.dump(self.published, f, indent=2)

    def import_from_url(self, article_url, canonical_url=None):
        """
        Importa um artigo do Dev.to para Medium

        NOTA: Medium nao tem API para importacao direta.
        Esta funcao gera as instrucoes para importacao manual
        ou usa o import tool do Medium.
        """
        # Verificar se ja foi importado
        if article_url in self.published:
            logger.info(f"Artigo ja importado: {article_url}")
            return self.published[article_url]

        # Medium Import Tool URL
        import_url = "https://medium.com/p/import"

        instructions = {
            "steps": [
                f"1. Acesse: {import_url}",
                f"2. Cole a URL: {article_url}",
                f"3. Clique em 'Import'",
                f"4. Adicione a canonical URL: {canonical_url or article_url}",
                f"5. Revise e publique"
            ],
            "import_url": import_url,
            "source_url": article_url,
            "canonical_url": canonical_url or article_url
        }

        if self.config["general"]["dry_run"]:
            logger.info(f"[DRY RUN] Importaria no Medium: {article_url}")
            return instructions

        # Registrar tentativa
        self.published[article_url] = {
            "status": "pending_import",
            "instructions": instructions,
            "source_url": article_url
        }
        self._save_published()

        logger.info(f"Instrucoes de importacao geradas para: {article_url}")
        return instructions

    def import_from_devto(self, devto_url, canonical_url=None):
        """Importa um artigo do Dev.to"""
        return self.import_from_url(devto_url, canonical_url)

    def create_medium_post(self, project_key, content):
        """
        Cria um post direto no Medium (requer integration token)

        NOTA: A API do Medium foi descontinuada para novos tokens.
        Esta funcao e mantida para referencia futura.
        """
        logger.warning("API do Medium nao esta disponivel para novos tokens.")
        logger.info("Use a ferramenta de importacao do Medium em: https://medium.com/p/import")

        return {
            "status": "api_unavailable",
            "message": "Use o import tool do Medium",
            "url": "https://medium.com/p/import"
        }


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1:
        devto_url = sys.argv[1]
        importer = MediumImporter()
        result = importer.import_from_devto(devto_url)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Uso: python medium_importer.py <devto_url>")
