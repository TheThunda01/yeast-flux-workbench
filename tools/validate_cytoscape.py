"""Import an exported network into local Cytoscape, verify attributes, and render it.

Start Cytoscape first. This optional check uses its bundled CyREST API and only
adds a new network/style; it never saves or replaces the user's whole session.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_roundtrip(source, imported):
    """Account for Cytoscape's new SUIDs while requiring original attributes."""
    def indexed(items, field, label):
        rows = {}
        for item in items:
            row = item['data']
            key = row.get(field)
            if not isinstance(key, str) or not key or key in rows:
                raise ValueError(f'{label}: missing or duplicate {field}')
            rows[key] = row
        return rows

    imported_nodes = indexed(imported['elements']['nodes'], 'id_original', 'nodes')
    node_ids = {}
    for original_id, row in imported_nodes.items():
        native_id = row.get('id')
        if native_id is None or str(native_id) == '' or str(native_id) in node_ids.values():
            raise ValueError('nodes: missing or duplicate native identifier')
        node_ids[original_id] = str(native_id)
    counts = {}
    for kind in ('nodes', 'edges'):
        original = indexed(source['elements'][kind], 'id', kind)
        actual = indexed(imported['elements'][kind], 'id_original', kind)
        if original.keys() != actual.keys():
            raise ValueError(f'{kind}: imported identifiers differ')
        for key, expected in original.items():
            row = actual[key]
            for field, value in expected.items():
                imported_field = field + '_original' if field in ('id', 'source', 'target') else field
                if row.get(imported_field) != value:
                    raise ValueError(f'{key}: changed attribute {field}')
            if kind == 'edges':
                for endpoint in ('source', 'target'):
                    expected_id = node_ids.get(expected[endpoint])
                    if expected_id is None or str(row.get(endpoint)) != expected_id:
                        raise ValueError(f'{key}: changed native {endpoint} endpoint')
            if expected.get('fva_status') == 'not_requested':
                if row.get('fva_minimum') is not None or row.get('fva_maximum') is not None:
                    raise ValueError(f'{key}: missing FVA was replaced by a numerical value')
        counts[kind] = len(original)
    for field, value in source['data'].items():
        if imported['data'].get(field) != value:
            raise ValueError(f'Network scope attribute changed: {field}')
    return counts


def style():
    def mapping(column, prop, values):
        return {'mappingType': 'discrete', 'mappingColumn': column,
                'mappingColumnType': 'String', 'visualProperty': prop,
                'map': [{'key': key, 'value': value} for key, value in values.items()]}
    defaults = {'NETWORK_BACKGROUND_PAINT': '#FFFFFF', 'NODE_FILL_COLOR': '#65B6CF',
                'NODE_SIZE': 28, 'NODE_LABEL_COLOR': '#18333E', 'NODE_LABEL_FONT_SIZE': 10,
                'NODE_BORDER_WIDTH': 1.2, 'NODE_BORDER_PAINT': '#24566B',
                'EDGE_WIDTH': 1.4, 'EDGE_STROKE_UNSELECTED_PAINT': '#8C9CA3',
                'EDGE_TARGET_ARROW_SHAPE': 'DELTA'}
    return {'title': 'Yeast9 FVA inspection',
            'defaults': [{'visualProperty': k, 'value': v} for k, v in defaults.items()],
            'mappings': [
                {'mappingType': 'passthrough', 'mappingColumn': 'name',
                 'mappingColumnType': 'String', 'visualProperty': 'NODE_LABEL'},
                mapping('kind', 'NODE_SHAPE', {'reaction': 'ROUND_RECTANGLE', 'metabolite': 'ELLIPSE'}),
                mapping('fva_status', 'NODE_FILL_COLOR', {'available': '#EAB75E', 'not_requested': '#DCE2E5'})]}


def validate(source_path, out, port=1234):
    source_path, out = Path(source_path).resolve(), Path(out).resolve()
    if out == ROOT or any(out == ROOT / p or ROOT / p in out.parents for p in ('data', 'results')):
        raise ValueError('Choose a new output folder outside data/ and results/')
    if out.exists():
        raise ValueError('Output folder already exists; choose a new folder')
    source = json.loads(source_path.read_text(encoding='utf-8'))
    manifest = json.loads((source_path.parent / 'manifest.json').read_text(encoding='utf-8'))
    if manifest['output_sha256'][source_path.name] != digest(source_path):
        raise ValueError('Export fingerprint does not match its manifest')
    if not 1 <= port <= 65535:
        raise ValueError('Port must be between 1 and 65535')
    base = f'http://127.0.0.1:{port}/v1/'

    def request(endpoint, method='GET', body=None, binary=False):
        payload = None if body is None else json.dumps(body).encode('utf-8')
        req = urllib.request.Request(base + endpoint, data=payload, method=method,
                                     headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=60) as response:
            data = response.read()
        return data if binary else json.loads(data) if data else None

    version = request('version')
    network_id = request('networks?format=json&collection=Yeast9-inspection', 'POST', source)['networkSUID']
    imported = request(f'networks/{network_id}')
    counts = verify_roundtrip(source, imported)
    visual_style = style()
    style_name = request('styles', 'POST', visual_style)['title']
    request(f'apply/styles/{urllib.parse.quote(style_name, safe="")}/{network_id}')
    request(f'apply/layouts/force-directed/{network_id}')
    # CyREST queues drawing work on the desktop event thread. Wait for a
    # nondegenerate, stable layout before fitting/exporting the view.
    previous, stable = None, 0
    for _ in range(60):
        view = request(f'networks/{network_id}/views/first')
        positions = sorted((n['data']['id'], n['position']['x'], n['position']['y'])
                           for n in view['elements']['nodes'])
        stable = stable + 1 if positions == previous else 0
        if stable >= 3 and len({(p[1], p[2]) for p in positions}) > 1:
            break
        previous = positions
        time.sleep(.25)
    else:
        raise ValueError('Cytoscape layout did not settle within 15 seconds')
    request(f'apply/fit/{network_id}')
    time.sleep(.5)  # Let the queued fit repaint before requesting raster output.
    png = request(f'networks/{network_id}/views/first.png?w=1600', binary=True)
    if not png.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('Cytoscape did not return a PNG image')
    out.mkdir(parents=True)
    (out / 'network-preview.png').write_bytes(png)
    (out / 'visual-style.json').write_text(json.dumps(visual_style, indent=2) + '\n', encoding='utf-8',newline='\n')
    reactions = [n['data'] for n in source['elements']['nodes'] if n['data']['kind'] == 'reaction']
    report = {'schema_version': 1, 'cytoscape': version, 'input_sha256': digest(source_path),
              'validator_sha256': digest(__file__), 'all_original_attributes_preserved': True,
              'native_edge_endpoints_preserved': True,
              **counts, 'fva_available': sum(r['fva_status'] == 'available' for r in reactions),
              'fva_not_requested': sum(r['fva_status'] == 'not_requested' for r in reactions),
              'layout': 'force-directed; coordinates may vary between runs',
              'scope': 'Native application import, attribute readback and rendering; not biological validation.',
              'output_sha256': {name: digest(out / name) for name in ('network-preview.png', 'visual-style.json')}}
    (out / 'import-verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8',newline='\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT / 'examples/cytoscape/fva-neighborhood.cyjs')
    parser.add_argument('--out', type=Path, default=ROOT / '.reproduction-cytoscape-import')
    parser.add_argument('--port', type=int, default=1234)
    args = parser.parse_args()
    print(json.dumps(validate(args.input, args.out, args.port), indent=2))
