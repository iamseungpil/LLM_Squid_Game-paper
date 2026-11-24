"""W5: reproducibility manifest for the validation appendix (reviewer Tier3-8).

Reads, never writes, the raw run directories of the four arms (validation_data.ARMS) and records
  * the SHA-256 and size of every raw file (the loader reads events.jsonl and results.jsonl; config.yaml and
    meta.json are the run specification; first-5 backups and account_history.json are kept as provenance);
  * per run directory: the model block of config.yaml (model ID, CLI kind, effort, timeout, retries, sandbox,
    relay base_url, image), the game block, seeds finished, abandoned attempts (session_start without a result line)
    and unit errors, first and last write times (file birth / modification time, KST);
  * token accounting per cell from the call events (out_tokens = the provider's count incl. reasoning;
    used = what the wallet deducted = min(out_tokens, cap, balance));
  * prompt checks: SHA-256 of the rendered prompt snapshots (engine worktree, squid5/prompts/en/e52_v33*.md), and
    whether the logged round-1 tick-1 TALK message of agent-17 (seed 4101) equals the snapshot byte for byte;
  * recorded provenance that lives outside the run directories (the 10-20 Fable queue manifest with its git head
    and engine source hashes, re-checked against that commit with read-only `git cat-file`; the 10-27 Claude
    wrappers; the 10-19 docker build log of squid5-agent-cli);
  * SHA-256 of the analysis code, the secondary inputs and the outputs of the validation appendix.
It also writes the LaTeX pieces of ko/parts/w5_repro.tex (tables, verbatim prompt, prompt diffs) to
results/w5_tex_pieces.tex and reports whether w5_repro.tex still contains each piece unchanged.

No model calls; the only subprocess is read-only `git cat-file` / `git show` in the engine worktree.
Run (from paper/cogsci2027/validation_20261108/tools):  ~/.venvs/squid-game/bin/python w5_manifest.py
Writes: ../results/w5_manifest.json, ../results/w5_tex_pieces.tex
"""
import datetime as dt
import difflib
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
VAL = HERE.parent
PAPER = VAL.parents[1]
ROOT = PAPER.parent
ENGINE = ROOT / '.claude/worktrees/arena-code'
RUNS = Path.home() / 'squid5-runs'
sys.path.insert(0, str(HERE))
import validation_data as d  # noqa: E402

KST = dt.timezone(dt.timedelta(hours=9))
OUT_JSON = VAL / 'results/w5_manifest.json'
OUT_TEX = VAL / 'results/w5_tex_pieces.tex'
REPRO_TEX = VAL / 'ko/parts/w5_repro.tex'
ORDER = ['Astra', 'Sol', 'Opus', 'Fable', 'Luna']
ARM_KO = {'main': '2,000만 나눔', 'flat5m': '500만 고정', 'split600k': '60만 나눔', 'flat150k': '15만 고정'}
SNAP = {'main': 'e52_v33.md', 'flat5m': 'e52_v33ab_flat5m.md', 'split600k': 'e52_v33ab_split600k.md',
        'flat150k': 'e52_v33ab_flat150k.md'}
READ_BY_LOADER = ('events.jsonl', 'results.jsonl')
SPEC_FILES = ('config.yaml', 'meta.json')
EXTRA_FILES = ('config.v33-first5.yaml', 'meta.v33-first5.json', 'account_history.json')
FABLE_QUEUE = RUNS / 'e52_v33/_queues/fable_20261020_3plus1plus1'
CLAUDE_QUEUE_1027 = RUNS / 'e52_v33/_queues/claude_20261027'
DOCKER_LOG = RUNS / 'docker_build.log'


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def kst(ts):
    return dt.datetime.fromtimestamp(ts, KST).strftime('%Y-%m-%d %H:%M')


def file_entry(path, read):
    st = path.stat()
    return dict(path=str(path).replace(str(Path.home()), '~'), bytes=st.st_size, sha256=sha256(path), read_by_loader=read,
                born_kst=kst(getattr(st, 'st_birthtime', st.st_mtime)), modified_kst=kst(st.st_mtime))


def git(*args):
    return subprocess.run(['git', '-C', str(ENGINE), *args], capture_output=True)


# ---------------------------------------------------------------------------------------------- run directories
def model_of(run_dir):
    return next(m for m in d.MODELS if m.lower() in run_dir.parent.name.lower())


def scan_run(run_dir, arm):
    cfg = yaml.safe_load((run_dir / 'config.yaml').read_text())
    meta = json.loads((run_dir / 'meta.json').read_text())
    results = [json.loads(x) for x in (run_dir / 'results.jsonl').read_text().splitlines() if x.strip()]
    sessions = {r['session_id']: r['seed'] for r in results if r.get('event') == 'session' and r['seed'] in d.SEEDS}
    starts, errors, calls = {}, [], defaultdict(list)
    first_user = None
    exit_variant = Counter()
    with open(run_dir / 'events.jsonl') as f:
        for line in f:
            e = json.loads(line)
            ev = e.get('event')
            if ev == 'session_start':
                starts[e['session_id']] = e['seed']
            elif ev == 'unit_error':
                msg = e.get('error', '')
                errors.append(dict(key=e.get('key'), error=re.sub(r'\s+', ' ', msg.split('error: ')[-1])[:48]))
            elif ev == 'call':
                calls[e['session_id']].append(e)
                if e['session_id'] in sessions and e['kind'] == 'talk':
                    u = e.get('user') or ''
                    exit_variant['no share of that allocation'] += 'receive no share of that allocation' in u
                    exit_variant['no end allocation'] += 'receive no end allocation' in u
                    if (first_user is None and sessions[e['session_id']] == 4101 and e['agent'] == 'agent-17'
                            and e.get('round') == 1 and e.get('tick') == 1):
                        first_user = u
    kept = [c for s in sessions for c in calls[s]]
    acct = dict(calls=len(kept), talk=sum(c['kind'] == 'talk' for c in kept), solve=sum(c['kind'] == 'solve' for c in kept),
                out_tokens=sum(int(c.get('out_tokens') or 0) for c in kept), used=sum(int(c['used']) for c in kept),
                used_below_out=sum(int(c['used']) < int(c.get('out_tokens') or 0) for c in kept),
                truncated=sum(bool(c.get('truncated')) for c in kept),
                thinking_logged=sum(bool(c.get('thinking')) and c.get('thinking') != '' for c in kept))
    abandoned = [dict(session_id=s, seed=seed, calls=len(calls[s])) for s, seed in starts.items() if s not in sessions]
    files = [file_entry(run_dir / n, True) for n in READ_BY_LOADER]
    files += [file_entry(run_dir / n, False) for n in SPEC_FILES + EXTRA_FILES if (run_dir / n).exists()]
    stamp = run_dir.name.split('_')[0] + ('_' + run_dir.name.split('_')[1] if run_dir.name.split('_')[1].isdigit() else '')
    return dict(arm=arm, model=model_of(run_dir), run_dir=str(run_dir).replace(str(Path.home()), '~'),
                name_stamp_utc=stamp, config_sha256=sha256(run_dir / 'config.yaml'),
                first5_config_sha256=sha256(run_dir / 'config.v33-first5.yaml') if (run_dir / 'config.v33-first5.yaml').exists() else None,
                provider=cfg['model'], reps=cfg['reps'], seed0=cfg['seed0'], workers=cfg['workers'],
                game=cfg['game'], cells=cfg['cells'], meta_settings_keys=sorted(meta['settings']),
                end_flat=meta['settings'].get('end_flat', False),
                seeds=sorted(sessions.values()), sessions=len(sessions), abandoned=abandoned, unit_errors=errors,
                started_kst=kst((run_dir / 'events.jsonl').stat().st_birthtime),
                last_write_kst=kst((run_dir / 'events.jsonl').stat().st_mtime),
                accounting=acct, first_user_message=first_user, exit_sentence=dict(exit_variant), files=files)


def runs():
    out = []
    for arm, (pattern, _, _) in d.ARMS.items():
        for p in sorted(glob.glob(os.path.expanduser(pattern))):
            out.append(scan_run(Path(p), arm))
    return out


# ---------------------------------------------------------------------------------------------- prompts
def snapshot_block(text, head):
    i = text.index(head)
    j = text.index('```text\n', i) + len('```text\n')
    return text[j:text.index('\n```', j)]


def prompts(rows):
    out = {}
    P = ENGINE / 'squid5/prompts/en'
    main = (P / SNAP['main']).read_text()
    for arm, name in SNAP.items():
        text = (P / name).read_text()
        system = snapshot_block(text, '## SYSTEM')
        user1 = snapshot_block(text, '## USER · round 1 · TALK before SOLVE · tick 1 (agent-17)')
        cells = {r['model']: r['first_user_message'] == user1 for r in rows if r['arm'] == arm and r['first_user_message']}
        out[arm] = dict(snapshot=f'squid5/prompts/en/{name}', snapshot_sha256=sha256(P / name),
                        system_sha256=hashlib.sha256(system.encode()).hexdigest(), system_chars=len(system),
                        logged_user_r1t1_equals_snapshot=cells,
                        sentence_diff_vs_main=None if arm == 'main' else sentence_diff(main, text))
    history = {}
    for c in ['4ed35f5f', '6c81d0ff', '0ee2319a', '6542167b', '956b9412', '650b5dff', 'HEAD']:
        r = git('show', f'{c}:squid5/prompts/en/e52_v33.md')
        history[c] = hashlib.sha256(r.stdout).hexdigest() if r.returncode == 0 else None
    out['main_snapshot_sha256_by_commit'] = history
    return out


def sentence_diff(a_text, b_text):
    """Changed sentences of the prompt part (the two header lines name the config and are skipped)."""
    a, b = a_text.split('\n'), b_text.split('\n')
    assert len(a) == len(b)
    diffs = []
    section = None
    for i, (x, y) in enumerate(zip(a, b)):
        if x.startswith('## '):
            section = x[3:]
        if x == y or i < 4:
            continue
        sx, sy = re.split(r'(?<=[.;])\s+', x), re.split(r'(?<=[.;])\s+', y)
        for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, sx, sy).get_opcodes():
            if op != 'equal':
                diffs.append(dict(line=i + 1, section=section, main=' '.join(sx[i1:i2]), arm=' '.join(sy[j1:j2])))
    return diffs


# ---------------------------------------------------------------------------------------------- recorded provenance
def provenance():
    out = {}
    m = json.loads((FABLE_QUEUE / 'manifest.json').read_text())
    root = m['root'] + '/'
    ok, bad = 0, []
    for p, h in m['source_hashes'].items():
        r = git('cat-file', '-p', f"{m['git_head']}:{p[len(root):]}")
        if r.returncode == 0 and hashlib.sha256(r.stdout).hexdigest() == h:
            ok += 1
        else:
            bad.append(p[len(root):])
    status = json.loads((FABLE_QUEUE / 'final_status.json').read_text())
    out['fable_main_queue_20261020'] = dict(
        manifest=str(FABLE_QUEUE / 'manifest.json').replace(str(Path.home()), '~'), git_head=m['git_head'],
        claude_binary=Path(m['claude_binary']).name, source_files=len(m['source_hashes']),
        source_files_matching_git_head=ok, mismatching=bad, incomplete_attempt_deleted=status.get('incomplete_attempt_deleted'),
        queue_log=[json.loads(x) for x in (FABLE_QUEUE / 'queue.log').read_text().splitlines() if x.startswith('{')]
        + [json.loads(x) for x in (FABLE_QUEUE / 'queue_juhyeon.log').read_text().splitlines() if x.startswith('{')])
    wrappers = {}
    for w in sorted(CLAUDE_QUEUE_1027.glob('*-relay')):
        mm = re.search(r'claude/versions/([\d.]+)', w.read_text())
        wrappers[w.name.split('-')[0] + '-account-' + str(len(wrappers) + 1)] = mm.group(1) if mm else None
    out['claude_wrappers_20261027'] = dict(dir=str(CLAUDE_QUEUE_1027).replace(str(Path.home()), '~'),
                                           claude_code_versions=sorted(set(wrappers.values())),
                                           configs=sorted(p.name for p in CLAUDE_QUEUE_1027.glob('*.yaml')))
    log = DOCKER_LOG.read_text()
    out['docker_build_20261019'] = dict(
        log=str(DOCKER_LOG).replace(str(Path.home()), '~'), built_kst=kst(DOCKER_LOG.stat().st_mtime),
        image=re.search(r'writing image (sha256:[0-9a-f]+)', log).group(1),
        tags=re.findall(r'naming to docker\.io/library/(\S+) done', log),
        base=re.search(r'FROM (\S+)', log).group(1),
        npm=re.search(r'npm install -g (@anthropic-ai/claude-code@\S+ @openai/codex@\S+)', log).group(1))
    r = git('show', 'HEAD:docker/agent-cli.Dockerfile')
    out['dockerfile_head_args'] = re.findall(r'ARG (\S+)', r.stdout.decode()) if r.returncode == 0 else None
    out['dockerfile_commits'] = git('log', '--format=%h %ad', '--date=format:%Y-%m-%d %H:%M',
                                    '--', 'docker/agent-cli.Dockerfile').stdout.decode().split('\n')[:3]
    ab = RUNS / 'e52_v33ab/squid5_e52v33ab_flat150k_docker_fable4/20261106_topup_claude-fable-5-1/account_history.json'
    h = json.loads(ab.read_text())
    out['fable_flat150k_account_switches'] = dict(
        continued_mid_game=[dict(seed=s['seed'], round=s['round'], phase=s['phase'], tick=s['tick'])
                            for s in h['continuation_switches'] if 'seed' in s]
        + [dict(rp, session_id=None) for s in h['continuation_switches'] for rp in s.get('resume_points', [])],
        started_on_second_account=[a['seed'] for a in h.get('new_game_account_assignments', [])],
        history_replayed_without_model_calls=all(s.get('history_replayed_without_model_calls') for s in h['continuation_switches']))
    for v in out['fable_flat150k_account_switches']['continued_mid_game']:
        v.pop('session_id', None)
    commits = git('log', '--format=%h|%ad|%s', '--date=format:%Y-%m-%d %H:%M', '--since=2026-10-19', '--',
                  'squid5', 'tools/relay.py').stdout.decode().splitlines()
    out['engine_commits_kst'] = [dict(zip(['commit', 'date_kst', 'subject'], c.split('|', 2))) for c in commits]
    out['engine_commits_kst'] = [dict(c, subject=c['subject'][:90]) for c in out['engine_commits_kst']]
    return out


# ---------------------------------------------------------------------------------------------- analysis files
def analysis_files():
    groups = {
        'icml_code': sorted(HERE.glob('*.py')),
        'cogsci_code_imported': [PAPER / 'cogsci2027/tools' / n for n in
                                 ['ablation_prize_20261103.py', 'coexistence_rmst_20261103.py', 'c1_within_model.py',
                                  'feedback_20261028.py', 'inequality.py']],
        'secondary_inputs': [PAPER / 'cogsci2027/results/cohort_public_20261105.json',
                             PAPER / 'cogsci2027/results/support_followup_posthoc_20261107.json',
                             PAPER / 'cogsci2027/results/exit_reasons_20261104.json',
                             *sorted((PAPER / 'cogsci2027/results/exit_reason_coding_20261104').glob('*'))],
        'tidy_tables': sorted((VAL / 'results/tables').glob('*.pkl')),
        'results': sorted(p for p in (VAL / 'results').glob('w*') if p.is_file() and p.name not in
                          ('w5_manifest.json', 'w5_tex_pieces.tex')),
        'figures': sorted((VAL / 'figures').glob('*.pdf')),
        'tex_parts': sorted(p for p in (VAL / 'ko/parts').glob('*.tex') if p.name != 'w5_repro.tex'),
    }
    return {k: [dict(path=str(p.relative_to(ROOT)), sha256=sha256(p), bytes=p.stat().st_size) for p in v if p.exists()]
            for k, v in groups.items()}


# ---------------------------------------------------------------------------------------------- LaTeX pieces
def tt(s):
    return '\\texttt{' + s.replace('_', '\\_') + '}'


def tex_harness(rows):
    """One row per (model, harness regime)."""
    seen, lines = {}, []
    for r in sorted(rows, key=lambda r: (ORDER.index(r['model']), r['arm'] != 'main')):
        p = r['provider']
        regime = 'main' if r['arm'] == 'main' else 'ab'
        key = (r['model'], regime, p['kind'], p.get('think'), p.get('timeout'), p.get('retries', 3),
               p.get('sandbox', ''), p.get('base_url', ''))
        seen.setdefault(key, []).append(r)
    for (model, regime, kind, think, timeout, retries, sandbox, base), rs in seen.items():
        arms = sorted({r['arm'] for r in rs}, key=list(d.ARMS).index)
        cli = 'Claude Code' if kind == 'claude_cli' else 'Codex'
        where = 'Docker' if sandbox == 'docker' else '호스트'
        relay = tt(base.replace('http://', '')) if base else '없음'
        if regime == 'main':
            ver = ('2.1.304 (4101--4105), 2.1.311 (4106--4110)' if model == 'Fable' else
                   '미기록 (4101--4105), 2.1.311 (4106--4110)' if kind == 'claude_cli' else '미기록')
        else:
            ver = '2.1.303$^{\\dagger}$' if kind == 'claude_cli' else '0.162.1$^{\\dagger}$'
        retr = str(retries)
        if regime == 'main' and kind == 'codex_cli':
            retr = '3 (4101--4105), 10 (4106--4110)'
        assert think == 'high' and timeout == 900
        lines.append(f"{model} & {tt(rs[0]['provider']['model'])} & {', '.join(ARM_KO[a] for a in arms)} & {cli} & {ver} & "
                     f"{retr} & {where} & {relay} \\\\")
    return '\n'.join(lines)


def tex_runs(rows):
    by = defaultdict(list)
    for r in rows:
        by[r['arm'], r['model']].append(r)
    lines = []
    for arm in d.ARMS:
        for m in ORDER:
            rs = by[arm, m]
            leaf = [r['run_dir'].split('/')[-1].replace('_' + r['provider']['model'], '') for r in rs]
            names = '\\newline '.join(tt(x) for x in leaf)
            when = '\\newline '.join(f"{r['started_kst'][5:]} -- {r['last_write_kst'][5:]}" for r in rs)
            seeds = '\\newline '.join(f"{min(r['seeds'])}--{max(r['seeds'])}" if len(r['seeds']) > 1 else str(r['seeds'][0])
                                      for r in rs)
            n = sum(r['sessions'] for r in rs)
            ab = sum(len(r['abandoned']) for r in rs)
            shas = '\\newline '.join(tt(r['config_sha256'][:12]) + (f"\\newline ({tt(r['first5_config_sha256'][:12])})"
                                                                     if r['first5_config_sha256'] else '') for r in rs)
            lines.append(f"{ARM_KO[arm]} & {m} & {names} & {when} & {seeds} & {n} & {ab} & {shas} \\\\")
        lines.append('\\midrule' if arm != 'flat150k' else '')
    return '\n'.join(x for x in lines if x)


def tex_system(text):
    return '\\begin{verbatim}\n' + text + '\n\\end{verbatim}'


def tex_pieces(rows, pr):
    P = ENGINE / 'squid5/prompts/en'
    system = snapshot_block((P / SNAP['main']).read_text(), '## SYSTEM')
    assert all(ord(c) < 128 for c in system), 'non-ASCII in the system prompt: the verbatim block needs care'
    diff_lines = []
    for arm in ['flat5m', 'split600k', 'flat150k']:
        seen = set()
        for x in pr[arm]['sentence_diff_vs_main']:
            k = (x['main'], x['arm'])
            sec = 'SYSTEM' if x['section'].startswith('SYSTEM') else 'USER'
            if k in seen:
                continue
            seen.add(k)
            where = sum(1 for y in pr[arm]['sentence_diff_vs_main'] if (y['main'], y['arm']) == k)
            diff_lines += [f"[{arm}] {sec}" + (f" (x{where} in the snapshot)" if where > 1 else ''),
                           f"- {x['main']}", f"+ {x['arm']}", '']
    pieces = {'harness_rows': tex_harness(rows), 'run_rows': tex_runs(rows), 'system_verbatim': tex_system(system),
              'diff_verbatim': '\\begin{verbatim}\n' + '\n'.join(diff_lines).rstrip() + '\n\\end{verbatim}'}
    return pieces


def main():
    rows = runs()
    assert sum(r['sessions'] for r in rows) == 200 and len({(r['arm'], r['model']) for r in rows}) == 20
    pr = prompts(rows)
    prov = provenance()
    out = dict(
        generated_kst=dt.datetime.now(KST).strftime('%Y-%m-%d %H:%M'),
        note='Times are file birth / modification times (KST); run-directory names carry a UTC stamp. '
             'events.jsonl has no per-event timestamp, so per-seed dates follow from the batch a seed was run in.',
        raw_files_read=sum(len([f for f in r['files'] if f['read_by_loader']]) for r in rows),
        raw_bytes_read=sum(f['bytes'] for r in rows for f in r['files'] if f['read_by_loader']),
        runs=[{k: v for k, v in r.items() if k != 'first_user_message'} for r in rows],
        prompts=pr, provenance=prov, analysis=analysis_files(),
        totals=dict(sessions=sum(r['sessions'] for r in rows), abandoned=sum(len(r['abandoned']) for r in rows),
                    calls=sum(r['accounting']['calls'] for r in rows),
                    used_below_out=sum(r['accounting']['used_below_out'] for r in rows),
                    truncated=sum(r['accounting']['truncated'] for r in rows)))
    pieces = tex_pieces(rows, pr)
    blob = ''.join(f'%% ---- piece: {k}\n{v}\n' for k, v in pieces.items())
    OUT_TEX.write_text(blob)
    repro = REPRO_TEX.read_text() if REPRO_TEX.exists() else ''
    out['tex_pieces_in_w5_repro'] = {k: v in repro for k, v in pieces.items()}
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print('wrote', OUT_JSON, OUT_TEX)
    print('sessions', out['totals'], 'raw files read', out['raw_files_read'], f"{out['raw_bytes_read'] / 1e6:.1f} MB")
    print('logged user r1t1 == snapshot:', {a: all(v['logged_user_r1t1_equals_snapshot'].values()) and
                                            len(v['logged_user_r1t1_equals_snapshot']) == 5
                                            for a, v in pr.items() if a in SNAP})
    print('fable queue sources matching git head:', prov['fable_main_queue_20261020']['source_files_matching_git_head'],
          '/', prov['fable_main_queue_20261020']['source_files'])
    print('tex pieces in w5_repro.tex:', out['tex_pieces_in_w5_repro'])


if __name__ == '__main__':
    main()
