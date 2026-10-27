"""Inventory-only hypothetical layer union. Never opens Source or game files."""
import csv
import hashlib
import json
import pathlib
import re
from collections import Counter

LAYERS = ('app', 'patch', 'rePatch')


def summarize(rows):
    layers = {layer: {} for layer in LAYERS}
    for row in rows:
        match = re.fullmatch(r'/ux0:/(app|patch|rePatch)/PCSG00350/(.+)', row['RemotePath'])
        if not match:
            raise ValueError('unexpected inventory root')
        layer, path = match.groups()
        if '\\' in path or any(p in ('', '.', '..') for p in path.split('/')):
            raise ValueError('unsafe relative path')
        size = int(row['Bytes'])
        digest = row['SHA256'].lower()
        if size < 0 or not re.fullmatch('[0-9a-f]{64}', digest):
            raise ValueError('invalid size/hash')
        if path in layers[layer]:
            raise ValueError('duplicate path in layer')
        layers[layer][path] = (size, digest)
    union = {}
    transitions = []
    for layer in LAYERS:
        counts = Counter()
        for path, value in layers[layer].items():
            counts['new' if path not in union else 'identical' if union[path][1] == value else 'different'] += 1
            union[path] = (layer, value)
        transitions.append(dict(layer=layer, **{k: counts[k] for k in ('new', 'identical', 'different')}))
    winners = Counter(layer for layer, _ in union.values())
    return dict(scope='Historical inventory only; hypothetical app < patch < rePatch precedence; no observed mounts, copying, package or execution.',
                layers={k: dict(files=len(v), bytes=sum(x[0] for x in v.values())) for k, v in layers.items()},
                transitions=transitions, union_files=len(union), union_bytes=sum(v[0] for _, v in union.values()),
                winning_layers=dict(winners), metadata_files_retained=sum(p.startswith('sce_sys/') for p in union),
                warning='Union includes installation metadata and is not an installable or isolated staging tree. Hashes are inventory claims, not fresh verification.')


if __name__ == '__main__':
    root = pathlib.Path(__file__).resolve().parents[3]
    source = root / 'research/vita-existing-copy-manifest.csv'
    with source.open(encoding='utf-8-sig', newline='') as stream:
        result = summarize(csv.DictReader(stream))
    result['inventory_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    target = pathlib.Path(__file__).with_name('layer-union.json')
    target.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))