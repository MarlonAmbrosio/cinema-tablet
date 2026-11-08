"""Importa metadados e enderecos de embeds presentes no HTML publico.

Nao baixa videos, nao autentica usuarios e nao resolve desafios ou protecoes.
"""
import argparse
import concurrent.futures
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

SOURCE = 'https://filmesamadoresgratis.com/'
SERVERS = {
    'superflixapi.boats': 'Servidor 1',
    'embedplayapi.top': 'Servidor 2',
    'embed.embedplayer.site': 'Servidor 3',
    'vidsrc.sh': 'Servidor 4',
    'embed69.org': 'Servidor 5',
    'cinesrc.st': 'Servidor 6',
}

class Page(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.links, self.frames, self.meta = [], [], {}
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a' and a.get('href'):
            self.links.append(a['href'])
        if tag == 'iframe' and a.get('src'):
            self.frames.append(a['src'])
        if tag == 'meta' and a.get('content'):
            self.meta[a.get('property', a.get('name', ''))] = a['content']

def read(url):
    request = Request(url, headers={'User-Agent': 'CinemaTablet/1.0 (public HTML catalog reader)'})
    with urlopen(request, timeout=30) as response:
        if urlparse(response.url).hostname != urlparse(url).hostname:
            raise ValueError('Redirecionamento para outro dominio; importacao interrompida')
        return response.read(3_000_000).decode('utf-8', errors='replace')

def movie(url):
    page = Page(read(url))
    title = page.meta.get('og:title', '').strip()
    title = re.sub(r'\s*[-|]\s*Pobreflix.*$', '', title, flags=re.I)
    title = re.sub(r'^Assistir\s+', '', title, flags=re.I)
    title = re.sub(r'\s+Online(?:\s+Gr[áa]tis)?$', '', title, flags=re.I)
    if not title:
        raise ValueError('Titulo ausente')
    servers, seen = [], set()
    for raw in page.frames + page.links:
        address = urljoin(url, raw)
        parsed = urlparse(address)
        if parsed.scheme == 'https' and parsed.hostname in SERVERS and address not in seen:
            seen.add(address)
            servers.append({'name': SERVERS[parsed.hostname], 'url': address})
    image = page.meta.get('og:image', '')
    if urlparse(image).scheme != 'https':
        image = ''
    return {'id': urlparse(url).path.strip('/').split('/')[-1], 'title': title,
            'poster': image, 'source': url, 'servers': servers}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limite', type=int, default=16)
    args = parser.parse_args()
    home = Page(read(SOURCE))
    links = []
    for raw in home.links:
        address = urljoin(SOURCE, raw)
        parsed = urlparse(address)
        if (parsed.hostname == urlparse(SOURCE).hostname and parsed.path.startswith('/filme/')
                and len(parsed.path.strip('/').split('/')) == 2 and not parsed.query
                and address not in links):
            links.append(address)
    links = links[:max(1, min(args.limite, 100))]
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        jobs = {pool.submit(movie, url): url for url in links}
        for task in concurrent.futures.as_completed(jobs):
            url = jobs[task]
            try:
                item = task.result()
                results[url] = item
                print(f"OK: {item['title']} ({len(item['servers'])} players publicos)")
            except Exception as error:
                print(f'Falha: {url}: {error}')
    items = [results[url] for url in links if url in results]
    if not items:
        raise SystemExit('Nenhum titulo importado. Catalogo anterior preservado.')
    root = Path(__file__).resolve().parents[1]
    payload = json.dumps(items, ensure_ascii=False, indent=2).replace('<', '\\u003c')
    (root / 'catalogo.json').write_text(payload + '\n', encoding='utf-8')
    (root / 'catalogo.js').write_text('window.CATALOGO = ' + payload + ';\n', encoding='utf-8')
    print(f'Catalogo salvo: {len(items)} titulos. Nenhum video foi baixado.')

if __name__ == '__main__':
    main()
