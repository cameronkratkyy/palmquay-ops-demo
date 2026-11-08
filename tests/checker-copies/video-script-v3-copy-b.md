# 2-minute video script: the Palmquay demo (v3, 11/8: a story that names the company, the people, and the paperwork; tightened after an outside review)

*Fictional company, fake data. The demo happens in one window: `dashboard/index.html`, opened in Edge (Snipping Tool records it). Read the **Say** column out loud; the **On screen** column is what to click. The times assume about 150 words a minute, slower than normal talking, plus about 1.5 seconds for each click or scroll. If you run long, cut words, not clicks.*

## Before you record (about 5 minutes)
1. Open this folder in File Explorer, open `dashboard`, and double-click `index.html`. It opens in Edge. It's a file on this PC: nothing loads from the internet.
2. In Edge press **F11** for full screen (hides tabs, address bar, and bookmarks). If the text looks small, press **Ctrl** and **+** once (110%) so numbers read on a phone.
3. Click the clock in the taskbar and turn on **Do not disturb**, so no pop-ups land in the video.
4. Close every other window except Edge. Nothing outside this page should be on screen.
5. Open **Snipping Tool** (Start menu, type "Snipping"). Click the **video camera** icon, then **+ New**, and drag a box over the whole screen. In the recording bar, turn the **microphone** on and system audio off. Click **Start**; it counts down from 3.
6. To finish, click the red **stop** button in Snipping Tool's recording bar. Then press **F11** in Edge to leave full screen.
7. Do one practice run with a timer before the real one.

## Who's who (say the names; they're on the dashboard)
| Person (fictional) | Job at Palmquay | What they decide in this video |
|---|---|---|
| Dana Reyes | Facilities manager | First sign-off on every contractor; sends the follow-up emails; signs any change to an approved order |
| Marcus Hale | Procurement lead | Signs off on work over $10,000 |
| Priya Natarajan | Legal | Signs off on work over $50,000 |
| Tom Becker | Finance (controller) | Last sign-off on work over $50,000; decides which bills get paid |
| Lena Ortiz | Property manager | Asked for Unit 4B to be furnished |

**The story in one line:** a property company has two paperwork-heavy jobs (letting contractors work on its buildings, and buying furniture for its units); the AI does the reading, checking, and drafting, and four named people make every decision.

**The paperwork, in plain words:** before a contractor can work on a Palmquay building it sends four papers: a **W-9** (the tax form), a **certificate of insurance** (proof it's insured), its **license**, and a **work request** (what job, which building, how much).

## The script
| Time | On screen | Say |
|---|---|---|
| 0:00–0:10 | **Overview** tab. Let the tiles row sit; the "fictional company, fake data" note stays on screen. | Can this contractor start work, and who acts next? I designed this AI system to answer that for Palmquay, a fictional Sarasota property company. |
| 0:10–0:22 | **Overview** tab. Move the mouse down the "Waiting on people" table. | The AI reads the paperwork and drafts the next step. Four employees make the decisions: Dana in facilities, Marcus in procurement, Priya in legal, and Tom in finance. |
| 0:22–0:36 | **Onboarding** tab. Point down the Vendors table. | Each contractor sends four papers: a W-9 tax form, an insurance certificate, a license, and a work request. Eight sample contractors sent theirs, and the AI checked each one against Palmquay's written rules. |
| 0:36–0:47 | **Onboarding** tab. Scroll to "The record behind each vendor," open "Saltmarsh Roofing Co." and point at the "insurance end date" row. | Saltmarsh Roofing wants a $48,000 roof job, but its insurance had expired. The workflow marks it blocked and shows the exact line it found. |
| 0:47–0:55 | **Onboarding** tab, same section: scroll down to Saltmarsh's follow-up draft. Point at "DRAFT, not sent." | It drafts the email asking for current insurance. It stays unsent until Dana reviews it. |
| 0:55–1:06 | **Onboarding** tab. Open "Skyquay Lift & Fire Inc." (last in the list) and scroll its packet to the sign-offs at the bottom. | Skyquay Lift & Fire passed every check. Its $120,000 elevator job goes to all four approvers, in order: Dana, Marcus, Priya, then Tom. |
| 1:06–1:23 | **Buying** tab. Point down the seven steps table: the /source row, then the /change row (it shows the $108 over budget). | Palmquay also buys furniture. Lena, a property manager, asked for Unit 4B to be furnished for $5,200. After a late sofa and then a backorder, the replacement puts the project $108 over budget, so the change waits for Dana's approval. |
| 1:23–1:36 | **Buying** tab: scroll to "Invoices: three-way match" and point at the HOLD row. | Each bill is checked against the order and the delivery. This one bills three lamps instead of two, at a higher price: $872 against $713. It's held for Tom in finance. |
| 1:36–1:44 | **Checks** tab. Scroll to "The checker: a second AI" and point at its table. | A second AI, set up to only read, reviews the work. It flagged the planted errors shown here. |
| 1:44–1:52 | **Audit log** tab. Click **Play** and let the board fill in (about 8 seconds). | Every step is logged, and the dashboard replays itself from that log. |
| 1:52–2:00 | **Overview** tab. | I designed the process, the rules, and the tests; Claude Code wrote the code. The AI prepares the work; people decide. |

**Shorter cut (about 75-90 seconds, for a LinkedIn post):** beats 0:00-0:55, then 1:06-1:23, then the last beat. Skyquay, the invoice, the checker, and the replay stay in the 2-minute version.

## After you record
1. After you click stop, Snipping Tool shows the video. Click **Save** (the floppy-disk icon). Name it `palmquay-demo.mp4` and save it to Videos.
2. Watch it once with sound. Check: nothing personal on screen, every number readable, and it ends by 2:00. To trim the ends, open it in **Clipchamp** (already on this PC), drag the clip's edges, then **Export** at 1080p.
3. Share it: drag the file into Google Drive, right-click it, **Share**, set General access to **Anyone with the link** (Viewer), then **Copy link**.
4. LinkedIn: on your profile, **Add section** > **Recommended** > **Add featured** > **Add a link**, paste the Drive link, and title it "AI operations system: vendor onboarding and procurement (demo)". Add `docs/diagram.png` the same way with **Add media**.

## What this script doesn't cover
- How the recording looks and sounds. That gets checked when you watch it back (step 2 above).
- The Snipping Tool, Clipchamp, Drive, and LinkedIn clicks were written from their usual menus and not clicked through on this screen. If a button has moved, the same option is usually under the **...** menu.
- Questions after the video. The explainer (`docs/explainer.md`) covers those.
