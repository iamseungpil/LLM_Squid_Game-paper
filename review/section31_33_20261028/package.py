"""Package final figures plus an embedded-image HTML research report."""
import hashlib
import json
import subprocess
from pathlib import Path
import fitz

OUT=Path(__file__).resolve().parent
text=(OUT/'REPORT.md').read_text()
for marker,name,caption in [
    ('### 1. 한 명이 남는 것과 넷이 함께 남는 것은 다른 결과다','table31_outcomes','25판 전체 완주 결과'),
    ('### 2. 실제 과제 성과와 초기 대화 비용은 완주와 함께 움직인다','fig31_relations','3.1: 판별 완주 인원과 관측 행동'),
    ('### 3. 협력의 총량과 빈도는 서로 다른 질문에 답한다','supplement_giving_definitions','협력 지표 정의를 바꾼 비교'),
    ('### 1. 결과 전에 조금씩 주는 모델과 결과 뒤에 버퍼를 주는 모델','fig33_behavior','3.3: 모델별 행동과 raw 사건 순서')]:
    text=text.replace(marker,marker+f'\n\n![{caption}](final/{name}.png)\n')
(OUT/'report_with_figures.md').write_text(text)
subprocess.run(['pandoc','report_with_figures.md','--standalone','--embed-resources','--css','report.css','--metadata','title=3.1·3.3 raw 재분석','--output','report.html'],cwd=OUT,check=True)
book=fitz.open()
names=['table31_outcomes','fig31_relations','fig33_behavior','supplement_giving_definitions']
for name in names:
    with fitz.open(OUT/'final'/f'{name}.pdf') as doc:
        assert len(doc)==1
        book.insert_pdf(doc)
book.set_metadata({'title':'Section 3.1 and 3.3: raw-data figures','author':'Research analysis; Fable blind review'})
book.save(OUT/'figures.pdf');book.close()
render=OUT/'pdf_render';render.mkdir(exist_ok=True)
with fitz.open(OUT/'figures.pdf') as book:
    for i,page in enumerate(book):
        page.get_pixmap(matrix=fitz.Matrix(1.3,1.3)).save(render/f'page{i+1}.png')
        assert page.get_text().strip()
artifacts={str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.rglob('*')) if p.is_file() and p.suffix in ['.py','.json','.csv','.md','.pdf','.png','.html'] and p.name!='manifest.json' and '__pycache__' not in str(p)}
(OUT/'manifest.json').write_text(json.dumps({'files_sha256':artifacts},indent=2))
print('Created report.html, four-page figures.pdf; rendered all PDF pages and wrote manifest.json')
