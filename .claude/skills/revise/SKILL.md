---
name: revise
description: Palmquay onboarding (fictional demo): a signer asked for a change after others signed an approval packet. Reads the e-signature export, decides whether the change is material (scope, price, dates, contract terms, insurance), builds the next version with the change marked word for word, lists who must sign again, and routes it from the first approver with every sign-off blank. Never voids, sends, or signs. Use for "/revise <vendor>" or "Legal wants a change to the packet".
argument-hint: <vendor>
---

# /revise: a change during sign-off

Operating policy is `CLAUDE.md` (section 12); every rule comes from `company/rules.json` under `exceptions`.

## Steps
1. **Rules agree?** If `CLAUDE.md` section 12 and `company/rules.json` disagree, stop and say which.
2. **Read the files yourself:** the vendor's approval packet, its e-signature export (`vendors/<vendor>/esign-status-*.md`), its work request, and the approval tiers. Note what you expect first: who signed, what changed, who signs next.
3. **Run the helper** (it does the signer order and the routing):
   ```
   python -I -X utf8 tools/exceptions.py revise <vendor>
   ```
   It writes `vendors/<vendor>/packet-v2.md` and `vendors/<vendor>/revision.json`, and appends exactly one row to `audit/exceptions-log.csv`. Version 1 is never edited.
   - Exit 2 `UNREADABLE`: a file is missing or unreadable. Say which, and stop.
   - Exit 3 `REFUSED`: it already ran, the log's chain is broken, or the change isn't material (a person corrects it in the e-signature tool). Tell the user.
4. **Compare** with what you expected. Never hand-edit the outputs, and never copy an old signature onto the new version.
5. **Report**: what changed and who asked, who signed the old version and now signs again, and the new order. The Facilities Manager voids the old version and sends the new one.

## Limits
Never void, send, sign, approve, or pay. Fake data only.
