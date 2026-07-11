<!-- indra-os · github.com/gahlautabhinav · Catppuccin Mocha / neon cyan -->

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&height=160&color=0:00ffcc,60:0891b2,100:090d16&text=indra-os&fontColor=090d16&fontSize=60&fontAlignY=34&desc=agentic%20workstation%20//%20booting%20from%20GitHub&descAlignY=57&descSize=14&descColor=a6adc8" width="100%"/>

<img src="https://img.shields.io/badge/HOST-indra--os-00ffcc?style=flat-square&labelColor=090d16"/>
<img src="https://img.shields.io/badge/USER-abhinav-89b4fa?style=flat-square&labelColor=090d16"/>
<img src="https://img.shields.io/badge/WM-Hyprland-a6e3a1?style=flat-square&labelColor=090d16"/>
<img src="https://img.shields.io/badge/SHELL-zsh%20%2B%20p10k-cba6f7?style=flat-square&labelColor=090d16"/>
<img src="https://img.shields.io/badge/STATE-ONLINE-00ffcc?style=flat-square&labelColor=090d16"/>

</div>

```text
 HOST indra-os │ USER abhinav │ WS 2:research  ─╴  CPU 34%  MEM 11.2/32G  GPU ▁▂▃▂  ─╴  AGENTS ●●● 3  MODEL claude-opus-4  ─╴  GIT main ✔  UP 6d 04:11  ONLINE
```

## `⏻` boot

```text
indra-os UEFI · rev 26.07 ──────────────────────────────────────────────────
[  0.128] kernel 6.11.0-indra ..................................... ok
[  0.774] Hyprland + Waybar  (Wayland) ............................ ok
[  1.144] AI agent scheduler · claude · codex · gemini ............ ok
[  1.640] knowledge graph mounted  (/mnt/graph) ................... ok
[  2.560] cross-chain bridge  Stellar ↔ EVM ...................... ok
[  3.010] Reached target Multi-Agent Runtime. · 9 units · 0 failed
```

## `❯` fastfetch

```text
          ▟█▙              abhinav@indra-os
        ▟█████▙            ─────────────────────────────────────────
      ▟███▛ ▜███▙          OS        indra-os (arch-based) x86_64
    ▟███▛  ╭─╮  ▜███▙      Kernel    6.11.0-indra   ·   Uptime  6d 4h
    ▜███▙  │◆│  ▟███▛      Shell     zsh 5.9 + powerlevel10k
      ▜███▙╰─╯▟███▛        WM        Hyprland · Waybar · eww
        ▜█████▛            Terminal  foot / alacritty   Editor  nvim · VS Code
          ▜█▛              Theme     Catppuccin-Mocha · JetBrainsMono NF
   ─────────────────────────────────────────────────────────────────────
   CPU Detected · GPU Detected · MEM 11.2/32G   Python 3.10 · Node 20 · Docker 27
   Models  ◆ Claude Code   ◆ Codex   ◆ Gemini Flash   ○ local (planned)
```

## `❯` running services — `systemctl status --all`

```text
UNIT                     LOAD    ACTIVE  SUB      DESCRIPTION
──────────────────────── ─────── ─────── ──────── ─────────────────────────────────
● orchestrator.service   loaded  active  running  indra-os · agent mission control
● vedicmind.service      loaded  active  running  ved-project · FSA meter compiler + RAG
● intel.service          loaded  active  running  xint · OSINT identity graph
● telegram.service       loaded  active  running  telint · Telegram collection
● tripcode.service       loaded  active  running  yotsuba-intel · 4chan correlation
● bridge.service         loaded  active  running  Stellar ↔ EVM intent settlement
● market.service         loaded  active  running  stock-intelligence · NSE council
● tray.service           loaded  active  running  gptray · desktop LLM tray daemon
● cron.service           loaded  active  running  github-ai-updates · repo poller
──────────────────────── ─────── ─────── ──────── ─────────────────────────────────
  9 loaded · 9 active · 0 failed
```

<details>
<summary><code>❯ inspect service internals</code></summary>

```text
● vedicmind.service  →  github.com/gahlautabhinav/ved-project
    stack   Next.js 14 · FastAPI · PostgreSQL + pgvector · Gemini Flash
    engine  rule-based compiler · Finite State Automata · Pratishakhya grammar
    data    18,910 samples · 96.5% meter-detection accuracy
    pipe    text ▸ normalize ▸ Pratishakhya rules ▸ FSA compile
            ▸ meter detect ▸ RAG ▸ explanation ▸ API

● orchestrator.service  →  github.com/gahlautabhinav/indra-os
    role    mission control. routes tasks to claude/codex/gemini, owns the
            terminal workspace + knowledge graph. parent of every unit below.

● intel.service   →  xint         graph traversal · identity correlation · viz
  telegram.service→  telint       live channel collection · relationship extraction
  tripcode.service→  yotsuba-intel 4chan tripcode + anon identity correlation
    all three feed one OSINT graph (sources: X · Telegram · 4chan).

● bridge.service  →  github.com/gahlautabhinav/Cross-Chain-Intent-Bridge-Protocol
    Stellar ↔ EVM · intent engine · asset locking · cross-chain settlement · state sync

● market.service  →  stock-intelligence   Bayesian agent council over NSE,
    premarket briefing, serverless Cloud Functions pipeline.

● tray.service    →  gptray               desktop system-tray LLM daemon + notifications
● cron.service    →  github-ai-updates    scheduled GitHub polling · dependency monitoring
```
</details>

<div align="center">

<img src="https://img.shields.io/badge/Python-3.10-00ffcc?style=flat-square&logo=python&logoColor=090d16&labelColor=1e1e2e"/>
<img src="https://img.shields.io/badge/TypeScript-89b4fa?style=flat-square&logo=typescript&logoColor=090d16&labelColor=1e1e2e"/>
<img src="https://img.shields.io/badge/Next.js%2014-cdd6f4?style=flat-square&logo=nextdotjs&logoColor=090d16&labelColor=1e1e2e"/>
<img src="https://img.shields.io/badge/FastAPI-a6e3a1?style=flat-square&logo=fastapi&logoColor=090d16&labelColor=1e1e2e"/>
<img src="https://img.shields.io/badge/PostgreSQL%2Fpgvector-89dceb?style=flat-square&logo=postgresql&logoColor=090d16&labelColor=1e1e2e"/>
<img src="https://img.shields.io/badge/Gemini-cba6f7?style=flat-square&logo=googlegemini&logoColor=090d16&labelColor=1e1e2e"/>
<img src="https://img.shields.io/badge/Stellar-f5c2e7?style=flat-square&logo=stellar&logoColor=090d16&labelColor=1e1e2e"/>
<img src="https://img.shields.io/badge/Solidity-fab387?style=flat-square&logo=solidity&logoColor=090d16&labelColor=1e1e2e"/>
<img src="https://img.shields.io/badge/Docker-74c7ec?style=flat-square&logo=docker&logoColor=090d16&labelColor=1e1e2e"/>

</div>

## `❯` observability — `btop`

```text
┌─ SYSTEM ────────────────────────────────┐ ┌─ RUNTIME ─────────────────────────────┐
│ CPU  ███████████░░░░░░░░░░░░░░░░  34%    │ │ Services running .............. 9      │
│ MEM  █████████████░░░░░░░░░░░░░░  41%    │ │ Agents scheduled .............. 3      │
│ GPU  ██████░░░░░░░░░░░░░░░░░░░░░░  18%    │ │ Repositories .................. 9      │
│ NET  ↓ 1.2 MB/s   ↑ 0.3 MB/s             │ │ Inference queue ............... 2      │
└──────────────────────────────────────────┘ └───────────────────────────────────────┘
┌─ ENGINES ───────────────────────────────┐ ┌─ INTEL ───────────────────────────────┐
│ Compiler accuracy ████████████████ 96.5%│ │ Threat graph .............. OSINT-ALPHA│
│ Dataset samples ............. 18,910     │ │ Sources ............. X · TG · 4chan   │
│ Bridge latency ▁▂▃▂▁ nominal (Stellar↔EVM)│ │ Graph traversal ........... online     │
└──────────────────────────────────────────┘ └───────────────────────────────────────┘
```

## `❯` tmux — active panes

<table>
<tr>
<td width="50%" valign="top">

```text
❯ journalctl -fu vedicmind.service
[14:20:57] normalize  verse ......... ok
[14:20:58] fsa compile  states=311 .. ok
[14:20:58] meter detect → Anushtubh . 0.981
[14:20:58] rag retrieve  ctx k=6 .... ok
[14:20:59] explain → /api/verse ..... 200
```

</td>
<td width="50%" valign="top">

```text
❯ git log --oneline --graph
* a1f4c22 indra-os: route intel → gemini
* 7d90b1e ved: meter acc → 96.5% / 18,910
* 3c1aa87 bridge: harden Stellar↔EVM sync
* 55e02fd xint: merge telint + yotsuba edges
* e9b7740 market: NSE council → serverless
```

</td>
</tr>
</table>

## `❯` contribution telemetry

<div align="center">

<img width="100%" src="https://github-readme-activity-graph.vercel.app/graph?username=gahlautabhinav&bg_color=090d16&color=00ffcc&line=00ffcc&point=89b4fa&area=true&hide_border=true&custom_title=contribution%20telemetry"/>

</div>

```text
❯ uptime
 up 6 days, 4:11 · 1 user · load 0.34 0.29 0.31 · daemons still running.
```

<div align="center">
<img src="https://capsule-render.vercel.app/api?type=waving&section=footer&height=90&color=0:090d16,40:0891b2,100:00ffcc&fontColor=090d16"/>
</div>
