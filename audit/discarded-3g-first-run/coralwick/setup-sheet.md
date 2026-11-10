# Draft setup sheet: Coralwick Rentals LLC, 6032 Driftmark Way

*Sample records for a demo. DRAFT, not entered in any software. A person types it into Palmquay's property management software (for example AppFolio or Buildium, named as examples only) after the sign-offs below; the AI doesn't connect to any software.*

## Owner

| Field | Value | From |
|---|---|---|
| Owner name(s) | Coralwick Rentals LLC | owners/coralwick/documents/agreement.md |
| Owner type | LLC | owners/coralwick/owner.md |
| Email | derrick@coralwick-rentals.example | owners/coralwick/owner.md |
| Phone | (555) 010-0204 | owners/coralwick/owner.md |
| Mailing address | 7 Bramblecrest Ln, Lakewood Ranch, FL 34202 (fictional) | owners/coralwick/owner.md |
| Tax form | W-9 on file, taxpayer ID XX-XXX0204 (sample) | owners/coralwick/documents/w9.md |
| Owner payments to | Gulfline Community Bank (sample), checking ending 7752, in the name(s) Derrick Ostrowski | owners/coralwick/documents/ach.md |
| Payments turned on | No: Owen Pratt turns them on after calling the owner back on the phone number in owner.md | company/owner-rules.json |

## Property

| Field | Value | From |
|---|---|---|
| Address | 6032 Driftmark Way, Lakewood Ranch, FL 34202 (fictional) | owners/coralwick/owner.md |
| County | Manatee | owners/coralwick/owner.md |
| Parcel ID | DEMO-1690-30-0115 | owners/coralwick/documents/county-record.md |
| Type | Townhome | owners/coralwick/owner.md |
| Year built | 2016 | owners/coralwick/documents/county-record.md |
| Bedrooms / baths | 3 / 3 | owners/coralwick/owner.md |
| Association | Driftmark Village HOA (fictional) | owners/coralwick/owner.md |
| Keys | 2 door keys, 1 pool fob | owners/coralwick/owner.md |

## Agreement

| Field | Value | From |
|---|---|---|
| Agreement | PQ-MA-0204 | owners/coralwick/documents/agreement.md |
| Effective date | 2026-11-15 | owners/coralwick/documents/agreement.md |
| Management fee | 9% of rent collected | owners/coralwick/documents/agreement.md |
| Owner reserve | $500 | owners/coralwick/documents/agreement.md |

## Open items (from owners/coralwick/intake.json)

- ACH_NAME_MISMATCH: The bank account isn't in the owner's name (Money active)

## Sign-offs (blank: a person signs)

| Gate | Who signs | What the AI found | Signed by | Date |
|---|---|---|---|---|
| Management accepted | Gail Mercer, Broker of Record | Nothing blocking | | |
| Money active | Owen Pratt, Trust Accountant | Blocked: ACH_NAME_MISMATCH | | |
| Leasing-ready or takeover complete | Lena Ortiz, Property Manager | Nothing blocking | | |
| Entered in the software | Talia Brooks, Owner Onboarding Coordinator | After the three above | | |
