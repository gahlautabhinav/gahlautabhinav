#!/usr/bin/env python3
"""Generate the GitHub profile image: assets/operator.svg

One Hyprland-style desktop in Catppuccin Mocha: wallpaper + YASB bar + a frosted
tmux window split into seven panes — AI · Quant · Econ · GTM · Business · Finance · Valuation.

Live parts (refreshed every 6h by .github/workflows/desktop.yml):
  - AI pane    real recent commits      tools/recent_commits.json (written by the Action)
  - Quant pane NIFTY candles + signals  } Yahoo chart API, cached to tools/markets.json
  - Econ pane  US yield curve + macro   } so a failed fetch falls back to the last good data
  - Fin pane   NVIDIA latest 10-K       SEC EDGAR XBRL, cached to tools/fundamentals.json
  - Val pane   CAPM → WACC → reverse DCF from live price, 10Y yield and beta

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
    "nvda": "NVDA",                                                 # valuation target
}

# ── fundamentals: SEC EDGAR XBRL (official, free, no key) ───────────────────
CIK = "0001045810"          # NVIDIA
SEC_UA = "indra-os-profile-bot/1.0"


def _latest(g, tags, instant=False, n=1):
    """Latest 10-K value(s) across candidate us-gaap tags.
    Flows need a ~1-year duration; stocks are point-in-time. Returns [(end, val), ...] newest first."""
    best = {}
    for tag in tags:
        for v in next(iter(g.get(tag, {}).get("units", {}).values()), []):
            if v.get("form") != "10-K" or ("start" in v) == instant:
                continue
            if not instant:
                days = (datetime.date.fromisoformat(v["end"]) - datetime.date.fromisoformat(v["start"])).days
                if not 350 <= days <= 380:
                    continue
            k = v["end"]
            if k not in best or v.get("filed", "") > best[k][0]:
                best[k] = (v.get("filed", ""), v["val"])
    ends = sorted(best, reverse=True)[:n]
    return [(e, best[e][1]) for e in ends]


def fundamentals():
    """Latest-FY statements for CIK, cached to tools/fundamentals.json."""
    import urllib.request
    p = os.path.join(HERE, "fundamentals.json")
    try:
        req = urllib.request.Request(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{CIK}.json",
                                     headers={"User-Agent": SEC_UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            facts = json.load(r)["facts"]
        g = facts["us-gaap"]
        one = lambda tags, inst=False: _latest(g, tags, inst)[0][1]
        rev = _latest(g, ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"], n=2)
        f = dict(
            fy_end=rev[0][0], rev=rev[0][1], rev_prev=rev[1][1],
            cogs=one(["CostOfRevenue"]), gp=one(["GrossProfit"]), opex=one(["OperatingExpenses"]),
            opinc=one(["OperatingIncomeLoss"]), tax=one(["IncomeTaxExpenseBenefit"]), ni=one(["NetIncomeLoss"]),
            assets=one(["Assets"], True), liab=one(["Liabilities"], True), equity=one(["StockholdersEquity"], True),
            cfo=one(["NetCashProvidedByUsedInOperatingActivities"]),
            capex=one(["PaymentsToAcquireProductiveAssets", "PaymentsToAcquirePropertyPlantAndEquipment"]),
            cash=one(["CashAndCashEquivalentsAtCarryingValue"], True)
                 + next(iter(_latest(g, ["MarketableSecuritiesCurrent",
                                         "AvailableForSaleSecuritiesDebtSecuritiesCurrent"], True)), (0, 0))[1],
            debt=one(["LongTermDebt", "LongTermDebtNoncurrent"], True),
            shares=facts["dei"]["EntityCommonStockSharesOutstanding"]["units"]["shares"][-1]["val"],
        )
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(f, fh, indent=1)
        return f
    except Exception as e:
        print(f"fundamentals: SEC fetch failed ({e}) — using cache")
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)


def dcf_ev(fcf0, g, w, gT, n=10):
    """Two-stage DCF: n years at g, then Gordon terminal at gT. Returns enterprise value."""
    pv, f = 0.0, fcf0
    for t in range(1, n + 1):
        f *= 1 + g
        pv += f / (1 + w) ** t
    return pv + f * (1 + gT) / (w - gT) / (1 + w) ** n


def valuation(f, m, erp=0.05, gT=0.03):
    """CAPM → WACC → reverse DCF: the 10y FCF growth the current price implies."""
    px = dict(zip(m["nvda"]["d"], m["nvda"]["c"]))
    sx = dict(zip(m["spx"]["d"], m["spx"]["c"]))
    days = [d for d in m["nvda"]["d"] if d in sx]
    ra = [math.log(px[b] / px[a]) for a, b in zip(days, days[1:])]
    rb = [math.log(sx[b] / sx[a]) for a, b in zip(days, days[1:])]
    beta = st.covariance(ra, rb) / st.variance(rb)
    rf = m["y10"]["c"][-1] / 100
    price = m["nvda"]["c"][-1]
    E, D = price * f["shares"], f["debt"]
    t = f["tax"] / (f["ni"] + f["tax"])
    ke, kd = rf + beta * erp, rf + 0.01
    w = E / (E + D) * ke + D / (E + D) * kd * (1 - t)
    fcf0 = f["cfo"] - f["capex"]
    net_cash = f["cash"] - D
    lo, hi = -0.5, 1.5                                   # bisection on equity(g) = market cap
    for _ in range(80):
        g = (lo + hi) / 2
        lo, hi = (g, hi) if dcf_ev(fcf0, g, w, gT) + net_cash < E else (lo, g)
    per_share = lambda ww, gg: ((dcf_ev(fcf0, g, ww, gg) + net_cash) / f["shares"]
                                if ww - gg > 0.01 else None)
    grid = [[per_share(w + dw, gg) for gg in (0.02, 0.03, 0.04)] for dw in (-0.01, 0, 0.01)]
    return dict(beta=beta, rf=rf, ke=ke, w=w, dv=D / (D + E), fcf0=fcf0, g=g, price=price, mcap=E,
                chg=price / m["nvda"]["c"][-2] - 1, erp=erp, gT=gT, grid=grid, tax=t)


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


def money(v):
    a = abs(v)
    s = f"${a / 1e12:.2f}T" if a >= 1e12 else f"${a / 1e9:,.1f}B" if a >= 1e9 else f"${a / 1e6:,.0f}M"
    return ("−" if v < 0 else "") + s


def pane_fin(x0, y0, w, f):
    """Accounting: income-statement waterfall, A = L + E check, cash conversion."""
    O = "overlay"
    out = [pane_title(x0 + 14, y0 + 20, "5:fin", w - 28),
           T(x0 + 14, y0 + 42, [("NVDA ", "mauve"), (f"FY{f['fy_end'][:4]} · 10-K · income statement · $B", O)])]
    other = f["ni"] + f["tax"] - f["opinc"]
    items = [("revenue", f["rev"], 1, "blue"), ("cogs", -f["cogs"], 0, None), ("gross", f["gp"], 1, "sapphire"),
             ("opex", -f["opex"], 0, None), ("op inc", f["opinc"], 1, "teal"), ("other", other, 0, None),
             ("tax", -f["tax"], 0, None), ("net", f["ni"], 1, "green")]
    base, top = y0 + 150, y0 + 66
    Y = lambda v: base - v / f["rev"] * (base - top)
    slot = (w - 28) / len(items)
    level, prev_x = 0.0, None
    for i, (lab, v, total, col) in enumerate(items):
        x = x0 + 14 + i * slot + slot * 0.14
        bw = slot * 0.72
        a, b = (0, v) if total else (level, level + v)
        level = v if total else level + v
        cc = C[col] if total else C["green" if v >= 0 else "red"]
        out.append(f'<rect x="{x:.1f}" y="{Y(max(a, b)):.1f}" width="{bw:.1f}" height="{max(abs(Y(a) - Y(b)), 1.5):.1f}" '
                   f'rx="2" fill="{cc}" fill-opacity="{0.9 if total else 0.75}"/>')
        if prev_x is not None:     # dashed connector at the running level
            out.append(f'<line x1="{prev_x:.1f}" y1="{Y(level if total else a):.1f}" x2="{x:.1f}" '
                       f'y2="{Y(level if total else a):.1f}" stroke="{C["overlay"]}" stroke-dasharray="2 2"/>')
        prev_x = x + bw
        lbl = f"{money(v)[:-1] if total else ('+' if v >= 0 else '−') + f'{abs(v) / 1e9:.0f}'}"
        out.append(T(x + bw / 2, Y(max(a, b)) - 5, [(lbl, "text" if total else "subtext")], 10.5, "middle")
                   + T(x + bw / 2, base + 14, [(lab, O)], 10.5, "middle"))
    pc = lambda v: f"{v / f['rev'] * 100:.1f}%"
    gap = f["assets"] - f["liab"] - f["equity"]
    ok = abs(gap) / f["assets"] < 0.005
    fcf = f["cfo"] - f["capex"]
    out += [
        T(x0 + 14, y0 + 186, [("margins ", O), ("gross ", "subtext"), (pc(f["gp"]), "text"), ("  op ", "subtext"),
                              (pc(f["opinc"]), "text"), ("  net ", "subtext"), (pc(f["ni"]), "text"),
                              ("  rev ", "subtext"), (f"{(f['rev'] / f['rev_prev'] - 1) * 100:+.0f}% y/y", "green")], 12.5),
        T(x0 + 14, y0 + 205, [("balance ", O), ("A ", "subtext"), (money(f["assets"]), "text"), (" = L ", "subtext"),
                              (money(f["liab"]), "text"), (" + E ", "subtext"), (money(f["equity"]) + "  ", "text"),
                              ("✓ balances" if ok else f"Δ {money(gap)}", "green" if ok else "yellow")], 12.5),
        T(x0 + 14, y0 + 224, [("cash    ", O), ("CFO ", "subtext"), (money(f["cfo"]), "text"), (" − capex ", "subtext"),
                              (money(f["capex"]), "text"), (" = FCF ", "subtext"), (money(fcf), "teal"),
                              (f"  {fcf / f['ni'] * 100:.0f}% of NI", O)], 12.5),
    ]
    return "".join(out)


def pane_val(x0, y0, w, v):
    """Corporate finance: CAPM → WACC → reverse DCF, plus a WACC × gT sensitivity grid."""
    O = "overlay"
    a, col = arrow(v["chg"])
    out = [pane_title(x0 + 14, y0 + 20, "6:val", w - 28),
           T(x0 + 14, y0 + 42, [("NVDA ", "mauve"), (f"${v['price']:,.2f} ", "text"), (a, col),
                                ("  mcap ", "subtext"), (money(v["mcap"]), "text")])]
    p = lambda x: f"{x * 100:.2f}%"
    rows = [
        [("rf    ", "subtext"), (p(v["rf"]) + "  ", "text"), ("US10Y · live", O)],
        [("β     ", "subtext"), (f"{v['beta']:.2f}   ", "yellow"), ("vs S&P · 6m daily", O)],
        [("Ke    ", "subtext"), (p(v["ke"]) + "  ", "text"), (f"rf + β·{v['erp'] * 100:.0f}% ERP", O)],
        [("WACC  ", "subtext"), (p(v["w"]) + "  ", "mauve"), (f"D/V {v['dv'] * 100:.1f}%", O)],
        [("FCF₀  ", "subtext"), (money(v["fcf0"]) + "  ", "teal"), (f"gT {v['gT'] * 100:.0f}%", O)],
    ]
    out += [T(x0 + 14, y0 + 66 + i * LH, r, 12.5) for i, r in enumerate(rows)]

    gx, gy, cw_, ch = x0 + w - 14 - 44 - 3 * 46, y0 + 58, 46, 22
    out.append(T(gx, gy, [("value/share", "mauve"), (" · WACC×gT", O)], 11))
    for j, gg in enumerate(("2%", "3%", "4%")):
        out.append(T(gx + 44 + j * cw_ + cw_ / 2, gy + 18, [(gg, O)], 10.5, "middle"))
    for i, dw in enumerate((-0.01, 0, 0.01)):
        out.append(T(gx, gy + 38 + i * ch, [(f"{(v['w'] + dw) * 100:.1f}%", "mauve" if dw == 0 else O)], 10.5))
        for j in range(3):
            val = v["grid"][i][j]
            if val is None:
                continue
            up = val >= v["price"]
            out.append(f'<rect x="{gx + 44 + j * cw_ + 1:.1f}" y="{gy + 24 + i * ch:.1f}" width="{cw_ - 2}" height="{ch - 2}" '
                       f'rx="3" fill="{C["green" if up else "red"]}" '
                       f'fill-opacity="{min(0.85, 0.15 + abs(val / v["price"] - 1) * 1.5):.2f}"/>'
                       + T(gx + 44 + j * cw_ + cw_ / 2, gy + 38 + i * ch, [(f"${val:,.0f}", "text")], 10.5, "middle"))
    out += [
        T(x0 + 14, y0 + 172, [("reverse DCF ", O), ("market prices in ", "subtext"),
                              (f"{v['g'] * 100:.1f}%", "yellow"), (" FCF CAGR for 10y", "subtext")], 13.5, weight=600),
        T(x0 + 14, y0 + 193, [("= FCF ", O), (f"×{(1 + v['g']) ** 10:.1f}", "text"),
                              (" by year 10, then gT forever · centre cell ≈ price", O)], 11.5),
        T(x0 + 14, y0 + 222, [("# 2-stage DCF · ERP 5% · Kd = rf+1% · FCF = CFO − capex · not advice", O)], 10.5),
    ]
    return "".join(out)


# ── compose ─────────────────────────────────────────────────────────────────
def operator(m, f):
    W, H = 984, 830
    TOP, MID, MID2, BOT = 40, 307, 548, 792   # row starts / end
    c1, c2, b1, f1 = 328, 656, 400, 492       # column splits: top row, middle row, bottom row
    O, S1 = C["overlay"], C["surface1"]
    seps = (f'<line x1="{c1}" y1="{TOP}" x2="{c1}" y2="{MID - 4}" stroke="{O}"/>'
            f'<line x1="{c2}" y1="{TOP}" x2="{c2}" y2="{MID - 4}" stroke="{O}"/>'
            f'<line x1="10" y1="{MID}" x2="{W - 10}" y2="{MID}" stroke="{S1}"/>'
            f'<line x1="{b1}" y1="{MID + 4}" x2="{b1}" y2="{MID2 - 4}" stroke="{O}"/>'
            f'<line x1="10" y1="{MID2}" x2="{W - 10}" y2="{MID2}" stroke="{S1}"/>'
            f'<line x1="{f1}" y1="{MID2 + 4}" x2="{f1}" y2="{BOT}" stroke="{O}"/>')
    sb = H - 30
    status = (f'<rect x="8" y="{sb}" width="{W - 16}" height="24" rx="7" fill="{C["green"]}"/>'
              f'<rect x="8" y="{sb}" width="78" height="24" rx="7" fill="{C["mauve"]}"/>'
              + T(22, sb + 17, [("indra", "crust")], PS, weight=700)
              + T(100, sb + 17, [("0:ai  1:quant  2:econ  3:gtm  4:biz  5:fin  6:val", "crust")])
              + T(W - 22, sb + 17, [(f"data {m['asof']}", "crust")], 12, "end"))
    win = (f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" fill="{C["base"]}" '
           f'fill-opacity="0.80" stroke="{S1}"/>'
           + titlebar(W, "abhinav@indra-os — tmux: operator")
           + seps
           + pane_ai(0, TOP, c1) + pane_quant(c1, TOP, c2 - c1, m) + pane_econ(c2, TOP, W - c2, m)
           + pane_gtm(0, MID, b1) + pane_biz(b1, MID, W - b1)
           + pane_fin(0, MID2, f1, f) + pane_val(f1, MID2, W - f1, valuation(f, m))
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
    svg = operator(markets(), fundamentals())
    import xml.dom.minidom
    xml.dom.minidom.parseString(svg)            # ponytail: one self-check — well-formed XML
    p = os.path.join(os.path.dirname(HERE), "assets", "operator.svg")
    with open(p, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {p}  ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
