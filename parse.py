#!/usr/bin/env python3
"""Phase 1: parse NFL26_CS_PPR.pdf into structured player data by x-position."""
import pdfplumber, re, json, sys
from collections import defaultdict

PDF = "NFL26_CS_PPR.pdf"

def col_of(x0):
    if x0 < 140: return 0
    if x0 < 270: return 1
    if x0 < 410: return 2
    return 3

pdf = pdfplumber.open(PDF)
page = pdf.pages[0]
words = page.extract_words(use_text_flow=False, keep_blank_chars=False)

# Cluster words into physical rows by 'top' (tolerance 3px)
words_sorted = sorted(words, key=lambda w: (w['top'], w['x0']))
rows = []
for w in words_sorted:
    placed = False
    for r in rows:
        if abs(r[0] - w['top']) <= 3:
            r[1].append(w); placed = True; break
    if not placed:
        rows.append((w['top'], [w]))

RANK = re.compile(r'^\d+\.$')

# Walk each row left-to-right; start a new entry at each rank token.
entries = []
for rep_top, ws in rows:
    ws = sorted(ws, key=lambda w: w['x0'])
    cur = None
    for w in ws:
        if RANK.match(w['text']):
            if cur: entries.append(cur)
            cur = {'x0': w['x0'], 'top': rep_top, 'tokens': [w['text']]}
        elif cur is not None:
            cur['tokens'].append(w['text'])
    if cur: entries.append(cur)

# Offensive: POSRANK. (OVERALL) Name, TEAM $AAV BYE   (NOT anchored to end)
OFF = re.compile(r'^(\d+)\.\s*\((\d+)\)\s*(.+?),\s*([A-Z]{2,3}|FA)\s+\$(\d+)\s+(\d+)')
# D/ST: POSRANK. (OVERALL) TeamName D/ST (Wk 1: ...) $AAV BYE
DST = re.compile(r'^(\d+)\.\s*\((\d+)\)\s*(.+?)\s+D/ST\b.*?\$(\d+)\s+(\d+)\b')

def position_for(col, top):
    if col == 0:
        return 'QB' if top < 412 else 'TE'
    if col == 1:
        return 'RB'
    if col == 2:
        return 'RB' if top < 143 else 'WR'
    if top < 271: return 'WR'
    if top < 412: return 'DST'
    return 'K'

players = []
unparsed = []
for e in entries:
    col = col_of(e['x0'])
    pos = position_for(col, e['top'])
    text = ' '.join(e['tokens'])
    if pos == 'DST':
        m = DST.match(text)
        if not m:
            unparsed.append((pos, text)); continue
        posrank, overall, name, aav, bye = m.groups()
        players.append(dict(posRank=int(posrank), overall=int(overall),
                            name=name.strip(), team=None, pos='DST',
                            aav=int(aav), bye=int(bye)))
    else:
        m = OFF.match(text)
        if not m:
            unparsed.append((pos, text)); continue
        posrank, overall, name, team, aav, bye = m.groups()
        players.append(dict(posRank=int(posrank), overall=int(overall),
                            name=name.strip(), team=team, pos=pos,
                            aav=int(aav), bye=int(bye)))

print(f"parsed entries: {len(entries)}  players parsed: {len(players)}  unparsed: {len(unparsed)}")
for pos, t in unparsed:
    print("  UNPARSED", pos, "::", t)

# Dedupe on globally-unique OVERALL; keep sole holder of its (pos, posRank).
by_overall = defaultdict(list)
for p in players:
    by_overall[p['overall']].append(p)
pp_count = defaultdict(int)
for p in players:
    pp_count[(p['pos'], p['posRank'])] += 1

deduped = []
dupe_report = []
for ov, plist in by_overall.items():
    if len(plist) == 1:
        deduped.append(plist[0]); continue
    dupe_report.append((ov, [(p['name'], p['pos'], p['posRank']) for p in plist]))
    sole = [p for p in plist if pp_count[(p['pos'], p['posRank'])] == 1]
    deduped.append(sole[0] if sole else plist[0])
if dupe_report:
    print("\nDUPLICATE overall ranks resolved:")
    for ov, items in dupe_report:
        print(f"  ({ov}):", items)
players = deduped

print("\n=== COUNTS ===")
order = ['QB','RB','WR','TE','K','DST']
expected = {'QB':40,'RB':85,'WR':90,'TE':35,'K':15,'DST':15}
bypos = defaultdict(list)
for p in players:
    bypos[p['pos']].append(p)
ok = True
for pos in order:
    plist = sorted(bypos[pos], key=lambda p: p['posRank'])
    ranks = [p['posRank'] for p in plist]
    contiguous = ranks == list(range(1, len(ranks)+1))
    exp = expected[pos]
    good = (len(plist) == exp) and contiguous
    ok = ok and good
    print(f"  {pos}: {len(plist)} (expected {exp}) contiguous={contiguous} {'OK' if good else 'FAIL'}")
print(f"\nTOTAL: {len(players)} (expected 280)  overall-unique={len(set(p['overall'] for p in players))}")
print("ALL VALID" if ok and len(players)==280 else "VALIDATION ISSUES")

with open('players_raw.json','w') as f:
    json.dump(players, f, indent=1)
print("wrote players_raw.json")
