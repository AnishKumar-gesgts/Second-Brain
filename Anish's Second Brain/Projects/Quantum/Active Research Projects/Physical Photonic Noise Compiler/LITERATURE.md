# Literature Position

Reviewed 2026-09-06 using primary papers and official project documentation.

## Established foundations

- Fusion-based quantum computation already separates fusion errors and erasures and emphasizes that bias, correlations, and operation ordering can affect fault-tolerance predictions. [Bartolucci et al., Nature Communications 14, 912 (2023)](https://doi.org/10.1038/s41467-023-36493-1)
- Architecture-specific photonic studies already propagate loss, distinguishability, and emitter errors into fault-tolerance simulations. The compiler cannot claim that physical photonic noise has never been mapped to QEC. [Chan et al., PRX Quantum 6, 020304 (2025)](https://doi.org/10.1103/PRXQuantum.6.020304)
- Stim detector error models express probabilistic detector symptoms and logical-frame changes for decoder consumption. The project should build on this representation rather than claim a new generic decoder format. [Stim detector-error-model specification](https://github.com/quantumlib/Stim/blob/main/doc/file_format_dem_detector_error_model.md)
- Recent work shows that successful photonic fusion events can transform partial distinguishability differently depending on the protocol, heralding outcome, and physical error model. This strengthens the need for protocol-specific adapters. [van den Hoven et al., arXiv:2609.01019 (2026)](https://arxiv.org/abs/2609.01019)
- A current comparison of five heralded Bell-state generators develops a hierarchy from lumped loss to heralded sources with vacuum and multiphoton components. Its exact one-count source model supplies the second adapter's distribution, while its circuit results show that loss and multiphoton robustness are scheme-dependent. [Randles, Muñoz-Arias, and Sarovar, arXiv:2608.01549 (2026)](https://arxiv.org/abs/2608.01549)
- A standard linear-optical Bell measurement distinguishes only two of four Bell states and has 50% ideal success. Experimental data identify multiphoton emission as a limitation on Bell-state discrimination, so false records are an established mechanism rather than a standalone novelty claim. [Hauser et al., npj Quantum Information 11, 41 (2025)](https://www.nature.com/articles/s41534-025-00986-2)
- Recent subthreshold analysis shows that fusion failure creates a logical-error floor and can make all-linear-optical FBQC substantially more resource intensive than emitter-based repeat-until-success architectures. This raises the publication bar from threshold crossing to realistic subthreshold overhead. [Löbl et al., arXiv:2606.28490 (2026)](https://arxiv.org/abs/2606.28490)

## Defensible research gap

The plausible contribution is a validated, reusable compiler and error-budget method that measures when a physical-to-QEC reduction changes a logical decision. The novelty is not any one adapter, the use of Stim/PyMatching, or the observation that correlations exist.

Publication potential depends on demonstrating generality and decision-level consequences across multiple mechanisms. Event-table differences alone are insufficient.

The source-level false-herald mechanism is established rather than novel by itself. The open contribution is compiling its hidden physical histories through a specified fusion primitive into decoder-honest QEC consequences and testing whether common reductions change a decision.
