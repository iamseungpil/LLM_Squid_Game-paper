from pathlib import Path
import re,json,tempfile,sys
w=Path(__file__).resolve().parents[1]; root=w.parents[0]; tag=sys.argv[1]
sections=['00_abstract','01_introduction','02_related_work','03_framework','04_arena','07_discussion']
def clean(t):
 t=re.sub(r'(?m)^%.*\n','',t)
 t=re.sub(r'\\begin\{(figure\*?|table\*?)\}.*?\\end\{\1\}','',t,flags=re.S)
 t=re.sub(r'\\(?:label|citep|citet)\{[^}]*\}','',t)
 t=re.sub(r'\\(?:section|subsection)\{([^}]*)\}',r'\n\n# \1\n\n',t)
 t=t.replace('\\begin{abstract}','').replace('\\end{abstract}','')
 t=re.sub(r'\\textbf\{Keywords:\}.*','',t,flags=re.S)
 return t.strip()
allp=[];targets={}
for s in sections:
 t=clean((root/f'cogsci2027/ko/sections/{s}.tex').read_text()); old=clean((w/f'original/cogsci2027/ko/sections/{s}.tex').read_text())
 for p in re.split(r'\n\s*\n',t):
  if not p.strip():continue
  allp.append(p)
  if p not in old and not p.startswith(('#','\\begin','\\label')):targets[str(len(targets))]=p
text='\n\n'.join(allp)
(w/f'targets_{tag}.json').write_text(json.dumps(targets,ensure_ascii=False,indent=2))
(w/f'render/prose_{tag}.md').write_text(text)
for role in ['openai','anthropic']:
 d=Path(tempfile.mkdtemp(prefix='paper_reader_'));(d/'document.md').write_text(text)
 (w/f'logs/{tag}_{role}_folder.txt').write_text(str(d));print(role,d)
print('targets',len(targets))
