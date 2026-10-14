# 3D Gyaan — nightly video factory runbook

This is the procedure the nightly scheduled session follows. Goal: **3 Hindi 3D explainer videos on today's biggest world news, rendered between 10:00 PM and 1:00 AM IST and handed to the owner, who reviews and posts them.**

## 0. Setup (every session, ~3 min)
```bash
cd <repo> && ./setup.sh
```
Environment variables (set in the cloud environment settings, never in chat or in the repo):
- `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID` (the "Viraj" voice) — optional; without them the free offline Hindi voice is used.
- `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` — needed for upload.
- Network allow-list must include `api.elevenlabs.io`, `oauth2.googleapis.com`, `www.googleapis.com`.

## 1. Pick 3 topics (≤ 20 min)
Use web search for the last 24 hours of world news. Pick **3 different, big, visual stories** (space, tech, science, economy, world events, sports, climate…).

**Hard safety rules — skip a story if any apply:**
- Active tragedies with casualties, terror attacks, communal/religious conflict, or anything that could inflame violence.
- Elections, candidates, or political claims that are disputed.
- Health/medical advice, or unverified rumours / single-source claims.
- Anything about a private individual.
Every fact must appear in **at least 2 reputable sources** (Reuters, AP, BBC, PTI, The Hindu, Indian Express, NDTV, Bloomberg, official sites). If unsure of a number, leave it out. Never invent quotes, numbers or dates.
Don't repeat a topic already covered — check `published.json`.

## 2. Write the plan (`plans/YYYY-MM-DD-<slug>.json`)
2.5–3.5 min. Tone: friendly "bhai" Hindi for Indian teens, fun but accurate. Structure:
1. **Hook** (≤15 s): shocking number/question, `bigcount` + `bigtext` + a center `stamp`.
2. **Title** scene (`title` or `headline` overlay, ~3 s).
3. 6–9 story scenes, one idea each, with a **different 3D shot each time**.
4. **Verdict/what it means for India** scene.
5. **Outro**: question for comments + "3D Gyaan को सब्सक्राइब करो".

Schema:
```json
{
 "title": "YouTube title (≤ 90 chars, Hinglish, no clickbait lies)",
 "caption_keywords": ["isro","india","…"],
 "thumbnail": {"scene":0,"f":0.9,"line1":"BIG TEXT","line2":"second line","badge":"🚨 BREAKING"},
 "meta": {"description":"…(include a Sources: list of URLs and 'AI-generated narration & visuals')","tags":["…"],"categoryId":"25"},
 "scenes": [
  {"voice": "Hindi (Devanagari) narration — numbers written as words",
   "caption": "Same sentence in Hinglish (Roman Hindi) — shown as subtitles",
   "shots": [ {shot}, … ], "beats": [0, 0.5],            // beat = fraction of scene when each shot starts
   "overlay": [ {overlay}, … ]}
 ]
}
```
**Shots** (`type`):
- `globe` `{lat, lon, dist:0.6–2.5, pins:[{lat,lon,label,color:"red"|"green"}], arcs:[{from:[lat,lon],to:[lat,lon],color}], cities:true (India city lights), india:true (India remote sites), sats:false}`
- `globeWide` `{spin, sats:true}` — whole Earth spinning, optional 10,000-satellite swarm
- `bars` `{items:[{label:"NAME · ₹123", value:123}, …]}` — gold coin stacks (2–4 items, labels in Latin script)
- `city` `{close:false}` — night city skyline with traffic
- `rocket` `{lat, lon, train:false}` — launch from that spot, camera follows
- `preset` `{name}` — `title`, `outro`, `swarm`, `hookwide`, `hero` (satellite close-up), `vWide`/`vHouse`/`vSky` (Ladakh village), `boatWide`/`boatClose` (sea + police boat), `cmp` (orbit comparison), `shells` (satellite orbits)

**Overlays** (`kind`, `f` = when it appears, fraction of the voice line):
`kin` (big headline, top-left, `{n|suffix}` inside text makes an animated counter, e.g. `"{900|M+} लोग"`), `stk` (sticker, `color: y|r|g|""`), `stamp` (`text,color: red|green|gold, f, center:true`), `bigcount` `{value,suffix,label,hide}`, `bigtext` `{text,show}`, `versus` `{a,c,f}`, `title` `{tag,a,vs,c}`, `headline` `{tag,text,size}`, `outro` `{big,q,cta,src}`, `foot` `{text}`.
Keep on-screen text short (≤ 5 words). Every story scene: 1 `kin` + 1–3 `stk`, a `stamp` on the 2–3 biggest moments only.

Validate quickly before rendering: `node scripts/render.js probe 0:0.5 2:0.5 …` with `engine/plan.js` (written by `scripts/caps.py`), then look at the `pr_*.jpg` frames (`python3 scripts/sheet.py`).

## 3. Make each video (~35 min each at 720p, sequential)
```bash
scripts/make_video.sh plans/<file>.json out/<slug>
```
Write `out/<slug>/meta.json` from the plan's `meta` + `title`. Look at `thumbnail.jpg` and 3–4 frames of `video.mp4` (`ffmpeg -ss <t> -i video.mp4 -frames:v 1 x.jpg`) — fix and re-render if text overlaps, the globe is empty, or captions are missing.

## 4. Deliver (the owner posts by hand)
Do NOT upload. For each video send the owner `out/<slug>/video_send.mp4` and `out/<slug>/thumbnail.jpg`, and write out the
YouTube title, description (with Sources and the line "AI-generated narration & visuals") and tags, ready to paste.
Remind them to tick YouTube's "altered or synthetic content" box when it applies.
Append `{date, slug, title}` to `published.json`, commit and push.
(`scripts/upload_youtube.py` exists for later, if the owner sets up YouTube API access and asks for uploads.)

## 5. Report
End with a short summary: the 3 titles, YouTube links (or why an upload failed), the voice used, and anything skipped for safety.
