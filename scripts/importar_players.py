"""Importacao incremental de HTML publico; interrompe ao receber bloqueios.

Nao baixa videos, nao contorna Cloudflare, DRM, autenticacao ou restricoes.
--limite 100 processa ate 100 paginas; --todos percorre o indice ate concluir
ou encontrar bloqueio. Execute novamente para retomar. Nao publica sozinho.
"""
import argparse
import json
import time
from collections import Counter
from datetime import datetime, timezone
from itertools import zip_longest
from pathlib import Path
from urllib.error import HTTPError
from atualizar_catalogo import movie, read

ROOT = Path(__file__).resolve().parents[1]

def atomic(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(value, encoding='utf-8')
    temp.replace(path)

def load_overlay():
    path = ROOT / 'players.js'
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8').split('=', 1)[1].strip().rstrip(';'))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limite', type=int, default=100)
    parser.add_argument('--todos', action='store_true')
    parser.add_argument('--tipos', nargs='+', choices=['filme','serie','episodio','temporada'], default=['filme','serie','episodio'])
    args = parser.parse_args()
    state_path = ROOT / '.progresso-players.json'
    state = json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {}
    overlay = load_overlay()
    items = json.loads((ROOT / 'catalogo.json').read_text(encoding='utf-8'))
    groups = [[item for item in items if item['kind'] == kind and item['id'] not in state and item['id'] not in overlay and not item.get('servers')] for kind in args.tipos]
    # Alterna filmes, series e episodios, evitando esgotar um tipo antes de outro.
    pending = (item for row in zip_longest(*groups) for item in row if item is not None)
    processed, blocked, failures = 0, None, []
    for item in pending:
        if not args.todos and processed >= max(1, args.limite):
            break
        try:
            html = read(item['source'])
            if any(marker in html.lower() for marker in ['cf-chl-', 'just a moment', 'executando verificação de segurança']):
                blocked = {'source':item['source'], 'reason':'Verificacao anti-bot; nenhuma tentativa de contorno.'}
                break
            result = movie(item['source'], html)
            result['id'], result['kind'] = item['id'], item['kind']
            if result['servers']:
                overlay[item['id']] = result
            state[item['id']] = {'status':'importado' if result['servers'] else 'sem_player_no_html', 'source':item['source']}
            processed += 1
            print(item['id'], len(result['servers']), flush=True)
        except HTTPError as error:
            if error.code in (401, 403, 429):
                blocked = {'source':item['source'], 'reason':'HTTP ' + str(error.code) + '; importacao interrompida.'}
                break
            failures.append({'source':item['source'], 'error':str(error)})
            processed += 1
        except Exception as error:
            failures.append({'source':item['source'], 'error':str(error)})
            processed += 1
            if len(failures) >= 5:
                blocked = {'reason':'Cinco falhas nesta execucao; interrompido para evitar insistencia.'}
                break
        atomic(state_path, json.dumps(state, ensure_ascii=False))
        atomic(ROOT / 'players.js', 'window.SALA_PLAYERS=' + json.dumps(overlay, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c') + ';\n')
        time.sleep(1)
    report = {'checkedAt':datetime.now(timezone.utc).isoformat(), 'processedThisRun':processed,
              'overlayWithPlayers':len(overlay), 'overlayByKind':dict(Counter(i.get('kind','filme') for i in overlay.values())),
              'blocked':blocked, 'failures':failures,
              'note':'Players extraidos nao equivalem a reproducao validada. Catalogo original preservado.'}
    atomic(ROOT / 'relatorio-importacao.json', json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=True), flush=True)

if __name__ == '__main__':
    main()
