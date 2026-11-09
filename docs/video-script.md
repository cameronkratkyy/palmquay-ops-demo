# Video script: the Palmquay demo (v9.4, 11/9: the three contractor problems are named one by one, then listed together before buying; Unit 4B gets furniture because Palmquay rents some apartments furnished; the close says what a team gets back: time and mental space. About 4:10)

*Fictional company, sample records. The video happens in one window: `dashboard/index.html`. Read the **Say** column out loud; the **On screen** column is what the recorder clicks while you talk. The times assume about 150 words a minute; the recorder clicks while you talk, and the test render reports any scene whose clicks run past its window. The finished video is timed to your voice. If you run long, cut words, not clicks.*

## How it gets recorded (about 5 minutes for you)
1. Open **Sound Recorder** (Start menu, type "Sound Recorder"). Use the same mic as the 11/8 takes.
2. Click the red record button and read the **Say** column below, top to bottom, at your normal pace, in one take. There's nothing to click and nothing on screen to manage.
3. Flub a line? Pause, then re-read that whole sentence. The recorder matches your words to this script, so restarts are fine; ad-libs are not, so re-read instead.
4. Stop. It saves an `.m4a` in Documents > Sound recordings. Tell Jarvis "voice is done." The recorder then drives the dashboard in a throwaway browser, starts each click on its cue word in your voice, and mixes your voice in.

## Who's who (say the names; they're on the dashboard)
| Person (fictional) | Job at Palmquay | What they decide in this video |
|---|---|---|
| Dana Reyes | Facilities manager | First sign-off on every contractor; sends the follow-up emails; steps aside when a contractor discloses a conflict with her; signs any change to an approved order; decides whether to send the shipping-credit request |
| Marcus Hale | Procurement lead | Signs off on work over $10,000; signs in Dana's place when she steps aside |
| Priya Natarajan | Legal counsel | Reviews conflict-of-interest disclosures; signs off on work over $50,000; asks for the warranty change on Skyquay's packet |
| Tom Becker | Finance (controller) | Last sign-off on work over $50,000; decides which bills get paid |
| Lena Ortiz | Property manager | Asked for Unit 4B to be furnished |

**The story in one line:** a property company has two kinds of paperwork (letting contractors work on its buildings, and buying furniture for the apartments it rents furnished); the AI does the reading, checking, and drafting, and named people make every decision.

**The paperwork, in plain words:** before a contractor can work on a Palmquay building it sends a **W-9** (the tax form), a **certificate of insurance** (proof it's insured), and its **license** if the trade needs one.

**Who built it:** designed and directed by the author; the code was written by Claude Code. The video doesn't say this (the author's call, 11/9: "just explain that we can save companies a lot of time"); the README, the dashboard's Map tab, and the explainer's "Did you code it?" answer do.

## The script
| Time | On screen | Say |
|---|---|---|
| 0:00–0:08 | **Overview** tab. Let the tiles row sit; the "Fictional company with sample records." note in the header stays on screen. | I built an AI system that helps property management companies handle contractor and purchasing paperwork, while people keep every approval. |
| 0:08–0:27 | **Overview** tab. One slow sweep of the mouse across the five people cards under "Who works at Palmquay". | To show it, I set up a fictional company called Palmquay Properties, which manages 14 buildings around Sarasota. Five people there handle this work: Lena, a property manager; Dana, the facilities manager; Marcus, the procurement lead; Priya, the legal counsel; and Tom, the controller. |
| 0:27–0:48 | **Onboarding** tab. Point at the Vendors table, then run down its eight rows. | Before a contractor can work on a Palmquay building, it sends over its paperwork: a W-9 tax form, proof of insurance, and a license if its trade needs one. The AI checked the paperwork from eight contractors, and three of them show the kinds of problems that slow this work down. |
| 0:48–1:06 | **Onboarding** tab. Scroll to "The record behind each vendor", open "Saltmarsh Roofing Co.", point at its "insurance end date" row, then scroll its email to "DRAFT, not sent." | The first problem is expired insurance. Saltmarsh Roofing quoted $42,000 for a roof job, but its insurance ended in September, so the AI blocked the job and drafted an email for Dana to send, asking for a current certificate. |
| 1:06–1:23 | **Onboarding** tab. Scroll up to "Screening: conflict-of-interest disclosures" and point at Kestrelbay's row (its "Brother of Dana Reyes" cell, then "Legal reviews"). | The second problem is a conflict of interest. Kestrelbay Air & Heat sent the right papers, but Dana's brother owns part of the company, so the AI flagged it, and Marcus signs in Dana's place after Priya reviews it. |
| 1:23–1:41 | **Onboarding** tab. Open "Skyquay Lift & Fire Inc." (last in the list) and scroll its first packet to the sign-offs at the bottom. | The third problem is a change in the middle of signing. Skyquay Lift & Fire has a $120,000 elevator job, and a job that size needs four people to sign it in order: Dana, Marcus, Priya, and then Tom. |
| 1:41–1:56 | **Onboarding** tab, same record: keep scrolling to "Approval packet, newest version" and point at its "What changed" row. | After Dana and Marcus signed, Priya asked to add a one-year warranty. Because the contract changed, the AI built a second version with the change marked, and the signing starts over with Dana. |
| 1:56–2:09 | **Onboarding** tab. Back up to the Vendors table; point at Saltmarsh, Kestrelbay, then Skyquay as each problem is named. | So from contractors simply sending over their paperwork, the AI caught three problems: expired insurance, a conflict of interest, and a contract that changed while people were signing it. |
| 2:09–2:37 | **Buying** tab. Point at the budget, then the /change row (it shows the $108 over budget). | Palmquay also rents some of its apartments furnished, so the same team buys furniture, too. Lena asked to furnish Unit 4B's living room and bedroom for $5,200 by November 20, and Dana approved the order. Then the sofa was backordered until December, and the replacement sofa would put the project $108 over budget, so the AI wrote up the change, and it waits for Dana's signature. |
| 2:37–2:52 | **Buying** tab: scroll to "Shipping credit for a late delivery" and point at its row. | On top of that, the bed frame from Gulfweave Furnishings will arrive a week late, so the AI drafted a request for Dana to send, asking Gulfweave to credit half its $185 shipping charge. |
| 2:52–3:18 | **Buying** tab: scroll to "Invoices: three-way match" and point at the HOLD row. | Before Palmquay pays a bill, the bill has to match what was ordered and what actually showed up. The lamp supplier, Keystone Coast Furniture, billed for three lamps instead of two, at a higher price, so its bill came to $872 instead of $713. The AI put the bill on hold and showed Tom the line, and Tom decides what gets paid. |
| 3:18–3:51 | **Checks** tab. Scroll to "The checker: a second AI" so its table shows; then click **Audit log** and **Play**. | So how do you know the AI got all of this right? A second AI, which is told to only read, checks the first one's work. To test it, I hid mistakes in test copies of the paperwork, like a wrong deadline in a draft email, and it caught them. Every step along the way is also logged, whether it's an expired certificate, a conflict of interest, or a signature that has to start over, so you can replay it. |
| 3:51–4:10 | **Overview** tab. | If your team is chasing paperwork, or your digital process feels like a pain to go through every time you log in or sign off, whatever the case may be, we can save your company a lot of time and mental space for other activities. |

**Shorter cut (about 2 minutes):** beats 0:00-1:06, then 1:56-2:37, then the last beat.

## After you record
1. Jarvis renders the video from your voice, then checks it: video length equals voice length, how many script words matched, which beats ran long, and a frame from every beat.
2. You watch it once with sound. Check: nothing personal on screen, every number readable.
3. Sharing (D121): it goes on the demo's video page next to the live dashboard. Nothing is pushed until you say so.

## What this script doesn't cover
- The one-page diagram (Map tab) doesn't show the two newest steps yet (`/revise`, `/credit`); the dashboard tabs do.
- How the recording sounds. Jarvis can't hear audio; that gets checked when you watch it back (step 2 above).
- Questions after the video. The explainer (`docs/explainer.md`) covers those, including "Did you code it?"
