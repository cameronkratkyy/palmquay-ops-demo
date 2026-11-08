# 2-minute video script: the Palmquay demo (v6.4, 11/8: beat 2 points at the new org chart; adds "each keeps working in their own tools"; more context at his ask: who each contractor and supplier is, what it asked for, and what happened; about 2:39)

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
| Priya Natarajan | Legal counsel | Signs off on work over $50,000 |
| Tom Becker | Finance (controller) | Last sign-off on work over $50,000; decides which bills get paid |
| Lena Ortiz | Property manager | Asked for Unit 4B to be furnished |

**The story in one line:** a property company has two paperwork-heavy jobs (letting contractors work on its buildings, and buying furniture for its units); the AI does the reading, checking, and drafting, and four named people make every decision.

**The paperwork, in plain words:** before a contractor can work on a Palmquay building it sends four papers: a **W-9** (the tax form), a **certificate of insurance** (proof it's insured), its **license**, and a **work request** (what job, which building, how much).

## The script
| Time | On screen | Say |
|---|---|---|
| 0:00–0:08 | **Overview** tab. Let the tiles row sit; the "Fictional company with sample records." note in the header stays on screen. | I built an AI system that helps property management companies handle contractor and purchasing paperwork, while people keep every approval. |
| 0:08–0:32 | **Overview** tab. One slow sweep of the mouse across the five people cards under "Who works at Palmquay" (each has its own color). | To show it, I set up a fictional company: Palmquay Properties, a Sarasota company managing 14 buildings. Five employees handle this work: Lena, a property manager; Dana, the facilities manager; Marcus, the procurement lead; Priya, legal counsel; and Tom, the controller. Each keeps working in their own tools; this board shows what's waiting on whom. |
| 0:32–0:49 | **Onboarding** tab. Point at the Vendors table. | Before a contractor can work on a Palmquay building, it sends four papers: a W-9 tax form, proof of insurance, a work request, and a license if its trade needs one. Eight contractors applied. |
| 0:49–1:09 | **Onboarding** tab. Scroll to "The record behind each vendor," open "Saltmarsh Roofing Co." and point at the "insurance end date" row. | Take Saltmarsh Roofing, a Sarasota roofer. It asked for a $42,000 job re-coating the roof at Bayfront Commons, one of Palmquay's buildings, and sent all four papers. But its insurance had expired, so the AI marked it blocked. |
| 1:09–1:19 | **Onboarding** tab, same section: scroll down to Saltmarsh's follow-up draft. Point at "DRAFT, not sent." | The AI drafted an email asking Saltmarsh for current insurance. It stays unsent until Dana reviews it. |
| 1:19–1:38 | **Onboarding** tab. Open "Skyquay Lift & Fire Inc." (last in the list) and scroll its packet to the sign-offs at the bottom. | Skyquay Lift & Fire is the opposite: a $120,000 job modernizing two elevators at Bayfront Commons, with every paper in order. So the AI built its approval packet, with four sign-offs in order: Dana, Marcus, Priya, then Tom. |
| 1:38–1:57 | **Buying** tab. Point at the /source row, then the /change row (it shows the $108 over budget). | Palmquay also furnishes apartments between tenants. Lena asked to furnish Unit 4B for $5,200. The sofa picked was backordered, and the replacement puts the project $108 over budget, so the change waits for Dana. |
| 1:57–2:14 | **Buying** tab: scroll to "Invoices: three-way match" and point at the HOLD row. | Each bill is checked against its order and delivery. Supplier Keystone Coast Furniture billed three lamps, not two, at a higher price, so the bill is $872, not $713. It's held for Tom. |
| 2:14–2:25 | **Checks** tab. Scroll to "The checker: a second AI" and point at its table. | A second AI, told to only read, caught the errors I planted to test it. |
| 2:25–2:39 | **Overview** tab. | If your team chases paperwork, this is how it could work: AI reads and drafts; your people decide. I designed the process, rules, and tests; Claude Code wrote the code. |

**Shorter cut (about 75-90 seconds, for a LinkedIn post):** beats 0:00-1:19, then 1:38-1:57, then the last beat.

## After you record
1. After you click stop, Snipping Tool shows the video. Click **Save** (the floppy-disk icon). Name it `palmquay-demo.mp4` and save it to Videos.
2. Watch it once with sound. Check: nothing personal on screen, every number readable, and it ends by about 2:40. To trim the ends, open it in **Clipchamp** (already on this PC), drag the clip's edges, then **Export** at 1080p.
3. Share it: drag the file into Google Drive, right-click it, **Share**, set General access to **Anyone with the link** (Viewer), then **Copy link**.
4. LinkedIn: on your profile, **Add section** > **Recommended** > **Add featured** > **Add a link**, paste the Drive link, and title it "AI operations system: vendor onboarding and procurement (demo)". Add `docs/diagram.png` the same way with **Add media**.

## What this script doesn't cover
- How the recording looks and sounds. That gets checked when you watch it back (step 2 above).
- The Snipping Tool, Clipchamp, Drive, and LinkedIn clicks were written from their usual menus and not clicked through on this screen. If a button has moved, the same option is usually under the **...** menu.
- Questions after the video. The explainer (`docs/explainer.md`) covers those.
