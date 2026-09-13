# CE-QS v0.6 CTRS Adapter Proof Obligations

## CET-liftability checklist

- [ ] C1 Exact extraction: accepted proof extracts >= q distinct signer identities.
- [ ] C2 Same-set aggregate binding: extracted identities are exactly those represented by sigma_agg.
- [ ] C3 Trace binding relation: prove G_tr(x_i)=X_i.
- [ ] C4 Mask binding relation: prove K_i=Mask.Commit(k_i).
- [ ] C5 Mask evaluation relation: prove r_i=Mask.Eval(k_i,tau).
- [ ] C6 CET equation: prove e_i=r_i+c*x_i.
- [ ] C7 Hidden permutation: hide tag-to-registry mapping.
- [ ] C8 Zero knowledge/WI survives extension.
- [ ] C9 Extraction/equivocation properties survive extension.
- [ ] C10 Exact threshold remains exact; no approximate n_f/n_p gap.
- [ ] C11 Concrete n=64,q=43 proof size <= 32 KiB.
- [ ] C12 Security model explicitly ROM/QROM/standard-model.

## Go condition

All C1-C12 must be discharged before CTRS may replace the abstract ExactAgg backend in the CE-QS theorem.
