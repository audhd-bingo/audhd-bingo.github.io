#!/usr/bin/env python3
"""Attach a plain-English description + verified source pages to each symptom.

Descriptions are short (2-3 sentences), name the jargon in parentheses, and
point to real, curl-verified pages the player can open. Run: python3 add_desc.py
"""
import json

S = {
 "chadd_time":  {"title":"CHADD: Managing Time Blindness at Work","u":"https://chadd.org/adhd-news/adhd-news-adults/attention-time-unbound-managing-time-blindness-at-work/"},
 "add_time":    {"title":"ADDA: ADHD Time Blindness","u":"https://add.org/adhd-time-blindness/"},
 "auhd_over":   {"title":"Autistica: ADHD and autism (AuDHD)","u":"https://www.autistica.org.uk/what-is-autism/adhd-and-autism"},
 "adult_auhd":  {"title":"Autism Society: Recognising Autism and ADHD","u":"https://autism.org/adult-audhd-recognising-autism-and-adhd-later-in-life/"},
 "add_auhd":    {"title":"ADDitude: AuDHD Symptoms in Adults","u":"https://www.additudemag.com/adult-autism-symptoms-adhd/"},
 "chadd_ef":    {"title":"CHADD: Executive Function Skills","u":"https://chadd.org/about-adhd/executive-function-skills/"},
 "chadd_melt":  {"title":"CHADD: Understanding Meltdowns (ADHD Volcano)","u":"https://chadd.org/adhd-news/adhd-news-adults/understanding-emotional-meltdowns/"},
 "rsd_add":     {"title":"ADDitude: Rejection Sensitive Dysphoria","u":"https://www.additudemag.com/rejection-sensitive-dysphoria-adhd-emotional-dysregulation/"},
 "rsd_cc":      {"title":"Cleveland Clinic: Rejection Sensitive Dysphoria","u":"https://my.clevelandclinic.org/health/diseases/24099-rejection-sensitive-dysphoria-rsd"},
 "sens_asuk":   {"title":"National Autistic Society: Sensory Processing","u":"https://www.autism.org.uk/advice-and-guidance/about-autism/sensory-processing"},
 "sens_as":     {"title":"Autism Speaks: Sensory Issues","u":"https://www.autismspeaks.org/sensory-issues"},
 "mask_pmc":    {"title":"PMC: Experiences of Masking","u":"https://pmc.ncbi.nlm.nih.gov/articles/PMC8992921/"},
 "mask_nk":     {"title":"Neurokin: Autism Masking in Adults","u":"https://www.neurokin.com/autism-masking-in-adults"},
 "cm_spd":      {"title":"Child Mind Institute: Sensory Processing Issues","u":"https://childmind.org/article/sensory-processing-issues-explained/"},
 "ea_faq":      {"title":"Embrace Autism: AuDHD FAQ","u":"https://embrace-autism.com/audhd-faq/"},
}

DESC = {
 "Time blindness — '5 minutes' becomes 50":
   ("Time blindness (time agnosia) is a common ADHD experience of not being able to perceive or estimate time — how long a task takes, or how long has passed. Instead of a clock, time feels like \"now\" or \"not now\", so a quick task can absorb an hour and leave you late.",
    ["chadd_time","add_time"]),
 "Losing the thing in your hand":
   ("Losing items even while holding them is a working-memory sign. The ADHD brain drops the active thought (\"keys in hand\") the moment something new arrives, so the object effectively disappears from awareness.",
    ["chadd_ef","adult_auhd"]),
 "Hyperfixation for weeks, then total drop":
   ("Hyperfixation is an intense, all-consuming focus on one interest that can last days or weeks, common to both ADHD and autism. When the interest fades, engagement can drop to zero almost overnight — a classic AuDHD pattern of intense focus alternating with boredom.",
    ["auhd_over","ea_faq"]),
 "Zoning out mid-conversation":
   ("Zoning out (spacing out or dissociating) happens when the brain's attention network loses the thread of a conversation, often in AuDHD where attention can pull toward internal thoughts or sensory details. It is not a choice — you can lose whole sentences while your face keeps nodding.",
    ["adult_auhd","add_auhd"]),
 "Rambling / talking over people":
   ("Talking over people or rambling is linked to ADHD impulsivity — the thought must come out before it is forgotten. In autism it can look like info-dumping on a special interest without reading whether the listener is still engaged.",
    ["adult_auhd","auhd_over"]),
 "Rehearsing conversations in your head":
   ("Rehearsing conversations is a form of autism masking and social scripting — planning exact words in advance because spontaneous social exchange feels unpredictable. The cost is extra mental effort and replaying past conversations again afterward.",
    ["mask_nk","mask_pmc"]),
 "Stimming to regulate":
   ("Stimming (self-stimulatory behaviour) — hand flapping, rocking, bouncing a leg — is how many autistic and AuDHD people regulate focus, emotion, or sensory overload. It is functional, not a behaviour to suppress; stopping it can increase distress.",
    ["sens_as","sens_asuk"]),
 "Sensory overload meltdown":
   ("Sensory overload is when the brain receives more sensory input than it can process, and overwhelm builds until the nervous system can no longer regulate. That is what a meltdown is — an involuntary response to overload, very different from a tantrum.",
    ["sens_asuk","sens_as"]),
 "Masking until you're exhausted":
   ("Masking (camouflaging) is consciously or unconsciously hiding autistic/ADHD traits to appear \"normal\" — suppressing stims, scripting responses, forcing eye contact. It works socially but costs enormous energy, which is why AuDHD people often crash after social events.",
    ["mask_pmc","mask_nk"]),
 "Difficulty with transitions":
   ("Task-switching (transitioning) draws heavily on executive function, which is often delayed in ADHD. Moving from one activity to another — especially away from something absorbing — can feel physically hard and needs explicit support rather than willpower.",
    ["chadd_ef","adult_auhd"]),
 "Interrupting because you'll forget":
   ("Interrupting to say something before it escapes is a working-memory impulse: in ADHD, holding a thought while waiting for a turn is unreliable, so the brain blurts it out to preserve it. It is usually not rudeness — it is memory management.",
    ["chadd_ef","add_auhd"]),
 "Flat affect (resting face)":
   ("Flat affect (a neutral resting face) does not mean feeling nothing. In autism, expressive communication differs — the face may not track internal emotion, leading to \"resting serious face\" and others misreading mood. The feeling is usually much bigger than the face shows.",
    ["adult_auhd","auhd_over"]),
 "Task paralysis / executive dysfunction":
   ("Executive dysfunction is the brain's difficulty starting, planning, or sustaining tasks — not laziness. Task paralysis is the stuck state where you know what to do, want to do it, but cannot initiate; ADHD brains run on urgency and interest, not importance.",
    ["chadd_ef","adult_auhd"]),
 "Rejection sensitivity":
   ("Rejection sensitive dysphoria (RSD) is extreme emotional pain triggered by real or perceived rejection or criticism, strongly associated with ADHD. The response is involuntary and out of proportion because rejection-related brain signals are less filtered, not because the person is fragile.",
    ["rsd_cc","rsd_add"]),
 "Special interest monologues":
   ("Special interests are deep, long-term passions typical of autism and common in AuDHD. Monologuing (info-dumping) is sharing that interest with real enthusiasm — but without noticing the listener's cues, the conversation can become a one-way lecture.",
    ["auhd_over","ea_faq"]),
 "Fidgeting constantly":
   ("Fidgeting is automatic movement — tapping, leg-bouncing, pen-clicking — that helps the ADHD/autistic brain maintain arousal and focus. For many it is not a distraction but a regulation tool that actually improves attention.",
    ["add_auhd","sens_as"]),
 "Forgetting to eat or drink":
   ("Forgetting to eat is linked to interoception — sensing internal body signals like hunger — which is often weaker in autism and ADHD, and to hyperfocus that blocks the signal. You can go hours without noticing you are hungry or thirsty.",
    ["auhd_over","adult_auhd"]),
 "Reading social cues wrong":
   ("Reading social cues involves interpreting tone, facial expression, and implied meaning, which autistic social communication processes differently. The result is missed or misread signals — not a lack of care, just a different social operating system.",
    ["auhd_over","add_auhd"]),
 "Oversharing / too blunt":
   ("Oversharing or being blunt comes from autistic communication style (direct, literal, honest) and ADHD impulsivity (words out before the filter). It is typically not about attention-seeking — it is treating honesty as the default.",
    ["ea_faq","adult_auhd"]),
 "Can't start a task unless it's urgent":
   ("ADHD motivation is interest- and urgency-based: without a deadline or adrenaline, starting can feel impossible, so last-minute pressure becomes the engine. This 'procrastination' is actually executive function differences, not a character flaw.",
    ["chadd_ef","adult_auhd"]),
 "Echolalia / repeating phrases":
   ("Echolalia is repeating words or phrases — often from a show, song, or someone else — as a form of stimming, regulation, or processing. In AuDHD it can be automatic verbal playback used to self-soothe or to hold onto a satisfying sound.",
    ["sens_as","sens_asuk"]),
 "Sensory-seeking (crash, squeeze, weighted)":
   ("Sensory seeking is deliberately pursuing input — crashing into cushions, firm hugs, weighted blankets, deep pressure — to balance the nervous system. It is the opposite pole to sensory overload and helps many AuDHD people regulate.",
    ["sens_as","sens_asuk"]),
 "Invisible panic before phone calls":
   ("Phone-call anxiety is a common AuDHD freeze: the call is unstructured, with no visible cues and real-time demands on social scripts and attention. The panic — racing thoughts, rehearsing lines, avoiding dialling — is anticipation of an unpredictable social task, not shyness.",
    ["mask_nk","adult_auhd"]),
 "Collecting hobbies, finishing none":
   ("Starting many hobbies and finishing few is the AuDHD pattern of dopamine-driven novelty: the chase of a new interest is rewarding, while follow-through needs sustained executive function. The collection of half-finished projects is the natural result.",
    ["adult_auhd","ea_faq"]),
 "Body feels things others don't notice":
   ("Heightened sensory awareness (hyper-sensitivity) means noticing — and being bothered by — sounds, lights, textures, and body sensations others filter out. Autistic and ADHD nervous systems often lack the usual sensory 'volume control'.",
    ["sens_asuk","cm_spd"]),
 "Hyperfocus for hours":
   ("Hyperfocus is an intense state where attention locks onto one thing for hours and the rest of the world — time, hunger, people — drops away. It is the flip side of ADHD inattention: involuntary, powerful, and hard to interrupt.",
    ["adult_auhd","chadd_time"]),
 "Scripting what to say":
   ("Social scripting is preparing exact words for expected situations — greetings, calls, small talk — a common autism masking strategy. It reduces the unpredictability of interaction but consumes working memory and can fail when the conversation goes off-script.",
    ["mask_nk","mask_pmc"]),
 "Detail blindness then whole checklist matters":
   ("Detail processing differs in AuDHD: autistic attention can lock onto specific details while the bigger picture blurs, and ADHD can skip details that feel uninteresting. Either way, rules, checklists, and order often act as the missing scaffolding.",
    ["chadd_ef","ea_faq"]),
 "Forgot why you walked into the room":
   ("Walking into a room and forgetting why is working-memory loss in action — the goal thought was displaced by new input (the doorway, the room). It is common in ADHD and described as the brain's RAM being cleared by a context switch.",
    ["chadd_ef","adult_auhd"]),
 "Textures / tags unbearable":
   ("Texture and clothing-tag sensitivity is sensory hyper-sensitivity: fabric, seams, and tags generate input that the nervous system flags as genuinely uncomfortable. It is a real sensory difference, not fussiness, and can dominate attention until removed.",
    ["sens_asuk","cm_spd"]),
 "Needs a routine but can't keep one":
   ("Autistic brains often thrive on predictability and routine, while ADHD brains struggle to initiate and sustain them — the AuDHD contradiction of craving structure and rebelling against it. The result is elaborate planning systems that last days.",
    ["auhd_over","ea_faq"]),
 "Obsessive rules fairness":
   ("Strong fairness and rule sensitivity comes from autistic black-and-white thinking and justice sensitivity — a visceral reaction to unfairness or rule-breaking. It reflects a deeply principled, literal relationship with how things 'should' work.",
    ["ea_faq","add_auhd"]),
 "Can't filter background noise":
   ("Difficulty filtering background noise is auditory hyper-sensitivity plus ADHD attention: every sound competes for the same attention channel. Cafes and open offices become exhausting because the brain cannot mute the irrelevant sounds.",
    ["sens_asuk","cm_spd"]),
 "Meltdown after masking all day":
   ("An after-masking meltdown is the overflow of a day spent suppressing stims, scripting, and performing 'normal'. Masking depletes the nervous system's regulation budget, and at home — where it is safe — the pressure finally releases.",
    ["mask_pmc","chadd_melt"]),
 "Music strictly one song on repeat":
   ("Playing one song on repeat is a form of stimming and dopamine regulation: predictable, satisfying auditory input that helps focus or soothe. The repetition is calming precisely because it is known and controllable.",
    ["sens_as","auhd_over"]),
 "Loves a good spreadsheet to organise":
   ("Loving spreadsheets, lists, and colour-coded systems is externalised executive function — offloading the planning and remembering that ADHD brains find unreliable onto a visible structure. The system is the coping mechanism, not the obsession.",
    ["chadd_ef","adult_auhd"]),
 "Takes jokes literally":
   ("Taking jokes literally is about literal, detail-focused language processing common in autism: sarcasm, irony, and implied meaning are decoded as facts. It is not missing humour — the humour is often enjoyed once the intended layer is made explicit.",
    ["auhd_over","ea_faq"]),
 "Exhausted by socialising even when fun":
   ("Socialising drains AuDHD energy fast because it taxes attention, sensory filtering, scripting, and masking at once — even when it is enjoyable. This is the 'social battery' draining at double speed, which is why after a great night you may crash completely.",
    ["mask_pmc","auhd_over"]),
 "Keeps 'nice to haves' in your bag for 3 months":
   ("Carrying 'just in case' items for months is planning for every possible future — an anxious, future-thinking habit common in AuDHD (the bag becomes a safety net against being caught unprepared). Forgetting to remove them is the working-memory half.",
    ["adult_auhd","chadd_ef"]),
 "Double empathy — reads animals better than people":
   ("The double empathy problem describes mutual misunderstanding between autistic and non-autistic people — neither instinctively reads the other. Many AuDHD people find animal communication easier to read than human social cues, because it is honest and non-verbal.",
    ["ea_faq","auhd_over"]),
}

def main():
    d = json.load(open("symptoms.json"))
    missing = [s["name"] for s in d["symptoms"] if s["name"] not in DESC]
    if missing:
        raise SystemExit("no desc for: " + ", ".join(missing))
    for s in d["symptoms"]:
        text, keys = DESC[s["name"]]
        s["desc"] = text
        s["sources"] = [S[k] for k in keys]
    json.dump(d, open("symptoms.json","w"), ensure_ascii=False, indent=2)
    print(f"attached desc + {sum(len(s.get('sources',[])) for s in d['symptoms'])} sources to {len(d['symptoms'])} symptoms")

if __name__ == "__main__":
    main()