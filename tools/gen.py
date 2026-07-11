#!/usr/bin/env python3
"""Generate Catppuccin Mocha 'terminal window' SVGs for the GitHub profile README.

Each panel is a self-contained SVG (own bg + window chrome + colored monospace
text) so it renders identically in GitHub light/dark via <img>. Animations use
CSS keyframes inside the SVG, which GitHub's image proxy plays (same trick as
readme-typing-svg / the contribution snake).

Run:  py -3.10 tools/gen.py      ->  writes assets/*.svg
"""
import os, html

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


def terminal(title, lines, *, animate=False, min_cols=0, cursor=True,
             accent="mauve", pre_svg=""):
    """lines: list of list-of-spans. Returns SVG string.
    pre_svg: raw SVG drawn in the body area behind the text (e.g. a vector logo)."""
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

    dots = "".join(
        f'<circle cx="{22 + k*20}" cy="{BAR/2:.0f}" r="6" fill="{col}"/>'
        for k, col in enumerate([C['red'], C['yellow'], C['green']])
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img">
<style>{css}</style>
<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="{C['base']}" stroke="{C['surface0']}"/>
<path d="M0.5 12.5 A12 12 0 0 1 12.5 0.5 H{W-12.5} A12 12 0 0 1 {W-0.5} 12.5 V{BAR} H0.5 Z" fill="{C['mantle']}"/>
<line x1="0.5" y1="{BAR}" x2="{W-0.5}" y2="{BAR}" stroke="{C['surface0']}"/>
{dots}
<text x="{W/2:.0f}" y="{BAR/2+4:.0f}" text-anchor="middle" class="ttl">{esc(title)}</text>
{pre_svg}
{"".join(body)}
{cur}
</svg>'''


def tmux_session():
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
        [sp("EDIT  ", "mauve"), sp("nvim · foot", "text")],
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

    # ── vector diamond in the fastfetch pane ──────────────────────────────
    cx, cy, rx, ry, g = colx(9), rowy(6) - 4, 64, 118, 10
    dia = lambda sx, sy: f"{cx:.0f},{cy-sy:.0f} {cx+sx:.0f},{cy:.0f} {cx:.0f},{cy+sy:.0f} {cx-sx:.0f},{cy:.0f}"
    diamond = (f'<polygon points="{dia(rx, ry)}" fill="{C["mauve"]}"/>'
               f'<polygon points="{dia(rx*0.6, ry*0.6)}" fill="{C["base"]}"/>'
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

    dots = "".join(f'<circle cx="{22+k*20}" cy="{BAR/2:.0f}" r="6" fill="{col}"/>'
                   for k, col in enumerate([C['red'], C['yellow'], C['green']]))

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img">
<style>text{{font-family:{FONT};font-size:{FS}px;font-variant-ligatures:none;white-space:pre;}} .ttl{{font-size:13px;fill:{C['subtext']};}}</style>
<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="{C['base']}" stroke="{C['surface0']}"/>
<path d="M0.5 12.5 A12 12 0 0 1 12.5 0.5 H{W-12.5} A12 12 0 0 1 {W-0.5} 12.5 V{BAR} H0.5 Z" fill="{C['mantle']}"/>
<line x1="0.5" y1="{BAR}" x2="{W-0.5}" y2="{BAR}" stroke="{C['surface0']}"/>
{dots}
<text x="{W/2:.0f}" y="{BAR/2+4:.0f}" text-anchor="middle" class="ttl">abhinav@indra-os — tmux</text>
{diamond}
{lines}
{"".join(body)}
{sbar}
</svg>'''


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

    out["waybar"] = waybar()
    out["tmux"] = tmux_session()
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    adir = os.path.join(root, "assets")
    os.makedirs(adir, exist_ok=True)
    KEEP = {"waybar", "tmux"}      # single-window tmux layout + the waybar strip
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
