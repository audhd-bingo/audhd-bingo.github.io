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
        "on repeat",
        "same song",
        "one song"
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
    hits = []
    for sg in segs:
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
                # phrase closeness: multiple distinct phrases -> higher
        if sc:
            hits.append((sg["s"], sg["e"], sc))
    if not hits:
        return []
    # cluster into windows: consecutive segments (within gap) -> one clip
    wins = []
    for s, e, sc in hits:
        if wins and s - wins[-1]["e"] < 2.0:
            wins[-1]["e"] = e
            wins[-1]["score"] = max(wins[-1]["score"], sc)
        else:
            wins.append({"s": s, "e": e, "score": sc})
    # expand each window a bit for context, cap length
    expanded = []
    for w in wins:
        segs_in = [sg for sg in segs if sg["s"] >= w["s"] - 3 and sg["e"] <= w["e"] + 3]
        if segs_in:
            w["s"] = max(0, segs_in[0]["s"])
            w["e"] = segs_in[-1]["e"]
        if w["e"] - w["s"] > 45:
            w["e"] = w["s"] + 45
        expanded.append(w)
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
                key = vidShort[vid]
                sym["clips"].append({
                    "video": key, "start": round(w["s"]), "end": round(w["e"]),
                    "score": w["score"], "title": title, "text": seg_text(rec, w)
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--score", action="store_true")
    a = ap.parse_args()
    transcripts = fetch_transcripts(force=a.fetch) if a.fetch else {
        f[:-5]: json.load(open(os.path.join(TRANS_DIR, f)))
        for f in os.listdir(TRANS_DIR) if f.endswith(".json")
    }
    if a.score:
        build(transcripts)
    else:
        print("transcripts ready. run with --score to build symptoms.json + review.csv")


if __name__ == "__main__":
    main()