"""
Repost automatico de posts antigos do QA Overflow
Seleciona um post aleatorio com mais de 30 dias e gera conteudo para Dev.to e LinkedIn
Usado no GitHub Actions para publicacao semanal (Ter/Qui)
"""
import json
import os
import sys
import random
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("ERRO: openai nao instalado. Rode: pip install openai")
    sys.exit(1)

import yaml


HISTORY_FILE = "repost_history.json"


def load_config(config_path="config.github.yaml"):
    """Carrega configuracao lendo API key de variavel de ambiente."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERRO: OPENAI_API_KEY nao configurada")
        sys.exit(1)

    config["apis"]["openai"]["api_key"] = api_key
    return config


def load_history():
    """Carrega historico de reposts."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"reposted": []}


def save_history(history):
    """Salva historico de reposts."""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def load_posts(site_repo_path):
    """Carrega posts do site QA Overflow."""
    posts_file = os.path.join(site_repo_path, "src", "_data", "posts.json")
    if not os.path.exists(posts_file):
        print(f"ERRO: {posts_file} nao encontrado")
        sys.exit(1)

    with open(posts_file, "r", encoding="utf-8") as f:
        return json.load(f)


def select_post_for_repost(posts, history):
    """Seleciona um post aleatorio com mais de 30 dias que nao foi repostado."""
    cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    reposted_slugs = {r["slug"] for r in history.get("reposted", [])}

    candidates = [
        p for p in posts
        if p.get("status") == "published"
        and p.get("datePublished", "9999") < cutoff_date
        and p.get("slug") not in reposted_slugs
        and p.get("slug")  #Tem slug
    ]

    if not candidates:
        print("Nenhum post disponivel para repost")
        return None

    return random.choice(candidates)


def generate_repost_content(client, model, post):
    """Gera conteudo de repost para Dev.to e LinkedIn."""
    title = post.get("title", "")
    summary = post.get("summary", post.get("description", ""))
    slug = post.get("slug", "")
    tags = post.get("tags", ["qa", "testing"])[:4]
    canonical_url = f"https://qaoverflow.com/post/{slug}/"

    # Gerar Dev.to
    prompt_devto = f"""Reescreva um post antigo como um repost para Dev.to.
    O post original e sobre QA e automacao de testes.

    TITULO ORIGINAL: {title}
    RESUMO: {summary}

    RETORNE NO SEGUINTE FORMATO JSON:
    {{
        "title": "Revisitando: {title} (ou titulo atrativo similar)",
        "body_markdown": " corpo do artigo em Markdown com 500-800 palavras, reescrevendo os pontos principais do artigo original. Inclua um link para o artigo completo no final.",
        "description": "Descricao curta (120-150 chars)"
    }}

    REGRAS:
    - Titulo deve comecar com 'Revisitando:' ou ser atrativo sobre o tema
    - Reescreva os pontos principais, nao copie
    - Inclua link para o artigo original no final
    - Tom tecnico e util
    - Maximo 800 palavras"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Voce e um redator tecnico. Responda em JSON valido."},
            {"role": "user", "content": prompt_devto}
        ],
        max_tokens=1500,
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    devto_content = json.loads(response.choices[0].message.content)

    # Gerar LinkedIn
    prompt_linkedin = f"""Gere um post de repost para LinkedIn sobre um artigo antigo que esta sendo reintroado.

    TITULO: {title}
    RESUMO: {summary}
    URL: https://qaoverflow.com/post/{slug}/

    RETORNE NO SEGUINTE FORMATO JSON:
    {{
        "text": "Texto do post LinkedIn (max 1300 caracteres, com hashtags no final)"
    }}

    REGRAS:
    - Comece com 'Revisiting' ou 'Recomendado' ou ' vale reler'
    - Mencione que e um repost de um artigo popular
    - Inclua o link para o artigo
    - Hashtags no final (max 5)
    - Tom profissional"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Voce e um especialista em LinkedIn. Responda em JSON valido."},
            {"role": "user", "content": prompt_linkedin}
        ],
        max_tokens=800,
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    linkedin_content = json.loads(response.choices[0].message.content)

    return {
        "blog_post": {
            "title": devto_content.get("title", f"Revisitando: {title}"),
            "slug": slug,
            "body_markdown": devto_content.get("body_markdown", ""),
            "description": devto_content.get("description", summary[:150]),
            "tags": tags,
        },
        "devto": {
            "tags": tags,
            "canonical_url": canonical_url,
        },
        "linkedin": linkedin_content,
    }


def main():
    print("=" * 60)
    print("REPOST AUTOMATICO - POSTS ANTIGOS")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"
    site_repo = os.environ.get("QA_OVERFLOW_REPO", "qaoverflow-site")

    config = load_config()
    client = OpenAI(api_key=config["apis"]["openai"]["api_key"])
    model = config["apis"]["openai"]["model"]

    # Carregar posts e historico
    print(f"\nLendo posts de {site_repo}...")
    posts = load_posts(site_repo)
    print(f"  Total de posts: {len(posts)}")

    history = load_history()
    print(f"  Posts ja repostados: {len(history.get('reposted', []))}")

    # Selecionar post
    print("\nSelecionando post para repost...")
    post = select_post_for_repost(posts, history)
    if not post:
        print("Nenhum post disponivel. Saindo.")
        sys.exit(0)

    print(f"  Post selecionado: {post.get('title')}")
    print(f"  Slug: {post.get('slug')}")
    print(f"  Data: {post.get('datePublished')}")

    # Gerar conteudo
    print("\nGerando conteudo de repost via OpenAI...")
    repost_content = generate_repost_content(client, model, post)
    print(f"  Titulo Dev.to: {repost_content['blog_post']['title']}")

    # Salvar JSON
    output_dir = Path(config["paths"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}_repost_{post.get('slug', 'unknown')}.json"
    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(repost_content, f, ensure_ascii=False, indent=2)

    print(f"\n  Conteudo salvo: {filepath}")

    if dry_run:
        print("\nDRY RUN - Nenhuma publicacao realizada")
        print(json.dumps(repost_content, ensure_ascii=False, indent=2)[:2000])
        return

    # Publicar
    print("\n" + "=" * 60)
    print("PUBLICANDO REPOST...")
    print("=" * 60)

    script_dir = Path(__file__).parent
    json_path = str(filepath)

    # NÃO publicar no site - so LinkedIn e Dev.to

    # Publicar no Dev.to
    print("\n[DEV.TO] Publicando repost no Dev.to...")
    result = subprocess.run(
        ["python", str(script_dir / "publish_devto.py"), json_path],
        capture_output=True, text=True,
        env={**os.environ, "DEVTO_API_KEY": os.environ.get("DEVTO_API_KEY", "")}
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"  ERRO no Dev.to: {result.stderr}")

    # Publicar no LinkedIn
    print("\n[LINKEDIN] Publicando repost no LinkedIn...")
    result = subprocess.run(
        ["python", str(script_dir / "publish_linkedin.py"), json_path],
        capture_output=True, text=True,
        env={**os.environ}
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"  ERRO no LinkedIn: {result.stderr}")

    # Atualizar historico
    history["reposted"].append({
        "slug": post.get("slug"),
        "date": date_str,
        "platforms": ["devto", "linkedin"]
    })
    save_history(history)
    print(f"\n  Historico atualizado: {len(history['reposted'])} posts repostados")

    print("\n" + "=" * 60)
    print("REPOST CONCLUIDO")
    print("=" * 60)


if __name__ == "__main__":
    main()
