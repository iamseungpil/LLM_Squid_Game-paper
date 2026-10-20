# Overleaf and local latexmk: find the official venue styles (cogsci.sty, sn-jnl.cls, sn-nature.bst) from main.tex
ensure_path('TEXINPUTS', './cogsci2027/style//', './natmi/style//');
ensure_path('BSTINPUTS', './natmi/style//');
