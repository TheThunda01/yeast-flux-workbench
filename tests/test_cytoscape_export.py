import json
import copy
from pathlib import Path
import tempfile
import unittest

import numpy as np
from scipy.sparse import csc_matrix

from flux_workbench import Model
from tools.export_cytoscape import build_network, export, neighborhood
from tools.validate_cytoscape import verify_roundtrip

ROOT=Path(__file__).resolve().parents[1]


class NetworkExportTests(unittest.TestCase):
    @staticmethod
    def native_fixture():
        source={'data': {'scope': 'partial'}, 'elements': {'nodes': [
            {'data': {'id': 'rxn:r1', 'fva_status': 'not_requested', 'fba_flux': -2.0}},
            {'data': {'id': 'met:m1', 'compartment': 'cell'}}], 'edges': [
            {'data': {'id': 'r1:m1', 'source': 'met:m1', 'target': 'rxn:r1',
                      'stoichiometric_coefficient': -2.0}}]}}
        imported=copy.deepcopy(source)
        node_ids={item['data']['id']:str(number+1)
                  for number,item in enumerate(source['elements']['nodes'])}
        for item in imported['elements']['nodes']:
            row=item['data']
            row['id_original']=row['id']
            row['id']=node_ids[row['id_original']]
        for number,item in enumerate(imported['elements']['edges']):
            row=item['data']
            row['id_original']=row['id']
            row['id']=str(number+len(node_ids)+1)
            for key in ('source','target'):
                row[key+'_original']=row[key]
                row[key]=node_ids[row[key+'_original']]
        return source, imported

    def test_native_readback_keeps_attributes_and_missing_fva_distinct(self):
        source,imported=self.native_fixture()
        self.assertEqual(verify_roundtrip(source,imported),{'nodes':2,'edges':1})
        imported['elements']['nodes'][0]['data']['fva_minimum']=0.0
        with self.assertRaisesRegex(ValueError,'missing FVA'):
            verify_roundtrip(source,imported)
        del imported['elements']['nodes'][0]['data']['fva_minimum']
        imported['elements']['edges'][0]['data']['stoichiometric_coefficient']=-1.0
        with self.assertRaisesRegex(ValueError,'stoichiometric_coefficient'):
            verify_roundtrip(source,imported)

    def test_reversed_native_endpoints_fail_even_when_original_labels_match(self):
        source,imported=self.native_fixture()
        edge=imported['elements']['edges'][0]['data']
        edge['source'],edge['target']=edge['target'],edge['source']
        with self.assertRaisesRegex(ValueError,'native source endpoint'):
            verify_roundtrip(source,imported)

    def test_invalid_native_endpoint_is_rejected(self):
        for endpoint in ('source','target'):
            with self.subTest(endpoint=endpoint):
                source,imported=self.native_fixture()
                imported['elements']['edges'][0]['data'][endpoint]='unknown-SUID'
                with self.assertRaisesRegex(ValueError,'native .* endpoint'):
                    verify_roundtrip(source,imported)

    def test_duplicate_imported_identity_is_rejected(self):
        source,imported=self.native_fixture()
        imported['elements']['nodes'].append(copy.deepcopy(imported['elements']['nodes'][0]))
        with self.assertRaisesRegex(ValueError,'duplicate id_original'):
            verify_roundtrip(source,imported)

    def test_integer_native_endpoints_resolve_to_same_nodes(self):
        source,imported=self.native_fixture()
        for endpoint in ('source','target'):
            edge=imported['elements']['edges'][0]['data']
            edge[endpoint]=int(edge[endpoint])
        self.assertEqual(verify_roundtrip(source,imported),{'nodes':2,'edges':1})

    def test_stoichiometric_direction_and_coefficients_are_not_flux_direction(self):
        model=Model([[-2,0],[1,-1]],[-10,0],[10,10],[0,1],[0,0],('reaction','drain'),('reaction','drain'))
        mets=[{'id':'A','name':'A','compartment':'cell'},{'id':'B','name':'B','compartment':'cell'}]
        graph=build_network(model,mets,[0],[-3,0],{},model.lower,model.upper,'toy',.99)
        edges=[e['data'] for e in graph['elements']['edges']]
        self.assertEqual([(e['source'],e['target'],e['stoichiometric_coefficient']) for e in edges],
                         [('met:A','rxn:reaction',-2),('rxn:reaction','met:B',1)])
        reaction=graph['elements']['nodes'][0]['data']
        self.assertEqual(reaction['fba_flux'],-3)
        self.assertEqual(reaction['fva_status'],'not_requested')
        self.assertNotIn('fva_minimum',reaction)

    def test_neighborhood_stops_after_seed_metabolite_neighbors(self):
        matrix=csc_matrix([[-1,1,0,0],[0,-1,1,0],[0,0,-1,1]])
        self.assertEqual(neighborhood(matrix,[0]),[0,1])

    def test_real_export_preserves_requested_and_missing_fva_states(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest=export(ROOT/'results',Path(temp))
            self.assertEqual((manifest['reaction_nodes'],manifest['metabolite_nodes'],manifest['edges']),(18,34,54))
            graph=json.loads((Path(temp)/'fva-neighborhood.cyjs').read_text())
            ids={n['data']['id'] for n in graph['elements']['nodes']}
            self.assertEqual(len(ids),52)
            self.assertTrue(all(e['data']['source'] in ids and e['data']['target'] in ids for e in graph['elements']['edges']))
            reactions=[n['data'] for n in graph['elements']['nodes'] if n['data']['kind']=='reaction']
            requested=[n for n in reactions if n['fva_status']=='available']
            self.assertEqual({n['reaction_id'] for n in requested},set(manifest['seed_reactions']))
            self.assertTrue(all(n['fva_minimum']<=n['fva_maximum'] for n in requested))
            self.assertTrue(all(n['growth_floor_slack']>0 for n in requested))
            self.assertEqual(sum('fva_minimum' not in n for n in reactions),12)


if __name__=='__main__':
    unittest.main()
