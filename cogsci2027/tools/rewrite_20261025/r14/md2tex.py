"""Markdown draft (seg1+seg2) -> cogsci2027/ko/sections r0-r4 and r5 (appendix tables reused from the previous build).
Usage: python md2tex.py seg1.md seg2.md prev_out_dir out_dir"""
import re, sys, os
s1, s2, prev, out = sys.argv[1:5]
md = open(s1).read().strip() + "\n\n" + open(s2).read().strip()
FIG = {1: ("fig:arena-round", "figure*", r"\resizebox{\textwidth}{!}{\input{cogsci2027/ko/figures/arena_round}}"),
       2: ("fig:rw-main", "figure*", r"\includegraphics[width=\textwidth]{cogsci2027/ko/figures/rw_fig2_main.pdf}"),
       3: ("fig:rw-validity", "figure*", r"\includegraphics[width=\textwidth]{cogsci2027/ko/figures/rw_fig3_validity.pdf}"),
       4: ("fig:rw-models", "figure*", r"\includegraphics[width=\textwidth]{cogsci2027/ko/figures/rw_fig4_models.pdf}")}
TAB = {"1": "tab:rw-models", "A1": "tab:rw-related", "A2": "tab:rw-metrics", "A3": "tab:rw-persona"}
FIG1_CAP = "한 라운드는 다섯 단계로 지나간다. 같은 모델 넷(A–D) 가운데 푸는 에이전트가 정해지고(①), 풀기 전 대화(②)에서 토큰을 청하거나(ASK) 건네고(GIVE), 떠날 수 있다(EXIT, 잔량에 20,000을 더해 나감). 푸는 에이전트가 과제를 풀어 답과 BELIEF를 내면(③) 결과가 공개되고, 결과 뒤 대화(④)에서는 토큰을 건넬 수 있지만 떠날 수는 없다. 오답이면 벌금을 라운드를 시작한 인원으로 나눠 함께 낸다(⑤). 막대는 잔량이며, 빗금은 건넨 칸, 파란 칸은 받은 칸, 빨간 칸은 벌금이다."
def esc(s):
    s = s.replace("\\", r"\textbackslash{}")
    for a, b in [("&", r"\&"), ("%", r"\%"), ("#", r"\#"), ("_", r"\_"), ("$", r"\$"), ("~", r"\textasciitilde{}"), ("^", r"\^{}")]:
        s = s.replace(a, b)
    for a, b in [("✓", r"\ding{51}"), ("✗", r"\ding{55}"), ("†", r"\textdagger{}"), ("×", r"$\times$"), ("≥", r"$\geq$"),
                 ("κ", r"$\kappa$"), ("ρ", r"$\rho$"), ("−", r"$-$"), ("→", r"$\rightarrow$"), ("÷", r"$\div$"), ("“", "``"), ("”", "''")]:
        s = s.replace(a, b)
    s = re.sub(r'"([^"]*)"', r"``\1''", s)
    s = re.sub(r"\[([a-z]+\d{4}[a-z]+(?:;\s*[a-z]+\d{4}[a-z]+)*)\]", lambda m: r"\citep{" + ",".join(k.strip() for k in m.group(1).split(";")) + "}", s)
    s = re.sub(r"그림 (\d)([a-d]?)", lambda m: r"그림~\ref{%s}%s" % (FIG[int(m.group(1))][0], m.group(2)), s)
    s = re.sub(r"표 (A\d|\d)", lambda m: r"표~\ref{%s}" % TAB[m.group(1)], s)
    return s
paras = [p.strip() for p in md.split("\n\n") if p.strip()]
files = {k: [] for k in ("abstract", "intro", "arena", "analysis", "discussion")}
cur = "abstract"; i = 0; fig1_done = False
SECS = {"## 1 서론": ("intro", r"\section{서론}\label{chap:intro}"), "## 2 아레나": ("arena", r"\section{아레나}\label{sec:rw-arena}"),
        "## 3 아레나 분석": ("analysis", r"\section{아레나 분석}\label{sec:analysis}"), "## 4 논의 및 결론": ("discussion", r"\section{논의 및 결론}\label{chap:discussion}")}
LAB = {"2.1": "sec:related", "2.2": "sec:design", "3.1": "sec:relation", "3.2": "sec:validity", "3.3": "sec:behavior"}
while i < len(paras):
    p = paras[i]
    if p in SECS:
        cur, head = SECS[p]; files[cur].append(head); i += 1; continue
    if p.startswith("### "):
        t = p[4:]; num = t.split()[0]
        if num in LAB: files[cur].append(r"\subsection{%s}\label{%s}" % (esc(t[len(num) + 1:]), LAB[num]))
        else: files[cur].append(r"\subsection*{%s}" % esc(t))
        i += 1; continue
    if p.startswith("#### "):
        files[cur].append(r"\subsubsection*{%s}" % esc(p[5:])); i += 1; continue
    if p.startswith("!["):
        n = int(re.match(r"!\[그림 (\d)", p).group(1)); cap = re.sub(r"^그림 \d\.\s*", "", paras[i + 1])
        lab, env, body = FIG[n]
        files[cur].append("\\begin{%s}[t]\n\\centering\n%s\n\\caption{\\rev{%s}}\n\\label{%s}\n\\end{%s}" % (env, body, esc(cap), lab, env)); i += 2; continue
    if p.startswith("표 1."):
        cap = re.sub(r"^표 1\.\s*", "", p); rows = [r.strip().strip("|").split("|") for r in paras[i + 1].splitlines() if not r.startswith("|---")]
        rows = [[esc(c.strip()) for c in r] for r in rows]
        head = " & ".join(r"\textbf{%s}" % c for c in rows[0]) + r" \\"
        body = "\n".join(" & ".join(r) + r" \\" for r in rows[1:])
        files[cur].append("\\begin{table*}[t]\n\\color{blue}\n\\caption{%s}\n\\label{tab:rw-models}\n\\scriptsize\n\\setlength{\\tabcolsep}{2.5pt}\n"
                          "\\begin{tabularx}{\\textwidth}{@{}>{\\raggedright\\arraybackslash}p{0.075\\textwidth}>{\\raggedright\\arraybackslash}X*{9}{c}@{}}\n\\toprule\n%s\n\\midrule\n%s\n\\bottomrule\n\\end{tabularx}\n\\end{table*}" % (esc(cap), head, body))
        i += 2; continue
    if cur == "abstract":
        if p.startswith("English"): i += 1; continue
        if p.startswith("키워드:"): files[cur].append("\\textbf{Keywords:}\n" + esc(p.split(":", 1)[1].strip())); i += 1; continue
    if cur == "arena" and not fig1_done and "(그림 1)" in p:
        files[cur].append(esc(p))
        files[cur].append("\\begin{figure*}[t]\n\\centering\n%s\n\\caption{\\rev{%s}}\n\\label{fig:arena-round}\n\\end{figure*}" % (FIG[1][2], esc(FIG1_CAP)))
        fig1_done = True; i += 1; continue
    files[cur].append(r"\placeholdertext{%s}" % esc(p) if p.startswith("[자리 표시") else esc(p)); i += 1
os.makedirs(out, exist_ok=True)
hdr = "%% 2026-10-25 6쪽 압축판(Claude Docs 원고에서 변환). 고친 글은 모두 파란색.\n"
names = {"abstract": "r0_abstract", "intro": "r1_introduction", "arena": "r2_arena", "analysis": "r3_analysis", "discussion": "r4_discussion"}
for k, v in files.items():
    body = "\n\n".join(v)
    body = "\\begin{abstract}\n\\color{blue}\n" + body + "\n\\end{abstract}" if k == "abstract" else "{\\color{blue}\n" + body + "\n}"
    open(os.path.join(out, names[k] + ".tex"), "w").write(hdr + body + "\n")
# appendix: reuse the three tables from the previous build, renumbered A1-A3
src = open(os.path.join(prev, "r2_arena.tex")).read() + open(os.path.join(prev, "r3_analysis.tex")).read()
def grab(lab):
    j = src.index("\\label{%s}" % lab); st = src.rindex("\\begin{table*}", 0, j); en = src.index("\\end{table*}", j) + len("\\end{table*}")
    return src[st:en]
tabs = {lab: grab(lab) for lab in ("tab:rw-related", "tab:rw-metrics", "tab:rw-persona")}
app = [hdr, "{\\color{blue}", r"\section{부록}\label{sec:rw-appendix}", r"\renewcommand{\thetable}{A\arabic{table}}\setcounter{table}{0}",
       r"\subsection*{A. 관련 연구와의 비교}", tabs["tab:rw-related"].replace("table*}[t]", "table*}[h]"),
       r"\subsection*{B. 지표 정의}", tabs["tab:rw-metrics"].replace("table*}[t]", "table*}[h]"),
       r"\subsection*{C. 페르소나 코딩}", tabs["tab:rw-persona"].replace("table*}[t]", "table*}[h]"), r"\FloatBarrier", "}"]
open(os.path.join(out, "r5_appendix.tex"), "w").write("\n\n".join(app) + "\n")
print({k: sum(len(x) for x in v) for k, v in files.items()})
