# How the Palmquay demo works: one page to talk from

*Palmquay Properties is fictional and every vendor, person, and price is fake. The structure copies the author's private AI system; the last three steps copy a real public-agency procurement packet (structure only). Each step is told twice: what it does, then how to say it.*

> **30 seconds:** "I designed and directed an AI operations system for a fictional property company. It handles two jobs: onboarding contractors and buying what a project needs. The AI reads the paperwork, checks it against written rules, drafts the follow-ups, and builds the approval packets. People approve, send, sign, and pay. A second AI checks the work, every action lands in an audit log, and tests with locked answers prove it caught every problem we planted."

**Start with your own story** (how you got here), then bridge: "To show it without my business's data, I copied the same structure into a fictional company."

## The steps
| Step | What it does | Say it like this |
|---|---|---|
| `/intake` | Reads the tax form, insurance, license, and work request against the rules: ready, on hold, or blocked, with evidence | "Automated compliance screening against a written policy" |
| `/chase` | Drafts one specific follow-up per stuck vendor; a named person sends it | "Exception handling with human review, no auto-send" |
| `/route` | Builds the approval packet; who signs depends on the dollar amount | "Tiered approval routing, segregation of duties" |
| `/status` | One line per vendor: stage, blocker, days waiting | "A work-in-progress board" |
| `/scope` | Turns a furnishing request into a brief; asks once for anything missing | "Requirements gathering" |
| `/source` | Checks each item's lead time against the install date | "Lead-time management" |
| `/quote` | One table for every quote; flags hidden fees and expired quotes; drafts the purchase request | "Quote comparison and purchase requisition" |
| `/approve` | Checks each product against the plan; anything unclear goes to a person | "Specification review that routes uncertain cases to a person" |
| `/change` | Prices a substitution; the approved order stays put until someone signs | "Change-order control, baseline management" |
| `/deliver` | Flags late or misaddressed deliveries, opens a task, drafts the update | "Exception management" |
| `/match` | Compares invoice, order, and receipt; Finance decides payment | "Three-way match, accounts payable controls" |
| `/screen` | Checks each contractor's conflict-of-interest disclosure and every name against an exclusion list; Legal decides | "Vendor due diligence, debarment screening, recusal" |
| `/request` | Fills in the approval request: type by dollar size, purpose, funding line, quotes per line; the approver signs | "Purchase requisition with competitive thresholds" |
| `/closeout` | Running totals, open items, and a supplier's "all delivered" checked against the receipt; two signatures | "Contract accounting and close-out" |

## Why you can trust it: five controls
1. **Written rules.** One rules file the AI reads every time, plus one file for every number; a check confirms the two agree. *Operating policy, single source of truth.*
2. **People approve.** The AI never sends, signs, orders, or pays: 0 times in 31 audit log rows. *Human in the loop.*
3. **A second AI, the checker.** Set up to only read, it reviews the work, with planted mistakes mixed in to prove it's really reading. *Maker-checker review, least privilege.*
4. **Audit log.** One row per action, hash-chained, so editing a past row shows. *Audit trail, tamper evidence.*
5. **Tests with a locked answer key.** The right answers were written and locked before the first run. 53 of 53 checks pass, and self-tests plant breaks in a throwaway copy to prove the checks catch them. *Acceptance tests, evals, mutation testing.*

**Numbers you can say:** 8 vendors, 6 planted problems, all caught · 7 buying steps, 13 planted problems, all caught · 3 steps from a real packet, 6 more problems, all caught · 20 decisions waiting on people · a test recounts every number in the dashboard's tiles and tables.

## If they ask
| They ask | You say |
|---|---|
| "Did you code it?" | "I designed it and directed the build: the process, the rules, and the tests. Claude Code wrote the code, and I can walk you through every piece." |
| "How do you know it's right?" | "The answers were locked before the first run, a script recounts every result its own way, and planted breaks prove the checks catch errors." |
| "Can the checker really only read?" | "It's defined with read and search tools only. In the earlier reviews that limit was an instruction, not enforced; the latest review ran as an agent with no write tools at all." |
| "Could it work here?" | "It's a demo on fake data and hasn't run with real users. I'd map your process with the people who do it, agree on pass and fail, pilot one workflow, and name an owner for exceptions." |
