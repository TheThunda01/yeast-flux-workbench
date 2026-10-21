"""Check saved solutions directly and re-solve extrema with HiGHS interior point."""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from flux_workbench import ValidationError, analyze, digest, load_pinned_model, read_config, scenario_bounds


def verify(data_dir,config_path,results_dir):
    data_dir,config_path,results_dir=map(Path,(data_dir,config_path,results_dir))
    manifest=json.loads((results_dir/'manifest.json').read_text())
    if manifest['model_sha256']!=digest(data_dir/'yeast-GEM.mat') or manifest['config_sha256']!=digest(config_path):
        raise ValidationError('Source/config fingerprint mismatch')
    if manifest['source_manifest_sha256']!=digest(data_dir/'provenance.json'):
        raise ValidationError('Source manifest fingerprint mismatch')
    required={'analysis.json','scenarios.csv','fva.csv','fba_fluxes.npz','report.md'}
    if not required<=set(manifest['outputs']):raise ValidationError('Missing required output fingerprints')
    for name,entry in manifest['outputs'].items():
        p=results_dir/name
        if p.parent.resolve()!=results_dir.resolve() or digest(p)!=entry['sha256'] or p.stat().st_size!=entry['bytes']:
            raise ValidationError(f'Output fingerprint mismatch: {name}')
    model=load_pinned_model(data_dir/'yeast-GEM.mat');config=read_config(config_path,model)
    saved=json.loads((results_dir/'analysis.json').read_text());by_name={r['name']:r for r in saved['scenarios']}
    if set(by_name)!={r['name'] for r in config['scenarios']} or len(by_name)!=len(saved['scenarios']):
        raise ValidationError('Saved scenario membership mismatch')
    with np.load(results_dir/'fba_fluxes.npz',allow_pickle=False) as vectors:
        if set(vectors.files)!={r['name'] for r in saved['scenarios'] if r['status']=='optimal'}:
            raise ValidationError('Stored flux-vector membership mismatch')
        for scenario in config['scenarios']:
            row=by_name[scenario['name']]
            if row['status']!='optimal':continue
            x=vectors[scenario['name']];lower,upper=scenario_bounds(model,scenario['glucose_uptake_cap'],scenario['oxygen_uptake_cap'])
            if x.shape!=model.objective.shape or not np.isfinite(x).all():raise ValidationError('Invalid saved flux vector')
            if max(np.max(abs(model.S@x-model.rhs)),np.max(lower-x),np.max(x-upper))>1e-7:
                raise ValidationError('Saved flux violates mass balance or bounds')
            if not np.isclose(model.objective@x,row['growth'],rtol=1e-8,atol=1e-8):raise ValidationError('Saved growth does not equal objective')
    # A different HiGHS algorithm checks the same LP, not independent biology.
    fresh=analyze(model,config,method='highs-ipm')
    for a,b in zip(saved['scenarios'],fresh['scenarios'],strict=True):
        if a['name']!=b['name'] or a['status']!=b['status']:raise ValidationError('Re-solved status differs')
        if a['growth'] is not None and not np.isclose(a['growth'],b['growth'],rtol=1e-6,atol=1e-7):
            raise ValidationError('Re-solved optimum differs')
        for key in ['glucose_uptake_cap','oxygen_uptake_cap','run_fva','expected_status']:
            if a[key]!=b[key]:raise ValidationError('Scenario metadata differs from configuration')
    if len(saved['ranges'])!=len(fresh['ranges']):raise ValidationError('FVA row count differs')
    for a,b in zip(saved['ranges'],fresh['ranges'],strict=True):
        for key in ['scenario','reaction','growth_fraction','minimum_status','maximum_status']:
            if a[key]!=b[key]:raise ValidationError('FVA identity/status differs')
        for key in ['minimum','maximum']:
            if a[key] is None or b[key] is None:
                if a[key]!=b[key]:raise ValidationError('FVA feasibility differs')
            elif not np.isclose(a[key],b[key],rtol=1e-6,atol=1e-5):raise ValidationError('Re-solved FVA bound differs')
        if not np.isclose(a['growth_floor'],b['growth_floor'],rtol=1e-6,atol=1e-7) or a['touches_artificial_cap']!=b['touches_artificial_cap']:
            raise ValidationError('FVA growth-floor or cap flag differs')
    for filename,rows,fields in [
        ('scenarios.csv',saved['scenarios'],['name','glucose_uptake_cap','oxygen_uptake_cap','status','growth','max_balance_residual','max_bound_violation','duality_gap']),
        ('fva.csv',saved['ranges'],['scenario','reaction','name','growth_fraction','requested_growth_floor','growth_floor','growth_floor_slack','minimum','maximum','minimum_status','maximum_status','touches_artificial_cap'])]:
        with (results_dir/filename).open(newline='') as handle:
            reader=csv.DictReader(handle)
            actual=list(reader)
            if reader.fieldnames!=fields:raise ValidationError('CSV schema differs')
        expected=[{k:'' if row[k] is None else str(row[k]) for k in fields} for row in rows]
        if actual!=expected:raise ValidationError('CSV differs from analysis JSON')
    return {'verified':True,'scenarios':len(saved['scenarios']),'fva_rows':len(saved['ranges']),
            'check':'Saved-vector feasibility plus HiGHS interior-point optimum/range check; not experimental validation.'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-dir',type=Path,default=Path('data'));p.add_argument('--config',type=Path,default=Path('scenarios.json'))
    p.add_argument('--results-dir',type=Path,default=Path('results'));a=p.parse_args()
    try:r=verify(a.data_dir,a.config,a.results_dir)
    except (ValidationError,OSError,KeyError,ValueError,TypeError) as e:p.exit(2,f'Verification stopped: {e}\n')
    print(json.dumps(r,indent=2))
