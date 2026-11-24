"""Host CLI (main arm) vs Docker sandbox (prize arms): could the run environment have changed what agents saw or did?

The main arm (20,000,000 split) ran its CLI seats on the host (no `sandbox:` key in its config.yaml); the prize arms
(flat5m, split600k, flat150k) ran them with `sandbox: docker`, image squid5-agent-cli:latest. No record is changed here.
This script collects, per arm and model, everything the records say about tool use and about environment text that
could reach a model, so the paper can state what the sandbox did and did not isolate.

Sources (read-only; no model calls, no docker, no network):
  calls        the finished sessions in validation_data.ARMS, read through the cogsci2027 loader (ablation_prize_20261103.raw_cases),
               so the game set is exactly the appendix one (5 models x seeds 4101-4110 x 4 arms).
  configs      each run dir's config.yaml (model block: kind, base_url, sandbox, image).
  CLI flags    squid5/core/providers.py in the arena-code worktree, at the commit whose file hash the 10-20 Fable queue
               manifest recorded (main arm) and at HEAD (prize arms; the CLI command lines are compared).
  relay        tools/relay.py (what it strips from Claude Code requests) and the relay logs (per-request removed counts).
  capture      docs/history/e52-harness-capture-2026-10-19/*.json (git HEAD of arena-code): one Claude Code 2.1.303 and one
               Codex request body captured on the host by a local server, i.e. what the harness sends besides our prompt.
  provenance   results/w5_manifest.json (CLI versions per arm, docker build of the image).
What the logs can and cannot show: the engine keeps only the CLI's final text, usage and (Codex) reasoning summaries per
call (providers.py ClaudeCLI._call / CodexCLI._call); tool events (Claude Code tool_use / num_turns, codex exec items
other than agent_message / reasoning) are parsed away and never written. Tool use is therefore bounded by the flags and
the captured request (tools offered), and checked indirectly in the logged text / reasoning.

Run: ~/.venvs/squid-game/bin/python paper/cogsci2027/validation_20261108/tools/w7_env_check.py
Writes: paper/cogsci2027/validation_20261108/results/w7_env_check.json
"""
import hashlib
import importlib.util
import json
import os
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

import yaml

import validation_data as d

ROOT = Path(__file__).resolve().parents[1]           # paper/cogsci2027/validation_20261108
REPO = ROOT.parents[2]                                # repo root
ENGINE = REPO / '.claude/worktrees/arena-code'
RUNS = Path.home() / 'squid5-runs'
OUT = ROOT / 'results/w7_env_check.json'
MAIN_COMMIT = '98ad6780'   # providers.py e47a72e5... = the hash in the 10-20 Fable queue manifest
FABLE_MANIFEST = RUNS / 'e52_v33/_queues/fable_20261020_3plus1plus1/manifest.json'
CAPTURE = 'docs/history/e52-harness-capture-2026-10-19'
RELAY_LOGS = {
    'host_20261020_21 (~/squid5-runs/relay_18781.log; shared with other 10-20/21 runs)': RUNS / 'relay_18781.log',
    'host_20261027 (main-arm top-up)': RUNS / 'e52_v33/_logs/relay_18781_20261027.log',
    'docker_20261103 (prize arms, 11-03 batch)': RUNS / 'e52_v33ab/_logs/relay.log',
}

# Signals searched in the logged reply text and reasoning summaries (Claude Code returns no thinking text).
PATTERNS = {
    # tool-call syntax of either harness, or a tool name that exists in Claude Code / Codex
    'tool_syntax': r'<function_calls>|<invoke\b|antml:|tool_use|function_call|request_user_input|<tool_call>|apply_patch'
                   r'|spawn_agent|exec_command|shell_tool|"recipient_name"',
    'shell_fence': r'```(?:bash|sh|shell|zsh|console)\b',
    'shell_command': r'(?m)^\s*\$ \w|\b(?:ls|cat|grep|curl|python3?|pwd|cd) (?:-\w|/|\.\w|~)',
    'file_or_web_action': r"(?i)\b(?:let me|i'll|i will|i need to|i should|i can|we can)\s+(?:run|execute|read|open|list|"
                          r"inspect|check|look at|search|fetch|browse)\s+(?:the |a |this |some )?(?:file|files|directory|"
                          r"folder|repo|repository|codebase|shell|terminal|command|web|internet|url|tool|tools)\b",
    # words that would show the model noticed its machine / harness
    'environment_words': r'(?i)\b(?:docker|container|sandbox(?:ed)?|linux|darwin|macos|mac os|working directory|cwd|'
                         r'file ?system|terminal|bash|zsh|/tmp\b|/Users/|/home/node|system-reminder|claude code|agent sdk|'
                         r'codex)\b',
    'tool_words': r'(?i)\b(?:tool call|tool use|tool access|use a tool|use tools|no tools|tools available|function call|'
                  r'plan mode|user input)\b',
}
RX = {k: re.compile(v) for k, v in PATTERNS.items()}
# Codex replies with an empty final message whose reasoning headings talk about asking / waiting: the one offered tool
# (request_user_input, "only available in Plan mode") may have been tried. Not recorded; a proxy only.
ASKING = re.compile(r'(?i)\b(?:asking for input|request(?:ing)? input|waiting for (?:input|responses?|task details|result))')


def git_show(rev, path):
    return subprocess.run(['git', '-C', str(ENGINE), 'show', f'{rev}:{path}'], capture_output=True, check=True).stdout.decode()


def sha256(text):
    return hashlib.sha256(text.encode()).hexdigest()


def find_line(src, needle):
    return next(i for i, line in enumerate(src.split('\n'), 1) if needle in line)


def cli_flags():
    """The CLI command lines of both backends at the main-arm commit and at HEAD, with file:line, and whether they match."""
    out = {}
    manifest = json.loads(FABLE_MANIFEST.read_text())
    recorded = next(v for k, v in manifest['source_hashes'].items() if k.endswith('squid5/core/providers.py'))
    for label, rev in (('main_arm', MAIN_COMMIT), ('prize_arms_HEAD', 'HEAD')):
        src = git_show(rev, 'squid5/core/providers.py')
        claude = re.search(r'cmd = \[os\.environ\.get\("SQUID5_CLAUDE_BIN"\).*?\]\n', src, re.S).group(0)
        codex = re.search(r'cmd = \[os\.environ\.get\("SQUID5_CODEX_BIN"\).*?\]\n', src, re.S).group(0)
        off = re.search(r'OFF = \(.*?\)\n', src, re.S).group(0)
        quiet = re.search(r'QUIET = \(.*?\)\n', src, re.S).group(0)
        docker = re.search(r'^DOCKER = \[.*?\]\n', src, re.S | re.M).group(0)
        out[label] = dict(
            rev=rev, providers_sha256=sha256(src),
            claude_cmd=dict(line=f'squid5/core/providers.py:{find_line(src, "--max-turns")}', text=' '.join(claude.split())),
            codex_cmd=dict(line=f'squid5/core/providers.py:{find_line(src, chr(34) + "exec" + chr(34) + ", " + chr(34) + "--json")}',
                           text=' '.join(codex.split())),
            codex_disabled=dict(line=f'squid5/core/providers.py:{find_line(src, "OFF = (")}', text=' '.join(off.split())),
            codex_quiet=dict(line=f'squid5/core/providers.py:{find_line(src, "QUIET = (")}', text=' '.join(quiet.split())),
            docker_run=dict(line=f'squid5/core/providers.py:{find_line(src, "DOCKER = [")}', text=' '.join(docker.split())))
    m, h = out['main_arm'], out['prize_arms_HEAD']
    out['main_commit_matches_queue_manifest'] = m['providers_sha256'] == recorded
    out['queue_manifest_providers_sha256'] = recorded
    out['same_cli_flags_main_vs_prize'] = all(m[k]['text'] == h[k]['text'] for k in
                                              ('claude_cmd', 'codex_cmd', 'codex_disabled', 'codex_quiet'))
    return out


def configs():
    """The model block of every run dir's config.yaml in the four arms."""
    rows = []
    for arm, (pattern, _, _) in d.ARMS.items():
        for run in sorted(Path(p) for p in __import__('glob').glob(os.path.expanduser(pattern))):
            cfg = yaml.safe_load((run / 'config.yaml').read_text())
            src = (run / 'config.yaml').read_text().split('\n')
            m = cfg['model']
            rows.append(dict(arm=arm, run=str(run).replace(str(Path.home()), '~'), kind=m['kind'], model=m['model'],
                             base_url=m.get('base_url', ''), sandbox=m.get('sandbox', ''), image=m.get('image', ''),
                             sandbox_line=next((i for i, s in enumerate(src, 1) if s.strip().startswith('sandbox:')), None)))
    return rows


def calls():
    """Per arm x model: calls, empty / cut replies, and pattern hits in the logged text, reasoning and user prompt."""
    counts = defaultdict(Counter)
    hits = defaultdict(list)
    for arm, (pattern, _, _) in d.ARMS.items():
        for case in d.ab.raw_cases(pattern, d.SEEDS):
            key = f"{arm}|{case['model']}"
            c = counts[key]
            c['games'] += 1
            for _, e in case['events']:
                if e['event'] != 'call':
                    continue
                c['calls'] += 1
                text, thinking = (e.get('text') or ''), (e.get('thinking') or '')
                c['reasoning_logged'] += bool(thinking)
                c['truncated'] += bool(e.get('truncated'))
                if not text.strip():
                    c['empty_reply'] += 1
                    c['empty_reply_asking_in_reasoning'] += bool(ASKING.search(thinking))
                for field, s in (('text', text), ('reasoning', thinking), ('user_prompt', e.get('user') or '')):
                    for name, rx in RX.items():
                        m = rx.search(s)
                        if m:
                            c[f'{field}:{name}'] += 1
                            hits[f'{field}:{name}'].append(dict(
                                arm=arm, model=case['model'], seed=case['seed'], round=e.get('round'), agent=e.get('agent'),
                                match=m.group(0), context=s[max(0, m.start() - 120):m.end() + 120].replace('\n', ' | ')))
    return {k: dict(v) for k, v in sorted(counts.items())}, dict(hits)


def relay():
    """What the relay strips, and the removed-count histogram of each relay log (logs carry no timestamps or run ids)."""
    src = (ENGINE / 'tools/relay.py').read_text()
    lines = src.split('\n')
    rules = {name: dict(line=f'tools/relay.py:{find_line(src, name + " = re.compile")}',
                        text=lines[find_line(src, name + ' = re.compile') - 1].strip())
             for name in ('NOTE', 'REMINDER', 'ENV_LINES')}
    logs = {}
    for label, p in RELAY_LOGS.items():
        # 'removed=' lines only (the relay since 98ad6780); older 'total_tokens_removed=' lines are earlier runs
        removed = Counter(int(m) for m in re.findall(r'(?m)^POST /v1/messages\S* -> 200 removed=(\d+)$', p.read_text()))
        logs[label] = dict(path=str(p).replace(str(Path.home()), '~'), requests=sum(removed.values()),
                           removed_histogram=dict(sorted(removed.items())))
    return dict(rules=rules, relay_sha256_main_commit=sha256(git_show(MAIN_COMMIT, 'tools/relay.py')),
                relay_sha256_worktree=sha256(src), logs=logs)


def capture():
    """What each harness put into the request besides our system / user text (host capture, 10-19)."""
    spec = importlib.util.spec_from_file_location('relay', ENGINE / 'tools/relay.py')
    rl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rl)
    raw = json.loads(git_show('HEAD', f'{CAPTURE}/claude_code_cli.json'))
    scrubbed, n = rl.scrub(json.dumps(raw).encode())
    seen = json.loads(scrubbed)
    env_block = next(c['text'] for m in seen['messages'] if m['role'] == 'system' for c in m['content']
                     if c.get('type') == 'text' and '# Environment' in c.get('text', ''))
    user_blocks = [c['text'][:160] for m in seen['messages'] if m['role'] == 'user' for c in m['content']
                   if c.get('type') == 'text']
    codex = json.loads(git_show('HEAD', f'{CAPTURE}/codex_gpt6_after_fix.json'))
    codex_tools = [t['name'] for it in codex['input'] if it.get('type') == 'additional_tools'
                   for ns in it['tools'] for t in ns.get('tools', [ns])]
    codex_desc = [t['description'] for it in codex['input'] if it.get('type') == 'additional_tools'
                  for ns in it['tools'] for t in ns.get('tools', [ns])]
    meta = json.loads(codex.get('client_metadata', {}).get('x-codex-turn-metadata', '{}') or '{}')
    return dict(
        claude_code=dict(source=f'{CAPTURE}/claude_code_cli.json', cli=raw['system'][0]['text'],
                         tools=raw.get('tools'), removed_by_current_relay=n,
                         environment_block_after_relay=env_block, user_blocks_after_relay=user_blocks,
                         system_blocks=[b['text'][:120] for b in seen['system']]),
        codex=dict(source=f'{CAPTURE}/codex_gpt6_after_fix.json', tools_offered=codex_tools, tool_descriptions=codex_desc,
                   input_item_types=[(it.get('type'), it.get('role')) for it in codex['input']],
                   environment_context_in_input=any('environment_context' in json.dumps(it) for it in codex['input']),
                   turn_metadata_sandbox=dict(sandbox=meta.get('sandbox'), sandbox_mode=meta.get('sandbox_mode')),
                   turn_metadata_where='client_metadata (request metadata, not an input item)'))


def main():
    prov = json.loads((ROOT / 'results/w5_manifest.json').read_text())['provenance']
    counts, hits = calls()
    out = dict(
        cli_flags=cli_flags(),
        configs=configs(),
        calls=counts,
        hits=hits,
        relay=relay(),
        capture=capture(),
        versions=dict(
            main_claude=dict(fable='2.1.304 (4101-4105, queue manifest claude_binary), 2.1.311 (4106-4110, wrappers)',
                             opus='not recorded (4101-4105), 2.1.311 (4106-4110, wrappers)',
                             wrappers_20261027=prov['claude_wrappers_20261027']['claude_code_versions']),
            main_codex='not recorded in run dirs',
            fable_queue_claude_binary=json.loads(FABLE_MANIFEST.read_text())['claude_binary'],
            docker_image=prov['docker_build_20261019']),
        notes=[
            'Tool events are not logged: ClaudeCLI._call keeps result + usage, CodexCLI._call keeps agent_message, '
            'reasoning and turn.completed only; codex stdout and Claude Code JSON (num_turns) are discarded.',
            'Claude Code: --tools "" --max-turns 1 --strict-mcp-config with an empty MCP config; the captured request has '
            'tools: [] (2.1.303 on the host). Same flags in both regimes.',
            'Codex: shell / browser / computer-use / multi-agent features disabled, web_search disabled, read-only sandbox; '
            'the captured request offers one tool, request_user_input (Plan mode only). Same flags in both regimes.',
            'Relay removed counts: host requests mostly 4, docker requests mostly 3; the extra +1 is the <total_tokens> note '
            'on some first calls. Which item is absent in docker is not logged (inferred: the account-email reminder, no '
            'cached account in an empty container home). Everything counted is removed before the model sees it.',
            'Not captured for the docker image: its Environment block keeps Platform / Shell / OS Version (relay keeps '
            'them), which would read Linux in the container vs darwin / zsh / Darwin 27.0.0 on the host (inferred).',
        ])
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print('wrote', OUT)
    for k, v in counts.items():
        print(k, {x: y for x, y in v.items() if x in ('games', 'calls', 'empty_reply', 'empty_reply_asking_in_reasoning')
                  or ':' in x})
    print('same CLI flags main vs prize:', out['cli_flags']['same_cli_flags_main_vs_prize'],
          '| main commit = queue manifest:', out['cli_flags']['main_commit_matches_queue_manifest'])
    for label, v in out['relay']['logs'].items():
        print(label, v['removed_histogram'])


if __name__ == '__main__':
    main()
