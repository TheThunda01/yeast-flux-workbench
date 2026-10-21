# Yeast flux constraints

These are model solutions under declared bounds, not measurements.

| Scenario | Oxygen cap | Glucose cap | Status | Maximum biomass flux |
| --- | ---: | ---: | --- | ---: |
| aerobic_reference | 1000 | 1 | optimal | 0.081100 |
| oxygen_2 | 2 | 1 | optimal | 0.070927 |
| oxygen_1 | 1 | 1 | optimal | 0.042021 |
| oxygen_05 | 0.5 | 1 | optimal | 0.027568 |
| oxygen_025 | 0.25 | 1 | optimal | 0.020341 |
| no_glucose_diagnostic | 1000 | 0 | infeasible | — |

Exchange fluxes use mmol gDW⁻¹ h⁻¹; biomass flux uses h⁻¹. Uptake is negative.

The zero-glucose diagnostic is infeasible with the fixed maintenance requirement; no growth value is substituted for a failed solve.

FVA ranges are individual feasible extrema conditional on the declared growth fraction. They are not confidence intervals, may involve different solutions, and can include internal cycles.

Changing oxygen bounds alone does not implement a physiological anaerobic model or validate the Crabtree effect.
