# 4. Moroccan Contract Compliance Auditor

## 4.1 Legal Grounding: Public Order Clauses (*Ordre Public*)

Under Moroccan law (specifically the *Dahir des Obligations et Contrats* (DOC) Article 62, and *Code du Travail* Article 11), any contractual clause that deprives an employee or tenant of mandatory statutory rights is **null and void (*nulle et de plein droit*)**, even if both parties willingly signed the agreement.

The **Moroccan Contract Compliance Auditor** (`src/contract_auditor.py`) scans employment contracts (*CDI / CDD*), commercial leases, residential leases (*Loi 67-12*), and privacy policies (*Loi 09-08*) for statutory nullities.

## 4.2 Compliance Rules Matrix

| Rule ID | Statutory Reference | Category | Violation Trigger | Remedy / Recommendation |
|:---|:---|:---|:---|:---|
| `probation_period_exceeded` | *Code du Travail Art. 14* | Labor Law | Probation exceeds 3 months (cadres), 1.5 months (employees), or 15 days (workers). | Cap probation period to statutory maximum; renewal permitted once only. |
| `statutory_working_hours` | *Code du Travail Art. 184* | Labor Law | Working hours exceeding 44 hours/week (or 2,288 hours/year) without overtime compensation. | Specify 44 hours/week limit and statutory overtime multipliers (25% day / 50% night / 100% holidays). |
| `advance_waiver_of_severance` | *Code du Travail Art. 41 & 51* | Labor Law | Employee waives severance, notice period compensation, or damages in advance. | Remove clause completely; waiver of labor rights prior to termination is legally void. |
| `cndp_biometric_processing` | *Loi n° 09-08 CNDP Art. 4 & 12* | Data Protection | Processing biometric data, fingerprints, or CCTV without prior CNDP authorization. | Add required statutory CNDP declaration notice, purpose limitation, and consent mechanisms. |
| `excessive_security_deposit` | *Loi n° 67-12 Art. 20* | Real Estate | Residential lease requiring a security deposit exceeding 2 months' rent. | Restrict deposit (*dépôt de garantie*) to a maximum of two months' rent. |

## 4.3 Risk Score Calculation

The auditor computes a risk score ($0 \le \text{Risk} \le 100$):
$$\text{RiskScore} = \min\left(100, \sum_{i \in \text{Violations}} W(\text{severity}_i)\right)$$
where:
- $\text{CRITICAL}$: $W = 50$
- $\text{HIGH}$: $W = 35$
- $\text{MEDIUM}$: $W = 20$
- $\text{LOW}$: $W = 10$

Status categories:
- **`COMPLIANT`**: Risk Score = 0
- **`REVIEW_REQUIRED`**: $1 \le \text{RiskScore} < 50$
- **`NON_COMPLIANT_HIGH_RISK`**: $\text{RiskScore} \ge 50$
