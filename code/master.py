"""Rebuild the grader-only package from saved responses, without model calls."""
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

import os
import subprocess
import sys
import tempfile

if sys.version_info < (3, 12):
    raise SystemExit("Use Python 3.12 or later; reference environment: Python 3.14.4.")
STEPS = [
    "check_records.py",
    "analyze_grader_outcomes.py",
    "analyze_grader_final_five_pay.py",
    "analyze_grader_final_five_information.py",
    "analyze_grader_verbatim_expansion.py",
    "make_grader_beliefs_by_position.py",
    "make_board_rule_outcomes.py",
    "make_grader_beliefs_by_position_information.py",
    "make_prompt_comparison.py",
    "extract_blog_examples.py",
]
OFFLINE_RUNNER = """
import pathlib, runpy, sys
def audit(event, args):
    if event in ('socket.connect', 'socket.getaddrinfo', 'urllib.Request'):
        raise RuntimeError('Network access attempted during offline rebuild')
sys.addaudithook(audit)
script = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(script.parent))
sys.argv = [str(script)]
runpy.run_path(str(script), run_name='__main__')
"""
env = {k: v for k, v in os.environ.items() if not k.endswith('API_KEY')}
with tempfile.TemporaryDirectory(prefix='swarm-cascades-') as cache:
    env.update(MPLCONFIGDIR=cache, XDG_CACHE_HOME=cache,
               FS_FONT_CACHE=str(Path(cache) / 'fonts'), PYTHONDONTWRITEBYTECODE='1')
    for index, name in enumerate(STEPS, 1):
        print(f'\n[{index}/{len(STEPS)}] {name}', flush=True)
        subprocess.run([sys.executable, '-c', OFFLINE_RUNNER, str(ROOT/'code'/name)],
                       cwd=ROOT, env=env, check=True)
print('\nDone. Grader-only figures: draft/. Tables: modified_data/. Notes: notes/.')
