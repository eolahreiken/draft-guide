#!/usr/bin/env python3
"""Phase 2+3: assign tiers, apply WR override, emit players.js."""
import json, re, sys

with open('players_raw.json') as f:
    players = json.load(f)

BREAKPOINTS = {
    'QB':[4,8,12,16,22,30], 'RB':[6,12,18,24,36,50,68],
    'WR':[6,12,18,24,36,50,68], 'TE':[3,6,10,16,24],
    'K':[3,8], 'DST':[3,8],
}
def default_tier(posrank, bps):
    for i, bp in enumerate(bps):
        if posrank <= bp: return i+1
    return min(len(bps)+1, 8)

# Eric's WR override (canonical ESPN spellings). Do not change without his say-so.
WR_OVERRIDE = [
    ("Puka Nacua",1),("Ja'Marr Chase",1),("Jaxon Smith-Njigba",1),
    ("Amon-Ra St. Brown",2),("CeeDee Lamb",2),
    ("Justin Jefferson",3),("Drake London",3),("A.J. Brown",3),("Rashee Rice",3),
    ("Nico Collins",3),("DeVonta Smith",3),("George Pickens",3),
    ("Tee Higgins",4),("Emeka Egbuka",4),("Ladd McConkey",4),("Zay Flowers",4),
    ("Davante Adams",4),("Mike Evans",4),("Tetairoa McMillan",4),("Chris Olave",4),
    ("Terry McLaurin",4),("Garrett Wilson",4),
    ("Malik Nabers",5),("Luther Burden III",5),("Jaylen Waddle",5),
    ("Marvin Harrison Jr.",5),("Jameson Williams",5),("Rome Odunze",5),
    ("Christian Watson",6),
]

def norm(s):
    s = s.lower()
    s = re.sub(r"[.\'’,]", "", s)
    s = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

for p in players:
    p['tier'] = default_tier(p['posRank'], BREAKPOINTS[p['pos']])

# boardRank: dense rank across ALL players by ESPN overall (overall is unique)
for i, p in enumerate(sorted(players, key=lambda x: x['overall'])):
    p['boardRank'] = i + 1

wrs = [p for p in players if p['pos'] == 'WR']
wr_by_norm = {norm(p['name']): p for p in wrs}
unmatched, override_set = [], []
for name, tier in WR_OVERRIDE:
    key = norm(name)
    p = wr_by_norm.get(key)
    if not p:
        cands = [q for q in wrs if norm(q['name']).startswith(key) or key in norm(q['name'])]
        p = cands[0] if len(cands) == 1 else None
    if not p:
        unmatched.append(name); continue
    override_set.append((p, tier))
if unmatched:
    print("!! UNMATCHED WR override names:", unmatched); sys.exit(1)

override_ids = {id(p) for p,_ in override_set}
remaining = sorted([p for p in wrs if id(p) not in override_ids], key=lambda p: p['posRank'])
pos = 1
for p, tier in override_set:
    p['posRank'] = pos; p['tier'] = tier; pos += 1
for idx, p in enumerate(remaining):
    p['posRank'] = pos; p['tier'] = 7 if idx < 16 else 8; pos += 1

print("WR override matched:", len(override_set), "remaining:", len(remaining))
assert [p['posRank'] for p in sorted(wrs, key=lambda p: p['posRank'])] == list(range(1,91))

out = []
for p in sorted(players, key=lambda x: x['boardRank']):
    out.append({
        "id": p['name'], "name": p['name'], "team": p['team'], "pos": p['pos'],
        "bye": (p['bye'] if p['bye'] else None), "tier": p['tier'],
        "posRank": p['posRank'], "adp": p['overall'],
        "boardRank": p['boardRank'], "aav": p['aav'],
    })
league = {"teams":10,"scoring":"Full PPR","slot":5,"rounds":16,"season":2026}
with open('players.js','w') as f:
    f.write("window.LEAGUE = " + json.dumps(league) + ";\n")
    f.write("window.PLAYERS = " + json.dumps(out, indent=1) + ";\n")
print(f"wrote players.js with {len(out)} players")
