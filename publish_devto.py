"""
Publicar artigos no Dev.to via API REST
Funciona no GitHub Actions (Linux) e localmente
"""
import json
import glob
import sys
import os
import requests


def publish_article(api_key, content):
    """Publica um artigo no Dev.to."""
    blog = content.get("blog_post")
    if not blog:
        print("  Nenhum blog_post encontrado no JSON, pulando...")
        return None

    payload = {
        "article": {
            "title": blog["title"],
            "body_markdown": blog["body_markdown"],
            "tags": blog.get("tags", ["qa", "testing", "automation"]),
            "published": True,
            "description": blog.get("description", ""),
        }
    }

    payload["article"]["tags"] = blog.get("tags", ["qa", "testing", "automation"])[:4]

    headers = {
        "api-key": api_key,
        "Content-Type": "application/json; charset=utf-8",
    }

    resp = requests.post(
        "https://dev.to/api/articles",
        headers=headers,
        json=payload,
    )

    if resp.status_code not in (200, 201):
        print(f"  ERRO {resp.status_code}: {resp.text[:200]}")
        return None

    result = resp.json()
    print(f"  URL: {result.get('url', 'N/A')}")
    print(f"  ID: {result.get('id', 'N/A')}")
    return result


def main():
    api_key = os.environ.get("DEVTO_API_KEY")
    if not api_key:
        print("ERRO: DEVTO_API_KEY nao configurada")
        sys.exit(1)

    files = sys.argv[1:] if len(sys.argv) > 1 else glob.glob("output/*_all_content.json")

    if not files:
        print("Nenhum arquivo de conteudo encontrado")
        sys.exit(1)

    success = 0
    fail = 0

    for filepath in files:
        print(f"\nProcessando: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            content = json.load(f)

        project = content.get("project", "unknown")
        print(f"  Projeto: {project}")

        result = publish_article(api_key, content)
        if result:
            success += 1
        else:
            fail += 1

    print(f"\n{'='*50}")
    print(f"RESULTADO: {success} sucesso, {fail} falha")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
