"""Reproduce the pinned yeast constraint scenarios and selected flux ranges."""
import argparse
import csv
import json
import os
from pathlib import Path
import platform
import tempfile

import numpy as np
import scipy

from flux_workbench import (ValidationError, analyze, digest, load_pinned_model,
                            read_config, SOLVER_OPTIONS, BALANCE_TOLERANCE)


def csv_file(path, rows, fields):
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction='ignore')
        writer.writeheader(); writer.writerows(rows)


def plots(result, directory):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    rows = [r for r in result['scenarios'] if r['status']=='optimal']
    fig, ax = plt.subplots(figsize=(7.2,4.4), layout='constrained')
    for cap in sorted({r['glucose_uptake_cap'] for r in rows}):
        subset=sorted([r for r in rows if r['glucose_uptake_cap']==cap],key=lambda r:r['oxygen_uptake_cap'])
        ax.plot([r['oxygen_uptake_cap'] for r in subset], [r['growth'] for r in subset], 'o-',label=f'Glucose cap {cap:g}')
    ax.set_xscale('log'); ax.set(xlabel='Declared oxygen-uptake cap (mmol gDW⁻¹ h⁻¹; log scale)',
                                ylabel='Maximum modeled biomass flux (h⁻¹)', title='Model growth under declared uptake constraints\nLines connect evaluated scenarios')
    if rows:ax.legend(frameon=False)
    else:ax.text(.5,.5,'No optimal scenarios; inspect the status report',ha='center',transform=ax.transAxes)
    ax.spines[['top','right']].set_visible(False); ax.grid(alpha=.2)
    fig.savefig(directory/'growth_constraints.png',dpi=150); plt.close(fig)
    candidates=result['ranges']
    if candidates:
        scenarios={r['name']:r for r in result['scenarios']}
        chosen=min({r['scenario'] for r in candidates},key=lambda n:(scenarios[n]['oxygen_uptake_cap'],n))
        available=[r['reaction'] for r in candidates if r['scenario']==chosen]
        reaction='r_1761' if 'r_1761' in available else available[0]
        selected=[r for r in candidates if r['scenario']==chosen and r['reaction']==reaction]
    else:selected=[]
    fig, ax=plt.subplots(figsize=(7.2,4.0),layout='constrained')
    for i,row in enumerate(selected):
        ax.plot([row['minimum'],row['maximum']],[i,i],lw=6,color='#b85b24',solid_capstyle='round')
        ax.scatter([row['minimum'],row['maximum']],[i,i],s=35,color='#673713',zorder=3)
    ax.set(yticks=range(len(selected)),yticklabels=[f"{r['growth_fraction']:.0%} target + numerical slack" for r in selected],
           xlabel='Feasible flux (mmol gDW⁻¹ h⁻¹)',title='Growth requirement changes feasible flux ranges')
    if selected:
        ax.set_xlabel('Feasible biomass flux (h⁻¹)' if reaction=='r_2111' else 'Feasible flux (mmol gDW⁻¹ h⁻¹)')
        ax.set_title(f"Growth requirement changes feasible flux ranges\n{reaction}: {selected[0]['name']} in {chosen}\nLP tolerance 1e−9; growth-floor slack {selected[0]['growth_floor_slack']:.2g} h⁻¹",fontsize=10)
    else:ax.text(.5,.5,'No FVA ranges requested for an optimal scenario',ha='center',transform=ax.transAxes)
    ax.spines[['top','right']].set_visible(False);ax.grid(axis='x',alpha=.2)
    fig.savefig(directory/'ethanol_fva.png',dpi=150);plt.close(fig)


def run(data_dir, config_path, output_dir, make_plots=True):
    data_dir, config_path, output_dir=map(Path,(data_dir,config_path,output_dir))
    if output_dir.resolve()==data_dir.resolve() or data_dir.resolve() in output_dir.resolve().parents:
        raise ValidationError('Outputs must be outside source data')
    model=load_pinned_model(data_dir/'yeast-GEM.mat')
    manifest=json.loads((data_dir/'provenance.json').read_text())
    for item in manifest['files']:
        path=data_dir/item['path']
        if path.parent.resolve()!=data_dir.resolve() or digest(path)!=item['sha256']:
            raise ValidationError('Source manifest fingerprint mismatch')
    config=read_config(config_path,model)
    result=analyze(model,config)
    payload={k:v for k,v in result.items() if k!='vectors'}
    payload['model']={'version':'9.1.1','metabolites':model.S.shape[0],'reactions':model.S.shape[1],
                      'genes':model.gene_count,
                      'stoichiometric_nonzeros':model.S.nnz,'objective':'r_2111',
                      'flux_units':'mmol gDW^-1 h^-1; biomass drain h^-1',
                      'interpretation':'Steady-state model feasibility, not observed growth or flux uncertainty.'}
    output_dir.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.flux_results_',dir=output_dir.parent) as temp:
        stage=Path(temp)
        (stage/'analysis.json').write_text(json.dumps(payload,indent=2,allow_nan=False)+'\n')
        csv_file(stage/'scenarios.csv',result['scenarios'],['name','glucose_uptake_cap','oxygen_uptake_cap','status','growth','max_balance_residual','max_bound_violation','duality_gap'])
        csv_file(stage/'fva.csv',result['ranges'],['scenario','reaction','name','growth_fraction','requested_growth_floor','growth_floor','growth_floor_slack','minimum','maximum','minimum_status','maximum_status','touches_artificial_cap'])
        np.savez_compressed(stage/'fba_fluxes.npz',**result['vectors'])
        lines=['# Yeast flux constraints', '', 'These are model solutions under declared bounds, not measurements.', '',
               '| Scenario | Oxygen cap | Glucose cap | Status | Maximum biomass flux |', '| --- | ---: | ---: | --- | ---: |']
        for r in result['scenarios']:
            growth='—' if r['growth'] is None else f"{r['growth']:.6f}"
            lines.append(f"| {r['name']} | {r['oxygen_uptake_cap']} | {r['glucose_uptake_cap']} | {r['status']} | {growth} |")
        lines+=['', 'Exchange fluxes use mmol gDW⁻¹ h⁻¹; biomass flux uses h⁻¹. Uptake is negative.', '',
                'The zero-glucose diagnostic is infeasible with the fixed maintenance requirement; no growth value is substituted for a failed solve.', '',
                'FVA ranges are individual feasible extrema conditional on the declared growth fraction. They are not confidence intervals, may involve different solutions, and can include internal cycles.', '',
                'Changing oxygen bounds alone does not implement a physiological anaerobic model or validate the Crabtree effect.']
        (stage/'report.md').write_text('\n'.join(lines)+'\n')
        if make_plots:plots(result,stage)
        run_manifest={'schema_version':1,'source_manifest_sha256':digest(data_dir/'provenance.json'),
                      'model_sha256':digest(data_dir/'yeast-GEM.mat'),'config_sha256':digest(config_path),
                      'versions':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},
                      'solver':{'method':'highs-ds','options':SOLVER_OPTIONS,'accepted_residual':BALANCE_TOLERANCE},
                      'code_sha256':{name:digest(Path(__file__).parent/name) for name in ['flux_workbench.py','run.py']},
                      'outputs':{p.name:{'sha256':digest(p),'bytes':p.stat().st_size} for p in stage.iterdir()}}
        (stage/'manifest.json').write_text(json.dumps(run_manifest,indent=2,sort_keys=True)+'\n')
        output_dir.mkdir(parents=True,exist_ok=True)
        for p in stage.iterdir():os.replace(p,output_dir/p.name)
        if not make_plots:
            for name in ['growth_constraints.png','ethanol_fva.png']:(output_dir/name).unlink(missing_ok=True)
    return payload


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,default=Path('data'))
    parser.add_argument('--config',type=Path,default=Path('scenarios.json'))
    parser.add_argument('--output-dir',type=Path,default=Path('results'))
    parser.add_argument('--no-plots',action='store_true')
    a=parser.parse_args()
    try:r=run(a.data_dir,a.config,a.output_dir,not a.no_plots)
    except (ValidationError,OSError,KeyError,TypeError,ValueError) as e:parser.exit(2,f'Analysis stopped: {e}\n')
    print(f"Solved {len(r['scenarios'])} scenarios; reported {len(r['ranges'])} conditional flux ranges.")
