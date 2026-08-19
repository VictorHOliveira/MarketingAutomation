"""
Gerar conteudo via OpenAI e publicar automaticamente
Usado no GitHub Actions para publicacao semanal (Seg/Qua/Sex)
"""
import json
import os
import sys
import subprocess
import yaml
from datetime import datetime
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("ERRO: openai nao instalado. Rode: pip install openai")
    sys.exit(1)


def load_config(config_path="config.github.yaml"):
    """Carrega configuracao lendo API key de variavel de ambiente."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERRO: OPENAI_API_KEY nao configurada como secret")
        sys.exit(1)

    config["apis"]["openai"]["api_key"] = api_key
    return config


def suggest_topic(client, model, project):
    """Usa IA para sugerir um topico trending."""
    prompt = f"""Sugira 1 topico relevante e trendy para o blog '{project['name']}'.
    PUBLICO: {project['target_audience']}
    CATEGORIAS: {', '.join(project.get('categories', []))}

    O topico deve:
    - Ser relevante para o publico de QA e automacao de testes
    - Ter potencial de SEO (pessoas buscam por isso)
    - Estar em alta no momento em 2026
    - Ser pratico e util com exemplos reais

    RETORNE APENAS o titulo do topico, sem aspas."""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Voce e um estrategista de conteudo tech. Responda apenas com o titulo."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100,
        temperature=0.8
    )
    return response.choices[0].message.content.strip().strip('"')


def generate_blog_post(client, model, project, content_config, topic):
    """Gera um artigo completo para o blog."""
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
    - Minimo 1500 palavras de conteudo"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Voce e um redator tecnico especializado em marketing de conteudo. Responda sempre em JSON valido."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2000,
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)


def generate_linkedin_post(client, model, project, blog_title):
    """Gera um post para LinkedIn."""
    prompt = f"""Gere um post profissional para LinkedIn sobre o projeto '{project['name']}'.

    CONTEXTO: Post sobre o artigo '{blog_title}'
    PUBLICO: {project['target_audience']}
    HASHTAGS: {', '.join(project.get('linkedin_hashtags', []))}

    RETORNE NO SEGUINTE FORMATO JSON:
    {{
        "text": "Texto do post LinkedIn (max 1300 caracteres, com hashtags no final)"
    }}

    REGRAS:
    - Comece com um hook forte na primeira linha
    - Use paragrafos curtos (1-2 frases)
    - Inclua emojis relevantes
    - Termine com call-to-action
    - Hashtags no final (max 5)
    - Tom profissional mas acessivel"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Voce e um especialista em marketing B2B no LinkedIn. Responda em JSON valido."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=800,
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)


def generate_devto_content(client, model, project, blog_post):
    """Gera overrides especificos para Dev.to."""
    tags = project.get("tags_devto", ["qa", "testing", "automation"])[:4]
    slug = blog_post.get("slug", "")
    canonical_url = f"https://qaoverflow.com/post/{slug}/"

    return {
        "tags": tags,
        "canonical_url": canonical_url
    }


def main():
    print("=" * 60)
    print("GERACAO E PUBLICACAO AUTOMATICA DE CONTEUDO")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    project_key = sys.argv[1] if len(sys.argv) > 1 else "qa_overflow"
    dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"

    config = load_config()

    if project_key not in config["projects"]:
        print(f"ERRO: Projeto '{project_key}' nao encontrado")
        sys.exit(1)

    project = config["projects"][project_key]
    content_config = config["content_generation"].get(project_key, {})

    print(f"\nProjeto: {project['name']}")
    print(f"Dry Run: {dry_run}")

    client = OpenAI(api_key=config["apis"]["openai"]["api_key"])
    model = config["apis"]["openai"]["model"]

    # 1. Sugerir topico
    print("\n[1/4] Sugerindo topico...")
    topic = suggest_topic(client, model, project)
    print(f"  Topico: {topic}")

    # 2. Gerar blog post
    print("\n[2/4] Gerando blog post...")
    blog_post = generate_blog_post(client, model, project, content_config, topic)
    print(f"  Titulo: {blog_post.get('title', 'N/A')}")
    print(f"  Slug: {blog_post.get('slug', 'N/A')}")

    # 3. Gerar LinkedIn
    print("\n[3/4] Gerando post LinkedIn...")
    linkedin = generate_linkedin_post(client, model, project, blog_post.get("title", ""))
    print(f"  Texto: {linkedin.get('text', '')[:100]}...")

    # 4. Gerar Dev.to overrides
    print("\n[4/4] Preparando Dev.to...")
    devto = generate_devto_content(client, model, project, blog_post)

    # Montar JSON final
    all_content = {
        "project": project_key,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "blog_post": blog_post,
        "linkedin": linkedin,
        "devto": devto
    }

    # Salvar
    output_dir = Path(config["paths"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}_{project_key}_{blog_post.get('slug', 'unknown')}.json"
    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(all_content, f, ensure_ascii=False, indent=2)

    print(f"\n  Conteudo salvo: {filepath}")

    if dry_run:
        print("\nDRY RUN - Nenhuma publicacao realizada")
        print(json.dumps(all_content, ensure_ascii=False, indent=2)[:2000])
        return

    # Publicar
    print("\n" + "=" * 60)
    print("PUBLICANDO...")
    print("=" * 60)

    script_dir = Path(__file__).parent
    json_path = str(filepath)

    # Publicar no site (so para qa_overflow)
    if project_key == "qa_overflow":
        print("\n[SITE] Publicando no QA Overflow...")
        site_repo = os.environ.get("QA_OVERFLOW_REPO", "qaoverflow-site")
        result = subprocess.run(
            ["python", str(script_dir / "publish_site.py"), json_path, site_repo],
            capture_output=True, text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(f"  ERRO no site: {result.stderr}")

        # Aguardar deploy
        print("\n[WAIT] Aguardando deploy do site (30s)...")
        import time
        time.sleep(30)

    # Publicar no Dev.to
    print("\n[DEV.TO] Publicando no Dev.to...")
    result = subprocess.run(
        ["python", str(script_dir / "publish_devto.py"), json_path],
        capture_output=True, text=True,
        env={**os.environ, "DEVTO_API_KEY": os.environ.get("DEVTO_API_KEY", "")}
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"  ERRO no Dev.to: {result.stderr}")

    # Publicar no LinkedIn
    print("\n[LINKEDIN] Publicando no LinkedIn...")
    result = subprocess.run(
        ["python", str(script_dir / "publish_linkedin.py"), json_path],
        capture_output=True, text=True,
        env={**os.environ}
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"  ERRO no LinkedIn: {result.stderr}")

    print("\n" + "=" * 60)
    print("PUBLICACAO CONCLUIDA")
    print("=" * 60)


if __name__ == "__main__":
    main()
