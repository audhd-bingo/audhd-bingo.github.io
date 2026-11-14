# AuDHD Bingo — clip & transcript data pipeline

Run with:  python3 build_clips.py --score   (cache transcripts) | --fetch --score (re-pull)

- transcripts/  : auto-caption segments (from yt-dlp) per source video
- symptoms.json : each symptom carries an ordered `clips` list (gallery order;
                  best match first) with {video, start, end, score, title, text}
- review.csv    : human gate — spot-check every auto-matched clip

## Semantic (BERT) extra matches

`python3 build_clips.py --score --semantic` runs an SBERT MiniLM pass that
appends cosine-similarity matches after the keyword clips and stamps `sem` on
every clip; the gallery toggle (🧠 Semantic order) then sorts by it.

**Known limitation:** on the current 7-video corpus the semantic scores do
NOT discriminate between symptoms — every video talks about generic AuDHD, so
correct windows score ≈ wrong windows (both ~0.5 cosine). The pass currently
adds noise, not signal. It was tested and intentionally NOT applied: keep the
data keyword-only. The pass becomes useful once the pool includes dedicated
per-symptom videos (one video about interoception, one about double empathy,
etc.). Re-run `--score --semantic` after expanding `VIDEOS`.

