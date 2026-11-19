#!/usr/bin/env python3
"""Generate Catppuccin Mocha 'terminal window' SVGs for the GitHub profile README.

Each panel is a self-contained SVG (own bg + window chrome + colored monospace
text) so it renders identically in GitHub light/dark via <img>. Animations use
CSS keyframes inside the SVG, which GitHub's image proxy plays (same trick as
readme-typing-svg / the contribution snake).

Run:  py -3.10 tools/gen.py      ->  writes assets/*.svg
"""
import os, html, json


def _recent_commits():
    """Read tools/recent_commits.json (written by the live-desktop Action).
    Returns a list of {sha,msg} dicts, or None to fall back to sample data."""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recent_commits.json")
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        return [c for c in data if c.get("msg")][:5] or None
    except Exception:
        return None

# ── Catppuccin Mocha palette ───────────────────────────────────────────────
C = dict(
    base="#1e1e2e", mantle="#181825", crust="#11111b", surface0="#313244",
    surface1="#45475a", overlay="#6c7086", text="#cdd6f4", subtext="#a6adc8",
    rosewater="#f5e0dc", flamingo="#f2cdcd", pink="#f5c2e7", mauve="#cba6f7",
    red="#f38ba8", maroon="#eba0ac", peach="#fab387", yellow="#f9e2af",
    green="#a6e3a1", teal="#94e2d5", sky="#89dceb", sapphire="#74c7ec",
    blue="#89b4fa", lavender="#b4befe",
)

# ── metrics ────────────────────────────────────────────────────────────────
FS = 15.5           # font size
CW = 9.3            # monospace char advance
LH = 25             # line height
PADX = 22
PADY = 18
BAR = 34            # title-bar height
FONT = "'JetBrains Mono','JetBrainsMono Nerd Font','Cascadia Code','Fira Code',ui-monospace,'DejaVu Sans Mono',monospace"


def esc(s):
    return html.escape(s, quote=True)


def sp(text, color="text"):
    """A colored span within a line."""
    return (text, C.get(color, color))


def _line_svg(spans, y):
    parts = []
    for text, color in spans:
        parts.append(f'<tspan fill="{color}">{esc(text)}</tspan>')
    return f'<text x="{PADX}" y="{y}" xml:space="preserve">{"".join(parts)}</text>'


def _wallpaper(W2, H2):
    """Catppuccin wallpaper canvas: base gradient + soft colour glows."""
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
        + f'<rect x="0.5" y="0.5" width="{W2-1}" height="{H2-1}" rx="18" fill="url(#wp)" stroke="{C["surface0"]}"/>'
        + "".join(f'<rect x="1" y="1" width="{W2-2}" height="{H2-2}" rx="18" fill="url(#b{i})"/>' for i in (1, 2, 3, 4))
    )


def _titlebar(W, title, frosted=False):
    """Linux tiling-WM style title bar: app dot + left-aligned title, no mac buttons."""
    op = ' fill-opacity="0.66"' if frosted else ''
    return (
        f'<path d="M0.5 12.5 A12 12 0 0 1 12.5 0.5 H{W-12.5} A12 12 0 0 1 {W-0.5} 12.5 V{BAR} H0.5 Z" fill="{C["mantle"]}"{op}/>'
        f'<line x1="0.5" y1="{BAR}" x2="{W-0.5}" y2="{BAR}" stroke="{C["surface0"]}"/>'
        f'<rect x="16" y="{BAR/2-5:.0f}" width="10" height="10" rx="3" fill="{C["mauve"]}"/>'
        f'<text x="34" y="{BAR/2+4:.0f}" xml:space="preserve" class="ttl">{esc(title)}</text>'
    )


def terminal(title, lines, *, animate=False, min_cols=0, cursor=True,
             accent="mauve", pre_svg="", frosted=False):
    """lines: list of list-of-spans. Returns SVG string.
    pre_svg: raw SVG drawn in the body area behind the text (e.g. a vector logo).
    frosted: float the (translucent) window on a wallpaper canvas."""
    cols = max([sum(len(t) for t, _ in ln) for ln in lines] + [len(title) + 6, min_cols])
    W = int(cols * CW + PADX * 2)
    H = int(BAR + PADY * 2 + len(lines) * LH)
    ac = C[accent]

    css = f"""
    text {{ font-family:{FONT}; font-size:{FS}px; font-variant-ligatures:none; white-space:pre; }}
    .ttl {{ font-size:13px; fill:{C['subtext']}; }}
    """
    if animate:
        # base opacity:1 so panel is visible even if a viewer strips CSS anim;
        # `both` fill shows the 0% (hidden) state during the stagger delay.
        css += ".row{opacity:1;animation:rev .45s ease both;}"
        css += "@keyframes rev{from{opacity:0;}to{opacity:1;}}"
        css += ".cur{animation:bl 1s steps(1) infinite;}@keyframes bl{50%{opacity:0;}}"
    else:
        css += ".cur{animation:bl 1.1s steps(1) infinite;}@keyframes bl{50%{opacity:0;}}"

    body = []
    y0 = BAR + PADY + FS
    for i, ln in enumerate(lines):
        y = y0 + i * LH
        row = _line_svg(ln, y)
        if animate:
            delay = 0.15 + i * 0.16
            row = f'<g class="row" style="animation-delay:{delay:.2f}s">{row}</g>'
        body.append(row)

    # blinking cursor on the last line
    cur = ""
    if cursor:
        last = lines[-1] if lines else []
        lastlen = sum(len(t) for t, _ in last)
        cx = PADX + lastlen * CW + 2
        cy = y0 + (len(lines) - 1) * LH - FS + 4
        delay = f'style="animation-delay:{0.15 + len(lines) * 0.16:.2f}s"' if animate else ""
        cur = (f'<rect class="cur row" {delay} x="{cx:.0f}" y="{cy:.0f}" '
               f'width="{CW:.0f}" height="{FS:.0f}" rx="1" fill="{ac}"/>')

    win_op = ' fill-opacity="0.80"' if frosted else ''
    edge = C['surface1'] if frosted else C['surface0']
    window = (
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="{C["base"]}"{win_op} stroke="{edge}"/>'
        + _titlebar(W, title, frosted) + pre_svg + "".join(body) + cur
    )
    if frosted:
        M = 28
        W2, H2 = W + 2 * M, H + 2 * M
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W2}" height="{H2}" viewBox="0 0 {W2} {H2}" role="img">'
                f'<style>{css}</style>{_wallpaper(W2, H2)}'
                f'<g transform="translate({M},{M})">{window}</g></svg>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img">'
            f'<style>{css}</style>{window}</svg>')


def tmux_session(live=None):
    """Everything in ONE terminal window, split into tmux panes + status bar."""
    NCOLS = 94
    VSPLIT = 52                                   # column of the vertical pane split
    top = BAR + 6                                 # y of the content area
    W = int(PADX * 2 + NCOLS * CW)
    STATUS = 30

    def colx(c):  return PADX + c * CW
    def rowy(r):  return top + FS + r * LH
    def txt(spans, c, r):
        x = colx(c)
        parts = "".join(f'<tspan fill="{col}">{esc(t)}</tspan>' for t, col in spans)
        return f'<text x="{x:.1f}" y="{rowy(r):.1f}" xml:space="preserve">{parts}</text>'

    def title(name, dashes):
        return [sp(name, "mauve"), sp(" " + "─" * dashes, "overlay")]

    # ── pane content ──────────────────────────────────────────────────────
    ff = [
        title("0:fastfetch", 20),
        [sp("abhinav", "green"), sp("@", "text"), sp("indra-os", "mauve")],
        [sp("─" * 28, "surface1")],
        [sp("OS    ", "mauve"), sp("arch-based x86_64", "text")],
        [sp("WM    ", "mauve"), sp("Hyprland · Waybar", "text")],
        [sp("SHELL ", "mauve"), sp("zsh + powerlevel10k", "text")],
        [sp("ROLE  ", "mauve"), sp("AI·Biz·Quant·Econ·GTM", "text")],
        [sp("THEME ", "mauve"), sp("Catppuccin Mauve", "text")],
        [sp("─" * 28, "surface1")],
        [sp("CPU ", "blue"), sp("Detected  ", "text"), sp("MEM ", "blue"), sp("11/32G", "text")],
        [sp("PY ", "blue"), sp("3.10  ", "text"), sp("NODE ", "blue"), sp("20  ", "text"), sp("DK ", "blue"), sp("27", "text")],
        [sp("AI  ", "blue"), sp("◆", "mauve"), sp("claude ", "text"), sp("◆", "mauve"), sp("codex ", "text"), sp("◆", "mauve"), sp("gemini", "text")],
    ]
    boot = [
        title("1:boot", 24),
        [sp("[0.128] ", "overlay"), sp("kernel 6.11 ", "text"), sp("···· ", "surface1"), sp("ok", "green")],
        [sp("[0.774] ", "overlay"), sp("Hyprland+bar ", "mauve"), sp("·· ", "surface1"), sp("ok", "green")],
        [sp("[1.144] ", "overlay"), sp("agents c·c·g ", "text"), sp("· ", "surface1"), sp("ok", "green")],
        [sp("[1.640] ", "overlay"), sp("graph mount ", "text"), sp("··· ", "surface1"), sp("ok", "green")],
        [sp("[2.560] ", "overlay"), sp("bridge S↔EVM ", "peach"), sp("· ", "surface1"), sp("ok", "green")],
    ]
    rc = _recent_commits()
    if rc:                                              # live: real recent commits
        git = [title("2:git", 25)]
        for c in rc:
            sha = (c.get("sha") or "").strip()[:7]
            msg = " ".join((c.get("msg") or "").split())
            msg = (msg[:26] + "…") if len(msg) > 27 else msg
            git.append([sp("* ", "yellow"), sp(f"{sha} ", "peach"), sp(msg, "text")])
    else:                                               # fallback sample
        git = [
            title("2:git", 25),
            [sp("* ", "yellow"), sp("a1f4c22 ", "peach"), sp("route → gemini", "text")],
            [sp("* ", "yellow"), sp("7d90b1e ", "peach"), sp("meter acc 96.5%", "text")],
            [sp("* ", "yellow"), sp("3c1aa87 ", "peach"), sp("harden bridge", "text")],
            [sp("* ", "yellow"), sp("55e02fd ", "peach"), sp("merge intel", "text")],
            [sp("* ", "yellow"), sp("e9b7740 ", "peach"), sp("NSE serverless", "text")],
        ]
    def svc(u, d):
        return [sp("● ", "green"), sp(f"{u:<21}", "mauve"), sp("loaded ", "overlay"),
                sp("active ", "green"), sp("running  ", "green"), sp(d, "subtext")]
    sysc = [
        title("3:systemctl status --all", 60),
        svc("orchestrator.service", "indra-os · agent mission control"),
        svc("vedicmind.service", "ved-project · FSA meter compiler + RAG"),
        svc("intel.service", "xint · OSINT identity graph"),
        svc("telegram.service", "telint · Telegram collection"),
        svc("tripcode.service", "yotsuba-intel · 4chan correlation"),
        svc("bridge.service", "Stellar ↔ EVM intent settlement"),
        svc("market.service", "stock-intelligence · NSE council"),
        svc("tray.service", "gptray · desktop LLM tray daemon"),
        svc("cron.service", "github-ai-updates · repo poller"),
        [sp("  9 loaded", "text"), sp(" · ", "overlay"), sp("9 active", "green"), sp(" · ", "overlay"), sp("0 failed", "green")],
    ]

    # ── place content ─────────────────────────────────────────────────────
    # fastfetch: title at col 1, info at col 19 to clear the diamond
    body = [txt(ff[0], 1, 0)] + [txt(ff[i], 19, i) for i in range(1, len(ff))]
    for i, ln in enumerate(boot):        # boot: right-top, rows 0..5
        body.append(txt(ln, VSPLIT + 2, i))
    for i, ln in enumerate(git):         # git: right-bottom, rows 6..11
        body.append(txt(ln, VSPLIT + 2, 6 + i))
    for i, ln in enumerate(sysc):        # systemctl: full width, rows 13..24
        body.append(txt(ln, 1, 13 + i))

    # ── indra-os diamond emblem (vector: renders everywhere, no font needed) ──
    cx, cy, rx, ry, g = colx(9), rowy(6) - 4, 64, 118, 11
    dia = lambda sx, sy: f"{cx:.0f},{cy-sy:.0f} {cx+sx:.0f},{cy:.0f} {cx:.0f},{cy+sy:.0f} {cx-sx:.0f},{cy:.0f}"
    diamond = (
        f'<polygon points="{dia(rx, ry)}" fill="none" stroke="{C["mauve"]}" stroke-width="9" stroke-linejoin="round"/>'
        f'<polygon points="{dia(rx*0.42, ry*0.42)}" fill="{C["mauve"]}" fill-opacity="0.18"/>'
        f'<rect x="{cx-g:.0f}" y="{cy-g:.0f}" width="{g*2}" height="{g*2}" rx="2" '
        f'fill="{C["teal"]}" transform="rotate(45 {cx:.0f} {cy:.0f})"/>')

    # ── pane split lines ──────────────────────────────────────────────────
    y_vtop = top + 2
    y_hbar = rowy(11) + 8                  # between top section and systemctl
    y_rgit = rowy(5) + 8                   # between boot and git
    x_vs = colx(VSPLIT) - CW / 2
    O = C['overlay']
    lines = (
        f'<line x1="{x_vs:.0f}" y1="{y_vtop:.0f}" x2="{x_vs:.0f}" y2="{y_hbar:.0f}" stroke="{O}"/>'
        f'<line x1="{x_vs:.0f}" y1="{y_rgit:.0f}" x2="{W-10}" y2="{y_rgit:.0f}" stroke="{O}"/>'
        f'<line x1="10" y1="{y_hbar:.0f}" x2="{W-10}" y2="{y_hbar:.0f}" stroke="{C["surface1"]}"/>'
    )

    # ── tmux status bar ───────────────────────────────────────────────────
    H = int(y_hbar + 13 * LH + 14 + STATUS)
    sb_y = H - STATUS - 6
    windows = "0:fastfetch  1:boot  2:git  3:systemctl"
    clock = "indra-os  14:22"
    sbar = (
        f'<rect x="8" y="{sb_y}" width="{W-16}" height="{STATUS-4}" rx="7" fill="{C["green"]}"/>'
        f'<rect x="8" y="{sb_y}" width="88" height="{STATUS-4}" rx="7" fill="{C["mauve"]}"/>'
        f'<text x="22" y="{sb_y+20}" xml:space="preserve" fill="{C["crust"]}" font-weight="700"> indra</text>'
        f'<text x="120" y="{sb_y+20}" xml:space="preserve" fill="{C["crust"]}">{esc(windows)}</text>'
        f'<text x="{W-24}" y="{sb_y+20}" xml:space="preserve" text-anchor="end" fill="{C["crust"]}">{esc(clock)}</text>'
    )

    # ── compose the desktop: wallpaper + YASB bar + frosted floating terminal ──
    M, GAP, BARH = 28, 18, 56
    W2 = W + 2 * M
    H2 = int(M + BARH + GAP + H + M)
    ty = M + BARH + GAP
    wp = _wallpaper(W2, H2)
    # frosted terminal body: translucent so the wallpaper bleeds through
    win = (
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="{C["base"]}" fill-opacity="0.80" stroke="{C["surface1"]}"/>'
        + _titlebar(W, "abhinav@indra-os — tmux", frosted=True)
        + f'{diamond}{lines}{"".join(body)}{sbar}'
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W2}" height="{H2}" viewBox="0 0 {W2} {H2}" role="img">
<style>text{{font-family:{FONT};font-size:{FS}px;font-variant-ligatures:none;white-space:pre;}} .ttl{{font-size:13px;fill:{C['subtext']};}}</style>
{wp}
<g transform="translate({M},{M})">{_yasb_inner(W, live=live)}</g>
<g transform="translate({M},{ty})">{win}</g>
</svg>'''


def _yasb_inner(W, H=56, live=None):
    """YASB status-bar content (bg + pills) drawn at 0,0 for the given width."""
    CR, ST, TX = C['crust'], C['subtext'], C['text']
    S0, MA = C['surface0'], C['mauve']
    y, ph = 12, 32                                    # pill y + height
    parts = []

    def pill(x, txt, fg, bg, pad=12):
        w = len(txt) * CW + pad * 2
        parts.append(
            f'<rect x="{x:.0f}" y="{y}" width="{w:.0f}" height="{ph}" rx="9" fill="{bg}"/>'
            f'<text x="{x+pad:.0f}" y="{y+22}" xml:space="preserve" fill="{fg}" font-weight="600">{esc(txt)}</text>')
        return x + w

    # left cluster: identity + workspaces
    x = 14
    x = pill(x, "◆ indra-os", CR, MA) + 10
    for ws in ("1", "2", "3"):
        active = ws == "2"
        w = CW + 20
        parts.append(
            f'<rect x="{x:.0f}" y="{y}" width="{w:.0f}" height="{ph}" rx="8" fill="{MA if active else S0}"/>'
            f'<text x="{x+w/2:.0f}" y="{y+22}" text-anchor="middle" fill="{CR if active else ST}">{ws}</text>')
        x += w + 6

    # right cluster: widgets, laid out right-to-left
    widgets = [live or ("CPU 34%", TX, S0), ("MEM 11.2G", TX, S0), ("● 3 agents", CR, C['green']),
               ("claude-opus", CR, C['blue']), ("main", CR, C['peach']), ("14:22", CR, C['lavender'])]
    rx = W - 14
    for txt, fg, bg in reversed(widgets):
        w = len(txt) * CW + 24
        rx -= w
        parts.append(
            f'<rect x="{rx:.0f}" y="{y}" width="{w:.0f}" height="{ph}" rx="9" fill="{bg}"/>'
            f'<text x="{rx+12:.0f}" y="{y+22}" xml:space="preserve" fill="{fg}" font-weight="600">{esc(txt)}</text>')
        rx -= 7

    bg = f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" fill="{C["mantle"]}" fill-opacity="0.82" stroke="{C["surface0"]}"/>'
    return bg + "".join(parts)


# ── live markets: Yahoo chart API, cached to tools/markets.json ──────────────
# (key, yahoo symbol, tape label, number format)
TICKERS = [
    ("nifty", "^NSEI", "NIFTY", "{:,.1f}"),
    ("spx", "^GSPC", "S&P500", "{:,.1f}"),
    ("btc", "BTC-USD", "BTC", "{:,.0f}"),
    ("inr", "INR=X", "USD/INR", "{:.2f}"),
    ("gold", "GC=F", "GOLD", "{:,.1f}"),
    ("tnx", "^TNX", "US10Y", "{:.2f}%"),
]
CORR = [("nifty", "NIF"), ("spx", "SPX"), ("btc", "BTC"), ("gold", "GLD"), ("inr", "INR")]


def _fetch(sym):
    """6 months of daily OHLC for one symbol, keyed by exchange-local date."""
    import urllib.request, urllib.parse, time
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
    if len(days) < 61:
        raise ValueError(f"only {len(days)} bars")
    return {"d": days, **{k: [round(rows[d][i], 4) for d in days] for i, k in enumerate("ohlc")}}


def markets():
    """Fetch every ticker; on any per-symbol failure fall back to the cached copy.
    Returns the merged dict, or None if some ticker has never been fetched."""
    import time
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "markets.json")
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    fresh = False
    for key, sym, *_ in TICKERS:
        try:
            data[key] = _fetch(sym)
            fresh = True
        except Exception as e:
            print(f"markets: {sym} fetch failed ({e}) — using cache")
    if fresh:
        data["asof"] = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, separators=(",", ":"))
    return data if all(k in data for k, *_ in TICKERS) else None


def signals(c):
    """Quant read-out from a close series (needs >= 61 closes)."""
    import math, statistics as st
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


def correlations(m, n=60):
    """n-day log-return correlation matrix over dates all CORR assets share."""
    import math, statistics as st
    common = sorted(set.intersection(*(set(m[k]["d"]) for k, _ in CORR)))[-(n + 1):]
    rets = []
    for k, _ in CORR:
        px = dict(zip(m[k]["d"], m[k]["c"]))
        s = [px[d] for d in common]
        rets.append([math.log(b / a) for a, b in zip(s, s[1:])])
    return [[st.correlation(a, b) for b in rets] for a in rets], len(common) - 1


def markets_panel(m):
    """Live quant desk: ticker tape, NIFTY candles + SMA20, signals, corr heatmap."""
    W, H = int(96 * CW + 2 * PADX), 512
    nf = m["nifty"]
    sig = signals(nf["c"])
    up_c, dn_c = C["green"], C["red"]

    def row(x, y, spans, size=None, anchor=None):
        st = f' style="font-size:{size}px"' if size else ""
        an = f' text-anchor="{anchor}"' if anchor else ""
        inner = "".join(f'<tspan fill="{C.get(col, col)}">{esc(s)}</tspan>' for s, col in spans)
        return f'<text x="{x:.1f}" y="{y:.1f}"{an}{st} xml:space="preserve">{inner}</text>'

    def arrow(v):
        return ("▲" if v >= 0 else "▼") + f"{abs(v) * 100:.2f}%", ("green" if v >= 0 else "red")

    # ── ticker tape (two copies scrolled left forever) ─────────────────────
    TFS = 14
    tcw = CW * TFS / FS
    spans, n = [], 0
    for key, _, label, fmt in TICKERS:
        c = m[key]["c"]
        a, col = arrow(c[-1] / c[-2] - 1)
        for s, k in ((label + " ", "subtext"), (fmt.format(c[-1]) + " ", "text"), (a, col), ("   ◆   ", "surface1")):
            spans.append((s, k))
            n += len(s)
    tw = n * tcw
    tape = (f'<clipPath id="tc"><rect x="1" y="40" width="{W - 2}" height="32"/></clipPath>'
            f'<rect x="1" y="40" width="{W - 2}" height="32" fill="{C["crust"]}" fill-opacity="0.55"/>'
            f'<g clip-path="url(#tc)"><g class="tape">'
            + row(14, 61, spans, TFS) + row(14 + tw, 61, spans, TFS) + '</g></g>')

    # ── header ─────────────────────────────────────────────────────────────
    live = f"LIVE  as of {m.get('asof', '?')}"
    head = (row(PADX, 102, [("❯ ", "green"), ("./quant-desk ", "text"), ("--live", "overlay")])
            + f'<circle cx="{W - PADX - len(live) * CW * 12.5 / FS - 10:.0f}" cy="98" r="4.5" fill="{up_c}" class="pulse"/>'
            + row(W - PADX, 102, [(live[:6], "green"), (live[6:], "overlay")], 12.5, "end"))

    # ── NIFTY candlesticks + SMA20 ────────────────────────────────────────
    N = 60
    x0, x1, y0, y1 = PADX + 4, 520, 152, 432
    o, h, l, c, d = (nf[k][-N:] for k in "ohlcd")
    lo, hi = min(l), max(h)
    pad = (hi - lo) * 0.06
    lo, hi = lo - pad, hi + pad
    Y = lambda v: y1 - (v - lo) / (hi - lo) * (y1 - y0)
    step = (x1 - x0) / N
    X = lambda i: x0 + step * (i + 0.5)
    grid = ""
    for k in range(5):
        v = lo + (hi - lo) * k / 4
        grid += (f'<line x1="{x0}" y1="{Y(v):.1f}" x2="{x1}" y2="{Y(v):.1f}" stroke="{C["surface0"]}"/>'
                 + (row(x1 + 8, Y(v) + 4, [(f"{v:,.0f}", "overlay")], 11)
                    if abs(Y(v) - Y(c[-1])) > 16 else ""))   # don't collide with last-price pill
    candles = ""
    for i in range(N):
        col = up_c if c[i] >= o[i] else dn_c
        top, bot = Y(max(o[i], c[i])), Y(min(o[i], c[i]))
        candles += (f'<line x1="{X(i):.1f}" y1="{Y(h[i]):.1f}" x2="{X(i):.1f}" y2="{Y(l[i]):.1f}" stroke="{col}"/>'
                    f'<rect x="{X(i) - step * 0.32:.1f}" y="{top:.1f}" width="{step * 0.64:.1f}" '
                    f'height="{max(bot - top, 1.2):.1f}" fill="{col}"/>')
    allc = nf["c"]
    sma = [sum(allc[j - 19:j + 1]) / 20 for j in range(len(allc) - N, len(allc))]
    sma_path = "M" + " L".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(sma))
    yl = Y(c[-1])
    lcol = up_c if sig["chg"] >= 0 else dn_c
    chart = (
        row(x0, 130, [("NIFTY 50  ", "mauve"), ("1D · 60 sessions   ", "overlay"), ("━ SMA20", "lavender")], 13.5)
        + grid
        + f'<clipPath id="rv"><rect x="{x0 - 4}" y="{y0 - 12}" width="{x1 - x0 + 8}" height="{y1 - y0 + 24}">'
          f'<animate attributeName="width" from="0" to="{x1 - x0 + 8}" dur="2.4s" fill="freeze"/></rect></clipPath>'
        + f'<g clip-path="url(#rv)">{candles}'
          f'<path d="{sma_path}" fill="none" stroke="{C["lavender"]}" stroke-width="1.8"/></g>'
        + f'<line x1="{x0}" y1="{yl:.1f}" x2="{x1}" y2="{yl:.1f}" stroke="{lcol}" stroke-dasharray="3 3" stroke-opacity="0.8"/>'
        + f'<rect x="{x1 + 3}" y="{yl - 10:.1f}" width="62" height="20" rx="4" fill="{lcol}"/>'
        + row(x1 + 34, yl + 4.5, [(f"{c[-1]:,.0f}", "crust")], 11.5, "middle")
        + "".join(row(X(i), y1 + 22, [(_md(d[i]), "overlay")], 11, "middle") for i in (0, N // 2, N - 1)))

    # ── signals ───────────────────────────────────────────────────────────
    sx = 604
    a, acol = arrow(sig["chg"])
    pct = lambda v: f"{v * 100:+.2f}%"
    rows = [
        [("last     ", "subtext"), (f"{sig['last']:,.1f}  ", "text"), (a, acol)],
        [("mom 20d  ", "subtext"), (pct(sig["mom20"]), "green" if sig["mom20"] >= 0 else "red")],
        [("vol 20d  ", "subtext"), (f"{sig['vol20'] * 100:.1f}% ", "text"), ("ann.", "overlay")],
        [("sharpe   ", "subtext"), (f"{sig['sharpe']:+.2f} ", "yellow"), ("60d", "overlay")],
        [("max dd   ", "subtext"), (pct(sig["mdd"]) + " ", "red"), ("60d", "overlay")],
        [("z-score  ", "subtext"), (f"{sig['z']:+.2f}σ ", "teal"), ("vs SMA20", "overlay")],
        [("regime   ", "subtext"), (sig["regime"], "peach")],
    ]
    sigs = row(sx, 130, [("SIGNALS", "mauve"), (" · NIFTY", "overlay")], 13.5)
    sigs += "".join(row(sx, 160 + i * 23, r, 14) for i, r in enumerate(rows))

    # ── correlation heatmap ───────────────────────────────────────────────
    M_, nret = correlations(m)
    hx, hy, cwid, chei = sx + 40, 348, 48, 20
    heat = row(sx, 330, [("CORR", "mauve"), (f" · {nret}d log-returns", "overlay")], 13.5)
    for j, (_, lab) in enumerate(CORR):
        heat += row(hx + j * cwid + cwid / 2, hy - 6, [(lab, "overlay")], 11, "middle")
    for i, (_, lab) in enumerate(CORR):
        heat += row(sx, hy + i * chei + 14, [(lab, "overlay")], 11)
        for j in range(len(CORR)):
            v = M_[i][j]
            col = C["blue"] if v >= 0 else C["red"]
            heat += (f'<rect x="{hx + j * cwid + 1}" y="{hy + i * chei + 1}" width="{cwid - 2}" height="{chei - 2}" '
                     f'rx="3" fill="{col}" fill-opacity="{0.12 + 0.78 * abs(v):.2f}"/>'
                     + row(hx + j * cwid + cwid / 2, hy + i * chei + 14,
                           [(f"{v:+.2f}" if i != j else "1", "crust" if abs(v) > 0.55 else "text")], 10.5, "middle"))

    foot = (f'<line x1="14" y1="{H - 38}" x2="{W - 14}" y2="{H - 38}" stroke="{C["surface1"]}"/>'
            + row(PADX, H - 16, [("# src ", "overlay"), ("Yahoo Finance", "subtext"),
                                 (" · recomputed every 6h by GitHub Actions · stdlib-only python · not advice", "overlay")], 12.5))

    css = (f"text{{font-family:{FONT};font-size:{FS}px;font-variant-ligatures:none;white-space:pre;}}"
           f".ttl{{font-size:13px;fill:{C['subtext']};}}"
           f".tape{{animation:tp {tw / 38:.0f}s linear infinite}}@keyframes tp{{to{{transform:translateX(-{tw:.0f}px)}}}}"
           ".pulse{animation:pl 1.4s ease-in-out infinite}@keyframes pl{50%{opacity:.2}}")
    window = (f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" fill="{C["base"]}" '
              f'fill-opacity="0.80" stroke="{C["surface1"]}"/>'
              + _titlebar(W, "abhinav@indra-os : ~/quant-desk", frosted=True)
              + tape + head + chart + sigs + heat + foot)
    Mg = 28
    W2, H2 = W + 2 * Mg, H + 2 * Mg
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W2}" height="{H2}" viewBox="0 0 {W2} {H2}" role="img">'
            f'<style>{css}</style>{_wallpaper(W2, H2)}<g transform="translate({Mg},{Mg})">{window}</g></svg>')


def _md(iso):
    """'2026-11-18' -> 'Nov 18'."""
    import datetime
    return datetime.date.fromisoformat(iso).strftime("%b %d")


def stack_panel():
    """Five-discipline operator panel: Business · AI · Quant · Economics · GTM.
    Left: the stack as a terminal listing. Right: a radar of the profile shape
    (solid = now, dashed = trajectory). Shape only, no fabricated numbers."""
    # (name, color, focus, status) — order = clockwise around the radar from top
    D = [
        ("AI",        "mauve", "agent systems · RAG · LLMOps",    "active"),
        ("Business",  "blue",  "strategy · ops · unit economics", "active"),
        ("GTM",       "peach", "PLG · founder sales · SEO loops", "active"),
        ("Economics", "green", "incentives · markets · macro",    "active"),
        ("Quant",     "yellow", "stats · time-series · backtests", "ramping"),
    ]
    now  = [0.92, 0.84, 0.80, 0.74, 0.42]   # ponytail: self-assessed shape, edit freely
    goal = [0.92, 0.84, 0.80, 0.82, 0.88]   # dashed trajectory (quant + econ growing)

    def row(name, col, focus, status):
        tag = [sp("● ", "green"), sp("active", "subtext")] if status == "active" \
            else [sp("▲ ", "yellow"), sp("ramping", "yellow")]
        return [sp("◆ ", col), sp(f"{name:<11}", col), sp(f"{focus:<33}", "text")] + tag

    L = [
        [sp("❯ ", "green"), sp("./operator ", "text"), sp("--stack", "overlay")],
        [sp("─" * 56, "surface1")],
        *[row(*d) for d in D],
        [sp("─" * 56, "surface1")],
        [sp("loop  ", "overlay"), sp("understand", "green"), sp(" ▸ ", "overlay"), sp("model", "yellow"),
         sp(" ▸ ", "overlay"), sp("build", "mauve"), sp(" ▸ ", "overlay"), sp("sell", "peach"),
         sp(" ▸ ", "overlay"), sp("scale", "blue")],
        [sp(" ", "base")],
        [sp("─" * 94, "surface1")],
        [sp("# thesis: ", "overlay"),
         sp("markets are systems — model them, then build and sell into them", "teal")],
    ]

    # ── radar (pentagon) ──────────────────────────────────────────────────
    import math
    cx, cy, R = 728, 170, 98
    ang = [math.radians(-90 + 72 * i) for i in range(5)]
    pt = lambda i, r: (cx + R * r * math.cos(ang[i]), cy + R * r * math.sin(ang[i]))
    poly = lambda vals: " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(i, v) for i, v in enumerate(vals)))
    S1, OV = C["surface1"], C["overlay"]
    grid = "".join(f'<polygon points="{poly([k] * 5)}" fill="none" stroke="{S1}" stroke-width="1"/>'
                   for k in (0.33, 0.66, 1.0))
    spokes = "".join(f'<line x1="{cx}" y1="{cy}" x2="{pt(i, 1)[0]:.1f}" y2="{pt(i, 1)[1]:.1f}" stroke="{S1}"/>'
                     for i in range(5))
    shape = (f'<polygon points="{poly(goal)}" fill="none" stroke="{C["yellow"]}" stroke-width="1.6" '
             f'stroke-dasharray="5 4" class="traj"/>'
             f'<polygon points="{poly(now)}" fill="{C["mauve"]}" fill-opacity="0.22" '
             f'stroke="{C["mauve"]}" stroke-width="2.2" stroke-linejoin="round"/>')
    dots = "".join(f'<circle cx="{pt(i, v)[0]:.1f}" cy="{pt(i, v)[1]:.1f}" r="4" fill="{C[D[i][1]]}"/>'
                   for i, v in enumerate(now))
    qx, qy = pt(4, goal[4])
    dots += f'<circle cx="{qx:.1f}" cy="{qy:.1f}" r="4" fill="{C["yellow"]}" class="pulse"/>'
    # axis labels, pushed out past the rim and anchored away from the centre
    labels = []
    for i, (name, col, _, _) in enumerate(D):
        x, y = pt(i, 1.17)
        c = math.cos(ang[i])
        anchor = "middle" if abs(c) < 0.2 else ("start" if c > 0 else "end")
        dy = -4 if i == 0 else (14 if math.sin(ang[i]) > 0.5 else 5)
        labels.append(f'<text x="{x:.1f}" y="{y + dy:.1f}" text-anchor="{anchor}" fill="{C[col]}" '
                      f'style="font-size:13.5px;font-weight:600">{name}</text>')
    legend = (f'<text x="{cx}" y="{cy + R + 28}" text-anchor="middle" fill="{OV}" style="font-size:12.5px">'
              f'━ now   ┅ trajectory</text>')
    css = ('<style>.traj{animation:dash 6s linear infinite}@keyframes dash{to{stroke-dashoffset:-90}}'
           '.pulse{animation:pl 1.6s ease-in-out infinite}@keyframes pl{50%{opacity:.25}}</style>')
    radar = css + grid + spokes + shape + dots + "".join(labels) + legend
    return terminal("abhinav@indra-os : ~/stack", L, cursor=False, min_cols=96, pre_svg=radar, frosted=True)


def waybar():
    """Horizontal Waybar with colored module pills."""
    mods = [
        ("  indra-os", C['crust'], C['mauve']),
        ("  abhinav", C['text'], C['surface0']),
        (" 2:research", C['crust'], C['blue']),
        (" 34%", C['text'], C['surface0']),
        (" 11.2/32G", C['text'], C['surface0']),
        ("  ●●● 3 agents", C['crust'], C['green']),
        ("  claude-opus", C['text'], C['surface0']),
        (" main", C['crust'], C['peach']),
        ("  up 6d", C['text'], C['surface0']),
        ("  ONLINE", C['crust'], C['teal']),
        (" 14:22", C['crust'], C['lavender']),
    ]
    H = 46
    padpill = 9
    gap = 8
    x = 12
    pills = []
    for txt, fg, bg in mods:
        w = len(txt) * CW + padpill * 2
        pills.append(
            f'<rect x="{x:.0f}" y="8" width="{w:.0f}" height="30" rx="8" fill="{bg}"/>'
            f'<text x="{x+padpill:.0f}" y="28" xml:space="preserve" fill="{fg}">{esc(txt)}</text>'
        )
        x += w + gap
    W = int(x + 4)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img">
<style>text{{font-family:{FONT};font-size:{FS}px;white-space:pre;}}</style>
<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="{C['mantle']}" stroke="{C['surface0']}"/>
{"".join(pills)}
</svg>'''


def bar_row(label, pct, color, width_chars=24):
    """observability gauge as spans (filled accent + dim remainder)."""
    filled = int(round(pct / 100 * width_chars))
    return [sp(f"{label:<5}", "subtext"), sp("█" * filled, color),
            sp("░" * (width_chars - filled), "surface1"), sp(f" {pct:>3}%", "text")]


def sbox(title, rows, innerW, tcolor):
    """A fixed-width titled box. rows = list of list-of-spans (visible len <= innerW).
    Returns list of lines (each exactly innerW+4 chars wide) so borders always align."""
    S = "surface1"
    Wb = innerW + 4
    d = Wb - 5 - len(title)                      # ╭─ TITLE <dashes>╮
    lines = [[sp("╭─ ", S), sp(title, tcolor), sp(" " + "─" * d, S), sp("╮", S)]]
    for r in rows:
        vis = sum(len(t) for t, _ in r)
        lines.append([sp("│ ", S)] + r + [sp(" " * max(0, innerW - vis), "base"), sp(" │", S)])
    lines.append([sp("╰" + "─" * (Wb - 2) + "╯", S)])
    return lines


def sbs(left, right, lw, gap=3):
    """Place two boxes side by side. lw = left box total width (for blank padding)."""
    n = max(len(left), len(right))
    out = []
    for i in range(n):
        l = left[i] if i < len(left) else [sp(" " * lw, "base")]
        r = right[i] if i < len(right) else []
        out.append(l + [sp(" " * gap, "base")] + r)
    return out


# ── panel definitions ───────────────────────────────────────────────────────
def build():
    out = {}

    # boot (animated)
    ok = lambda: sp("  ok", "green")
    boot = [
        [sp("indra-os UEFI · rev 26.07 ", "overlay"), sp("─" * 30, "surface1")],
        [sp("[  0.128] ", "overlay"), sp("kernel 6.11.0-indra", "text"), sp(" ....................", "surface1"), ok()],
        [sp("[  0.774] ", "overlay"), sp("Hyprland + Waybar ", "mauve"), sp("(Wayland)", "subtext"), sp(" ...........", "surface1"), ok()],
        [sp("[  1.144] ", "overlay"), sp("AI scheduler ", "text"), sp("claude · codex · gemini", "blue"), sp(" ....", "surface1"), ok()],
        [sp("[  1.640] ", "overlay"), sp("knowledge graph mounted ", "text"), sp("/mnt/graph", "teal"), sp(" ....", "surface1"), ok()],
        [sp("[  2.560] ", "overlay"), sp("cross-chain bridge ", "text"), sp("Stellar ↔ EVM", "peach"), sp(" .......", "surface1"), ok()],
        [sp("[  3.010] ", "overlay"), sp("Reached target ", "text"), sp("Multi-Agent Runtime", "green"), sp(". · 9 units · 0 failed", "subtext")],
    ]
    out["boot"] = terminal("abhinav@indra-os : boot", boot, animate=True)

    # fastfetch
    PAD = " " * 20                              # clears the vector logo drawn at left
    info = [
        [sp("abhinav", "green"), sp("@", "text"), sp("indra-os", "mauve")],
        [sp("─" * 33, "surface1")],
        [sp("OS        ", "mauve"), sp("indra-os (arch-based) x86_64", "text")],
        [sp("Kernel    ", "mauve"), sp("6.11.0-indra   ", "text"), sp("Uptime ", "mauve"), sp("6d 4h", "text")],
        [sp("Shell     ", "mauve"), sp("zsh 5.9 + powerlevel10k", "text")],
        [sp("WM        ", "mauve"), sp("Hyprland · Waybar · eww", "text")],
        [sp("Terminal  ", "mauve"), sp("foot / alacritty   ", "text"), sp("Editor ", "mauve"), sp("nvim", "text")],
        [sp("Theme     ", "mauve"), sp("Catppuccin Mocha · ", "text"), sp("Mauve", "mauve")],
        [sp("─" * 33, "surface1")],
        [sp("CPU ", "blue"), sp("Detected  ", "text"), sp("GPU ", "blue"), sp("Detected  ", "text"), sp("MEM ", "blue"), sp("11.2/32G", "text")],
        [sp("Python ", "blue"), sp("3.10  ", "text"), sp("Node ", "blue"), sp("20  ", "text"), sp("Docker ", "blue"), sp("27", "text")],
        [sp("Models  ", "blue"), sp("◆ ", "mauve"), sp("Claude Code  ", "text"), sp("◆ ", "mauve"), sp("Codex  ", "text"), sp("◆ ", "mauve"), sp("Gemini", "text")],
    ]
    # crisp vector diamond emblem (mauve ring + teal gem), perfectly centred
    cx, cy, rx, ry, g = 116, 205, 80, 148, 13
    dia = lambda sx, sy: f"{cx},{cy-sy} {cx+sx},{cy} {cx},{cy+sy} {cx-sx},{cy}"
    pre = (
        f'<polygon points="{dia(rx, ry)}" fill="{C["mauve"]}"/>'
        f'<polygon points="{dia(rx*0.62, ry*0.62)}" fill="{C["base"]}"/>'
        f'<rect x="{cx-g}" y="{cy-g}" width="{g*2}" height="{g*2}" rx="3" '
        f'fill="{C["teal"]}" transform="rotate(45 {cx} {cy})"/>'
    )
    ff = [[sp(PAD, "base")] + row for row in info]
    out["fastfetch"] = terminal("abhinav@indra-os : fastfetch", ff, cursor=False, pre_svg=pre)

    # services (systemctl)
    def svc(unit, desc, dc="subtext"):
        return [sp("● ", "green"), sp(f"{unit:<22}", "mauve"),
                sp("loaded ", "overlay"), sp("active ", "green"),
                sp("running  ", "green"), sp(desc, dc)]
    sv = [
        [sp("UNIT                    LOAD    ACTIVE  SUB      DESCRIPTION", "subtext")],
        [sp("─" * 68, "surface1")],
        svc("orchestrator.service", "indra-os · agent mission control"),
        svc("vedicmind.service", "ved-project · FSA meter compiler + RAG"),
        svc("intel.service", "xint · OSINT identity graph"),
        svc("telegram.service", "telint · Telegram collection"),
        svc("tripcode.service", "yotsuba-intel · 4chan correlation"),
        svc("bridge.service", "Stellar ↔ EVM intent settlement"),
        svc("market.service", "stock-intelligence · NSE council"),
        svc("tray.service", "gptray · desktop LLM tray daemon"),
        svc("cron.service", "github-ai-updates · repo poller"),
        [sp("─" * 68, "surface1")],
        [sp("  9 loaded", "text"), sp(" · ", "overlay"), sp("9 active", "green"), sp(" · ", "overlay"), sp("0 failed", "green")],
    ]
    out["services"] = terminal("abhinav@indra-os : systemctl status --all", sv, cursor=False)

    # observability (btop) — fixed-width boxes so borders align perfectly
    LW = 34 + 4  # left box total width
    def rt(name, val, vc="green"):
        return [sp(f"{name:<10}", "subtext"), sp("." * 13, "surface1"), sp(f"{val:>3}", vc)]
    sysbox = sbox("SYSTEM", [
        bar_row("CPU", 34, "mauve"),
        bar_row("MEM", 41, "blue"),
        bar_row("GPU", 18, "teal"),
        [sp("NET  ", "subtext"), sp("↓ 1.2  ", "green"), sp("↑ 0.3 MB/s", "peach")],
    ], 34, "mauve")
    runbox = sbox("RUNTIME", [
        rt("Services", 9), rt("Agents", 3), rt("Repos", 9), rt("Queue", 2, "yellow"),
    ], 26, "blue")
    engbox = sbox("ENGINES", [
        [sp("Compiler ", "subtext"), sp("█" * 16, "green"), sp(" 96.5%", "text")],
        [sp("Dataset  ", "subtext"), sp("." * 19, "surface1"), sp("18,910", "text")],
        [sp("Bridge   ", "subtext"), sp("▁▂▃▂▁ ", "teal"), sp("nominal ", "text"), sp("Stellar↔EVM", "peach")],
    ], 34, "mauve")
    intbox = sbox("INTEL", [
        [sp("Threat   ", "subtext"), sp("OSINT-ALPHA", "red")],
        [sp("Sources  ", "subtext"), sp("X · TG · 4chan", "peach")],
        [sp("Graph    ", "subtext"), sp("online", "green")],
    ], 26, "red")
    ob = sbs(sysbox, runbox, LW) + [[sp(" ", "base")]] + sbs(engbox, intbox, LW)
    out["observability"] = terminal("abhinav@indra-os : btop", ob, cursor=False, accent="mauve")

    # tmux journalctl pane
    jc = [
        [sp("❯ ", "green"), sp("journalctl -fu ", "text"), sp("vedicmind.service", "mauve")],
        [sp("[14:20:57] ", "overlay"), sp("normalize verse", "text"), sp(" ........ ", "surface1"), sp("ok", "green")],
        [sp("[14:20:58] ", "overlay"), sp("fsa compile ", "text"), sp("states=311", "teal"), sp(" .. ", "surface1"), sp("ok", "green")],
        [sp("[14:20:58] ", "overlay"), sp("meter detect ", "text"), sp("→ Anushtubh", "peach"), sp("  ", "surface1"), sp("0.981", "yellow")],
        [sp("[14:20:58] ", "overlay"), sp("rag retrieve ", "text"), sp("ctx k=6", "blue"), sp(" ..... ", "surface1"), sp("ok", "green")],
        [sp("[14:20:59] ", "overlay"), sp("explain → ", "text"), sp("/api/verse", "mauve"), sp(" ... ", "surface1"), sp("200", "green")],
    ]
    out["journal"] = terminal("vedicmind ~ journal", jc, cursor=True)

    # tmux git log pane
    gl = [
        [sp("❯ ", "green"), sp("git log --oneline --graph", "text")],
        [sp("* ", "yellow"), sp("a1f4c22 ", "peach"), sp("indra-os: route intel → gemini", "text")],
        [sp("* ", "yellow"), sp("7d90b1e ", "peach"), sp("ved: meter acc → 96.5% / 18,910", "text")],
        [sp("* ", "yellow"), sp("3c1aa87 ", "peach"), sp("bridge: harden Stellar↔EVM sync", "text")],
        [sp("* ", "yellow"), sp("55e02fd ", "peach"), sp("xint: merge telint + yotsuba", "text")],
        [sp("* ", "yellow"), sp("e9b7740 ", "peach"), sp("market: NSE council → serverless", "text")],
    ]
    out["gitlog"] = terminal("indra-os ~ git", gl, cursor=True)

    # service internals (replaces the old gray details code block)
    def hdr(name, target):
        return [sp("● ", "green"), sp(f"{name:<22}", "mauve"), sp("→  ", "overlay"), sp(target, "blue")]
    def sub(label, val, vc="text"):
        return [sp("    " + f"{label:<8}", "subtext"), sp(val, vc)]
    intern = [
        hdr("vedicmind.service", "ved-project"),
        sub("stack", "Next.js 14 · FastAPI · PostgreSQL + pgvector · Gemini Flash"),
        sub("engine", "rule-based compiler · Finite State Automata · Pratishakhya"),
        sub("data", "18,910 samples · 96.5% meter-detection accuracy", "green"),
        sub("pipe", "text ▸ normalize ▸ Pratishakhya ▸ FSA ▸ meter ▸ RAG ▸ API", "peach"),
        [sp(" ", "base")],
        hdr("orchestrator.service", "indra-os"),
        sub("role", "mission control · routes tasks to claude / codex / gemini,"),
        sub("", "owns the terminal workspace + knowledge graph."),
        [sp(" ", "base")],
        hdr("intel.service", "xint"),
        [sp("● ", "green"), sp(f"{'telegram.service':<22}", "mauve"), sp("→  ", "overlay"), sp("telint", "blue")],
        [sp("● ", "green"), sp(f"{'tripcode.service':<22}", "mauve"), sp("→  ", "overlay"), sp("yotsuba-intel", "blue")],
        sub("↳", "all three feed one OSINT graph  (X · Telegram · 4chan)", "subtext"),
        [sp(" ", "base")],
        hdr("bridge.service", "Cross-Chain-Intent-Bridge-Protocol"),
        sub("", "Stellar ↔ EVM · intent · asset lock · settlement · state sync", "peach"),
        [sp(" ", "base")],
        hdr("market.service", "stock-intelligence"),
        sub("", "Bayesian agent council · NSE · serverless Cloud Functions"),
        hdr("tray.service", "gptray"),
        sub("", "desktop system-tray LLM daemon + notifications"),
        hdr("cron.service", "github-ai-updates"),
        sub("", "scheduled GitHub polling · dependency monitoring"),
    ]
    out["internals"] = terminal("abhinav@indra-os : systemctl cat", intern, cursor=False)

    m = markets()
    pill = None
    if m:
        chg = m["nifty"]["c"][-1] / m["nifty"]["c"][-2] - 1
        pill = (f"NIFTY {'▲' if chg >= 0 else '▼'}{abs(chg) * 100:.2f}%", C["crust"], C["green" if chg >= 0 else "red"])
        out["markets"] = markets_panel(m)   # live quant desk
    out["desktop"] = tmux_session(pill)     # wallpaper + YASB bar + frosted terminal
    out["stack"] = stack_panel()            # Business · AI · Quant · Economics · GTM
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    adir = os.path.join(root, "assets")
    os.makedirs(adir, exist_ok=True)
    KEEP = {"desktop", "stack", "markets"}   # desktop + discipline stack + live quant desk
    panels = {k: v for k, v in build().items() if k in KEEP}
    for name, svg in panels.items():
        p = os.path.join(adir, f"{name}.svg")
        with open(p, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote {p}  ({len(svg)} bytes)")

    # ponytail: one self-check — every SVG well-formed + non-empty
    import xml.dom.minidom as m
    for name, svg in panels.items():
        m.parseString(svg)  # raises on malformed XML
        assert svg.count("<svg") == 1 and svg.strip().endswith("</svg>"), name
    print("ok: all SVGs well-formed")


if __name__ == "__main__":
    main()
