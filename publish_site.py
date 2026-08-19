"""
Publicar artigo no site QA Overflow (Eleventy)
Adiciona o post ao posts.json e faz commit/push para deploy automático
"""
import json
import subprocess
import sys
import os
import re
from datetime import datetime


def markdown_to_html(md):
    """Conversão simples de Markdown para HTML."""
    html = md

    # Headers
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

    # Bold e italic
    html = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', html)
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

    # Code blocks
    html = re.sub(r'```(\w+)?\n(.*?)```', lambda m: f'<pre><code class="language-{m.group(1) or ""}">{m.group(2)}</code></pre>', html, flags=re.DOTALL)

    # Inline code
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)

    # Links
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)

    # Lists
    lines = html.split('\n')
    result = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('- '):
            if not in_list:
                result.append('<ul>')
                in_list = True
            result.append(f'<li>{stripped[2:]}</li>')
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            result.append(line)
    if in_list:
        result.append('</ul>')
    html = '\n'.join(result)

    # Paragraphs
    paragraphs = html.split('\n\n')
    processed = []
    for p in paragraphs:
        p = p.strip()
        if p and not p.startswith('<'):
            p = f'<p>{p}</p>'
        processed.append(p)
    html = '\n'.join(processed)

    return html


def estimate_read_time(content):
    """Estima tempo de leitura em minutos."""
    words = len(content.split())
    minutes = max(1, words // 200)
    return f"{minutes} min"


def publish_site(content_file, site_repo_path):
    """Publica artigo no site QA Overflow."""
    with open(content_file, 'r', encoding='utf-8') as f:
        content = json.load(f)

    blog = content.get('blog_post')
    if not blog:
        print("ERRO: blog_post não encontrado no JSON")
        return False

    posts_file = os.path.join(site_repo_path, 'src', '_data', 'posts.json')
    with open(posts_file, 'r', encoding='utf-8') as f:
        posts = json.load(f)

    slug = blog['slug']
    existing = [p for p in posts if p.get('slug') == slug]
    if existing:
        print(f"Artigo com slug '{slug}' já existe no site. Pulando...")
        return True

    today = datetime.now().strftime('%Y-%m-%d')
    dated = datetime.now().strftime('%B %d, %Y %I:%M %p')

    body_md = blog.get('body_markdown', '')
    content_html = markdown_to_html(body_md)

    tags = blog.get('tags', ['qa', 'testing', 'automation'])

    new_post = {
        'author': 'Victor Oliveira',
        'title': blog['title'],
        'tags': tags,
        'category': 'boas-praticas',
        'body': blog.get('description', blog['title']),
        'datePublished': today,
        'dateModified': today,
        'dated': dated,
        'coverImage': blog.get('cover_image_prompt', ''),
        'readTime': estimate_read_time(body_md),
        'slug': slug,
        'categorySlug': 'boas-praticas',
        'status': 'published',
        'summary': blog.get('description', ''),
        'description': blog.get('description', ''),
        'content': content_html
    }

    posts.append(new_post)

    with open(posts_file, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=4)

    print(f"Post adicionado: {slug}")

    subprocess.run(['git', 'add', 'src/_data/posts.json'], cwd=site_repo_path, check=True)
    subprocess.run(['git', 'commit', '-m', f'Add post: {blog["title"]}'], cwd=site_repo_path, check=True)

    pat = os.environ.get('QA_OVERFLOW_PAT')
    if pat:
        remote_url = f'https://{pat}@github.com/VictorHOliveira/QA_OverFlow.git'
    else:
        remote_url = 'origin'

    result = subprocess.run(
        ['git', 'push', remote_url, 'main'],
        cwd=site_repo_path,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"ERRO no push: {result.stderr}")
        return False

    print(f"Deploy iniciado! URL: https://qaoverflow.com/{slug}")
    return True


def main():
    if len(sys.argv) < 3:
        print("Uso: python publish_site.py <content.json> <site_repo_path>")
        sys.exit(1)

    content_file = sys.argv[1]
    site_repo_path = sys.argv[2]

    if not os.path.exists(content_file):
        print(f"ERRO: Arquivo {content_file} não encontrado")
        sys.exit(1)

    if not os.path.exists(site_repo_path):
        print(f"ERRO: Repositório do site não encontrado em {site_repo_path}")
        sys.exit(1)

    success = publish_site(content_file, site_repo_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
