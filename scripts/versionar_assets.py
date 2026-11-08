"""Atualiza os URLs dos scripts quando o conteudo muda, evitando cache antigo."""
import hashlib
import re
from pathlib import Path

def main(root=None):
    root = root or Path(__file__).resolve().parents[1]
    index = root / 'index.html'
    if not index.exists(): return
    html = index.read_text(encoding='utf-8')
    for name in ['app.js','players.js','status-players.js']:
        asset = root / name
        if not asset.exists(): continue
        digest = hashlib.sha256(asset.read_bytes()).hexdigest()[:12]
        html = re.sub(r'src="' + re.escape(name) + r'(?:\?[^"<>]*)?"', 'src="' + name + '?v=' + digest + '"', html)
    index.write_text(html, encoding='utf-8')

if __name__ == '__main__': main()
