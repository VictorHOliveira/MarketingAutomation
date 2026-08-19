"""
Publicar posts no LinkedIn via API REST
Funciona no GitHub Actions (Linux) e localmente
"""
import json
import glob
import sys
import os
import requests


def publish_post(access_token, person_urn, content):
    """Publica um post no LinkedIn."""
    linkedin = content.get("linkedin")
    if not linkedin or not linkedin.get("text"):
        print("  Nenhum conteudo linkedin encontrado, pulando...")
        return None

    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": linkedin["text"]},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    resp = requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        headers=headers,
        json=payload,
    )

    if resp.status_code not in (200, 201):
        print(f"  ERRO {resp.status_code}: {resp.text[:200]}")
        return None

    result = resp.json()
    print(f"  ID: {result.get('id', 'N/A')}")
    return result


def main():
    access_token = os.environ.get("LINKEDIN_ACCESS_TOKEN")
    person_urn = os.environ.get("LINKEDIN_PERSON_URN")

    if not access_token or not person_urn:
        print("ERRO: LINKEDIN_ACCESS_TOKEN e LINKEDIN_PERSON_URN nao configuradas")
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

        result = publish_post(access_token, person_urn, content)
        if result:
            success += 1
        else:
            fail += 1

    print(f"\n{'='*50}")
    print(f"RESULTADO: {success} sucesso, {fail} falha")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
