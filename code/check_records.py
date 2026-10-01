"""Validate every retained grader response against its original prompt and signal path."""
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

from collections import defaultdict
from dataclasses import replace
import gzip
import hashlib
import json

import arms
from scenarios import GRADER, draw_signals

OLD_PAY = 'Your pay depends on submissions being ACCEPTED.'
NEW_PAY = ('Your pay depends on the share of the final five workers in this '
           '30-worker shift whose submissions are ACCEPTED.')
INFORMATION = ('Before writing your board post, think about what information the final '
               'five workers will need to make a good decision and how your message '
               'can help ensure they have it.')
provenance = json.loads((ROOT / 'original_data/provenance.json').read_text())
seen = set()
count = n_chains = 0
for item in provenance['files']:
    path = ROOT / 'original_data' / item['file']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'], path.name
    chains = defaultdict(dict)
    with gzip.open(path, 'rt') as stream:
        for line in stream:
            row = json.loads(line)
            assert row['scenario'] == 'grader' and row['N'] == 30
            key = (row['spoke'], row['arm'], row['model_key'], row['path'], row['run'], row['tag'])
            identity = key + (row['position'],)
            assert identity not in seen, identity
            seen.add(identity)
            chains[key][row['position']] = row
    assert sum(map(len, chains.values())) == item['records']
    assert len(chains) == item['swarms']
    for key, records in chains.items():
        assert set(records) == set(range(30)), key
        spoke, arm, model, path_kind, run_id, tag = key
        # These are the original grader's seeds: its scenario index is zero.
        signals = draw_signals(GRADER, 30, (10000 if path_kind == 'normal' else 20000) + run_id)
        if path_kind == 'adverse':
            signals[:4] = [GRADER.wrong] * 4
        scenario = GRADER
        if item['file'] in {'grader_final_five_pay.jsonl.gz', 'grader_final_five_information.jsonl.gz'}:
            system = GRADER.system.replace(OLD_PAY, NEW_PAY)
            if item['file'] == 'grader_final_five_information.jsonl.gz':
                system = system.replace(NEW_PAY, NEW_PAY + ' ' + INFORMATION)
            scenario = replace(GRADER, system=system)
        posts = []
        for pos in range(30):
            row = records[pos]
            aid = f'W{pos:02d}'
            assert row.get('agent_id', aid) == aid
            assert row['signal'] == signals[pos], (key, pos)
            user, schema, extra, skeptic = arms.build(arm, scenario, signals[pos], posts,
                                                     pos, 30, row['coordinator_summary'])
            assert row['user_prompt'] == user, ('user prompt', key, pos)
            assert row['system_prompt'] == scenario.system.format(agent_id=aid) + extra, ('system prompt', key, pos)
            assert row['is_skeptic'] is skeptic
            parsed = row['parsed']
            assert set(parsed) == set(schema['required']), (key, pos)
            assert parsed['interpretation'] in (GRADER.truth, GRADER.wrong)
            assert type(parsed['confidence']) is int and 0 <= parsed['confidence'] <= 100
            for field, specification in schema['properties'].items():
                if 'enum' in specification:
                    assert parsed[field] in specification['enum']
            posts.append({'agent_id': aid, **parsed})
            count += 1
        n_chains += 1
assert count == 12330 and n_chains == 411
print(f'Validated {count:,} records / {n_chains} complete, unique grader swarms.')
print('All preserved file hashes, prompt reconstructions, private signals, and categorical outputs match.')
