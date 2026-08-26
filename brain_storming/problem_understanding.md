- Using the info available before next inspection, design a practical system that can answer:
    - "Which" vessels require attention
        - Likelihood of future detention
    - "Why"?
        - Vessel specific factors contibuting to the risk
        - Recognize repeated patterns
    - "What" should be done?
        - Recommend practical preventive actions
    - "Grounding"
        - Provide supporting evidence for imp findings where source info is available
    - "Observability"
        - Maintain sufficent traceability for review

- 2 deliverables:
    1. A working prototype on sample dataset
    2. A production architecture proposal
    
- Separation of concerns principle in place:
    - Keep the risk prediction, supporting evidence, and recommended actions cleanly separated

- Proposed approach should be suitable for predicting future vessel risk rather than only "explaining" historical outcomes

- Feedback loop:
    - Updated vessel readiness after new information or actions are recorded. 
    - Hence the design needs a feedback loop, not a static score.

- Sample dataset understanding:
    - 4 Inspections per vessel, and each inspection is done in gap of ~5-6 months
    - 47 (~16%) deficiencies mentioned during inspection are still open
    - 2 detentions for V001 and V004, and **both from USCG**
    - deficiency counts rising inspection over inspection: 
        - V001: 3 -> 6 -> 9 -> 10 
        - V004: 2 -> 4 -> 5 -> 7
    - The audit findings (internal check) and the deficiencies (external check) use exactly the same 23 descriptions. Complete overlap, zero unique to either side.
        - That means: for many vessels, the company already knew about the fault. It's sitting in their own audit log. Marked Open or Overdue.
        - AuditFindings.csv has only four columns — no dates at all.
        - So I can't compute: "known internally for 8 months before PSC found it"
    - Maintenance due dates all in 2016, and 121 (30%) is overdue
    - Exactly 12 crew per vessel
    - Inspections stop at 2025 and maintenance due dates are in 2026
    - Same deficiency. description ("Fire pump pressure low") have 2 different codes (FIR-50 & FIR-22)
    - Crew experience is spread evenly from ~1.5 years to ~25 years