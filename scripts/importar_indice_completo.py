"""Importa todos os registros dos sitemaps publicos, sem baixar videos.

Os sitemaps nao contem enderecos dos players nem nomes oficiais: nesses casos
o titulo e uma etiqueta derivada do URL. Detalhes ja conhecidos sao preservados.
"""
import concurrent.futures
import csv
import importlib.util
import json
import os
import re
import threading
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('catalog_reader', ROOT / 'scripts/atualizar_catalogo.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
NS = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9', 'i': 'http://www.google.com/schemas/sitemap-image/1.1'}
KINDS = {'movies': 'filme', 'tvshows': 'serie', 'episodes': 'episodio', 'seasons': 'temporada'}
lock = threading.Lock()
last_request = 0.0
CACHE = Path(os.environ.get('SALA_CACHE', str(ROOT / '.cache-indice')))

def read(url):
    global last_request
    for attempt in range(3):
        try:
            with lock:
                pause = max(0, 0.45 - (time.monotonic() - last_request))
                time.sleep(pause)
                last_request = time.monotonic()
            return reader.read(url)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** (attempt + 1))

def fetch_map(url):
    name = urlparse(url).path.strip('/')
    cached = CACHE / name
    if cached.exists() and time.time() - cached.stat().st_mtime < 3600:
        content = cached.read_text(encoding='utf-8')
    else:
        content = read(url)
        ET.fromstring(content)
        cached.write_text(content, encoding='utf-8')
    tree = ET.fromstring(content)
    kind = KINDS[re.match(r'(movies|tvshows|episodes|seasons)', name).group(1)]
    entries = []
    for node in tree.findall('s:url', NS):
        address = node.findtext('s:loc', '', NS)
        parsed = urlparse(address)
        parts = parsed.path.strip('/').split('/')
        if parsed.hostname != urlparse(reader.SOURCE).hostname or len(parts) != 2:
            continue
        slug = parts[-1]
        label = unquote(slug).replace('-', ' ').strip().capitalize()
        image = node.findtext('i:image/i:loc', '', NS)
        entries.append({'id': kind + ':' + slug, 'title': label, 'kind': kind, 'poster': image,
                        'source': address, 'servers': [], 'titleSource': 'url'})
    return entries

def atomic(path, content):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(content, encoding='utf-8')
    temp.replace(path)

def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    index = ET.fromstring(read(reader.SOURCE + 'sitemap_index.xml'))
    maps = [n.findtext('s:loc', '', NS) for n in index.findall('s:sitemap', NS)]
    maps = [url for url in maps if re.search(r'/(movies|tvshows|episodes|seasons)-sitemap\d*\.xml$', url)]
    old = json.loads((ROOT / 'catalogo.json').read_text(encoding='utf-8'))
    known = {entry['source']: entry for entry in old}
    results, failures = {}, []
    print(f'Sitemaps de conteudo encontrados: {len(maps)}', flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        jobs = {pool.submit(fetch_map, url): url for url in maps}
        for future in concurrent.futures.as_completed(jobs):
            address = jobs[future]
            try:
                records = future.result()
                results[address] = records
                print(f'{len(results) + len(failures)}/{len(maps)}: {urlparse(address).path}: {len(records)} registros', flush=True)
            except Exception as error:
                failures.append({'url': address, 'error': str(error)})
                print(f'FALHA {address}: {error}', flush=True)
    if failures:
        atomic(ROOT / 'falhas-importacao.json', json.dumps(failures, ensure_ascii=False, indent=2))
        raise SystemExit('Importacao incompleta. Arquivos anteriores preservados; execute novamente para retomar.')
    unique = {}
    for address in maps:
        for entry in results[address]:
            previous = known.get(entry['source'])
            if previous:
                entry.update(previous)
                entry['kind'] = KINDS[re.search(r'/(movies|tvshows|episodes|seasons)', address).group(1)]
                if previous.get('servers'):
                    entry.pop('titleSource', None)
            if not entry.get('servers'):
                entry['id'] = entry['kind'] + ':' + urlparse(entry['source']).path.strip('/').split('/')[-1]
            unique[entry['source']] = entry
    items = list(unique.values())
    counts = {kind: sum(item['kind'] == kind for item in items) for kind in KINDS.values()}
    report = {'sitemaps': len(maps), 'failedSitemaps': 0, 'counts': counts,
              'total': len(items), 'withPlayers': sum(bool(i.get('servers')) for i in items),
              'urlLabels': sum(i.get('titleSource') == 'url' for i in items),
              'note': 'Indice completo dos sitemaps publicos. Nao equivale a players resolvidos ou reproducao testada.'}
    atomic(ROOT / 'catalogo.json', json.dumps(items, ensure_ascii=False, separators=(',', ':')) + '\n')
    # Payload compacto: economiza nomes de campos repetidos e objetos no carregamento.
    groups = {kind: [] for kind in KINDS.values()}
    for item in items:
        groups[item['kind']].append([item['id'], item['title'], item['kind'], item['poster'], item['source'], item.get('servers', []), item.get('titleSource', '')])
    data_dir = ROOT / 'dados'
    data_dir.mkdir(exist_ok=True)
    for kind, rows in groups.items():
        if kind != 'filme':
            payload = json.dumps(rows, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
            atomic(data_dir / (kind + '.js'), 'window.SALA_RECEBER(' + json.dumps(kind) + ',' + payload + ');\n')
    payload = json.dumps(groups['filme'], ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    atomic(ROOT / 'catalogo.js', 'window.CATALOGO_RESUMO=' + json.dumps(counts) + ';\nwindow.CATALOGO_COMPACTO=' + payload + ';\n')
    atomic(ROOT / 'cobertura.json', json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    with (ROOT / 'servidores.csv').open('w', encoding='utf-8-sig', newline='') as out:
        writer = csv.writer(out)
        writer.writerow(['Filme', 'Servidor', 'Endereco', 'Origem'])
        for item in items:
            for server in item.get('servers', []):
                writer.writerow([item['title'], server['name'], server['url'], item['source']])
    print(json.dumps(report, ensure_ascii=False), flush=True)

if __name__ == '__main__':
    main()
