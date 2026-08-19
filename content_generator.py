"""
Gerador de Conteudo via IA
Gera artigos, posts e threads para todos os projetos usando OpenAI
"""

import yaml
import json
import os
import logging
from datetime import datetime
from pathlib import Path
from openai import OpenAI

logger = logging.getLogger(__name__)


class ContentGenerator:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.client = OpenAI(api_key=self.config["apis"]["openai"]["api_key"])
        self.model = self.config["apis"]["openai"]["model"]
        self.output_dir = Path(self.config["paths"]["output_dir"])
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_blog_post(self, project_key, topic=None):
        """Gera um post completo para o blog"""
        project = self.config["projects"][project_key]
        content_config = self.config["content_generation"][project_key]

        if not topic:
            topic = self._suggest_topic(project_key)

        prompt = f"""Voce e um especialista em marketing de conteudo tecnico.
        Escreva um artigo completo para o blog '{project['name']}'.

        TEMA: {topic}
        PUBLICO: {project['target_audience']}
        TOM: {content_config['tone']}
        ESTILO: {content_config['style']}
        TAMANHO: {content_config['word_count']} palavras
        IDIOMA: Portugues do Brasil

        RETORNE NO SEGUINTE FORMATO JSON:
        {{
            "title": "Titulo otimizado para SEO (max 60 caracteres)",
            "description": "Meta description (120-155 caracteres)",
            "slug": "url-do-post",
            "tags": ["tag1", "tag2", "tag3"],
            "body_markdown": "Conteudo completo em Markdown",
            "cover_image_prompt": "Prompt para gerar imagem de capa",
            "excerpt": "Resumo de 2-3 frases"
        }}

        IMPORTANTE:
        - Use heading hierarchy (##, ###)
        - Inclua exemplos praticos de codigo se aplicavel
        - O titulo deve conter palavras-chave de SEO
        - Escreva de forma clara e objetiva
        - Use emojis moderadamente nos subtitulos
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Voce e um redator tecnico especializado em marketing de conteudo. Responda sempre em JSON valido."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=self.config["apis"]["openai"]["max_tokens"],
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        content = json.loads(response.choices[0].message.content)

        # Salvar no output
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date_str}_{project_key}_{content['slug']}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=2)

        logger.info(f"Blog post gerado: {filepath}")
        return content

    def generate_linkedin_post(self, project_key, blog_title=None):
        """Gera um post para LinkedIn"""
        project = self.config["projects"][project_key]

        prompt = f"""Gere um post profissional para LinkedIn sobre o projeto '{project['name']}'.

        DESCRIÇÃO: {project['description']}
        PUBLICO: {project['target_audience']}
        HASHTAGS: {', '.join(project.get('linkedin_hashtags', []))}

        CONTEXTO: {'Post sobre o artigo: ' + blog_title if blog_title else 'Post sobre o projeto'}

        RETORNE NO SEGUINTE FORMATO JSON:
        {{
            "text": "Texto do post LinkedIn (max 1300 caracteres, com hashtags no final)",
            "image_prompt": "Prompt para gerar imagem complementar"
        }}

        REGRAS:
        - Comece com um hook forte na primeira linha
        - Use paragrafos curtos (1-2 frases)
        - Inclua emojis relevantes
        - Termine com call-to-action
        - Hashtags no final (max 5)
        - Tom profissional mas acessivel
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Voce e um especialista em marketing B2B no LinkedIn. Responda em JSON valido."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

    def generate_twitter_thread(self, project_key, blog_title=None, blog_url=None):
        """Gera uma thread para Twitter/X"""
        project = self.config["projects"][project_key]

        prompt = f"""Gere uma thread para Twitter/X sobre '{project['name']}'.

        DESCRIÇÃO: {project['description']}
        CONTEXTO: {blog_title or 'Visao geral do projeto'}
        URL: {blog_url or project['url']}

        RETORNE NO SEGUINTE FORMATO JSON:
        {{
            "tweets": [
                "Tweet 1 - Hook forte (max 280 chars)",
                "Tweet 2 - Conteudo (max 280 chars)",
                "Tweet 3 - Mais detalhes (max 280 chars)",
                "Tweet 4 - CTA + link (max 280 chars)"
            ]
        }}

        REGRAS:
        - Cada tweet maximo 280 caracteres
        - Primeiro tweet deve ser um hook atrativo
        - Ultimo tweet sempre com link
        - Use emojis com moderacao
        - Tom tecnico mas acessivel
        - Maximo 4 tweets por thread
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Voce e um especialista em Twitter/X para tech. Responda em JSON valido."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

    def generate_reddit_post(self, project_key, subreddit, blog_title=None):
        """Gera um post para Reddit"""
        project = self.config["projects"][project_key]

        prompt = f"""Gere um post para o subreddit r/{subreddit} sobre '{project['name']}'.

        DESCRIÇÃO: {project['description']}
        SUBREDDIT: r/{subreddit}
        CONTEXTO: {blog_title or 'Apresentacao do projeto'}

        RETORNE NO SEGUINTE FORMATO JSON:
        {{
            "title": "Titulo do post (max 300 chars, sem clickbait)",
            "body": "Corpo do post em Markdown (max 4000 chars)",
            "flair": "Flair sugerida (se aplicavel)"
        }}

        REGRAS:
        - titulo informativo, sem clickbait
        - corpo com valor real para a comunidade
        - Nao ser spam - oferecer valor primeiro
        - Incluir contexto e motivacao
        - Se for link, incluir resumo no post
        - Tom natural, como um membro da comunidade
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Voce e um membro ativo de comunidades Reddit de tech. Responda em JSON valido."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

    def generate_medium_import(self, project_key, blog_content):
        """Gera versao adaptada para Medium"""
        prompt = f"""Adapte o seguinte artigo para publicacao no Medium.
        O artigo original e do blog '{self.config['projects'][project_key]['name']}'.

        ARTIGO ORIGINAL:
        Titulo: {blog_content.get('title', '')}
        Conteudo: {blog_content.get('body_markdown', '')[:2000]}

        RETORNE NO SEGUINTE FORMATO JSON:
        {{
            "title": "Titulo adaptado para Medium",
            "body_markdown": "Conteudo adaptado em Markdown",
            "tags": ["tag1", "tag2", "tag3"],
            "canonical_url": "URL do artigo original"
        }}

        ADAPTACOES:
        - Mantenha o conteudo principal
        - Ajuste o titulo para o estilo Medium
        - Adapte eventualmente para publico Medium (mais diversificado)
        - Mantenha canonical URL para SEO
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Voce e um editor do Medium especializado em tech. Responda em JSON valido."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=self.config["apis"]["openai"]["max_tokens"],
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

    def _suggest_topic(self, project_key):
        """Sugere um topico baseado em trending topics"""
        project = self.config["projects"][project_key]

        prompt = f"""Sugira 1 topico relevante e trendy para o blog '{project['name']}'.
        PUBLICO: {project['target_audience']}
        CATEGORIAS: {', '.join(project.get('categories', []))}

        O topico deve:
        - Ser relevante para o publico
        - Ter potencial de SEO (pessoas buscam por isso)
        - Estar em alta no momento
        - Ser pratico e util

        RETORNE APENAS o titulo do topico, sem aspas.
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Voce e um estrategista de conteudo tech. Responda apenas com o titulo."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.8
        )

        return response.choices[0].message.content.strip().strip('"')

    def generate_all_content(self, project_key):
        """Gera todo o conteudo para um projeto de uma vez"""
        logger.info(f"Gerando conteudo completo para {project_key}...")

        # 1. Blog post
        blog_post = self.generate_blog_post(project_key)

        # 2. LinkedIn post
        linkedin = self.generate_linkedin_post(project_key, blog_post["title"])

        # 3. Twitter thread
        twitter = self.generate_twitter_thread(
            project_key,
            blog_post["title"],
            f"{self.config['projects'][project_key]['url']}/{blog_post['slug']}"
        )

        # 4. Reddit posts (para os subreddits principais)
        subreddits = self.config["social_channels"]["reddit_subreddits"].get(project_key, [])
        reddit_posts = []
        for sub in subreddits[:2]:  # Max 2 subreddits
            reddit_post = self.generate_reddit_post(project_key, sub, blog_post["title"])
            reddit_posts.append({"subreddit": sub, **reddit_post})

        # 5. Medium import
        medium = self.generate_medium_import(project_key, blog_post)

        # Salvar tudo junto
        date_str = datetime.now().strftime("%Y-%m-%d")
        all_content = {
            "project": project_key,
            "date": date_str,
            "blog_post": blog_post,
            "linkedin": linkedin,
            "twitter": twitter,
            "reddit": reddit_posts,
            "medium": medium
        }

        filepath = self.output_dir / f"{date_str}_{project_key}_all_content.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(all_content, f, ensure_ascii=False, indent=2)

        logger.info(f"Todo o conteudo salvo em: {filepath}")
        return all_content


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    project = sys.argv[1] if len(sys.argv) > 1 else "qa_overflow"

    gen = ContentGenerator()
    result = gen.generate_all_content(project)
    print(json.dumps(result, ensure_ascii=False, indent=2))
