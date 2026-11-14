# AuDHD Bingo — clip & transcript data pipeline

Run with:  python3 build_clips.py --score   (cache transcripts) | --fetch --score (re-pull)

- transcripts/  : auto-caption segments (from yt-dlp) per source video
- symptoms.json : each symptom carries an ordered `clips` list (gallery order;
                  best match first) with {video, start, end, score, title, text}
- review.csv    : human gate — spot-check every auto-matched clip

