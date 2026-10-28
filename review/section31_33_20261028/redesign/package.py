"""Build a portable report and vector figure collection from the final analysis."""
import hashlib
import json
import subprocess
from pathlib import Path
import fitz
P=Path(__file__).resolve().parent
subprocess.run(['pandoc','RECOMMENDATION.md','--standalone','--embed-resources','--css','../report.css','--metadata','title=3.1·3.3 분석 및 그림 재설계','--output','report.html'],cwd=P,check=True)
names=['fig31_profiles','fig31_budget','fig33_effective_giving','fig33_all_crossings','appendix_token_trajectories','appendix_preprize_gini']
book=fitz.open()
for name in names:
    with fitz.open(P/f'{name}.pdf') as d:
        assert len(d)==1 and d[0].get_text().strip()
        book.insert_pdf(d)
book.set_metadata({'title':'Section3.1/3.3 revised analyses and appendix','author':'Frozen raw-data reanalysis'})
book.save(P/'figures.pdf');book.close()
r=P/'renders';r.mkdir(exist_ok=True)
with fitz.open(P/'figures.pdf') as d:
    for i,page in enumerate(d):page.get_pixmap(matrix=fitz.Matrix(1,1)).save(r/f'page{i+1}.png')
files={str(p.relative_to(P)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(P.rglob('*')) if p.is_file() and p.suffix in {'.md','.py','.json','.csv','.pdf','.png','.html'} and p.name!='manifest.json'}
(P/'manifest.json').write_text(json.dumps({'sha256':files,'figure_book_order':names},indent=2))
print('Packaged embedded report.html and6page vector figures.pdf; rendered6pages.')
