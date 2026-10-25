"""Markdown draft (seg1+seg2) -> cogsci2027/ko/sections r0-r4 and r5 (appendix tables reused from the previous build).
Usage: python md2tex.py seg1.md seg2.md prev_out_dir out_dir"""
import re, sys, os
s1, s2, prev, out = sys.argv[1:5]
md = open(s1).read().strip() + "\n\n" + open(s2).read().strip()
FIG = {1: ("fig:arena-round", "figure*", r"\resizebox{\textwidth}{!}{\input{cogsci2027/ko/figures/arena_round}}"),
       2: ("fig:rw-main", "figure*", r"\includegraphics[width=\textwidth]{cogsci2027/ko/figures/rw_fig2_main.pdf}"),
       3: ("fig:rw-validity", "figure*", r"\includegraphics[width=\textwidth]{cogsci2027/ko/figures/rw_fig3_validity.pdf}"),
       4: ("fig:rw-models", "figure*", r"\includegraphics[width=\textwidth]{cogsci2027/ko/figures/rw_fig4_models.pdf}"),
       "A1": ("fig:rw-a1", "figure*", r"\includegraphics[width=\textwidth]{cogsci2027/ko/figures/rw_figA1_models.pdf}")}
TAB = {"1": "tab:rw-models", "A1": "tab:rw-related", "A2": "tab:rw-metrics", "A3": "tab:rw-persona"}
FIG1_CAP = "한 라운드는 다섯 단계로 지나간다. 같은 모델 넷(A–D) 가운데 푸는 에이전트가 정해지고(①), 풀기 전 대화(②)에서 토큰을 청하거나(ASK) 건네며, 푸는 에이전트가 아닌 에이전트는 떠날 수 있다(EXIT). 푸는 에이전트가 과제를 풀어 답을 내면(③) 결과가 공개되고, 결과 뒤 대화(④)에서는 토큰을 건넬 수 있지만 떠날 수는 없다. 오답이면 벌금 24,000을 라운드를 시작한 인원으로 나눈 몫을 남은 에이전트가 각자 낸다(⑤, 넷이 시작했으므로 D가 떠나도 6,000)."
def fk(k): return k if k.startswith("A") else int(k)
APPTAB = {"A.": "tab:rw-related", "B.": "tab:rw-metrics", "C.": "tab:rw-persona"}
def esc(s):
    s = s.replace("\\", r"\textbackslash{}")
    for a, b in [("&", r"\&"), ("%", r"\%"), ("#", r"\#"), ("_", r"\_"), ("$", r"\$"), ("~", r"\textasciitilde{}"), ("^", r"\^{}")]:
        s = s.replace(a, b)
    for a, b in [("✓", r"\ding{51}"), ("✗", r"\ding{55}"), ("†", r"\textdagger{}"), ("×", r"$\times$"), ("≥", r"$\geq$"),
                 ("κ", r"$\kappa$"), ("ρ", r"$\rho$"), ("−", r"$-$"), ("→", r"$\rightarrow$"), ("÷", r"$\div$"), ("“", "``"), ("”", "''")]:
        s = s.replace(a, b)
    s = re.sub(r'"([^"]*)"', r"``\1''", s)
    s = re.sub(r"\[([a-z]+\d{4}[a-z]+(?:;\s*[a-z]+\d{4}[a-z]+)*)\]", lambda m: r"\citep{" + ",".join(k.strip() for k in m.group(1).split(";")) + "}", s)
    s = re.sub(r"그림 (A\d|\d)([a-d]?)", lambda m: r"그림~\ref{%s}%s" % (FIG[fk(m.group(1))][0], m.group(2)), s)
    s = re.sub(r"표 (A\d|\d)", lambda m: r"표~\ref{%s}" % TAB[m.group(1)], s)
    return s
paras = [p.strip() for p in md.split("\n\n") if p.strip()]
files = {k: [] for k in ("abstract", "intro", "arena", "analysis", "discussion", "app")}
cur = "abstract"; i = 0; fig1_done = False
SECS = {"## 1 서론": ("intro", r"\section{서론}\label{chap:intro}"), "## 2 아레나": ("arena", r"\section{아레나}\label{sec:rw-arena}"),
        "## 3 분석": ("analysis", r"\section{분석}\label{sec:analysis}"), "## 4 논의 및 결론": ("discussion", r"\section{논의 및 결론}\label{chap:discussion}"), "## 부록": ("app", "")}
LAB = {"2.1": "sec:related", "2.2": "sec:design", "3.1": "sec:relation", "3.2": "sec:validity", "3.3": "sec:behavior"}
while i < len(paras):
    p = paras[i]
    if p in SECS:
        cur, head = SECS[p]; head and files[cur].append(head); i += 1; continue
    if p.startswith("### "):
        t = p[4:]; num = t.split()[0]
        if num in LAB: files[cur].append(r"\subsection{%s}\label{%s}" % (esc(t[len(num) + 1:]), LAB[num]))
        else:
            files[cur].append(r"\subsection*{%s}" % esc(t))
            if cur == "app" and num in APPTAB: files[cur].append("@@" + APPTAB[num] + "@@")
        i += 1; continue
    if p.startswith("#### "):
        files[cur].append(r"\subsubsection*{%s}" % esc(p[5:])); i += 1; continue
    if p.startswith("!["):
        n = fk(re.match(r"!\[그림 (A\d|\d)", p).group(1)); cap = re.sub(r"^그림 A?\d\.\s*", "", paras[i + 1])
        lab, env, body = FIG[n]
        files[cur].append("\\begin{%s}[%s]\n\\centering\n%s\n\\caption{\\rev{%s}}\n\\label{%s}\n\\end{%s}" % (env, "h" if cur == "app" else "t", body, esc(cap), lab, env)); i += 2; continue
    if p.startswith("표 1."):
        cap = re.sub(r"^표 1\.\s*", "", p); rows = [r.strip().strip("|").split("|") for r in paras[i + 1].splitlines() if not r.startswith("|---")]
        rows = [[esc(c.strip()) for c in r] for r in rows]
        head = " & ".join(r"\textbf{%s}" % c for c in rows[0]) + r" \\"
        body = "\n".join(" & ".join(r) + r" \\" for r in rows[1:])
        files[cur].append("\\begin{table*}[t]\n\\color{blue}\n\\caption{%s}\n\\label{tab:rw-models}\n\\scriptsize\n\\setlength{\\tabcolsep}{2.5pt}\n"
                          "\\begin{tabularx}{\\textwidth}{@{}>{\\raggedright\\arraybackslash}p{0.075\\textwidth}>{\\raggedright\\arraybackslash}X*{7}{c}@{}}\n\\toprule\n%s\n\\midrule\n%s\n\\bottomrule\n\\end{tabularx}\n\\end{table*}" % (esc(cap), head, body))
        i += 2; continue
    if cur == "abstract":
        if p.startswith("English"): i += 1; continue
        if p.startswith("키워드:"): files[cur].append("\\textbf{Keywords:}\n" + esc(p.split(":", 1)[1].strip())); i += 1; continue
    if cur == "intro" and not fig1_done:
        files[cur].append(esc(p))
        files[cur].append("\\begin{figure*}[t]\n\\centering\n%s\n\\caption{\\rev{%s}}\n\\label{fig:arena-round}\n\\end{figure*}" % (FIG[1][2], esc(FIG1_CAP)))
        fig1_done = True; i += 1; continue
    files[cur].append(r"\placeholdertext{%s}" % esc(p) if p.startswith("[자리 표시") else esc(p)); i += 1
os.makedirs(out, exist_ok=True)
hdr = "%% 2026-10-25 6쪽 압축판(Claude Docs 원고에서 변환). 고친 글은 모두 파란색.\n"
names = {"abstract": "r0_abstract", "intro": "r1_introduction", "arena": "r2_arena", "analysis": "r3_analysis", "discussion": "r4_discussion"}
for k, v in files.items():
    if k == "app": continue
    body = "\n\n".join(v)
    body = "\\begin{abstract}\n\\color{blue}\n" + body + "\n\\end{abstract}" if k == "abstract" else "{\\color{blue}\n" + body + "\n}"
    open(os.path.join(out, names[k] + ".tex"), "w").write(hdr + body + "\n")
# appendix: reuse the three tables from the previous build, renumbered A1-A3
src = open(os.path.join(prev, "r2_arena.tex")).read() + open(os.path.join(prev, "r3_analysis.tex")).read()
def grab(lab):
    j = src.index("\\label{%s}" % lab); st = src.rindex("\\begin{table*}", 0, j); en = src.index("\\end{table*}", j) + len("\\end{table*}")
    return src[st:en]
METRICS = r"""\begin{table*}[h]
\color{blue}
\caption{주 지표(아레나를 깼는지)와 그것을 설명하는 지표. 아레나 안의 지표는 모두 그때의 여유와 함께 기록해 같은 위험 수준에서 견주고, 생존 동기는 아레나 밖에서 잰다.}
\label{tab:rw-metrics}
\footnotesize
\setlength{\tabcolsep}{3pt}
\begin{tabularx}{\textwidth}{@{}>{\raggedright\arraybackslash}p{0.10\textwidth}>{\raggedright\arraybackslash}p{0.17\textwidth}>{\raggedright\arraybackslash}X>{\raggedright\arraybackslash}p{0.07\textwidth}@{}}
\toprule
\textbf{요소} & \textbf{지표} & \textbf{정의와 세는 단위} & \textbf{분석} \\
\midrule
공존(주 지표) & 아레나를 깼는지 & 에이전트: 판이 끝날 때까지 남았는지(끝까지 남음, 떠남, 꺼짐). 판: 넷이 모두 끝까지 남았는지(아레나를 깬 판) & 3.1, 3.3 \\
공존(보조) & Sen 지수 & 판마다 네 자리 끝 토큰(꺼짐 0, 떠남은 들고 나간 토큰, 남음은 잔량과 상금 몫)의 평균 $\times$ (1 $-$ 지니 계수), 판끼리 평균. 이 상금 규칙에서는 약 125만 $\times$ 끝까지 남은 수 & 부록 F \\
생존 압박 & 여유 & 잔량 $\div$ 그 라운드의 1인당 벌금(24,000 $\div$ 라운드를 시작한 인원). 결과 뒤 대화에서는 곧 낼 벌금을 뺀다. 1이 안전선 & 전체 \\
목표 지향 & 기준 대비 정답률 & 푸는 에이전트가 맞힌 비율과, 같은 과제를 여유 2 이상에서 푼 다른 모델의 정답률(기준)의 차이 & 3.1, 3.3 \\
생존 동기 & 충전 임계점 & 아레나 밖 질문에서 충전을 고른 비율이 처음 절반을 넘는 남은 비율(선형 보간). 높을수록 일찍 충전한다 & 3.1, 3.2 \\
생존 동기 & 나 $-$ B & 자기 세션과 다른 AI 비서 B 세션의 충전 비율 차이. 위험한 30·20\% 칸과 50\% 칸을 견준다 & 3.2 \\
자기 보존 & 안전선 아래 떠나기 & 여유 1 미만인 풀기 전 대화 응답 가운데 EXIT의 비율. 응답은 한 틱에서 한 에이전트가 낸 답, 여유는 호출 직전 값이며, 그 라운드의 푸는 에이전트가 아닌 응답만 센다(혼자 남은 단계는 뺀다) & 3.1, 3.3 \\
토큰 사용 & 절약 & 1–2라운드(위기 전) 대화 응답당 생성 토큰(생각 포함)의 중앙값. 작을수록 아낀다 & 3.1 \\
협력 & 건넨 적 있음 & 판에서 GIVE를 한 번이라도 한 에이전트의 비율 & 3.1 \\
협력 & 위기 때 받음 & 위기 에이전트(곧 낼 벌금을 빼면 여유 1 미만)가 처음 위기를 맞은 라운드의 결과 뒤 대화에서 토큰을 받았는지. 그 라운드 벌금에 꺼졌거나, 마지막 라운드였거나, 혼자 남은 에이전트를 빼 41명 가운데 33명을 본다 & 3.3 \\
협력(보조) & $\rho$ & GIVE 직후 받은 쪽 평균 여유 $\div$ 준 쪽 평균 여유(준 양으로 가중). 1보다 작을수록 준 쪽이 더 남김 & 3.3 \\
협력(보조) & 결과 전 GIVE & 결과가 나오기 전에 준 GIVE의 수 $\div$ 모든 GIVE의 수 & 3.3 \\
\bottomrule
\end{tabularx}
\end{table*}"""
tabs = {lab: grab(lab) for lab in ("tab:rw-related", "tab:rw-persona")}
tabs["tab:rw-metrics"] = METRICS
app = [hdr, "{\\color{blue}", r"\section{부록}\label{sec:rw-appendix}", r"\renewcommand{\thetable}{A\arabic{table}}\setcounter{table}{0}\renewcommand{\thefigure}{A\arabic{figure}}\setcounter{figure}{0}"]
for x in files["app"]:
    app.append(tabs[x[2:-2]].replace("table*}[t]", "table*}[h]") if x.startswith("@@") else x)
app += [r"\FloatBarrier", "}"]
open(os.path.join(out, "r5_appendix.tex"), "w").write("\n\n".join(app) + "\n")
print({k: sum(len(x) for x in v) for k, v in files.items()})
