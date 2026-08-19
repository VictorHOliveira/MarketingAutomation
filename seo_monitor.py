"""
SEO Monitor - Monitora rankings e performace de SEO
"""

import yaml
import json
import logging
import requests
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class SEOMonitor:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.output_dir = Path(self.config["paths"]["output_dir"])
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def check_page_speed(self, url):
        """Verifica velocidade de carregamento da pagina"""
        try:
            start_time = datetime.now()
            response = requests.get(url, timeout=10)
            load_time = (datetime.now() - start_time).total_seconds()

            return {
                "url": url,
                "status_code": response.status_code,
                "load_time_seconds": round(load_time, 2),
                "content_length": len(response.content),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "url": url,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def check_seo_basics(self, url):
        """Verifica elementos basicos de SEO"""
        try:
            response = requests.get(url, timeout=10)
            html = response.text

            checks = {
                "has_title": "<title>" in html.lower(),
                "has_meta_description": 'meta name="description"' in html.lower(),
                "has_og_tags": "og:" in html.lower(),
                "has_canonical": 'rel="canonical"' in html.lower(),
                "has_robots": "robots" in html.lower(),
                "has_sitemap": self._check_sitemap(url),
                "has_rss": self._check_rss(url)
            }

            score = sum(checks.values()) / len(checks) * 100

            return {
                "url": url,
                "checks": checks,
                "score": round(score, 1),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "url": url,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _check_sitemap(self, base_url):
        """Verifica se existe sitemap"""
        try:
            sitemap_url = f"{base_url}/sitemap.xml"
            response = requests.get(sitemap_url, timeout=5)
            return response.status_code == 200
        except:
            return False

    def _check_rss(self, base_url):
        """Verifica se existe feed RSS"""
        try:
            rss_url = f"{base_url}/rss.xml"
            response = requests.get(rss_url, timeout=5)
            return response.status_code == 200
        except:
            return False

    def monitor_all_projects(self):
        """Monitora todos os projetos"""
        results = {}

        for project_key, project in self.config["projects"].items():
            logger.info(f"Monitorando {project['name']}...")

            url = project["url"]
            page_speed = self.check_page_speed(url)
            seo_basics = self.check_seo_basics(url)

            results[project_key] = {
                "name": project["name"],
                "url": url,
                "page_speed": page_speed,
                "seo_basics": seo_basics
            }

        # Salvar resultado
        date_str = datetime.now().strftime("%Y-%m-%d")
        filepath = self.output_dir / f"{date_str}_seo_report.json"

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info(f"Relatorio SEO salvo em: {filepath}")
        return results

    def generate_report(self):
        """Gera relatorio de SEO"""
        results = self.monitor_all_projects()

        report_lines = [
            "# Relatorio SEO - " + datetime.now().strftime("%Y-%m-%d"),
            "",
        ]

        for project_key, data in results.items():
            report_lines.append(f"## {data['name']}")
            report_lines.append(f"URL: {data['url']}")

            if "error" not in data["page_speed"]:
                report_lines.append(f"Tempo de carregamento: {data['page_speed']['load_time_seconds']}s")
                report_lines.append(f"Status HTTP: {data['page_speed']['status_code']}")
            else:
                report_lines.append(f"Erro: {data['page_speed']['error']}")

            if "error" not in data["seo_basics"]:
                report_lines.append(f"Score SEO: {data['seo_basics']['score']}%")
                report_lines.append("Checks:")
                for check, passed in data["seo_basics"]["checks"].items():
                    status = "OK" if passed else "FALHOU"
                    report_lines.append(f"  - {check}: {status}")
            else:
                report_lines.append(f"Erro SEO: {data['seo_basics']['error']}")

            report_lines.append("")

        report = "\n".join(report_lines)

        # Salvar relatorio
        date_str = datetime.now().strftime("%Y-%m-%d")
        report_path = self.output_dir / f"{date_str}_seo_report.md"

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

        logger.info(f"Relatorio gerado: {report_path}")
        return report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    monitor = SEOMonitor()
    report = monitor.generate_report()
    print(report)
