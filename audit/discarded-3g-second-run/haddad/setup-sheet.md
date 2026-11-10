# Draft setup sheet: Beverly Haddad, 1340 Lanternfish Cir

*Sample records for a demo. DRAFT, not entered in any software. A person types it into Palmquay's property management software (for example AppFolio or Buildium, named as examples only) after the sign-offs below; a restricted draft record can be made earlier. The AI doesn't connect to any software.*

## Owner

| Field | Value | From |
|---|---|---|
| Owner name(s) | Beverly Haddad | owners/haddad/documents/agreement.md |
| Owner type | Individual | owners/haddad/owner.md |
| Email | bev.haddad@owner-mail.example | owners/haddad/owner.md |
| Phone | (555) 010-0205 | owners/haddad/owner.md |
| Mailing address | 26 Osprey Point Dr, Venice, FL 34285 (fictional) | owners/haddad/owner.md |
| Tax form | W-9 on file, taxpayer ID XXX-XX-0205 (sample); a person reviews it | owners/haddad/documents/w9.md |
| Owner payments to | Gulfline Community Bank (sample), checking ending 5208, in the name(s) Beverly Haddad | owners/haddad/documents/ach.md |
| Owner payouts | Held until Owen Pratt confirms the account by calling the owner at a number Palmquay already had or confirmed separately, and records how | company/owner-rules.json |

## Property

| Field | Value | From |
|---|---|---|
| Address | 1340 Lanternfish Cir, Venice, FL 34293 (fictional) | owners/haddad/owner.md |
| County | Sarasota | owners/haddad/owner.md |
| Parcel ID | DEMO-0890-14-0031 | owners/haddad/documents/county-record.md |
| Type | Single-family house | owners/haddad/owner.md |
| Year built | 1986 | owners/haddad/documents/county-record.md |
| Bedrooms / baths | 3 / 2 | owners/haddad/owner.md |
| Association | None | owners/haddad/owner.md |
| Keys | Coming from Tidewell Rentals | owners/haddad/owner.md |

## Agreement

| Field | Value | From |
|---|---|---|
| Agreement | PQ-MA-0205 | owners/haddad/documents/agreement.md |
| Effective date | 2026-11-15 | owners/haddad/documents/agreement.md |
| Management fee | 9% of rent collected | owners/haddad/documents/agreement.md |
| Owner reserve | $500 | owners/haddad/documents/agreement.md |

## Tenant already in place

| Field | Value | From |
|---|---|---|
| Tenant | Marco Ellison | owners/haddad/tenant/lease.md |
| Lease term | 2026-03-01 to 2027-02-28 | owners/haddad/tenant/lease.md |
| Monthly rent | $2,350 | owners/haddad/tenant/lease.md |
| Deposit per the lease | $2,400 | owners/haddad/tenant/lease.md |
| Deposit received | $2,200 on 2026-11-03 | owners/haddad/tenant/deposit-transfer.md |
| Difference | $200 open with Owen Pratt (DEPOSIT_SHORT); both amounts are recorded now, and only 'reconciled' waits | owners/haddad/takeover.json |
| A person also reviews | The lease's amendments, the tenant ledger, the paid-through date, any arrears, notices, and open repairs (not in this sample packet) | company/owner-rules.json |

## Open items (from owners/haddad/intake.json)

- DEPOSIT_SHORT: Less deposit came over than the lease says (Accounting approved, Leasing-ready or takeover complete)
- INSURANCE_NOT_LANDLORD: A homeowner policy: the agent must confirm it covers a rental (Management accepted)

Not on this sheet: The walk-through, condition photos, repairs, utilities, rent pricing, and marketing are tracked elsewhere. A paperwork sign-off here doesn't mean they happened.

## Sign-offs (blank: a person signs)

| Gate | Who signs | What the AI found | Signed by | Date |
|---|---|---|---|---|
| Management accepted | Gail Mercer, Broker of Record | Blocked: INSURANCE_NOT_LANDLORD | | |
| Accounting approved | Owen Pratt, Trust Accountant | Blocked: DEPOSIT_SHORT | | |
| Leasing-ready or takeover complete | Lena Ortiz, Property Manager | Blocked: DEPOSIT_SHORT | | |
| Entered in the software by a person | Talia Brooks, Owner Onboarding Coordinator | After the three above | | |
