# Draft setup sheet: Gregory Whitlock; Ana Whitlock, 2217 Saltwhistle Ln

*Sample records for a demo. DRAFT, not entered in any software. A person types it into Palmquay's property management software (for example AppFolio or Buildium, named as examples only) after the sign-offs below; a restricted draft record can be made earlier. The AI doesn't connect to any software.*

## Owner

| Field | Value | From |
|---|---|---|
| Owner name(s) | Gregory Whitlock; Ana Whitlock | owners/whitlock/documents/agreement.md |
| Owner type | Two individuals | owners/whitlock/owner.md |
| Email | g.whitlock@owner-mail.example | owners/whitlock/owner.md |
| Phone | (555) 010-0201 | owners/whitlock/owner.md |
| Mailing address | 88 Juniper Ridge Rd, Asheville, NC 28801 (fictional) | owners/whitlock/owner.md |
| Tax form | W-9 on file, taxpayer ID XXX-XX-0201 (sample); a person reviews it | owners/whitlock/documents/w9.md |
| Owner payments to | Gulfline Community Bank (sample), checking ending 4471, in the name(s) Gregory Whitlock; Ana Whitlock | owners/whitlock/documents/ach.md |
| Owner payouts | Held until Owen Pratt confirms the account by calling the owner at a number Palmquay already had or confirmed separately, and records how | company/owner-rules.json |

## Property

| Field | Value | From |
|---|---|---|
| Address | 2217 Saltwhistle Ln, Sarasota, FL 34232 (fictional) | owners/whitlock/owner.md |
| County | Sarasota | owners/whitlock/owner.md |
| Parcel ID | DEMO-0471-02-0019 | owners/whitlock/documents/county-record.md |
| Type | Single-family house | owners/whitlock/owner.md |
| Year built | 1971 | owners/whitlock/documents/county-record.md |
| Bedrooms / baths | 3 / 2 | owners/whitlock/owner.md |
| Association | None | owners/whitlock/owner.md |
| Keys | 2 door keys, 1 garage remote | owners/whitlock/owner.md |

## Agreement

| Field | Value | From |
|---|---|---|
| Agreement | PQ-MA-0201 | owners/whitlock/documents/agreement.md |
| Effective date | 2026-11-15 | owners/whitlock/documents/agreement.md |
| Management fee | 9% of rent collected | owners/whitlock/documents/agreement.md |
| Owner reserve | $500 | owners/whitlock/documents/agreement.md |

## Open items (from owners/whitlock/intake.json)

- AGREEMENT_UNSIGNED_OWNER: An owner on the county record hasn't signed the agreement (Management accepted)
- LEAD_DISCLOSURE_MISSING: Built before 1978, no lead-paint disclosure (Leasing-ready or takeover complete)

Not on this sheet: The walk-through, condition photos, repairs, utilities, rent pricing, and marketing are tracked elsewhere. A paperwork sign-off here doesn't mean they happened.

## Sign-offs (blank: a person signs)

| Gate | Who signs | What the AI found | Signed by | Date |
|---|---|---|---|---|
| Management accepted | Gail Mercer, Broker of Record | Blocked: AGREEMENT_UNSIGNED_OWNER | | |
| Accounting approved | Owen Pratt, Trust Accountant | Nothing blocking | | |
| Leasing-ready or takeover complete | Lena Ortiz, Property Manager | Blocked: LEAD_DISCLOSURE_MISSING | | |
| Entered in the software by a person | Talia Brooks, Owner Onboarding Coordinator | After the three above | | |
