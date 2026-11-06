---
name: route
description: Palmquay Properties approval packet (fictional demo). For a READY vendor, builds vendors/<slug>/packet.md with the job, what intake checked, and the approvers for the contract amount's tier in order from company/rules.json, with every decision, date and signature left blank for a person. Never approves. Use for "/route <slug>", "/route all", or "build the approval packet".
argument-hint: <vendor-slug | all>
---

# /route: build the approval packet (people approve)

The assistant builds the packet. People approve, in order (`CLAUDE.md` section 6). The assistant never approves, signs, pays, or notifies an approver.

## Steps (per vendor)

1. **READY only.** Read `vendors/<slug>/intake.json`. HOLD or BLOCKED vendors are not routed. Say who will approve once it's fixed, and point to `/chase`.
2. **Build it:**
   ```
   python -I -X utf8 tools/onboard.py packet <slug>
   ```
   It refuses (exit 3) if the vendor isn't READY, if a packet already exists, or if `intake.json`'s approvers differ from `rules.json`. Then you stop and say so. On success it writes `vendors/<slug>/packet.md`, sets the Stage line, and appends one audit row.
3. **Read the packet back** and confirm:
   - The sign-off rows match the tier for the contract amount, in this order: up to $10,000 Facilities Manager; up to $50,000 adds Procurement Lead; over $50,000 adds Legal, then Finance.
   - Names and emails match `company/people.md`.
   - Every Decision, Date and Signature cell is blank.
4. **Report**: vendor, amount, approvers in order, and who is first. A person sends it on.
5. **Checker review before done** (same as `/chase` step 7).

## Limits
Never approve, send, sign or pay. Never fill a sign-off cell. Fake data only.
