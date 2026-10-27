"""Export the one-hop FVA inspection neighborhood without inventing pathways.

The selected FVA reactions seed a reaction/metabolite bipartite graph. Include
every reaction sharing a seed metabolite, then all participants in those
reactions. This is a partial model neighborhood, not a balanced submodel.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

import numpy as np
from scipy.io import loadmat

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from flux_workbench import digest, load_pinned_model, read_config, scenario_bounds, ValidationError  # noqa: E402
from verify_results import verify  # noqa: E402


def neighborhood(matrix, seeds):
    metabolites=set()
    for index in seeds:
        metabolites.update(matrix[:,index].indices.tolist())
    rows=matrix.tocsr()
    reactions=set(seeds)
    for index in metabolites:
        reactions.update(rows[index,:].indices.tolist())
    return sorted(reactions)


def build_network(model, metabolites, selected, flux, ranges, lower, upper, scenario, fraction):
    if len(metabolites)!=model.S.shape[0] or np.asarray(flux).shape!=(len(model.ids),):
        raise ValidationError('Metabolite metadata or flux-vector dimensions disagree')
    if not np.isfinite(flux).all():
        raise ValidationError('Flux attributes must be finite')
    nodes,edges=[],[]
    used=set()
    for index in selected:
        reaction=model.ids[index]
        row={'id':'rxn:'+reaction,'name':reaction,'label':model.names[index],
             'kind':'reaction','reaction_id':reaction,'fba_flux':float(flux[index]),
             'flux_units':'h^-1' if model.objective[index] else 'mmol gDW^-1 h^-1',
             'lower_bound':float(lower[index]),'upper_bound':float(upper[index]),
             'fva_status':'available' if reaction in ranges else 'not_requested',
             'scenario':scenario,'growth_fraction':float(fraction)}
        if reaction in ranges:
            item=ranges[reaction]
            row.update(fva_minimum=float(item['minimum']),fva_maximum=float(item['maximum']),
                       requested_growth_floor=float(item['requested_growth_floor']),
                       effective_growth_floor=float(item['growth_floor']),
                       growth_floor_slack=float(item['growth_floor_slack']),
                       touches_artificial_cap=bool(item['touches_artificial_cap']))
        nodes.append({'data':row})
        column=model.S[:,index]
        for met_index,coefficient in zip(column.indices,column.data):
            used.add(int(met_index))
            met_id='met:'+metabolites[int(met_index)]['id']
            reactant=coefficient<0
            edges.append({'data':{'id':reaction+':'+metabolites[int(met_index)]['id'],
                                 'source':met_id if reactant else 'rxn:'+reaction,
                                 'target':'rxn:'+reaction if reactant else met_id,
                                 'interaction':'reactant' if reactant else 'product',
                                 'stoichiometric_coefficient':float(coefficient),
                                 'reaction_id':reaction,
                                 'metabolite_id':metabolites[int(met_index)]['id']}})
    for index in sorted(used):
        item=metabolites[index]
        nodes.append({'data':{'id':'met:'+item['id'],'name':item['id'],
                              'label':item['name'],'kind':'metabolite',
                              'metabolite_id':item['id'],'compartment':item['compartment']}})
    return {'data':{'name':f'Yeast9 FVA neighborhood: {scenario}, growth target {fraction:g}',
                    'scope':'One-hop neighborhood around selected FVA metabolites; partial network, not a balanced submodel.',
                    'arrow_meaning':'Stoichiometric forward direction, not inferred direction of net flux.',
                    'flux_meaning':'One saved feasible FBA optimum; alternative optima can differ.',
                    'fva_meaning':'Marginal feasible ranges at the declared growth target/slack; endpoints need not be jointly attainable.'},
            'elements':{'nodes':nodes,'edges':edges}}


def export(results_dir,out,scenario='aerobic_reference',fraction=.99):
    results_dir=Path(results_dir).resolve();out=Path(out).resolve()
    if out==ROOT or out.is_relative_to(ROOT/'data') or out.is_relative_to(results_dir):
        raise ValidationError('Choose output separate from source data and optimization results')
    checked=verify(ROOT/'data',ROOT/'scenarios.json',results_dir)
    model=load_pinned_model(ROOT/'data/yeast-GEM.mat')
    config=read_config(ROOT/'scenarios.json',model)
    settings=next((s for s in config['scenarios'] if s['name']==scenario),None)
    if settings is None or not settings['run_fva'] or fraction not in config['growth_fractions']:
        raise ValidationError('Select a configured scenario and growth fraction with saved FVA')
    analysis=json.loads((results_dir/'analysis.json').read_text(encoding='utf-8'))
    ranges={r['reaction']:r for r in analysis['ranges'] if r['scenario']==scenario and r['growth_fraction']==fraction}
    if set(ranges)!=set(config['fva_reactions']) or any(r['minimum_status']!='optimal' or r['maximum_status']!='optimal' for r in ranges.values()):
        raise ValidationError('The selected FVA range set is incomplete or not optimal')
    with np.load(results_dir/'fba_fluxes.npz',allow_pickle=False) as vectors:
        flux=vectors[scenario]
    lower,upper=scenario_bounds(model,settings['glucose_uptake_cap'],settings['oxygen_uptake_cap'])
    raw=loadmat(ROOT/'data/yeast-GEM.mat',simplify_cells=True)['model']
    metabolites=[{'id':str(identifier),'name':str(name),'compartment':str(raw['compNames'][int(comp)-1])}
                 for identifier,name,comp in zip(raw['mets'],raw['metNames'],raw['metComps'],strict=True)]
    selected=neighborhood(model.S,[model.index(r) for r in config['fva_reactions']])
    graph=build_network(model,metabolites,selected,flux,ranges,lower,upper,scenario,fraction)
    out.mkdir(parents=True,exist_ok=True)
    (out/'fva-neighborhood.cyjs').write_text(json.dumps(graph,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    reaction_nodes=[n['data'] for n in graph['elements']['nodes'] if n['data']['kind']=='reaction']
    fields=['reaction_id','label','scenario','fba_flux','flux_units','lower_bound','upper_bound','fva_status',
            'growth_fraction','fva_minimum','fva_maximum','requested_growth_floor','effective_growth_floor',
            'growth_floor_slack','touches_artificial_cap']
    with (out/'reaction-attributes.csv').open('w',newline='',encoding='utf-8') as handle:
        writer=csv.DictWriter(handle,fieldnames=fields,extrasaction='ignore',lineterminator='\n')
        writer.writeheader();writer.writerows(reaction_nodes)
    sources=[ROOT/'data/yeast-GEM.mat',ROOT/'scenarios.json',results_dir/'analysis.json',results_dir/'fba_fluxes.npz',results_dir/'manifest.json']
    manifest={'schema_version':1,'source_sha256':{p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else p.name:digest(p) for p in sources},
              'builder_sha256':digest(__file__),'upstream_model':'yeast-GEM v9.1.1; CC BY 4.0; see data/README.md',
              'scenario':scenario,'growth_fraction':fraction,'seed_reactions':config['fva_reactions'],
              'selection_rule':__doc__.strip(),'reaction_nodes':len(selected),
              'metabolite_nodes':len(graph['elements']['nodes'])-len(selected),
              'edges':len(graph['elements']['edges']),'fva_annotated_reactions':len(ranges),
              'source_result_verification':checked,
              'output_sha256':{p.name:digest(p) for p in (out/'fva-neighborhood.cyjs',out/'reaction-attributes.csv')}}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results-dir',type=Path,default=ROOT/'results')
    parser.add_argument('--out',type=Path,default=ROOT/'examples/cytoscape')
    parser.add_argument('--scenario',default='aerobic_reference')
    parser.add_argument('--growth-fraction',type=float,default=.99)
    args=parser.parse_args()
    try:
        print(json.dumps(export(args.results_dir,args.out,args.scenario,args.growth_fraction),indent=2))
    except (OSError,ValueError,KeyError,TypeError) as exc:
        parser.exit(2,f'Network export stopped: {exc}\n')
