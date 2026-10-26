from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from scipy.sparse import csc_matrix

from flux_workbench import (Model, ValidationError, fba, fva, load_pinned_model,
                            read_config, scenario_bounds, solve, FVA_FLOOR_TOLERANCE)
from run import run
from verify_results import verify

ROOT=Path(__file__).resolve().parents[1]


def toy():
    return Model(csc_matrix([[1,-1,-1,0],[0,1,1,-1]]),[0,0,0,0],[10,100,100,100],
                 np.array([0,0,0,1],dtype=np.uint8),[0,0],('input','path_a','path_b','growth'),
                 ('input','path A','path B','growth'))


class LinearProgramTests(unittest.TestCase):
    def test_unsigned_objective_is_cast_before_negation(self):
        model=toy();result,x=fba(model)
        self.assertEqual(model.objective.dtype,np.dtype(float))
        self.assertEqual(result['status'],'optimal');self.assertAlmostEqual(result['growth'],10)
        self.assertLess(result['duality_gap'],1e-10)
        np.testing.assert_allclose(model.S@x,0,atol=1e-10)

    def test_alternative_path_ranges_and_numerical_floor(self):
        model=toy();result,_=fba(model)
        rows=fva(model,model.lower,model.upper,result['growth'],['path_a','growth'],1)
        self.assertAlmostEqual(rows[0]['minimum'],0)
        self.assertAlmostEqual(rows[0]['maximum'],10)
        self.assertAlmostEqual(rows[1]['requested_growth_floor'],10)
        self.assertAlmostEqual(rows[1]['growth_floor_slack'],FVA_FLOOR_TOLERANCE*11)
        self.assertAlmostEqual(rows[1]['minimum'],10-FVA_FLOOR_TOLERANCE*11)
        for method in ('highs-ds','highs-ipm'):
            check=fva(model,model.lower,model.upper,10,['growth'],.9,method)[0]
            self.assertAlmostEqual(check['minimum'],9-check['growth_floor_slack'])

    def test_infeasible_and_unbounded_are_not_zero_growth(self):
        model=toy();lower=model.lower.copy();lower[-1]=11
        result,x=fba(model,lower,model.upper)
        self.assertEqual(result['status'],'infeasible');self.assertIsNone(x);self.assertIsNone(result['growth'])
        unbounded=Model([[1,-1]],[0,0],[np.inf,np.inf],[0,1],[0],('a','b'),('a','b'))
        result,x=fba(unbounded)
        self.assertEqual(result['status'],'unbounded');self.assertIsNone(result['growth'])

    def test_bad_models_are_rejected(self):
        good=toy()
        variants=[{'S':[[1,2]]},{'ids':('a','a','b','c')},{'upper':[-1,1,1,1]},
                  {'objective':[0,np.nan,0,1]},{'rhs':[np.inf,0]}]
        for changes in variants:
            values={key:getattr(good,key) for key in ('S','lower','upper','objective','rhs','ids','names')};values.update(changes)
            with self.subTest(changes=changes),self.assertRaises(ValidationError):Model(**values)

    def test_invalid_fva_inputs_fail(self):
        model=toy()
        for fraction in [0,1.1,float('nan'),True]:
            with self.subTest(fraction=fraction),self.assertRaises(ValidationError):
                fva(model,model.lower,model.upper,10,['growth'],fraction)
        with self.assertRaises(ValidationError):fva(model,model.lower,model.upper,0,['growth'])
        with self.assertRaisesRegex(ValidationError,'Unknown'):fva(model,model.lower,model.upper,10,['missing'])
        with self.assertRaisesRegex(ValidationError,'unique'):fva(model,model.lower,model.upper,10,['growth','growth'])


class PinnedModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.model=load_pinned_model(ROOT/'data/yeast-GEM.mat')

    def test_dimensions_growth_and_exchange_signs(self):
        self.assertEqual(self.model.S.shape,(2748,4105));self.assertEqual(self.model.S.nnz,15463)
        self.assertEqual(self.model.gene_count,1143)
        r,x=fba(self.model)
        self.assertAlmostEqual(r['growth'],.08110024,places=6)
        self.assertLess(x[self.model.index('r_1714')],0)

    def test_scenario_changes_only_two_declared_bounds(self):
        before=self.model.lower.copy();lo,hi=scenario_bounds(self.model,2,3)
        changed=set(np.flatnonzero(lo!=before))
        self.assertEqual(changed,{self.model.index('r_1714'),self.model.index('r_1992')})
        np.testing.assert_array_equal(before,self.model.lower);np.testing.assert_array_equal(hi,self.model.upper)
        for glucose,oxygen in [(-1,1),(1,0),(True,1),(1,np.inf)]:
            with self.subTest(glucose=glucose),self.assertRaises(ValidationError):scenario_bounds(self.model,glucose,oxygen)

    def test_corrupt_model_cannot_be_loaded(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'bad.mat';p.write_bytes((ROOT/'data/yeast-GEM.mat').read_bytes()+b'changed')
            with self.assertRaisesRegex(ValidationError,'SHA-256'):load_pinned_model(p)

    def test_config_rejects_unknown_reactions_and_duplicate_scenarios(self):
        original=json.loads((ROOT/'scenarios.json').read_text())
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/'config.json'
            for key in ('reaction','scenario'):
                value=deepcopy(original)
                if key=='reaction':value['fva_reactions']=['missing']
                else:value['scenarios'].append(value['scenarios'][0])
                path.write_text(json.dumps(value))
                with self.subTest(key=key),self.assertRaises(ValidationError):read_config(path,self.model)


class ReproductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.out=Path(cls.temp.name)/'results'
        # The report contains units unavailable in the legacy Windows code page.
        with patch('io.text_encoding', side_effect=lambda encoding, stacklevel=2: encoding or 'cp1252'):
            cls.result=run(ROOT/'data',ROOT/'scenarios.json',cls.out,make_plots=False)

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def test_expected_statuses_and_all_endpoint_diagnostics(self):
        self.assertIn('mmol gDW⁻¹ h⁻¹', (self.out/'report.md').read_text(encoding='utf-8'))
        self.assertEqual([r['status'] for r in self.result['scenarios']],['optimal']*5+['infeasible'])
        self.assertEqual(len(self.result['ranges']),36)
        for row in self.result['ranges']:
            self.assertLessEqual(row['minimum'],row['maximum']+1e-7)
            for side in ('minimum','maximum'):
                diagnostics=row[side+'_diagnostics']
                self.assertEqual(diagnostics['status'],'optimal')
                self.assertLessEqual(diagnostics['max_balance_residual'],1e-7)

    def test_saved_vectors_and_interior_point_crosscheck(self):
        result=verify(ROOT/'data',ROOT/'scenarios.json',self.out)
        self.assertTrue(result['verified']);self.assertEqual(result['fva_rows'],36)

    def test_rehashed_impossible_flux_vector_is_detected(self):
        import shutil
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'copy';shutil.copytree(self.out,out)
            with np.load(out/'fba_fluxes.npz',allow_pickle=False) as data:
                values={name:data[name] for name in data.files}
            values['aerobic_reference'][0]+=100
            np.savez_compressed(out/'fba_fluxes.npz',**values)
            manifest=json.loads((out/'manifest.json').read_text());raw=(out/'fba_fluxes.npz').read_bytes()
            manifest['outputs']['fba_fluxes.npz']={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
            (out/'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValidationError,'balance or bounds'):verify(ROOT/'data',ROOT/'scenarios.json',out)


if __name__=='__main__':unittest.main()
