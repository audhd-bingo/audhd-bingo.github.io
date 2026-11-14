#!/usr/bin/env python3
"""Build AuDHD Bingo clip + transcript data.

Pulls YouTube auto-captions for each candidate video (via yt-dlp), parses to
per-video segment JSON stored under transcripts/, keyword-matches each symptom
to the best windows, and writes symptom->ordered clip list into symptoms.json
plus a review.csv for a human spot-check. Idempotent per video.

Usage: python3 build_clips.py [--fetch] [--score]
  --fetch  re-pull missing transcripts with yt-dlp (else read cached)
  --score  re-run matching and rewrite symptoms.json + review.csv

One-time note: this is DETERMINISTIC offline stored data (a "sample in advance"
approach) — the live site just plays the recorded clip windows, no runtime AA.
"""
import argparse, json, os, re, subprocess, sys
ROOT = os.path.dirname(os.path.abspath(__file__))
SYMPTOMS_JSON = os.path.join(ROOT, "symptoms.json")
TRANS_DIR = os.path.join(ROOT, "transcripts")

# candidate videos: id -> (title). Titles for gallery + transcripts.
VIDEOS = {
    "7kBGUcGeKvM": "5 Signs You Have AuDHD (ADHD and Autism)",
    "rihlhHR3tow": "Autism vs ADHD: 5 Key Differences Explained",
    "ZlFSeamEJbA": "5 Signs You're A High-Masking Autistic With ADHD",
    "lsyVwDh99rQ": "AuDHD explained: Can you have ADHD and autism at the same time?",
    "jM3azhiOy5E": "How to Deal with Rejection Sensitivity",
    "rC3tG3lbrNM": "How to (Actually) Get Out the Door on Time",
    "wk_iX7pXGwk": "Time Blindness - An ADHD or Executive Dysfunction Trait",
    # ---- focused per-symptom pool (adds discriminating signal for semantic pass) ----
    "HszXKZO_H18": "Why I Can't Remember Things -- How ADHD Affects Working Memory",
    "EA5g83TsVJw": "The Trouble with Transitions: Task Switching and ADHD",
    "F0uEDEwJGx8": "ADHD & Interrupting - Episode 86 - ADHD Power Tools",
    "xR0Iy-1xOqo": "Face Value (Expressions & Flat Affect) Autism & Relationships",
    "QZBe0rtiInc": "ADHD Stimming | Why It Happens and How to Manage It",
    "ed0izgeDHYA": "The real reason your ADHD brain forgets to eat (it's not laziness)",
    "Xp805f-j1VI": "Why People with ADHD Procrastinate (And 4 Brain-Based Ways to Get Started)",
    "rSLPWgyV9Ls": "Echolalia & Autism - Understanding Why Autistic People Repeat Words",
    "bSW8wf4f2hE": "Anxiety and Sensory Processing Disorder - Which Comes First?",
    "8hnn0weNtjE": "How to Make Phone Calls When You Have Anxiety",
    "agdVnnS_Qb4": "The ADHD Hobby Trap: Dopamine, Rejection Sensitivity and Losing Interest",
    "yyziesUYVbs": "Why Autistic Sensory Issues Aren't What You Think",
    "E68ovEXFQAo": "ADHD Hyperfocus Explained (and how to use it to your ADVANTAGE)",
    "uunOBIBpi6E": "How to Be Social with Autism (Social skills)",
    "tipVjtS0NSI": "Why You Forget Why You Entered A Room (The Doorway Effect Explained)",
    "fMNHs3go788": "Why Can't I Ignore Clothing Tags & Sock Seams? Neurodivergent Sensory",
    "ikmB7iDXYqY": "Justice Sensitivity Is Draining ADHD & Autistic Lives",
    "BPKJ1sE3Ss8": "Autism, Humour & Sarcasm - What You Need to Know",
    "7DaWdaxzA3c": "The Double Empathy Problem - Dr Damian Milton - Autism Explained Online",
}

# symptom name -> search keywords (phrases; matched case/diacritic-insensitively)
KEYWORDS = {
    "Time blindness — '5 minutes' becomes 50": [
        "time blindness",
        "lose track of time",
        "hours go by",
        "five minutes",
        "how long has it been",
        "underestimate how long"
    ],
    "Losing the thing in your hand": [
        "can't find",
        "lost it",
        "misplace",
        "where did it go",
        "lose my"
    ],
    "Hyperfixation for weeks, then total drop": [
        "special interests",
        "intense focus",
        "hyperfixation",
        "obsessed with",
        "long special interests"
    ],
    "Zoning out mid-conversation": [
        "zone out",
        "zoning out",
        "spacing out",
        "checked out",
        "drift off"
    ],
    "Rambling / talking over people": [
        "talk over",
        "interrupt",
        "ramble",
        "more than usual",
        "blurt out"
    ],
    "Rehearsing conversations in your head": [
        "rehears",
        "scripting",
        "practice the conversation",
        "run through the conversation"
    ],
    "Stimming to regulate": [
        "stim",
        "flapping",
        "rock back",
        "repetitive movement",
        "hand flapping"
    ],
    "Sensory overload meltdown": [
        "sensory overload",
        "overstimulated",
        "meltdown",
        "sensory overwhelm"
    ],
    "Masking until you're exhausted": [
        "masking",
        "mask our",
        "pretending to be",
        "camouflage"
    ],
    "Difficulty with transitions": [
        "transitions",
        "hard to switch",
        "switching tasks",
        "get into a new"
    ],
    "Interrupting because you'll forget": [
        "interrupt",
        "so i don't forget",
        "before i forget"
    ],
    "Flat affect (resting face)": [
        "resting face",
        "flat affect",
        "don't look excited"
    ],
    "Task paralysis / executive dysfunction": [
        "executive function",
        "task paralysis",
        "can't get started",
        "overwhelm"
    ],
    "Rejection sensitivity": [
        "rejection",
        "rejection sensitivity",
        "rsd",
        "afraid of rejection",
        "fear of rejection"
    ],
    "Special interest monologues": [
        "special interests",
        "infodump",
        "info dump",
        "passionate about"
    ],
    "Fidgeting constantly": [
        "fidget",
        "can't sit still",
        "restless"
    ],
    "Forgetting to eat or drink": [
        "forget to eat",
        "haven't eaten",
        "skip meals",
        "not eating"
    ],
    "Reading social cues wrong": [
        "social cues",
        "miss the cue",
        "read the room"
    ],
    "Oversharing / too blunt": [
        "overshare",
        "too honest",
        "no filter",
        "blunt"
    ],
    "Can't start a task unless it's urgent": [
        "last minute",
        "deadline",
        "procrastinate",
        "urgent"
    ],
    "Echolalia / repeating phrases": [
        "echolalia",
        "repeat the same",
        "say it back"
    ],
    "Sensory-seeking (crash, squeeze, weighted)": [
        "deep pressure",
        "weighted",
        "crash pad",
        "grounding"
    ],
    "Invisible panic before phone calls": [
        "phone call",
        "phone anxiety",
        "dread the phone"
    ],
    "Collecting hobbies, finishing none": [
        "multiple hobbies",
        "start projects",
        "new hobby",
        "many interests"
    ],
    "Body feels things others don't notice": [
        "notice things",
        "bump into things"
    ],
    "Hyperfocus for hours": [
        "hyperfocus",
        "hours and hours"
    ],
    "Scripting what to say": [
        "script",
        "what to say before",
        "rehearse the conversation"
    ],
    "Detail blindness then whole checklist matters": [
        "miss details",
        "the details",
        "overlook"
    ],
    "Forgot why you walked into the room": [
        "why did i come",
        "walked into the room",
        "forgot what"
    ],
    "Textures / tags unbearable": [
        "tags",
        "itchy",
        "texture",
        "scratchy"
    ],
    "Needs a routine but can't keep one": [
        "routine",
        "structure",
        "keep a schedule"
    ],
    "Obsessive rules fairness": [
        "fair",
        "unfair",
        "rules",
        "justice"
    ],
    "Can't filter background noise": [
        "background noise",
        "too much noise",
        "every sound"
    ],
    "Meltdown after masking all day": [
        "meltdown",
        "shutdown",
        "crash when i get home"
    ],
    "Music strictly one song on repeat": [
        "same song",
        "one song",
        "listen to the same",
        "the same song",
        "song on repeat"
    ],
    "Loves a good spreadsheet to organise": [
        "spreadsheet",
        "organize",
        "to-do list",
        "planning system"
    ],
    "Takes jokes literally": [
        "take things literally",
        "take it literally",
        "sarcasm"
    ],
    "Exhausted by socialising even when fun": [
        "exhausted after socializing",
        "social battery",
        "drained by people"
    ],
    "Keeps 'nice to haves' in your bag for 3 months": [
        "in my bag",
        "never use",
        "carry around"
    ],
    "Double empathy — reads animals better than people": ["double empathy","empathy gap","understand people"]
}


# ---------- transcript parsing ----------
def parse_vtt(path):
    """Return list of {s,e,text} segments (times in seconds)."""
    segs = []
    cur_s = cur_e = None
    buf = []
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.rstrip("\n")
        m = re.match(r"(\d\d):(\d\d):(\d\d)\.(\d\d\d) --> (\d\d):(\d\d):(\d\d)\.(\d\d\d)", line)
        if m:
            hh,mm,ss,ms,h2,m2,s2,ms2 = (int(g) for g in m.groups())
            cur_s = hh*3600+mm*60+ss+ms/1000
            cur_e = h2*3600+m2*60+s2+ms2/1000
            continue
        if line and cur_s is not None and not line.startswith(("WEBVTT", "Kind:", "Language", "NOTE")):
            # strip VTT tags
            clean = re.sub(r"<[^>]+>", "", line).strip()
            if clean:
                buf.append(clean)
        elif not line and cur_s is not None:
            if buf:
                segs.append({"s": cur_s, "e": cur_e, "text": " ".join(buf)})
            buf = []
            cur_s = None
    if buf and cur_s is not None:
        segs.append({"s": cur_s, "e": cur_e, "text": " ".join(buf)})
    return segs


def fetch_transcripts(force=False):
    os.makedirs(TRANS_DIR, exist_ok=True)
    have = {}
    for vid, title in VIDEOS.items():
        jp = os.path.join(TRANS_DIR, vid + ".json")
        if os.path.exists(jp) and not force:
            have[vid] = json.load(open(jp))
            continue
        vtt = os.path.join("/tmp", "audhd_subs", vid + ".en.vtt")
        if not os.path.exists(vtt):
            subprocess.run(["yt-dlp", "--skip-download", "--write-auto-subs", "--write-subs",
                            "--sub-langs", "en", "--convert-subs", "vtt",
                            "-o", os.path.join("/tmp", "audhd_subs", "%(id)s"),
                            "https://www.youtube.com/watch?v=" + vid], check=False)
        segs = parse_vtt(vtt) if os.path.exists(vtt) else []
        rec = {"id": vid, "title": title, "segments": segs}
        json.dump(rec, open(jp, "w"), ensure_ascii=False, indent=1)
        have[vid] = rec
        print(f"  transcript {vid}: {len(segs)} segments")
    return have


def norm(s):
    s = s.lower()
    for a,b in [("’","'"),("‘","'"),("“",'"'),("”",'"'),("‐","-"),("–","-")]:
        s = s.replace(a,b)
    return re.sub(r"[^a-z0-9']+", " ", s).strip()


def flat_text(rec):
    """Yield (start, text) per segment."""
    for sg in rec["segments"]:
        yield sg["s"], sg["e"], norm(sg["text"])


# single words that are genuinely distinctive to a symptom (rare enough to be
# a strong signal on their own)
STRONG_WORDS = {"hyperfocus","hyperfixation","stimming","stim","echolalia","rsd",
                "meltingdown","shutdown","misplace","overshare","camouflage","remasking"}

def find_clip_windows(rec, keywords, dur_guess=30):
    """Return list of {s,e,score} best windows containing keyword hits, deduped.

    Scored by exact phrase presence; multi-word phrases and strong single tokens
    weigh more than generic single words, so "literally" can't gate a clip.
    """
    segs = rec["segments"]
    kws = [norm(k) for k in keywords if k]
    if not kws:
        return []
    def seg_score(sg):
        t = norm(sg["text"])
        sc = 0
        for k in kws:
            if k in t:
                # a multi-word phrase is a strong signal (e.g. "time blindness")
                if " " in k:
                    sc += 2
                # single generic word only counts if it's a distinctive token
                elif k.strip("'") in STRONG_WORDS:
                    sc += 2
                else:
                    sc += 0  # generic single word: no score, may still reorder
        return sc
    hits = []
    for sg in segs:
        sc = seg_score(sg)
        if sc:
            hits.append((sg["s"], sg["e"], sc))
    if not hits:
        return []
    # cluster into seed windows: consecutive scored segments (within gap) -> one clip
    wins = []
    for s, e, sc in hits:
        if wins and s - wins[-1]["e"] < 2.0:
            wins[-1]["e"] = e
            wins[-1]["score"] = max(wins[-1]["score"], sc)
        else:
            wins.append({"s": s, "e": e, "score": sc})
    # extend each seed: keep rolling forward while the topic is still being
    # discussed. A stretch of N keyword-free segments = subject moved on; cap
    # the clip so we never swallow half the video.
    TOPIC_RUN = 4    # consecutive keyword-free segments (~8s of unrelated speech) end the clip
    MAX_CLIP = 90    # hard ceiling (seconds)
    LEAD_IN = 4      # seconds of context before the first hit
    expanded = []
    for w in wins:
        s0 = max(0, w["s"] - LEAD_IN)
        e0 = w["e"]
        free_run = 0
        # find segment after the seed's end and keep appending it until the
        # keywords vanish for TOPIC_RUN segments straight.
        for sg in segs:
            if sg["s"] < e0:
                continue
            if seg_score(sg) == 0:
                free_run += 1
            else:
                free_run = 0
            if free_run > TOPIC_RUN:
                break
            e0 = max(e0, sg["e"])
            if e0 - s0 > MAX_CLIP:
                e0 = s0 + MAX_CLIP
                break
        # note: seg_score consumes the *current* segment; a keyword segment resets the run
        expanded.append({"s": s0, "e": e0, "score": w["score"]})
    # dedupe overlapping windows, keep best
    expanded.sort(key=lambda w: -w["score"])
    out = []
    for w in expanded:
        if not any(abs(w["s"] - o["s"]) < 8 for o in out):
            out.append(w)
        if len(out) >= 3:
            break
    return out


def load_symptoms():
    return json.load(open(SYMPTOMS_JSON))


def build(transcripts):
    data = load_symptoms()
    # video shorthand for symptoms.json: map id -> short name (first 6 chars) for compactness, but
    # keep a full reference list too
    vidShort = {v[0]: "v" + v[0][:6] for v in VIDEOS.items()}
    data["videos"] = {vidShort[k]: {"id": k, "title": t, "dur": 0} for k, t in VIDEOS.items()}
    rows = []
    for sym in data["symptoms"]:
        name = sym["name"]
        kws = KEYWORDS.get(name, [])
        sym["clips"] = []      # ordered by relevance
        for vid, title in VIDEOS.items():
            rec = transcripts.get(vid)
            if not rec or not rec.get("segments"):
                continue
            wins = find_clip_windows(rec, kws)
            for w in wins:
                if w["score"] < 2:
                    continue   # gate: a generic single-word hit is not a clip
                s2, e2 = _expand_to_sentence(rec, w["s"], w["e"])
                key = vidShort[vid]
                sym["clips"].append({
                    "video": key, "start": round(s2), "end": round(e2),
                    "score": w["score"], "title": title, "text": seg_text(rec, {"s": s2, "e": e2})
                })
        # order all clips across videos by score
        sym["clips"].sort(key=lambda c: -c["score"])
        # keep top 4 per symptom (gallery)
        sym["clips"] = sym["clips"][:4]
        for c in sym["clips"]:
            rows.append({"symptom": name, "video": c["video"], "start": c["start"],
                         "end": c["end"], "score": c["score"], "snippet": c["text"][:80]})
        if not sym["clips"]:
            rows.append({"symptom": name, "video": "", "start": "", "end": "",
                         "score": 0, "snippet": "NO MATCH - needs a dedicated video"})
    json.dump(data, open(SYMPTOMS_JSON, "w"), ensure_ascii=False, indent=2)
    import csv
    with open(os.path.join(ROOT, "review.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["symptom", "video", "start", "end", "score", "snippet"])
        w.writeheader()
        w.writerows(rows)
    print(f"wrote symptoms.json + review.csv ({len(rows)} clip rows, {sum(1 for r in rows if not r['video'])} unmatched)")


def seg_text(rec, w):
    return " ".join(sg["text"] for sg in rec["segments"]
                    if sg["s"] >= w["s"] and sg["e"] <= w["e"])


_FINAL = re.compile(r'[.?!…]["\'”’)\]]*\s*$')

def _expand_to_sentence(rec, s, e, cap_segs=4):
    """Expand [s,e] to self-contained sentence boundaries.

    Backward: include previous segments while the preceding segment does not
    end with final punctuation (the sentence started earlier).
    Forward: include following segments until one ends with final punctuation.
    cap_segs bounds how far we roam so a clip never swallows a new topic.
    """
    segs = rec["segments"]
    if not segs:
        return s, e
    i = next((k for k, g in enumerate(segs) if g["e"] >= s), 0)
    j = next((k for k, g in enumerate(segs) if g["s"] > e), len(segs))
    # backward: prepend while the kept start doesn't begin a sentence
    k = i
    for _ in range(cap_segs):
        if k == 0:
            break
        if _FINAL.search(segs[k - 1]["text"]):
            break
        k -= 1
    # forward: append until a segment ends a sentence
    m = max(j - 1, i)
    for _ in range(cap_segs):
        if m >= len(segs) - 1:
            break
        if _FINAL.search(segs[m]["text"]):
            break
        m += 1
    return segs[k]["s"], segs[m]["e"]


# ---------- semantic (BERT) extra matches ----------
# Appends clip windows ranked by sentence-embedding cosine similarity between
# the symptom's TTS description and transcript windows. Keyword clips keep the
# leading positions; semantic clips are appended AFTER them so the original
# gallery order stands. Uses a local SBERT MiniLM model; lazy import so the
# plain --score path never needs torch.
SEM_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
WIN_SEGS = 8      # transcript segments per candidate window (~16s of speech)
WIN_STEP = 4      # overlap between candidate windows
SEM_DIFF = 0.20   # discriminative score floor: sim-to-this minus sim-to-other-desc baseline
SEM_STRONG = 0.45 # above this, accept without a keyword anchor (focused-video wording differs)
SEM_MAX = 3       # extra clips appended per symptom
SEM_OVERLAP = 8   # seconds; skip windows too close to an existing clip

def _embed(model, texts):
    import numpy as np
    embs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(embs)

def _windows(rec):
    segs = rec["segments"]
    out = []
    for i in range(0, max(1, len(segs) - WIN_SEGS + 1), WIN_STEP):
        out.append((segs[i]["s"], segs[i + WIN_SEGS - 1]["e"],
                    " ".join(g["text"] for g in segs[i:i+WIN_SEGS])))
    return out

def _video_emb(transcripts, vid, model, cache_dir):
    """Cache window (start,end) + embeddings per video on disk; encode once."""
    import numpy as np
    import os as _os
    rec = transcripts.get(vid)
    if not rec or not rec.get("segments"):
        return None, None
    key = f"{vid}_{WIN_SEGS}_{WIN_STEP}"
    npz = _os.path.join(cache_dir, key + ".npz")
    if _os.path.exists(npz):
        z = np.load(npz, allow_pickle=True)
        return list(z["s_e"]), z["em"]
    wins = _windows(rec)
    if not wins:
        return None, None
    em = _embed(model, [w[2] for w in wins])
    _os.makedirs(cache_dir, exist_ok=True)
    np.savez(npz, s_e=np.array([(w[0], w[1]) for w in wins], dtype="float32"), em=em)
    return [(w[0], w[1]) for w in wins], em

def add_semantic(transcripts, sym, descs, D, model, cache_dir):
    """Discriminative semantic match: window sim to THIS desc minus its mean
    sim to the other 39 descs. Focused videos make this separate signal;
    generic AuDHD talk cancels out. Append at most SEM_MAX after keyword clips."""
    import numpy as np
    desc = (sym.get("desc") or "").strip()
    if not desc or desc not in descs:
        return
    self_i = descs.index(desc)
    dvec = D[self_i]
    # generic baseline: mean over all OTHER symptom descs
    mask = np.ones(D.shape[0], bool); mask[self_i] = False
    base = D[mask].mean(axis=0)
    # stamp sem on existing keyword clips (uniform sorting key)
    for c in sym.get("clips", []):
        t = c.get("text", "")
        c["sem"] = round(float(dvec @ _embed(model, [t])[0]), 3) if t else 0
    take = list(sym.get("clips", []))
    used = [(c["start"], c["end"]) for c in take]
    kws = [norm(k) for k in KEYWORDS.get(sym.get("name","") or "", [])]
    adds = []
    for vid, title in VIDEOS.items():
        s_e, em = _video_emb(transcripts, vid, model, cache_dir)
        if s_e is None:
            continue
        raw = em @ dvec
        gen = em @ base
        diff = raw - gen
        for (s, e), d in zip(s_e, diff):
            if float(d) < SEM_DIFF:
                continue
            s2, e2 = _expand_to_sentence(transcripts[vid], s, e)
            if any(abs(s2 - a) < SEM_OVERLAP for a, _ in used + [(x["start"], x["end"]) for x in adds]):
                continue
            txt = seg_text(transcripts[vid], {"s": s2, "e": e2})
            # hybrid gate: BERT ranks, but usually require the window to also
            # mention the symptom's own keyword phrases (no off-topic noise).
            # A very high discriminative score alone is accepted: focused
            # videos phrase things differently than the keyword lists.
            if kws and float(d) < SEM_STRONG:
                if not any(norm(k) in norm(txt) for k in kws):
                    continue
            adds.append({"video": "v" + vid[:6], "start": round(s2), "end": round(e2),
                         "score": 0, "sem": round(float(d), 3),
                         "title": title, "text": txt[:600]})
    adds.sort(key=lambda c: -c["sem"])
    sym["clips"] = take + adds[:SEM_MAX]   # keyword order first, then semantic


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--semantic", action="store_true", help="append BERT-semantic matches after keyword clips")
    a = ap.parse_args()
    transcripts = fetch_transcripts(force=a.fetch) if a.fetch else {
        f[:-5]: json.load(open(os.path.join(TRANS_DIR, f)))
        for f in os.listdir(TRANS_DIR) if f.endswith(".json")
    }
    if a.score:
        build(transcripts)
    if a.semantic:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(SEM_MODEL)
        data = load_symptoms()
        descs = [s.get("desc", "").strip() for s in data["symptoms"]]
        D = _embed(model, descs)   # 40 x 384, one encode
        cache_dir = os.path.join(ROOT, ".semcache")
        for sym in data["symptoms"]:
            add_semantic(transcripts, sym, descs, D, model, cache_dir)
        json.dump(data, open(SYMPTOMS_JSON, "w"), ensure_ascii=False, indent=2)
        n = sum(len(s["clips"]) for s in data["symptoms"])
        print(f"semantic pass done; {n} total clips across {len(data['symptoms'])} symptoms")
    if not (a.score or a.semantic):
        print("transcripts ready. run with --score to build symptoms.json + review.csv")


if __name__ == "__main__":
    main()