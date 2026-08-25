# Decision 2 — Dimensions to consider for risk score

Decision 1 talked about *what* the system outputs: a 0–100 score and a High / Medium / Low tier,
with an explanation attached.

This document settles *what goes into that score*.
---

## How dimensions were chosen

Before I list down those dimensions, I'd brief about metrics considered before chosing them:
- Is dimension distinct?
    - If two dimensions measure the same underlying fact, it's unnecessary to include both

- Does dimension point to an action?
    - An important goal of the system is to recommend actions.
    - "Overdue maintenance" tells a superintendent exactly what to fix.
    - "Vessel is 22 years old" is a genuine risk factor that nobody can act on.
    - Here both can be considered for scoring, but only the first helps in recommendation.

---

## Avoiding overfitting
- Only two vessels in this dataset were detained: V001 and V004.
- There is an obvious temptation to study those two, and build dimensions just around them
- But principle used here is: 
    - Chosen dimension should have a mechanism that can be explained without mentioning V001 and V004.
    - i.e. avoid overfitting on 2 detained vessels

---

## Now turn for dimensions

### 1. Repetition (Same deficiencies being noted multiple times)

- Mechanism:
    - During vessel inspection, if same fault come up in 3rd and 4th turn, conclusion drawn is required system for finding and fixing faults does not work.
    - Repeat findings are read as a management failure, and management failures are what escalate
    into detention.

- Measure:
    - For each vessel, count how many times a deficiency description appears more than its first 
    occurrence.

- Example:
    - V001 recorded "fire pump pressure low" 9 times


### 2. Trend (is it getting worse with time)
- Mechanism:
    - A vessel whose findings increase at every inspection needs attention from management
    - This is the "early warning"  feature of my solution

- Measure:
    - Direction and size of change in deficiency count across a vessel's successive inspections.

- Example:
    - V001 deficiencies went 3 -> 6 -> 9 -> 10 in each inspection.
    - While V012 deficiencis were flat 4 -> 5 -> 5 -> 4

### 3. Internal audits (findings the company raised against itself)
- Mechanism:
    - An audit finding is the company inspecting its own ship while a deficiency is an outside inspector finding the problem, on a public record.
    - When an audit finding is Open or Overdue and the same issue also appears as a deficiency, can we say *the company already knew, wrote it down, missed its own deadline, and an inspector then found it anyway.*

- Measure:
    - Count of Open and Overdue audit findings
    - Importantly, count of issues that are open internally *and* recurring externally.
    - It is the only measure of whether the company acts on what it already knows.

- Example:
    - Issues open internally that also appear as external deficiencies: V001 = 20, V004 = 14

- *Data limitation*:
    - `AuditFindings.csv` has only four columns and **no dates**.
    - Hence "known internally for eight months before an inspector found it" — cannot be built
    - A `finding_date` above would've made above statement possible.

    
### 4. Concentration (problems clustered in one area)

- Mechanism:
    - Faults clustered into one area suggest that a whole function on board is weak.

- Measure:
    - The share of a vessel's findings falling in its single largest category.

- Repetition vs Concentration:
    - These 2 sound like the same thing, but in reality, are different.
    - V001: fire pump ×9, fire alarm ×4, it says - "One broken item, never fixed"
    - V004: chart corrections ×4, ECDIS ×4, passage planning ×3 - "3 different problems"
    - Here V004 has no dominant single fault.

### 5. Crew (Experience)
- Mechanism:
    - Crew unfamiliarity can be a recognised route to serious findings during drills and equipment checks.

- Measure:
    - Number of crew who joined recently, and average rank experience.

- Why the obvious version was rejected:
    - Crew *compliance* training status and STCW validity are indeed the first instinct.
    - But 238 of 240 records are Compliant and 239 of 240 have valid certificates
    - And both above exceptions sit on a single vessel V001
    - It sounds important but not able to separate crew enough

- Example:
    - V009 has four crew who joined in the last 90 days 


### 6. Maintenance (Planned work not completed)
- Mechanism:
    - Planned maintenance exists to catch failures before they happen.
    - Overdue jobs are deferred risk

- Measure:
    - Count of maintenance jobs with status Overdue.

- Example:
    - 121 (30%) overdue jobs across the fleet where V001 alone has 11.

### 7. Equipment (Same equipment failing repeatedly)
- Mechanism:
    - Equipment that fails repeatedly has an unresolved underlying cause, and it might fai
    again, possibly during an inspection.

- Measure:
    - Count of repeat failures of the **same named equipment**

- Example: 
    - The most frequently failing items across the fleet are ECDIS (31), Fire Pump (27) and Oil Water Separator (26)


### Considered this but not implemented
- In this dataset, **both detentions were USCG inspections**
- This information should **drive recommendations, not scoring.** If the next inspection is USCG and that authority focuses on fire safety, then a vessel with fire safety findings should be given priority.




