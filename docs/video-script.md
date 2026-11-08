# Video script: the Palmquay demo (v8, 11/8: two real-world exceptions added, a change during sign-off and a shipping credit for a late delivery; sofa scene reworded; the close names tariff charges and damaged deliveries; 3:30)

*Fictional company, sample records. The demo happens in one window: `dashboard/index.html`, opened in Edge (Snipping Tool records it). Read the **Say** column out loud; the **On screen** column is what to click. The times assume about 150 words a minute, slower than normal talking, plus about 1.5 seconds for each click or scroll. If you run long, cut words, not clicks.*

## Before you record (about 5 minutes)
1. Open this folder in File Explorer, open `dashboard`, and double-click `index.html`. It opens in Edge. It's a file on this PC: nothing loads from the internet.
2. In Edge press **F11** for full screen (hides tabs, address bar, and bookmarks). If the text looks small, press **Ctrl** and **+** once (110%) so numbers read on a phone.
3. Click the clock in the taskbar and turn on **Do not disturb**, so no pop-ups land in the video.
4. Close every other window except Edge. Nothing outside this page should be on screen.
5. Open **Snipping Tool** (Start menu, type "Snipping"). Click the **video camera** icon, then **+ New**, and drag a box over the whole screen. In the recording bar, turn the **microphone** on and system audio off. Click **Start**; it counts down from 3.
6. To finish, click the red **stop** button in Snipping Tool's recording bar. Then press **F11** in Edge to leave full screen.
7. Do one practice run with a timer before the real one.
8. Keep this script on your phone or printed, not on the screen, so your mouse stays on the dashboard and every click in the **On screen** column happens. In the 11/8 take the page stopped moving at 1:11, so the furniture, invoice, and checker scenes played over the vendor table.

## Who's who (say the names; they're on the dashboard)
| Person (fictional) | Job at Palmquay | What they decide in this video |
|---|---|---|
| Dana Reyes | Facilities manager | First sign-off on every contractor; sends the follow-up emails; signs any change to an approved order; voids and resends a changed packet; decides whether to send the shipping-credit request |
| Marcus Hale | Procurement lead | Signs off on work over $10,000 |
| Priya Natarajan | Legal counsel | Signs off on work over $50,000; asks for the warranty change on Skyquay's packet |
| Tom Becker | Finance (controller) | Last sign-off on work over $50,000; decides which bills get paid |
| Lena Ortiz | Property manager | Asked for Unit 4B to be furnished |

**The story in one line:** a property company has two paperwork-heavy jobs (letting contractors work on its buildings, and buying furniture for its units); the AI does the reading, checking, and drafting, and four named people make every decision.

**The paperwork, in plain words:** before a contractor can work on a Palmquay building it sends four papers: a **W-9** (the tax form), a **certificate of insurance** (proof it's insured), its **license**, and a **work request** (what job, which building, how much).

## The script
| Time | On screen | Say |
|---|---|---|
| 0:00–0:08 | **Overview** tab. Let the tiles row sit; the "Fictional company with sample records." note in the header stays on screen. | I built an AI system that helps property management companies handle contractor and purchasing paperwork, while people keep every approval. |
| 0:08–0:29 | **Overview** tab. One slow sweep of the mouse across the five people cards under "Who works at Palmquay" (each has its own color). | To show it, I set up a fictional company: Palmquay Properties, a Sarasota company managing 14 buildings. Five employees handle this work: Lena, a property manager; Dana, the facilities manager; Marcus, the procurement lead; Priya, legal counsel; and Tom, the controller. This board shows what's waiting on whom. |
| 0:29–0:47 | **Onboarding** tab. Point at the Vendors table. | For each job, Dana writes a work request: building, work, and price. The contractor sends back a W-9 tax form, proof of insurance, and a license if needed. The AI checked all eight contractors against Palmquay's rules. |
| 0:47–1:11 | **Onboarding** tab. Scroll to "The record behind each vendor" and open "Saltmarsh Roofing Co." (its "insurance end date" row shows near the top), then scroll down to its email marked "DRAFT, not sent." | Take Saltmarsh Roofing, a Sarasota roofer quoting $42,000 to re-coat the roof at Bayfront Commons, one of Palmquay's buildings. Its insurance had expired, so the AI marked it blocked, showed the exact line, and drafted Dana an email asking for current insurance, unsent until she sends it. |
| 1:11–1:34 | **Onboarding** tab. Open "Skyquay Lift & Fire Inc." (last in the list) and scroll its first packet to the sign-offs at the bottom. | Skyquay Lift & Fire is the opposite: a $120,000 job modernizing two elevators, every paper in order. The AI built its approval packet with four blank sign-offs, in order: Dana, Marcus, Priya, then Tom. A person sends it in DocuSign or a similar tool; the AI never signs or sends. |
| 1:34–1:51 | **Onboarding** tab, same record: keep scrolling to "Approval packet, newest version" and point at its "What changed" row. | After Dana and Marcus signed, Priya asked to add a one-year warranty. Signatures don't carry over to a changed contract, so the AI built version two with the change marked, and signing restarts with Dana. |
| 1:51–2:18 | **Buying** tab. Point at the /change row (it shows the $108 over budget). | Lena asked for Unit 4B's living room and bedroom, furnished for $5,200 by November 20, and Dana approved the order. Then the sofa was backordered past move-in; the supplier suggested a replacement that arrives in time but puts the project $108 over budget, so the AI wrote a change request, and the order stays as is until Dana signs. |
| 2:18–2:33 | **Buying** tab: scroll to "Shipping credit for a late delivery" and point at its row. | Another item, the bed frame from supplier Gulfweave Furnishings, will arrive a week late, so the AI drafted Dana a request asking Gulfweave to credit half its $185 shipping charge. |
| 2:33–2:54 | **Buying** tab: scroll to "Invoices: three-way match" and point at the HOLD row. | Each bill is checked against the order and the delivery. Supplier Keystone Coast Furniture billed three lamps, not two, at a higher price, so its bill is $872, not $713. The AI holds it and shows Tom the line; Tom decides what gets paid. |
| 2:54–3:11 | **Checks** tab. Scroll to "The checker: a second AI" so its table shows; then click **Audit log** and **Play**. | A second AI, told to only read, caught the errors I planted to test it. And every step is written to a log you can replay. |
| 3:11–3:30 | **Overview** tab. | If your team chases paperwork, this could streamline it and help the work move faster, and we'd tailor it to fit your workflow, including cases like tariff charges or damaged deliveries. I designed the process, rules, and tests; Claude Code wrote the code. |

**Shorter cut (about 2 minutes):** beats 0:00-1:11, then 1:51-2:18, then the last beat.

## After you record
1. After you click stop, Snipping Tool shows the video. Click **Save** (the floppy-disk icon). Name it `palmquay-demo.mp4` and save it to Videos.
2. Watch it once with sound. Check: nothing personal on screen, every number readable, and it ends by about 3:30. To trim the ends, open it in **Clipchamp** (already on this PC), drag the clip's edges, then **Export** at 1080p.
3. Share it: drag the file into Google Drive, right-click it, **Share**, set General access to **Anyone with the link** (Viewer), then **Copy link**.
4. LinkedIn: on your profile, **Add section** > **Recommended** > **Add featured** > **Add a link**, paste the Drive link, and title it "AI operations system: vendor onboarding and procurement (demo)". Add `docs/diagram.png` the same way with **Add media**.

## What this script doesn't cover
- The one-page diagram (Map tab) doesn't show the two newest steps yet (`/revise`, `/credit`); the dashboard tabs do.
- How the recording looks and sounds. That gets checked when you watch it back (step 2 above).
- The Snipping Tool, Clipchamp, Drive, and LinkedIn clicks were written from their usual menus and not clicked through on this screen. If a button has moved, the same option is usually under the **...** menu.
- Questions after the video. The explainer (`docs/explainer.md`) covers those.
