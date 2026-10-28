from pathlib import Path
import subprocess,re,json
ROOT=Path('paper'); OUT=ROOT/'review/20261028_colors_1025'; SECTIONS=ROOT/'cogsci2027/ko/sections'
def group(s,i):
 assert s[i]=='{'
 depth=1;j=i+1
 while depth:
  if s[j]=='{' and s[j-1]!='\\':depth+=1
  if s[j]=='}' and s[j-1]!='\\':depth-=1
  j+=1
 return s[i+1:j-1],j

def strip(s):
 out='';i=0
 while i<len(s):
  m=re.match(r'\{\s*\\color\{(?:blue|black)\}\s*',s[i:])
  if m:
   body,j=group(s,i);body=re.sub(r'^\s*\\color\{(?:blue|black)\}\s*','',body);out+=strip(body);i=j;continue
  m=re.match(r'\\(?:textcolor\{(?:blue|black)\}|rev)\s*\{',s[i:])
  if m:
   start=i+m.end()-1;body,j=group(s,start);out+=strip(body);i=j;continue
  m=re.match(r'\\color\{(?:blue|black)\}',s[i:])
  if m:i+=m.end();continue
  out+=s[i];i+=1
 return out

def norm(s):
 s=re.sub(r'\\label\{[^}]*\}','',s)
 s=re.sub(r'%[^\n]*','',s) if False else s
 return re.sub(r'\s+','',s).replace('~','')

old=[]
files=sorted(SECTIONS.glob('0[0-4]*.tex'))
for f in files:
 raw=subprocess.check_output(['git','-C',str(ROOT),'show','2c15d11:'+'cogsci2027/ko/sections/r'+str(int(f.name[:2]))+'_'+f.name[3:]],text=True)
 clean=strip(raw);(OUT/('baseline_'+f.name)).write_text(clean);old.append(clean)
base=norm('\n'.join(old)); report=[]
def color(s,filename,kind='sentence'):
 if not s.strip():return s
 same=norm(s) in base
 report.append(dict(file=filename,kind=kind,color='black' if same else 'blue',text=s.strip()))
 leading=s[:len(s)-len(s.lstrip())]; trailing=s[len(s.rstrip()):]
 return leading+'\\textcolor{'+('black' if same else 'blue')+'}{'+s.strip()+'}'+trailing

def sentences(s):
 # Sentence boundaries outside braces/math, preserving whitespace.
 depth=0;math=False;start=0;i=0;out=[]
 while i<len(s):
  c=s[i]
  if c=='$' and (not i or s[i-1]!='\\'):math=not math
  if not math:
   if c=='{' and (not i or s[i-1]!='\\'):depth+=1
   elif c=='}' and (not i or s[i-1]!='\\'):depth-=1
  if c in '.?!' and depth==0 and not math and (i+1==len(s) or s[i+1].isspace()):
   out.append(s[start:i+1]);start=i+1
  i+=1
 if start<len(s):out.append(s[start:])
 return out

def prose(s,f):
 return ''.join(color(x,f) if x.strip() else x for x in sentences(s))

for f in files:
 clean=re.sub(r'(?<!\\)%[^\n]*', '', strip((OUT/'original'/f.name).read_text()));out=[];lines=clean.splitlines(keepends=True);i=0
 while i<len(lines):
  line=lines[i]
  if not line.strip() or line.lstrip().startswith('%'):out.append(line);i+=1;continue
  # Caption and heading contents are colored sentence by sentence.
  m=re.match(r'(\s*\\(?:caption|section|subsection|subsubsection)\*?){',line)
  if m:
   content,end=group(line,m.end()-1);out.append(line[:m.end()]+prose(content,f.name)+line[end-1:]);i+=1;continue
  if re.match(r'\s*\\begin\{equation\}',line):
   block=line;i+=1
   while '\\end{equation}' not in block:block+=lines[i];i+=1
   same=norm(block) in base
   out.append('{\\color{'+('black' if same else 'blue')+'}\n'+block+'}\n')
   report.append(dict(file=f.name,kind='equation',color='black' if same else 'blue',text=block));continue
  if re.match(r'\s*\\begin\{tabular',line):
   block=line;i+=1
   while not re.search(r'\\end\{tabular',block):block+=lines[i];i+=1
   same=norm(block) in base
   out.append('{\\color{'+('black' if same else 'blue')+'}\n'+block+'}\n');continue
  if line.lstrip().startswith('\\'):
   out.append(line);i+=1;continue
  # Normal prose can continue across lines; equations/figures terminate it.
  block=line;i+=1
  while i<len(lines) and lines[i].strip() and not lines[i].lstrip().startswith(('\\','%')):
   block+=lines[i];i+=1
  out.append(prose(block.rstrip('\n'),f.name)+'\n')
 result=''.join(out)
 # Color-only transformation must preserve all non-color source characters.
 assert norm(strip(result))==norm(clean),f.name
 f.write_text(result)
(OUT/'sentences.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
from collections import Counter
print(Counter(r['color'] for r in report))
