# Decision 1 — What the system predicts
 
## The decision
 The system gives every vessel: 
1. **risk score** from 0 to 100
2. **tier**: High, Medium or Low.
3. **Explanation**: Reasoning behind the score

---

## Why not a percentage
- The obvious thing to build is "V001 has an 18% chance of being detained."
- But to say that, I'd need to know:
    - How often vessels get detained and under what conditions
    - The dataset contains **2 detentions across 80 inspections**.
- So the system answers a question it can actually answer:
    "**which vessels should be dealt with first, and why.**"

---

## Why a score and a tier, not just a tier
- The tier is what people read. The score is what makes the tier work.
- **Sorting inside a tier**: If six vessels are all "High", the tier alone does not say where to start. A score of 89 versus 72 does.
- **Early warning**: A vessel score going from 40 -> 52 -> 61 may still be in medium tier, but it's clearly getting worse.

---

## What the score is built from
**1. What past inspections say about behaviour**
- the same problem coming back again and again
- problems getting worse from one inspection to the next
- findings still not closed
- problems piling up in one area

**2. vessel status right now**
- maintenance jobs overdue
- equipment failing repeatedly
- crew recently joined or short on experience

Reason: History alone is not enough. A ship with a clean inspection record but 11 overdue maintenance jobs is not a safe ship.


## The link to detention
- Detention is what happens when deficiencies get serious enough. So ranking vessels by their
deficiency patterns *is* ranking them by detention risk.
- One thing the data makes clear: it is not about **how many** deficiencies a vessel has.

| Vessel | Deficiencies count | Detained? |
|---|---|---|
| V004 | 18 | Yes |
| V012 | 18 | No |

- Same count, different outcome. The difference is in the pattern:
    - **V004** — 13 of its 18 findings ("deficiency_category") are "Navigation". Same area, over and over. 
    - **V012** — findings spread across six areas
    - **V001** - the other detained vessel, shows the same shape: half its findings are "Fire Safety"

- That is what leads to detention. So the score is built around **repetition, concentration and
direction of travel**, not volume.

---

## Case of new vessels
- My current system leans on repetition, trend and unclosed findings — all of which need a past to measure against. 
- A newly acquired vessel with no inspection history has no repeats, no trend and nothing open.
- This does not occur in the sample data — all 20 vessels have exactly 4 inspections — but it is
very much possible in a real fleet.
- If the score calls it **low risk**, then the truth being hidden is - nothing is known about this vessel.
- "Looks fine" and "has no track record" are opposite situations and must not be shown the same way.
- So right handling for such cases is: 
    - Fall back on current condition and basic facts (age, vessel type, flag)
    - and mark the result as **low confidence** rather than low risk.

---

## Techniques considered and rejected
- **Training a model to predict detention.**: 
    - Needs enough detentions to learn from. There are 2.

- **SMOTE / synthetic minority oversampling.**:
    - This technique fixes class imbalance case, say 500 detentions among 100,000 inspections.
    - There 500 real examples still show what detention looks like.
    - But in our case, the problem is *scarcity*: there are only 2 examples, so there is nothing to balance.

- **Using GenAI to write fake detention records.**
    - The records would reflect general maritime knowledge from the model's training, not this fleet.
    - Training on them measures how well the system predicts an invention.

- **What would work instead**
    - TO-DO: I'll check if external data source for detention records exist




 
