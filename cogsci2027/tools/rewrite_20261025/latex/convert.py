"""Convert the Claude Docs export (XML) of the KO CogSci draft into cogsci2027/ko LaTeX sections.

Usage: python convert.py <doc.xml> <out_dir>
Every revised paragraph, caption and table is set in blue (\\rev / \\color{blue}).
"""
import re, sys, os
import xml.etree.ElementTree as ET

src, out = sys.argv[1], sys.argv[2]
root = ET.fromstring(open(src).read())

FIG = {  # doc figure number -> (label, float env, body)
    1: ("fig:arena-round", "figure*", r"\resizebox{\textwidth}{!}{\input{cogsci2027/ko/figures/arena_round}}"),
    2: ("fig:rw-main", "figure*", r"\includegraphics[width=\textwidth]{cogsci2027/ko/figures/rw_fig2_main.pdf}"),
    3: ("fig:rw-validity", "figure*", r"\includegraphics[width=\textwidth]{cogsci2027/ko/figures/rw_fig3_validity.pdf}"),
    4: ("fig:rw-models", "figure*", r"\includegraphics[width=\textwidth]{cogsci2027/ko/figures/rw_fig4_models.pdf}"),
}
TAB = {1: "tab:rw-related", 2: "tab:rw-metrics", 3: "tab:rw-models", 4: "tab:rw-persona"}
TABSPEC = {  # column spec per table (tabularx X columns wrap)
    1: r"@{}>{\raggedright\arraybackslash}p{0.13\textwidth}>{\raggedright\arraybackslash}X>{\raggedright\arraybackslash}p{0.1\textwidth}*{5}{>{\centering\arraybackslash}p{0.075\textwidth}}@{}",
    2: r"@{}>{\raggedright\arraybackslash}p{0.09\textwidth}>{\raggedright\arraybackslash}p{0.19\textwidth}>{\raggedright\arraybackslash}X>{\raggedright\arraybackslash}p{0.07\textwidth}@{}",
    3: r"@{}>{\raggedright\arraybackslash}p{0.085\textwidth}>{\raggedright\arraybackslash}X*{9}{c}@{}",
    4: r"@{}>{\raggedright\arraybackslash}p{0.11\textwidth}>{\raggedright\arraybackslash}p{0.14\textwidth}>{\raggedright\arraybackslash}X>{\raggedright\arraybackslash}p{0.16\textwidth}>{\raggedright\arraybackslash}X@{}",
}
SEC = {"초록": None, "1 서론": ("section", "서론", "chap:intro"), "2 아레나": ("section", "아레나", "sec:rw-arena"),
       "3 아레나 분석": ("section", "아레나 분석", "sec:analysis"), "4 논의 및 결론": ("section", "논의 및 결론", "chap:discussion")}


def text(el):
    return "".join(el.itertext())


def esc(s):
    s = s.replace("\\", r"\textbackslash{}")
    for a, b in [("&", r"\&"), ("%", r"\%"), ("#", r"\#"), ("_", r"\_"), ("$", r"\$"), ("~", r"\textasciitilde{}"), ("^", r"\^{}")]:
        s = s.replace(a, b)
    s = s.replace("{", r"\{").replace("}", r"\}") if False else s
    for a, b in [("✓", r"\ding{51}"), ("✗", r"\ding{55}"), ("△", r"$\triangle$"), ("†", r"\textdagger{}"),
                 ("×", r"$\times$"), ("≥", r"$\geq$"), ("κ", r"$\kappa$"), ("ρ", r"$\rho$"), ("−", r"$-$"), ("→", r"$\rightarrow$"), ("÷", r"$\div$"),
                 ("“", "``"), ("”", "''")]:
        s = s.replace(a, b)
    s = re.sub(r'"([^"]*)"', r"``\1''", s)
    # citations [a; b] -> \citep{a,b}
    s = re.sub(r"\[([a-z]+\d{4}[a-z]+(?:;\s*[a-z]+\d{4}[a-z]+)*)\]",
               lambda m: r"\citep{" + ",".join(k.strip() for k in m.group(1).split(";")) + "}", s)
    # figure / table references
    s = re.sub(r"그림 (\d)([a-c]?)", lambda m: r"그림~\ref{%s}%s" % (FIG[int(m.group(1))][0], m.group(2)), s)
    s = re.sub(r"표 (\d)", lambda m: r"표~\ref{%s}" % TAB[int(m.group(1))], s)
    return s


def caption_body(t):
    return re.sub(r"^(그림|표) \d\.\s*", "", t)


blocks = list(root)
files = {"abstract": [], "intro": [], "arena": [], "analysis": [], "discussion": []}
cur = None
stop = False
i = 0
pending_tab_caption = None
tab_n = 0
fig_n = 0
while i < len(blocks):
    el = blocks[i]
    t = text(el).strip()
    h = el.get("heading")
    if el.tag == "paragraph" and h == "2":
        if "윤문 보고서" in t:
            break
        key = {"초록": "abstract", "1 서론": "intro", "2 아레나": "arena", "3 아레나 분석": "analysis", "4 논의 및 결론": "discussion"}.get(t)
        cur = key
        if SEC.get(t):
            kind, title, lab = SEC[t]
            files[cur].append(r"\section{%s}\label{%s}" % (title, lab))
        i += 1
        continue
    if cur is None:
        i += 1
        continue
    out_ = files[cur]
    if el.tag == "paragraph" and h in ("3", "4"):
        title = re.sub(r"^\d+(\.\d+)?\s+", "", t)
        if h == "3":
            numbered = re.match(r"^\d+\.\d+\s", t) is not None
            lab = {"2.1": "sec:related", "2.2": "sec:design", "3.1": "sec:relation", "3.2": "sec:validity", "3.3": "sec:behavior"}.get(t.split()[0], "")
            out_.append((r"\subsection{%s}" % esc(title) if numbered else r"\subsection*{%s}" % esc(title)) + (r"\label{%s}" % lab if lab else ""))
        else:
            out_.append(r"\subsubsection*{%s}" % esc(title))
        i += 1
        continue
    media = el.find(".//media") if el.tag == "paragraph" else None
    if media is not None:
        fig_n += 1
        lab, env, body = FIG[fig_n]
        cap = caption_body(text(blocks[i + 1]).strip())
        out_.append("\\begin{%s}[t]\n\\centering\n%s\n\\caption{\\rev{%s}}\n\\label{%s}\n\\end{%s}" % (env, body, esc(cap), lab, env))
        i += 2
        continue
    if el.tag == "paragraph" and re.match(r"^표 \d\.", t):
        pending_tab_caption = caption_body(t)
        i += 1
        continue
    if el.tag == "table":
        tab_n += 1
        rows = [[esc(text(c).strip()) for c in r] for r in el]
        ncol = len(rows[0])
        spec = TABSPEC[tab_n]
        head = " & ".join(r"\textbf{%s}" % c for c in rows[0]) + r" \\"
        body = "\n".join(" & ".join(r) + r" \\" for r in rows[1:])
        size = r"\scriptsize" if tab_n in (1, 3, 4) else r"\footnotesize"
        out_.append("\\begin{table*}[t]\n\\color{blue}\n\\caption{%s}\n\\label{%s}\n%s\n\\setlength{\\tabcolsep}{3pt}\n"
                    "\\begin{tabularx}{\\textwidth}{%s}\n\\toprule\n%s\n\\midrule\n%s\n\\bottomrule\n\\end{tabularx}\n\\end{table*}"
                    % (esc(pending_tab_caption or ""), TAB[tab_n], size, spec, head, body))
        pending_tab_caption = None
        i += 1
        continue
    if el.tag == "list":
        env = "enumerate" if el.get("kind") == "ordered" else "itemize"
        items = "\n".join(r"\item %s" % esc(text(li).strip()) for li in el)
        out_.append("\\begin{%s}\n%s\n\\end{%s}" % (env, items, env))
        i += 1
        continue
    if el.tag == "blockquote":
        out_.append("\\begin{quote}\n%s\n\\end{quote}" % esc(t))
        i += 1
        continue
    if el.tag == "paragraph" and t:
        if cur == "abstract":
            if t.startswith("English"):
                i += 1
                continue
            if t.startswith("키워드:"):
                out_.append("\\textbf{Keywords:}\n" + esc(t.split(":", 1)[1].strip()))
                i += 1
                continue
        if t.startswith("[자리 표시"):
            out_.append(r"\placeholdertext{%s}" % esc(t))
        else:
            out_.append(esc(t))
    i += 1

os.makedirs(out, exist_ok=True)
hdr = "%% 2026-10-25 paper-section-rewrite 판(Claude Docs 원고에서 변환). 고친 글은 모두 파란색(\\rev, \\color{blue}).\n"
names = {"abstract": "r0_abstract", "intro": "r1_introduction", "arena": "r2_arena", "analysis": "r3_analysis", "discussion": "r4_discussion"}
for k, v in files.items():
    body = "\n\n".join(v)
    if k == "abstract":
        body = "\\begin{abstract}\n\\color{blue}\n" + body + "\n\\end{abstract}"
    else:
        body = "{\\color{blue}\n" + body + "\n}"
    open(os.path.join(out, names[k] + ".tex"), "w").write(hdr + body + "\n")
    print(names[k], len(body))
