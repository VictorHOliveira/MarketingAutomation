"""
Social Scheduler - Orquestrador Principal
Coordena toda a automacao de marketing
"""

import yaml
import json
import logging
import schedule
import time
from datetime import datetime
from pathlib import Path

from content_generator import ContentGenerator
from canva_generator import CanvaGenerator
from devto_publisher import DevToPublisher
from linkedin_publisher import LinkedInPublisher
from reddit_publisher import RedditPublisher
from twitter_publisher import TwitterPublisher
from medium_importer import MediumImporter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/marketing.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SocialScheduler:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.content_gen = ContentGenerator(config_path)
        self.canva = CanvaGenerator(config_path)
        self.devto = DevToPublisher(config_path)
        self.linkedin = LinkedInPublisher(config_path)
        self.reddit = RedditPublisher(config_path)
        self.twitter = TwitterPublisher(config_path)
        self.medium = MediumImporter(config_path)

        self.output_dir = Path(self.config["paths"]["output_dir"])
        self.logs_dir = Path(self.config["paths"]["logs_dir"])
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def run_project_pipeline(self, project_key):
        """Executa o pipeline completo para um projeto"""
        logger.info(f"=== INICIANDO PIPELINE: {project_key.upper()} ===")

        try:
            # 1. Gerar conteudo
            logger.info("Etapa 1/5: Gerando conteudo...")
            content = self.content_gen.generate_all_content(project_key)

            # 2. Gerar imagens via Canva
            logger.info("Etapa 2/5: Gerando imagens...")
            images = {}
            try:
                images = self.canva.generate_all_images(project_key, content)
            except Exception as e:
                logger.warning(f"Erro ao gerar imagens: {e}. Continuando sem imagens...")

            # 3. Publicar no Dev.to
            logger.info("Etapa 3/5: Publicando no Dev.to...")
            devto_result = None
            try:
                devto_result = self.devto.publish_article(
                    project_key,
                    content["blog_post"]
                )
            except Exception as e:
                logger.error(f"Erro ao publicar no Dev.to: {e}")

            # 4. Publicar no LinkedIn
            logger.info("Etapa 4/5: Publicando no LinkedIn...")
            linkedin_result = None
            try:
                linkedin_result = self.linkedin.publish_post(
                    project_key,
                    content["linkedin"],
                    images.get("linkedin")
                )
            except Exception as e:
                logger.error(f"Erro ao publicar no LinkedIn: {e}")

            # 5. Publicar no Reddit
            logger.info("Etapa 5/5: Publicando no Reddit...")
            reddit_results = []
            for reddit_post in content.get("reddit", []):
                try:
                    result = self.reddit.publish_reddit_content(project_key, reddit_post)
                    reddit_results.append(result)
                except Exception as e:
                    logger.error(f"Erro ao publicar no Reddit: {e}")

            # 6. Publicar thread no Twitter
            logger.info("Bonus: Publicando thread no Twitter...")
            twitter_result = []
            try:
                twitter_result = self.twitter.publish_twitter_content(
                    project_key,
                    content["twitter"],
                    images.get("blog_cover")
                )
            except Exception as e:
                logger.error(f"Erro ao publicar no Twitter: {e}")

            # 7. Importar no Medium
            logger.info("Bonus: Preparando importacao Medium...")
            medium_result = None
            if devto_result and "url" in devto_result:
                medium_result = self.medium.import_from_url(
                    devto_result["url"],
                    canonical_url=f"{self.config['projects'][project_key]['url']}/{content['blog_post']['slug']}"
                )

            # Salvar resultado completo
            pipeline_result = {
                "project": project_key,
                "timestamp": datetime.now().isoformat(),
                "content_generated": True,
                "images_generated": bool(images),
                "devto": devto_result,
                "linkedin": linkedin_result,
                "reddit": reddit_results,
                "twitter": twitter_result,
                "medium": medium_result
            }

            result_file = self.output_dir / f"{datetime.now().strftime('%Y-%m-%d')}_{project_key}_pipeline_result.json"
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(pipeline_result, f, ensure_ascii=False, indent=2)

            logger.info(f"=== PIPELINE CONCLUIDO: {project_key.upper()} ===")
            logger.info(f"Resultado salvo em: {result_file}")

            return pipeline_result

        except Exception as e:
            logger.error(f"Erro no pipeline {project_key}: {e}")
            raise

    def run_all_projects(self):
        """Executa o pipeline para todos os projetos"""
        logger.info("=== INICIANDO PIPELINE PARA TODOS OS PROJETOS ===")

        results = {}
        for project_key in self.config["projects"]:
            try:
                results[project_key] = self.run_project_pipeline(project_key)
            except Exception as e:
                logger.error(f"Erro ao processar {project_key}: {e}")
                results[project_key] = {"error": str(e)}

        logger.info("=== TODOS OS PROJETOS PROCESSADOS ===")
        return results

    def run_weekly(self):
        """Executa tarefas semanais"""
        logger.info("=== EXECUTANDO TAREFAS SEMANAIS ===")

        # Gerar conteudo para todos os projetos
        self.run_all_projects()

        logger.info("=== TAREFAS SEMANAIS CONCLUIDAS ===")

    def setup_schedule(self):
        """Configura o agendamento automatico"""
        # Segunda-feira as 9h: gerar conteudo da semana
        schedule.every().monday.at("09:00").do(self.run_weekly)

        # Terca e Quinta as 14h: posts no LinkedIn
        schedule.every().tuesday.at("14:00").do(self._post_to_linkedin)
        schedule.every().thursday.at("14:00").do(self._post_to_linkedin)

        # Quarta as 10h: posts no Reddit
        schedule.every().wednesday.at("10:00").do(self._post_to_reddit)

        # Segunda, Quarta, Sexta as 12h: threads no Twitter
        schedule.every().monday.at("12:00").do(self._post_to_twitter)
        schedule.every().wednesday.at("12:00").do(self._post_to_twitter)
        schedule.every().friday.at("12:00").do(self._post_to_twitter)

        logger.info("Agendamento configurado:")
        logger.info("  - Seg 09:00: Gerar conteudo semanal")
        logger.info("  - Ter 14:00: Posts LinkedIn")
        logger.info("  - Qua 10:00: Posts Reddit")
        logger.info("  - Qui 14:00: Posts LinkedIn")
        logger.info("  - Sex 12:00: Threads Twitter")

    def _post_to_linkedin(self):
        """Posta nos projetos ativos no LinkedIn"""
        for project_key in self.config["projects"]:
            try:
                # Buscar conteudo mais recente
                latest_content = self._get_latest_content(project_key)
                if latest_content:
                    self.linkedin.publish_post(
                        project_key,
                        latest_content["linkedin"]
                    )
            except Exception as e:
                logger.error(f"Erro ao postar no LinkedIn para {project_key}: {e}")

    def _post_to_reddit(self):
        """Posta nos projetos ativos no Reddit"""
        for project_key in self.config["projects"]:
            try:
                latest_content = self._get_latest_content(project_key)
                if latest_content and latest_content.get("reddit"):
                    for reddit_post in latest_content["reddit"][:1]:
                        self.reddit.publish_reddit_content(project_key, reddit_post)
            except Exception as e:
                logger.error(f"Erro ao postar no Reddit para {project_key}: {e}")

    def _post_to_twitter(self):
        """Posta threads nos projetos ativos no Twitter"""
        for project_key in self.config["projects"]:
            try:
                latest_content = self._get_latest_content(project_key)
                if latest_content:
                    self.twitter.publish_twitter_content(
                        project_key,
                        latest_content["twitter"]
                    )
            except Exception as e:
                logger.error(f"Erro ao postar no Twitter para {project_key}: {e}")

    def _get_latest_content(self, project_key):
        """Busca o conteudo mais recente para um projeto"""
        pattern = f"*_{project_key}_all_content.json"
        files = sorted(self.output_dir.glob(pattern), reverse=True)
        if files:
            with open(files[0], "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def start(self):
        """Inicia o scheduler"""
        self.setup_schedule()
        logger.info("Scheduler iniciado. Pressione Ctrl+C para parar.")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Scheduler parado pelo usuario.")


def main():
    import sys

    scheduler = SocialScheduler()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "run":
            # Executar pipeline para todos os projetos
            scheduler.run_all_projects()

        elif command == "run-single":
            # Executar para um projeto especifico
            project = sys.argv[2] if len(sys.argv) > 2 else "qa_overflow"
            scheduler.run_project_pipeline(project)

        elif command == "start":
            # Iniciar scheduler automatico
            scheduler.start()

        elif command == "status":
            # Mostrar status
            print("=== STATUS DO SISTEMA ===")
            print(f"Projetos configurados: {list(scheduler.config['projects'].keys())}")
            print(f"Modo dry_run: {scheduler.config['general']['dry_run']}")
            print(f"Output dir: {scheduler.output_dir}")

            # Verificar APIs configuradas
            for api_name, api_config in scheduler.config["apis"].items():
                if isinstance(api_config, dict):
                    has_key = any(v for k, v in api_config.items() if "key" in k and v)
                    status = "OK" if has_key else "NAO CONFIGURADO"
                    print(f"API {api_name}: {status}")

        else:
            print("Uso: python social_scheduler.py [run|run-single <projeto>|start|status]")
    else:
        print("Uso: python social_scheduler.py [run|run-single <projeto>|start|status]")
        print()
        print("Comandos:")
        print("  run           - Executa pipeline para todos os projetos")
        print("  run-single    - Executa para um projeto especifico")
        print("  start         - Inicia scheduler automatico")
        print("  status        - Mostra status do sistema")


if __name__ == "__main__":
    main()
