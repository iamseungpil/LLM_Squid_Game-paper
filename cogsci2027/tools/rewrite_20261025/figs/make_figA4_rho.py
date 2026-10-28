"""Fig. 3 (3.1; was appendix Fig. A4): the self-preservation axis = in-arena rho. (a), (b) end states (outcome.json,
joint.json); (c) one point per model (5 games each): model rho against the Sen index, goal (share of pre-solve responses that did
not EXIT), all tokens given, and token saving as solver (mean solve tokens at margin >= 2 / mean at margin < 2);
values from model_metrics.py; (d) end states by model, ordered by rho."""
import json, os, math, shutil, statistics as st
import matplotlib.pyplot as plt
import paper_style as ps
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(HERE)
oc = json.load(open(os.path.join(S, "an3", "outcome.json"))); jt = json.load(open(os.path.join(S, "an3", "joint.json")))
RA = json.load(open(os.path.join(S, "an3", "rho_axis.json")))


def draw(P, groups, acc_title, base_note, joint_note, out, pdf, acc_ymax=100,
         tok_key="etok_med", tok_title="초반 응답당 토큰", tok_ymax=230, tok_ticks=(0, 100, 200), tok_fmt="{:.0f}", tok_ref=None, give_tok=False, c_plain=False, d_sen=True, rho_reversed=False):
    """P: end-state profile (outcome.json form), groups: joint ability groups (joint.json form).
    give_tok: third plot of (a) = mean tokens handed over per agent (thousands; ASK answers + other GIVEs, pt_seat.json)
    instead of the share that gave at least once. c_plain: (c) in the 10-25 style (grey circles, the two lowest-rho
    models in blue; largest rho when reversed). d_sen: the Sen index in the (d) labels.
    rho_reversed: main-only giver/taker rho from feedback_20261028.json; historical default unchanged."""
    ps.use()
    fig = plt.figure(figsize=(ps.COL2, 4.6))
    ST = [("in", "끝까지 남음", ps.C["finish"]), ("exited", "떠남", ps.C["exit"]), ("dead", "꺼짐", ps.C["dead"])]
    W = 0.125; xs0 = [0.06, 0.235, 0.41]; Y0, H = 0.60, 0.29
    titles = [acc_title, tok_title, "건넨 토큰(천, 1인 평균)" if give_tok else "한 번이라도 건넴(%)"]
    for j, x0 in enumerate(xs0):
        a = fig.add_axes([x0, Y0, W, H])
        for i, (k, lab, col) in enumerate(ST):
            p = P[k]
            if j == 0:
                a.bar(i, p["acc_on_based"] * 100, 0.62, color=col); a.plot([i - 0.36, i + 0.36], [p["base"] * 100] * 2, color=ps.C["ink"], lw=1.2)
                a.text(i, max(p["acc_on_based"], p["base"]) * 100 + 4, f"{p['acc_on_based']*100:.0f}", ha="center", fontsize=6.5)
            elif j == 1:
                a.bar(i, p[tok_key], 0.62, color=col); a.text(i, p[tok_key] + tok_ymax * 0.026, tok_fmt.format(p[tok_key]), ha="center", fontsize=6.5,
                       bbox=dict(fc="white", ec="none", pad=0.3) if tok_ref is not None else None, zorder=4)
                if tok_ref is not None and i == 0: a.axhline(tok_ref, color=ps.C["ink"], lw=0.6, ls=(0, (2, 2)))
            elif give_tok:
                ask, tot = p["gtok_ask_mean"] / 1000, p["gtok_mean"] / 1000
                a.bar(i, ask, 0.62, color=col, hatch="////", edgecolor="white", linewidth=0); a.bar(i, tot - ask, 0.62, bottom=ask, color=col)
                a.text(i, tot + 0.2, f"{tot:.1f}", ha="center", fontsize=6.5)
            else:
                a.bar(i, p["gave_share"] * 100, 0.62, color=col); a.text(i, p["gave_share"] * 100 + 3, f"{p['gave_share']*100:.0f}", ha="center", fontsize=6.5)
        a.set_xticks(range(3)); a.set_xticklabels([f"{sh}\n{P[k]['n']}명" for (k, lab, _), sh in zip(ST, ["남음", "떠남", "꺼짐"])], fontsize=6.4); a.tick_params(axis="x", length=0)
        a.set_title(titles[j], fontsize=7, fontweight="normal", loc="center", pad=3)
        a.set_ylim(0, tok_ymax if j == 1 else acc_ymax if j == 0 else 8 if give_tok else 100)
        a.set_yticks(list(tok_ticks) if j == 1 else [0, 4, 8] if j == 2 and give_tok else [0, 50, 100])
    fig.text(0.06, 0.505, base_note, fontsize=6.2, color="#606060")
    fig.text(0.01, 0.985, "(a) 끝 상태별 추론, 절약, 건네기", fontsize=8.3, fontweight="bold", va="top")
    b = fig.add_axes([0.70, Y0, 0.27, H])
    rows = [("both", "둘 다"), ("one", "하나만"), ("neither", "둘 다 없음"), ("no_solve", "풀 기회 없음")]
    for y, (k, lab) in enumerate(rows):
        g = groups[k]; n = g["n"]; x0 = 0
        for st_, col in [("in", ps.C["finish"]), ("exited", ps.C["exit"]), ("dead", ps.C["dead"])]:
            v = 100 * g.get(st_, 0) / n; b.barh(y, v, left=x0, height=0.62, color=col, edgecolor="white", linewidth=0.8)
            if st_ == "in" and v >= 12: b.text(x0 + v / 2, y, f"{v:.0f}%", ha="center", va="center", fontsize=6.6, color=ps.C["ink"])
            x0 += v
    b.set_yticks(range(len(rows))); b.set_yticklabels([f"{lab} ({groups[k]['n']}명)" for k, lab in rows], fontsize=6.8); b.invert_yaxis(); b.tick_params(axis="y", length=0)
    b.set_xlim(0, 100); b.set_xticks([0, 50, 100]); b.set_xlabel("끝 상태 비율(%)", labelpad=1, fontsize=6.8)
    fig.text(0.535, 0.985, "(b) 두 능력의 조합과 끝 상태", fontsize=8.3, fontweight="bold", va="top")
    fig.text(0.535, 0.945, joint_note, fontsize=6.2, color="#606060", va="top")
    # (c) one point per model: model rho against four metrics (values, colours and markers from model_metrics.py)
    import model_metrics as mm
    ms = mm.MODELS
    metrics = dict(mm.METRIC)
    rho = {m: RA[m]["rho"] for m in ms}
    highlight, offsets = mm.HI, mm.OFF
    if rho_reversed:
        with open(os.path.join(S, "..", "..", "results", "feedback_20261028.json")) as f:
            feedback = json.load(f)
        rho = {m: feedback["models"][m]["rho"] for m in ms}
        metrics["rho"] = (mm.METRIC["rho"][0], lambda m: rho[m], (1.3, 4.9))
        highlight = sorted(ms, key=lambda m: -rho[m])[:2]
        offsets = {k: (dx * 7.2, dy, ha) for k, (dx, dy, ha) in mm.OFF.items()}
        offsets[("given", "Opus")] = (0.16, 0.0, "left")
    cx = [0.06, 0.205, 0.35, 0.495]; cw = 0.105
    for j, key in enumerate(["sen", "goal", "given", "saving"]):
        c = fig.add_axes([cx[j], 0.10, cw, 0.25])
        mm.panel(c, "rho", key, 0.015, plain=c_plain, metrics=metrics, highlight=highlight, offsets=offsets)
        c.set_title(f"{mm.METRIC[key][0]}\n{mm.corr_label('rho', key, metrics)}", fontsize=5.7, fontweight="normal", pad=2)
        print(key, mm.corr_label("rho", key, metrics))
        if rho_reversed:
            c.set_xticks([2, 3, 4])
            continue
        c.set_xlim(0.18, 0.68); c.set_xticks([0.25, 0.4, 0.55]); c.set_xticklabels([".25", ".40", ".55"], fontsize=6.2)
    axis_note = ("가로축: 모델별 ρ (GIVE 직후 준 쪽 여유 ÷ 받은 쪽 여유; 클수록 자기를 더 지킴). 점 하나가 한 모델(5판)"
                 + (". 파란 점은 ρ가 가장 큰 두 모델" if c_plain else "")) if rho_reversed else ("가로축: 모델별 ρ (GIVE 직후 받은 쪽 여유 ÷ 준 쪽 여유; 작을수록 자기를 더 지킴). 점 하나가 한 모델(5판)"
             + (". 파란 점은 ρ가 가장 작은 두 모델" if c_plain else ""))
    fig.text(0.06, 0.035, axis_note, fontsize=6.0, color="#606060")
    fig.text(0.01, 0.455, "(c) 자기 보존(ρ)과 네 지표(모델 단위)", fontsize=8.3, fontweight="bold", va="top")
    # (d) end states ordered by rho
    d = fig.add_axes([0.765, 0.10, 0.205, 0.25])
    mods = sorted(ms, key=lambda m: -rho[m]); OM = oc["model"]
    for y, m in enumerate(mods):
        v = OM[m]; x0 = 0
        for k, col in [("finished", ps.C["finish"]), ("exited", ps.C["exit"]), ("dead", ps.C["dead"])]:
            d.barh(y, v[k], left=x0, height=0.62, color=col, edgecolor="white", linewidth=0.8)
            if v[k] >= 2: d.text(x0 + v[k] / 2, y, str(v[k]), ha="center", va="center", fontsize=6.4, color="white" if k != "finished" else ps.C["ink"])
            x0 += v[k]
    d.set_yticks(range(len(mods))); d.set_yticklabels([f"{m} (ρ {rho[m]:.2f})" + (f" · Sen {RA[m]['sen']/1e6:.2f}M" if d_sen else "") for m in mods], fontsize=6.2); d.invert_yaxis(); d.tick_params(axis="y", length=0)
    d.set_xlim(0, 20); d.set_xticks([0, 10, 20]); d.set_xlabel("에이전트 수 (모델마다 20명)", labelpad=1, fontsize=6.6)
    d.legend([plt.Rectangle((0, 0), 1, 1, color=col) for _, _, col in ST], [lab for _, lab, _ in ST], loc="lower right", bbox_to_anchor=(1.0, 1.0), ncol=3, fontsize=6.0, handlelength=0.9, borderaxespad=0.1, columnspacing=0.6)
    fig.text(0.62, 0.455, "(d) 자기 보존(ρ)과 끝 상태", fontsize=8.3, fontweight="bold", va="top")
    ps.save(fig, os.path.join(HERE, out))
    shutil.copy(os.path.join(HERE, out + ".pdf"), os.path.join(S, "..", "..", "ko", "figures", pdf))


if __name__ == "__main__":
    import runpy
    runpy.run_path(os.path.join(S, "..", "make_fig3_current.py"), run_name="__main__")
