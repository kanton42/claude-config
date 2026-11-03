---
description: Summarize local Claude Code spend (today / by model / last 7 days) from ~/.claude/metrics/costs.jsonl. Degrades gracefully if no cost-tracker is set up yet.
argument-hint: "[csv]"
allowed-tools: Bash(node *), Bash(ls *), Read
---

# Cost Report

Summarize Claude Code session spend from `~/.claude/metrics/costs.jsonl` (one cumulative JSON snapshot per
session-stop). Takes the latest row per `session_id` and sums across sessions. Cross-platform via `node`.

> **Note (honest):** this reads a metrics file that a Stop "cost-tracker" hook must write. Until one is
> wired this command will report "not set up". Adding the tracker is a small optional follow-up — until
> then, treat this command as ready-but-dormant. (Adapted from ECC, MIT.)

```bash
node -e '
const fs=require("fs"),os=require("os"),path=require("path");
const f=path.join(os.homedir(),".claude","metrics","costs.jsonl");
if(!fs.existsSync(f)){console.log("Cost tracker not set up: "+f+" not found. Wire a Stop cost-tracker hook and finish a session first.");process.exit(0);}
const rows=fs.readFileSync(f,"utf8").split(/\r?\n/).filter(Boolean).map(l=>{try{return JSON.parse(l)}catch{return null}}).filter(Boolean);
const bySession=new Map();
for(const r of rows){const k=r.session_id||r.transcript_path||r.timestamp;const p=bySession.get(k);if(!p||String(r.timestamp)>String(p.timestamp))bySession.set(k,r);}
const latest=[...bySession.values()];
const cost=r=>Number(r.estimated_cost_usd)||0, day=r=>String(r.timestamp||"").slice(0,10);
const today=new Date().toISOString().slice(0,10), yest=new Date(Date.now()-864e5).toISOString().slice(0,10);
const sum=a=>a.reduce((s,r)=>s+cost(r),0), f4=n=>"$"+n.toFixed(4);
console.log("=== Cost summary ===");
console.log("today:     "+f4(sum(latest.filter(r=>day(r)===today))));
console.log("yesterday: "+f4(sum(latest.filter(r=>day(r)===yest))));
console.log("total:     "+f4(sum(latest))+"  ("+latest.length+" sessions)");
const by=k=>{const m=new Map();for(const r of latest){const x=k(r)||"(unknown)";m.set(x,(m.get(x)||0)+cost(r));}return [...m].sort((a,b)=>b[1]-a[1]);};
console.log("\n=== By model ===");for(const [k,v] of by(r=>r.model))console.log(f4(v).padStart(12)+"  "+k);
console.log("\n=== Last 7 days ===");
const d=new Map();for(const r of latest){const k=day(r);d.set(k,(d.get(k)||0)+cost(r));}
[...d].sort((a,b)=>a[0]<b[0]?1:-1).slice(0,7).forEach(([k,v])=>console.log(k+"  "+f4(v)));
'
```

Report: (1) today/yesterday/total + session count, (2) by model ranked, (3) last 7 days. Use the
precomputed `estimated_cost_usd`; don't re-estimate from tokens. For `csv`, dump the last 100 raw rows.
