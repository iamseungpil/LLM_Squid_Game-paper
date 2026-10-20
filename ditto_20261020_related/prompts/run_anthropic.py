from pathlib import Path
import subprocess,os,sys
w=Path(__file__).resolve().parents[1];tag=sys.argv[1]
d=Path((w/f'logs/{tag}_anthropic_folder.txt').read_text())
prompt='Read ONLY document.md here. Fresh external reader of one author academic prose. Korean <=600words TOTAL subjective AI-written/edited impression, not authorship proof. Overallpercent; EVERY proseparagraph first5-8words exact +score (JSON enough, do NOT duplicate full table in prose); brief reasons cancombine; suspicious exactquotes severityhigh/medium/low; humanlike passages; oneauthor yes/no; structural suggestions. Skip headings/equations. No otherpaths. Finish exact one-lineJSON BLIND_JSON: {"overall":NN,"paragraphs":[["first5-8words",NN]],"high_spans":["exact high quotes"],"one_person":true}. Include allparagraphscores, keep wholeoutputunder600words. Do notwritefiles.'
env=os.environ.copy();env.pop('ANTHROPIC_API_KEY',None);env.pop('CLAUDECODE',None)
with (w/f'blind_{tag}_anthropic.md').open('w') as f,(w/f'logs/blind_{tag}_anthropic.err').open('w') as e:
 r=subprocess.run(['/Users/bagjuhyeon/.local/bin/claude-irregular6612','-p',prompt,'--model','fable','--output-format','text','--permission-mode','bypassPermissions'],cwd=d,env=env,stdout=f,stderr=e)
 print('exit',r.returncode)
