"""Invoke the user-requested claude-juhyeon credential profile, read-only Fable."""
import os
import subprocess
import sys
from pathlib import Path
folder=Path(sys.argv[1]).resolve()
env=os.environ.copy()
env.pop('ANTHROPIC_API_KEY',None)
env.pop('CLAUDECODE',None)
secret=subprocess.run(['security','find-generic-password','-s','claude-token-juhyeon','-w'],check=True,capture_output=True,text=True).stdout.strip()
env['CLAUDE_CODE_OAUTH_TOKEN']=secret
cmd=['claude','-p','--model','claude-fable-5-1','--effort','high','--safe-mode','--tools','Read','--allowedTools','Read','--permission-mode','dontAsk','--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--output-format','json','--no-session-persistence','--system-prompt','You are an independent read-only scientific figure reviewer. Follow the supplied blind review protocol.']
with (folder/'response.json').open('w') as out, (folder/'stderr.log').open('w') as err:
    p=subprocess.run(cmd,input=(folder/'prompt.txt').read_text(),cwd=folder,env=env,text=True,stdout=out,stderr=err)
print('review exit',p.returncode, 'output',folder/'response.json')
sys.exit(p.returncode)
