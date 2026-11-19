#!/usr/bin/env python3
"""Generate the GitHub profile image: assets/operator.svg

One Hyprland-style desktop in Catppuccin Mocha: wallpaper + YASB bar + a frosted
tmux window split into five panes — AI · Quant · Econ · GTM · Business.

Live parts (refreshed every 6h by .github/workflows/desktop.yml):
  - AI pane    real recent commits      tools/recent_commits.json (written by the Action)
  - Quant pane NIFTY candles + signals  } Yahoo chart API, cached to tools/markets.json
  - Econ pane  US yield curve + macro   } so a failed fetch falls back to the last good data

Self-contained SVG, stdlib only. Animations are CSS/SMIL inside the SVG, which
GitHub's image proxy plays.

Run:  py -3.10 tools/gen.py
"""
import os, html, json, math, time, datetime, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))

# ── Catppuccin Mocha ────────────────────────────────────────────────────────
C = dict(
    base="#1e1e2e", mantle="#181825", crust="#11111b", surface0="#313244",
    surface1="#45475a", overlay="#6c7086", text="#cdd6f4", subtext="#a6adc8",
    pink="#f5c2e7", mauve="#cba6f7", red="#f38ba8", peach="#fab387",
    yellow="#f9e2af", green="#a6e3a1", teal="#94e2d5", sky="#89dceb",
    sapphire="#74c7ec", blue="#89b4fa", lavender="#b4befe",
)
FONT = "'JetBrains Mono','JetBrainsMono Nerd Font','Cascadia Code','Fira Code',ui-monospace,'DejaVu Sans Mono',monospace"
FS, CW = 15.5, 9.3          # bar font size + monospace advance at that size
PS = 13                     # pane font size
PCW = CW * PS / FS          # pane char advance
LH = 19                     # pane line height
BAR = 34                    # window title-bar height


def esc(s):
    return html.escape(s, quote=True)


def T(x, y, spans, size=PS, anchor=None, weight=None):
    """Text at x,y. spans = str or [(text, color-key-or-hex), ...]."""
    if isinstance(spans, str):
        spans = [(spans, "text")]
    a = f' text-anchor="{anchor}"' if anchor else ""
    w = f' font-weight="{weight}"' if weight else ""
    inner = "".join(f'<tspan fill="{C.get(k, k)}">{esc(s)}</tspan>' for s, k in spans)
    return f'<text x="{x:.1f}" y="{y:.1f}" style="font-size:{size}px"{a}{w} xml:space="preserve">{inner}</text>'


def pill(cx, y, txt, fg, bg, size=PS, pad=9, h=22):
    """Pill centred on cx, top at y."""
    w = len(txt) * CW * size / FS + 2 * pad
    return (f'<rect x="{cx - w / 2:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" rx="7" fill="{C[bg]}"/>'
            + T(cx, y + h / 2 + size * 0.36, [(txt, fg)], size, "middle", 600))


def arrow(v):
    """(▲1.23%, color) for a fractional change."""
    return ("▲" if v >= 0 else "▼") + f"{abs(v) * 100:.2f}%", ("green" if v >= 0 else "red")


def pane_title(x, y, name, width):
    n = max(2, int((width - (len(name) + 1) * PCW) / PCW))
    return T(x, y, [(name, "mauve"), (" " + "─" * n, "surface1")])


# ── data ────────────────────────────────────────────────────────────────────
def recent_commits():
    try:
        with open(os.path.join(HERE, "recent_commits.json"), encoding="utf-8") as f:
            return [c for c in json.load(f) if c.get("msg")][:4]
    except Exception:
        return []


TICKERS = {
    "nifty": "^NSEI", "spx": "^GSPC", "btc": "BTC-USD", "inr": "INR=X", "gold": "GC=F",
    "oil": "CL=F", "dxy": "DX-Y.NYB",
    "y3m": "^IRX", "y5y": "^FVX", "y10": "^TNX", "y30": "^TYX",   # US Treasury yields
}


def _fetch(sym):
    """6 months of daily OHLC for one symbol, keyed by exchange-local date."""
    import urllib.request, urllib.parse
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/"
           f"{urllib.parse.quote(sym)}?range=6mo&interval=1d")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        res = json.load(r)["chart"]["result"][0]
    off = res["meta"].get("gmtoffset", 0)
    q = res["indicators"]["quote"][0]
    rows = {}
    for ts, o, h, l, c in zip(res["timestamp"], q["open"], q["high"], q["low"], q["close"]):
        if None not in (o, h, l, c):
            rows[time.strftime("%Y-%m-%d", time.gmtime(ts + off))] = (o, h, l, c)
    days = sorted(rows)
    if len(days) < 70:
        raise ValueError(f"only {len(days)} bars")
    return {"d": days, **{k: [round(rows[d][i], 4) for d in days] for i, k in enumerate("ohlc")}}


def markets():
    """Fetch every ticker; per-symbol failure falls back to the cached copy."""
    p = os.path.join(HERE, "markets.json")
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    fresh = False
    for key, sym in TICKERS.items():
        try:
            data[key] = _fetch(sym)
            fresh = True
        except Exception as e:
            print(f"markets: {sym} fetch failed ({e}) — using cache")
    if fresh:
        data["asof"] = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
        data = {k: data[k] for k in [*TICKERS, "asof"] if k in data}
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, separators=(",", ":"))
    missing = [k for k in TICKERS if k not in data]
    if missing:
        raise SystemExit(f"no market data (live or cached) for: {missing}")
    return data


def signals(c):
    """Quant read-out from a close series (needs >= 61 closes)."""
    r = [math.log(b / a) for a, b in zip(c, c[1:])]
    s20, s50 = sum(c[-20:]) / 20, sum(c[-50:]) / 50
    vol20 = st.stdev(r[-20:]) * math.sqrt(252)
    vol_all = st.stdev(r) * math.sqrt(252)
    peak, mdd = c[-60], 0.0
    for x in c[-60:]:
        peak = max(peak, x)
        mdd = min(mdd, x / peak - 1)
    trend = ("uptrend" if c[-1] > s50 and s20 > s50 else
             "downtrend" if c[-1] < s50 and s20 < s50 else "range")
    vreg = ("high vol" if vol20 > 1.2 * vol_all else
            "low vol" if vol20 < 0.8 * vol_all else "normal vol")
    return dict(
        last=c[-1], chg=c[-1] / c[-2] - 1, mom20=c[-1] / c[-21] - 1, vol20=vol20,
        sharpe=st.mean(r[-60:]) / st.stdev(r[-60:]) * math.sqrt(252), mdd=mdd,
        z=(c[-1] - s20) / st.stdev(c[-20:]), regime=f"{trend} · {vreg}")


# ── chrome ──────────────────────────────────────────────────────────────────
def wallpaper(W, H):
    def blob(i, cx, cy, r, col, op):
        return (f'<radialGradient id="b{i}" cx="{cx}%" cy="{cy}%" r="{r}%">'
                f'<stop offset="0" stop-color="{col}" stop-opacity="{op}"/>'
                f'<stop offset="1" stop-color="{col}" stop-opacity="0"/></radialGradient>')
    return (
        '<defs>'
        f'<linearGradient id="wp" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{C["crust"]}"/>'
        f'<stop offset="1" stop-color="{C["mantle"]}"/></linearGradient>'
        + blob(1, 16, 20, 60, C['mauve'], 0.40) + blob(2, 88, 14, 55, C['blue'], 0.32)
        + blob(3, 62, 98, 60, C['teal'], 0.24) + blob(4, 6, 94, 46, C['pink'], 0.18)
        + '</defs>'
        + f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="18" fill="url(#wp)" stroke="{C["surface0"]}"/>'
        + "".join(f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="18" fill="url(#b{i})"/>' for i in (1, 2, 3, 4))
    )


def titlebar(W, title):
    return (
        f'<path d="M0.5 12.5 A12 12 0 0 1 12.5 0.5 H{W - 12.5} A12 12 0 0 1 {W - 0.5} 12.5 V{BAR} H0.5 Z" '
        f'fill="{C["mantle"]}" fill-opacity="0.66"/>'
        f'<line x1="0.5" y1="{BAR}" x2="{W - 0.5}" y2="{BAR}" stroke="{C["surface0"]}"/>'
        f'<rect x="16" y="12" width="10" height="10" rx="3" fill="{C["mauve"]}"/>'
        + T(34, 21, [(title, "subtext")]))


def yasb(W, m, H=56):
    """Status bar: identity + workspaces | tagline | live widgets."""
    y, ph = 12, 32
    parts = [f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="14" fill="{C["mantle"]}" '
             f'fill-opacity="0.82" stroke="{C["surface0"]}"/>']

    def box(x, txt, fg, bg):
        w = len(txt) * CW + 24
        parts.append(f'<rect x="{x:.0f}" y="{y}" width="{w:.0f}" height="{ph}" rx="9" fill="{C[bg]}"/>'
                     + T(x + 12, y + 22, [(txt, fg)], FS, weight=600))
        return w

    x = 14
    x += box(x, "◆ indra-os", "crust", "mauve") + 10
    for ws in ("1", "2", "3"):
        w = CW + 20
        on = ws == "2"
        parts.append(f'<rect x="{x:.0f}" y="{y}" width="{w:.0f}" height="{ph}" rx="8" fill="{C["mauve" if on else "surface0"]}"/>'
                     + T(x + w / 2, y + 22, [(ws, "crust" if on else "subtext")], FS, "middle"))
        x += w + 6
    left_end = x

    chg = m["nifty"]["c"][-1] / m["nifty"]["c"][-2] - 1
    a, col = arrow(chg)
    widgets = [(f"NIFTY {a}", "crust", col), ("● 3 agents", "crust", "green"),
               (m["asof"][11:], "crust", "lavender")]
    rx = W - 14
    for txt, fg, bg in reversed(widgets):
        rx -= len(txt) * CW + 24
        box(rx, txt, fg, bg)
        rx -= 7
    parts.append(T((left_end + rx) / 2, y + 21,
                   [("AI", "mauve"), (" · ", "overlay"), ("Business", "blue"), (" · ", "overlay"),
                    ("Quant", "yellow"), (" · ", "overlay"), ("Econ", "green"), (" · ", "overlay"),
                    ("GTM", "peach")], 14, "middle", 600))
    return "".join(parts)


# ── panes ───────────────────────────────────────────────────────────────────
def pane_ai(x0, y0, w):
    cx = x0 + w / 2
    out = [pane_title(x0 + 14, y0 + 20, "0:ai", w - 28)]
    hy, my = y0 + 34, y0 + 84
    xs = [x0 + w * 0.2, cx, x0 + w * 0.8]
    for mx in xs:   # orchestrator → model edges, dashes flowing downward
        out.append(f'<path d="M{cx:.1f},{hy + 22} C{cx:.1f},{hy + 44} {mx:.1f},{my - 24} {mx:.1f},{my}" '
                   f'fill="none" stroke="{C["overlay"]}" stroke-width="1.4" class="flow"/>')
    out.append(pill(cx, hy, "◆ orchestrator", "crust", "mauve"))
    for mx, (name, col) in zip(xs, [("claude", "blue"), ("codex", "green"), ("gemini", "peach")]):
        out.append(pill(mx, my, name, "crust", col, 12.5, 8, 21))
    out.append(T(cx, y0 + 126, [("agents", "text"), (" · RAG · MCP · ", "overlay"), ("evals", "text")], 12.5, "middle"))
    out.append(T(x0 + 14, y0 + 152, [("git log", "mauve"), (" · live", "overlay")], 12.5))
    for i, c in enumerate(recent_commits()):
        msg = " ".join(c["msg"].split())
        msg = msg[:26] + "…" if len(msg) > 27 else msg
        out.append(T(x0 + 14, y0 + 171 + i * LH,
                     [("* ", "yellow"), ((c.get("sha") or "")[:7] + " ", "peach"), (msg, "text")], 12.5))
    out.append(T(x0 + 14, y0 + 250, [("● ", "green"), ("9 services", "text"), (" · 0 failed", "overlay")], 12.5))
    return "".join(out)


def pane_quant(x0, y0, w, m):
    nf = m["nifty"]
    sg = signals(nf["c"])
    a, col = arrow(sg["chg"])
    out = [pane_title(x0 + 14, y0 + 20, "1:quant", w - 28),
           T(x0 + 14, y0 + 42, [("NIFTY 50 ", "mauve"), (f"{sg['last']:,.1f} ", "text"), (a, col)])]

    N = 40
    cx0, cx1, cy0, cy1 = x0 + 14, x0 + w - 54, y0 + 54, y0 + 140
    o, h, l, c = (nf[k][-N:] for k in "ohlc")
    lo, hi = min(l), max(h)
    pad = (hi - lo) * 0.06
    lo, hi = lo - pad, hi + pad
    Y = lambda v: cy1 - (v - lo) / (hi - lo) * (cy1 - cy0)
    step = (cx1 - cx0) / N
    X = lambda i: cx0 + step * (i + 0.5)
    for k in range(3):
        v = lo + (hi - lo) * (k + 0.5) / 3
        out.append(f'<line x1="{cx0}" y1="{Y(v):.1f}" x2="{cx1}" y2="{Y(v):.1f}" stroke="{C["surface0"]}"/>'
                   + T(cx1 + 6, Y(v) + 3.5, [(f"{v:,.0f}", "overlay")], 10.5))
    candles = ""
    for i in range(N):
        cc = C["green"] if c[i] >= o[i] else C["red"]
        top, bot = Y(max(o[i], c[i])), Y(min(o[i], c[i]))
        candles += (f'<line x1="{X(i):.1f}" y1="{Y(h[i]):.1f}" x2="{X(i):.1f}" y2="{Y(l[i]):.1f}" stroke="{cc}"/>'
                    f'<rect x="{X(i) - step * 0.32:.1f}" y="{top:.1f}" width="{step * 0.64:.1f}" '
                    f'height="{max(bot - top, 1.2):.1f}" fill="{cc}"/>')
    allc = nf["c"]
    sma = [sum(allc[j - 19:j + 1]) / 20 for j in range(len(allc) - N, len(allc))]
    sma_path = "M" + " L".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(sma))
    # candles draw in left→right once (SMIL); static full width if animation unsupported
    out.append(f'<clipPath id="rv"><rect x="{cx0 - 2}" y="{cy0 - 8}" width="{cx1 - cx0 + 4}" height="{cy1 - cy0 + 16}">'
               f'<animate attributeName="width" from="0" to="{cx1 - cx0 + 4}" dur="2.2s" fill="freeze"/></rect></clipPath>'
               f'<g clip-path="url(#rv)">{candles}<path d="{sma_path}" fill="none" stroke="{C["lavender"]}" stroke-width="1.6"/></g>')
    yl = Y(c[-1])
    out.append(f'<line x1="{cx0}" y1="{yl:.1f}" x2="{cx1}" y2="{yl:.1f}" stroke="{C[col]}" stroke-dasharray="3 3" stroke-opacity="0.7"/>'
               f'<circle cx="{X(N - 1):.1f}" cy="{yl:.1f}" r="3.5" fill="{C[col]}" class="pulse"/>')

    pct = lambda v: f"{v * 100:+.2f}%"
    out += [
        T(x0 + 14, y0 + 164, [("mom20 ", "subtext"), (pct(sg["mom20"]), "green" if sg["mom20"] >= 0 else "red"),
                              ("  vol ", "subtext"), (f"{sg['vol20'] * 100:.1f}%", "text")]),
        T(x0 + 14, y0 + 183, [("sharpe ", "subtext"), (f"{sg['sharpe']:+.2f}", "yellow"),
                              ("  maxdd ", "subtext"), (pct(sg["mdd"]), "red")]),
        T(x0 + 14, y0 + 202, [("z ", "subtext"), (f"{sg['z']:+.2f}σ  ", "teal"), (sg["regime"], "peach")]),
    ]
    for i, pair in enumerate(((("spx", "S&P "), ("btc", "  BTC ")), (("gold", "GOLD "), ("inr", "  INR ")))):
        spans = []
        for key, lab in pair:
            cs = m[key]["c"]
            a2, c2 = arrow(cs[-1] / cs[-2] - 1)
            spans += [(lab, "subtext"), (a2, c2)]
        out.append(T(x0 + 14, y0 + 228 + i * LH, spans, 12.5))
    return "".join(out)


def pane_econ(x0, y0, w, m):
    out = [pane_title(x0 + 14, y0 + 20, "2:econ", w - 28),
           T(x0 + 14, y0 + 42, [("US curve ", "mauve"), ("━ now ", "teal"), ("┅ 3m ago", "overlay")])]
    keys, labs = ("y3m", "y5y", "y10", "y30"), ("3M", "5Y", "10Y", "30Y")
    now = [m[k]["c"][-1] for k in keys]
    ago = [m[k]["c"][-64] for k in keys]
    px0, px1, py0, py1 = x0 + 34, x0 + w - 30, y0 + 66, y0 + 128
    lo, hi = min(now + ago) - 0.12, max(now + ago) + 0.12
    X = lambda i: px0 + (px1 - px0) * i / 3
    Y = lambda v: py1 - (v - lo) / (hi - lo) * (py1 - py0)
    pts = lambda vals: " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(vals))
    out.append(f'<line x1="{px0}" y1="{py1 + 6}" x2="{px1}" y2="{py1 + 6}" stroke="{C["surface1"]}"/>')
    out.append(f'<polyline points="{pts(ago)}" fill="none" stroke="{C["overlay"]}" stroke-width="1.5" stroke-dasharray="4 3"/>')
    out.append(f'<polyline points="{pts(now)}" fill="none" stroke="{C["teal"]}" stroke-width="2.2" stroke-linejoin="round"/>')
    for i, v in enumerate(now):
        out.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="3.5" fill="{C["teal"]}"/>'
                   + T(X(i), Y(v) - 8, [(f"{v:.2f}", "teal")], 10.5, "middle")
                   + T(X(i), py1 + 21, [(labs[i], "overlay")], 10.5, "middle"))

    spread = now[2] - now[0]
    state, sc = (("inverted", "red") if spread < 0 else ("flat", "yellow") if spread < 0.5 else ("normal", "green"))
    m1 = lambda k: m[k]["c"][-1] / m[k]["c"][-22] - 1
    dx = m1("dxy")
    usd = "strong USD" if dx > 0.01 else "weak USD" if dx < -0.01 else "steady USD"

    def macro(k1, l1, f1, k2, l2, f2):
        s = []
        for k, lab, fmt in ((k1, l1, f1), (k2, l2, f2)):
            a, c = arrow(m1(k))
            s += [(lab, "subtext"), (fmt.format(m[k]["c"][-1]) + " ", "text"), (a, c)]
        return s
    out += [
        T(x0 + 14, y0 + 172, [("10Y–3M ", "subtext"), (f"{spread:+.2f}pp ", sc), (f"{state} curve", "text")]),
        T(x0 + 14, y0 + 191, macro("dxy", "DXY ", "{:.1f}", "inr", "  INR ", "{:.2f}"), 12.5),
        T(x0 + 14, y0 + 210, macro("oil", "OIL ", "{:.1f}", "gold", "  GOLD ", "{:,.0f}"), 12.5),
        T(x0 + 14, y0 + 232, [("read ", "overlay"), (f"{state} curve · {usd}", "peach")]),
        T(x0 + 14, y0 + 250, [("Δ = 1 month · rule-based", "overlay")], 10.5),
    ]
    return "".join(out)


def pane_gtm(x0, y0, w):
    out = [pane_title(x0 + 14, y0 + 20, "3:gtm", w - 28)]
    stages = [("acquire", "blue", "SEO · content · outbound"),
              ("activate", "sapphire", "time-to-value < 5 min"),
              ("retain", "teal", "habit loops · weekly value"),
              ("monetize", "green", "usage / seat pricing"),
              ("refer", "peach", "product-native virality")]
    fx = x0 + 14 + 76
    for i, (name, col, lever) in enumerate(stages):
        y = y0 + 34 + i * 31
        bw = 152 - i * 20
        out.append(f'<rect x="{fx - bw / 2:.1f}" y="{y}" width="{bw}" height="25" rx="5" fill="{C[col]}" '
                   f'fill-opacity="0.9"/>'
                   + T(fx, y + 17, [(name, "crust")], 12, "middle", 700)
                   + T(x0 + 174, y + 17, [("▸ ", "overlay"), (lever, "subtext")], 12.5))
    out.append(T(x0 + 14, y0 + 210, [("motion ", "overlay"), ("PLG", "text"), (" + ", "overlay"),
                                     ("founder-led sales", "text"), (" + ", "overlay"), ("content", "text")]))
    return "".join(out)


def radar(cx, cy, R, axes, now, goal):
    """5-axis profile: solid = now, dashed (animated) = trajectory. Shape only."""
    ang = [math.radians(-90 + 72 * i) for i in range(5)]
    pt = lambda i, r: (cx + R * r * math.cos(ang[i]), cy + R * r * math.sin(ang[i]))
    poly = lambda vals: " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(i, v) for i, v in enumerate(vals)))
    S1 = C["surface1"]
    out = [f'<polygon points="{poly([k] * 5)}" fill="none" stroke="{S1}"/>' for k in (0.5, 1.0)]
    out += [f'<line x1="{cx}" y1="{cy}" x2="{pt(i, 1)[0]:.1f}" y2="{pt(i, 1)[1]:.1f}" stroke="{S1}"/>' for i in range(5)]
    out.append(f'<polygon points="{poly(goal)}" fill="none" stroke="{C["yellow"]}" stroke-width="1.4" '
               f'stroke-dasharray="4 3" class="traj"/>'
               f'<polygon points="{poly(now)}" fill="{C["mauve"]}" fill-opacity="0.25" stroke="{C["mauve"]}" '
               f'stroke-width="2" stroke-linejoin="round"/>')
    for i, (name, col) in enumerate(axes):
        x, y = pt(i, now[i])
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{C[col]}"/>')
        x, y = pt(i, 1.22)
        c = math.cos(ang[i])
        anchor = "middle" if abs(c) < 0.2 else ("start" if c > 0 else "end")
        dy = -3 if i == 0 else (11 if math.sin(ang[i]) > 0.5 else 4)
        out.append(T(x, y + dy, [(name, col)], 11, anchor, 700))
    out.append(T(cx, cy + R + 34, [("━ now ", "mauve"), ("┅ next", "yellow")], 10.5, "middle"))
    return "".join(out)


def pane_biz(x0, y0, w):
    O = "overlay"
    out = [pane_title(x0 + 14, y0 + 20, "4:biz", w - 28)]
    tree = [
        [("profit ", "mauve"), ("─┬─ ", O), ("revenue ", "blue"), ("─┬─ ", O), ("users × conv × ARPU", "text")],
        [("        │           └─ ", O), ("NDR > 110%", "green"), ("  expansion", O)],
        [("        └─ ", O), ("costs ", "red"), ("───┬─ ", O), ("CAC  → payback < 12 mo", "text")],
        [("                    └─ ", O), ("COGS → gross margin > 70%", "text")],
    ]
    out += [T(x0 + 14, y0 + 44 + i * LH, r) for i, r in enumerate(tree)]
    out += [
        T(x0 + 14, y0 + 130, [("targets ", O), ("LTV/CAC > 3 · rule of 40 · burn < 1.5×", "text")]),
        T(x0 + 14, y0 + 149, [("moats   ", O), ("distribution · data · network effects", "text")]),
        T(x0 + 14, y0 + 168, [("loop    ", O), ("understand", "green"), (" ▸ ", O), ("model", "yellow"), (" ▸ ", O),
                              ("build", "mauve"), (" ▸ ", O), ("sell", "peach"), (" ▸ ", O), ("scale", "blue")]),
        T(x0 + 14, y0 + 194, [("# thesis: ", O), ("model the market, then build & sell into it", "teal")]),
    ]
    # ponytail: self-assessed shape, edit freely — order: AI, BIZ, GTM, ECON, QUANT
    out.append(radar(x0 + w - 82, y0 + 98, 50,
                     [("AI", "mauve"), ("BIZ", "blue"), ("GTM", "peach"), ("ECON", "green"), ("QUANT", "yellow")],
                     now=[0.92, 0.84, 0.80, 0.74, 0.42], goal=[0.92, 0.84, 0.80, 0.82, 0.88]))
    return "".join(out)


# ── compose ─────────────────────────────────────────────────────────────────
def operator(m):
    W, H = 984, 584
    TOP, MID, BOT = 40, 307, 548          # top-row start, row split, bottom-row end
    c1, c2, b1 = 328, 656, 400            # top-row column splits, bottom-row split
    O, S1 = C["overlay"], C["surface1"]
    seps = (f'<line x1="{c1}" y1="{TOP}" x2="{c1}" y2="{MID - 4}" stroke="{O}"/>'
            f'<line x1="{c2}" y1="{TOP}" x2="{c2}" y2="{MID - 4}" stroke="{O}"/>'
            f'<line x1="10" y1="{MID}" x2="{W - 10}" y2="{MID}" stroke="{S1}"/>'
            f'<line x1="{b1}" y1="{MID + 4}" x2="{b1}" y2="{BOT}" stroke="{O}"/>')
    sb = H - 30
    status = (f'<rect x="8" y="{sb}" width="{W - 16}" height="24" rx="7" fill="{C["green"]}"/>'
              f'<rect x="8" y="{sb}" width="78" height="24" rx="7" fill="{C["mauve"]}"/>'
              + T(22, sb + 17, [("indra", "crust")], PS, weight=700)
              + T(100, sb + 17, [("0:ai  1:quant  2:econ  3:gtm  4:biz", "crust")])
              + T(W - 22, sb + 17, [(f"data {m['asof']}", "crust")], 12, "end"))
    win = (f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" fill="{C["base"]}" '
           f'fill-opacity="0.80" stroke="{S1}"/>'
           + titlebar(W, "abhinav@indra-os — tmux: operator")
           + seps
           + pane_ai(0, TOP, c1) + pane_quant(c1, TOP, c2 - c1, m) + pane_econ(c2, TOP, W - c2, m)
           + pane_gtm(0, MID, b1) + pane_biz(b1, MID, W - b1)
           + status)

    M, BARH, GAP = 28, 56, 16
    W2, H2 = W + 2 * M, M + BARH + GAP + H + M
    css = (f"text{{font-family:{FONT};font-variant-ligatures:none;white-space:pre;}}"
           ".flow{stroke-dasharray:4 4;animation:fl 1.1s linear infinite}@keyframes fl{to{stroke-dashoffset:-16}}"
           ".traj{animation:tj 6s linear infinite}@keyframes tj{to{stroke-dashoffset:-70}}"
           ".pulse{animation:pl 1.4s ease-in-out infinite}@keyframes pl{50%{opacity:.2}}")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W2}" height="{H2}" viewBox="0 0 {W2} {H2}" role="img">'
            f'<title>abhinav · AI · Business · Quant · Economics · GTM</title>'
            f'<style>{css}</style>{wallpaper(W2, H2)}'
            f'<g transform="translate({M},{M})">{yasb(W, m)}</g>'
            f'<g transform="translate({M},{M + BARH + GAP})">{win}</g></svg>')


def main():
    svg = operator(markets())
    import xml.dom.minidom
    xml.dom.minidom.parseString(svg)            # ponytail: one self-check — well-formed XML
    p = os.path.join(os.path.dirname(HERE), "assets", "operator.svg")
    with open(p, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {p}  ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
