#!/usr/bin/env python3
import argparse, csv, json, os, random, re, time, urllib.request, urllib.error
from collections import defaultdict
from pathlib import Path

JSON_RE=re.compile(r"\{.*?\}", re.S)
LETTER_RE=re.compile(r"\b([A-Z])\b", re.I)

def norm(x):
    s="" if x is None else str(x).strip().lower()
    s=re.sub(r"\s+"," ",s)
    s=re.sub(r"^[a-z]\s*[\.)\:\-]\s*","",s)
    s=re.sub(r"[^a-z0-9%+\-./() ]+","",s)
    return s.strip()

def infer_gold(options, answer):
    ans="" if answer is None else str(answer).strip()
    letters=[chr(ord("A")+i) for i in range(len(options))]
    if ans.upper() in letters:
        i=letters.index(ans.upper()); return i, letters[i]
    nans=norm(ans)
    for i,opt in enumerate(options):
        if norm(opt)==nans: return i, letters[i]
    m=re.match(r"^([A-Z])\s*[\.)\:\-]\s*(.+)$", ans, re.I)
    if m and m.group(1).upper() in letters:
        i=letters.index(m.group(1).upper()); return i, letters[i]
    return None, None

def prepare(inp, outp, invalidp):
    outp.parent.mkdir(parents=True, exist_ok=True)
    total=kept=bad=0
    with inp.open(encoding="utf-8") as fin, outp.open("w",encoding="utf-8") as fout, invalidp.open("w",encoding="utf-8") as ferr:
        for line in fin:
            if not line.strip(): continue
            r=json.loads(line)
            if r.get("question_type")!="MCQA": continue
            total+=1
            options=[str(x) for x in (r.get("options") or [])]
            idx,let=infer_gold(options,r.get("answer"))
            if idx is None:
                bad+=1; ferr.write(json.dumps(r,ensure_ascii=False)+"\n"); continue
            row={k:r.get(k) for k in ["id","dataset","domain","subdomain","question_type","question","answer"]}
            row.update({"options":options,"answer_index":idx,"answer_letter":let,"speech_metadata":r.get("speech_metadata",{})})
            fout.write(json.dumps(row,ensure_ascii=False)+"\n"); kept+=1
    print(f"mcqa_total={total} kept={kept} invalid_gold_mapping={bad}")

def prompt(row):
    letters=[chr(ord("A")+i) for i in range(len(row["options"]))]
    opts="\n".join(f"{l}. {o}" for l,o in zip(letters,row["options"]))
    return ("You are answering a scientific multiple-choice question.\n"
            "Choose the single best answer.\n\n"
            "Return only valid JSON in this format: {\"answer\": \"A\"}\n\n"
            + "Question:\n" + str(row["question"]) + "\n\nOptions:\n" + opts)

def parse_pred(raw, options):
    allowed=[chr(ord("A")+i) for i in range(len(options))]
    raw=(raw or "").strip()
    for m in JSON_RE.finditer(raw):
        try: ans=str(json.loads(m.group(0)).get("answer","")).strip().upper()
        except Exception: continue
        if ans in allowed: return ans,"json_answer"
    if raw.strip("` ").upper() in allowed: return raw.strip("` ").upper(),"bare_letter"
    m=re.search(r"\"answer\"\s*:\s*\"([A-Z])\"", raw, re.I)
    if m and m.group(1).upper() in allowed: return m.group(1).upper(),"regex_json_answer"
    m=re.search(r"(?:answer|option|choice)\s*(?:is|:)?\s*([A-Z])\b", raw, re.I)
    if m and m.group(1).upper() in allowed: return m.group(1).upper(),"answer_phrase_letter"
    # For long reasoning outputs, do not take the first isolated letter; it is often from analysis, not final answer.
    if len(raw) <= 80:
        for m in LETTER_RE.finditer(raw):
            if m.group(1).upper() in allowed: return m.group(1).upper(),"first_letter"
    nr=norm(raw)
    for i,opt in enumerate(options):
        no=norm(opt)
        if nr==no or (no and no in nr): return allowed[i],"option_text_match"
    return None,"invalid_prediction"

def call_api(api_key, base_url, model, ptxt, timeout, temp, top_p, max_tokens, disable_qwen_thinking):
    url=base_url.rstrip("/")+"/chat/completions"
    body={"model":model,"messages":[{"role":"system","content":"You are a precise scientific multiple-choice QA evaluator. Return only the requested JSON."},{"role":"user","content":ptxt}],"temperature":temp,"top_p":top_p,"max_tokens":max_tokens}
    if not disable_qwen_thinking:
        body["enable_thinking"]=False
    req=urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Authorization":"Bearer "+api_key,"Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data=json.loads(resp.read().decode())
    msg=data["choices"][0]["message"]; return (msg.get("content") or msg.get("reasoning_content") or ""), data.get("usage",{})

def run_eval(args):
    key=os.environ.get(args.api_key_env)
    if not key: raise SystemExit(f"{args.api_key_env} is not set")
    rows=[json.loads(x) for x in args.eval_input.open(encoding="utf-8") if x.strip()]
    if args.shuffle: random.Random(args.seed).shuffle(rows)
    rows=rows[args.offset:]
    if args.limit: rows=rows[:args.limit]
    args.output.parent.mkdir(parents=True, exist_ok=True); args.invalid_output.parent.mkdir(parents=True, exist_ok=True)
    done=set()
    if args.resume and args.output.exists():
        for line in args.output.open(encoding="utf-8"):
            if line.strip(): done.add(json.loads(line)["id"])
    mode="a" if args.resume else "w"
    total=correct=invalid=0
    with args.output.open(mode,encoding="utf-8") as fout, args.invalid_output.open(mode,encoding="utf-8") as ferr:
        for i,row in enumerate(rows,1):
            if row["id"] in done: continue
            raw=""; usage={}; err=None
            for attempt in range(1,args.retries+1):
                try:
                    raw,usage=call_api(key,args.base_url,args.model,prompt(row),args.timeout,args.temperature,args.top_p,args.max_tokens,args.disable_qwen_thinking); err=None; break
                except urllib.error.HTTPError as e:
                    err=f"HTTPError {e.code}: "+e.read().decode(errors="replace")[:500]
                except Exception as e:
                    err=repr(e)
                time.sleep(min(8,1.5*attempt))
            pred,status=parse_pred(raw,row["options"])
            if err: status="api_error"
            rec={"id":row["id"],"dataset":row["dataset"],"domain":row["domain"],"subdomain":row["subdomain"],"question_type":row["question_type"],"gold_answer":row["answer"],"gold_letter":row["answer_letter"],"pred_letter":pred,"parse_status":status,"is_correct":bool(pred==row["answer_letter"] and not err),"raw_response":raw,"model":args.model,"usage":usage,"error":err}
            fout.write(json.dumps(rec,ensure_ascii=False)+"\n"); fout.flush()
            total+=1; correct+=int(rec["is_correct"])
            if status in {"invalid_prediction","api_error"}: invalid+=1; ferr.write(json.dumps(rec,ensure_ascii=False)+"\n"); ferr.flush()
            print("[{}/{}] id={} pred={} gold={} correct={} parse={}".format(i, len(rows), row["id"], pred, row["answer_letter"], rec["is_correct"], status), flush=True)
            time.sleep(args.sleep)
    print(f"completed={total} correct={correct} accuracy={(correct/total if total else 0):.4f} invalid_or_error={invalid}")

def write_group(rows, keys, path):
    groups=defaultdict(list)
    for r in rows: groups[tuple(r.get(k,"") for k in keys)].append(r)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f); w.writerow([*keys,"count","correct","accuracy","invalid_or_error"])
        for k,rs in sorted(groups.items(), key=lambda x:(-len(x[1]),x[0])):
            c=len(rs); cor=sum(1 for r in rs if r.get("is_correct") is True); inv=sum(1 for r in rs if r.get("parse_status") in {"invalid_prediction","api_error"})
            w.writerow([*k,c,cor,f"{cor/c:.6f}",inv])

def summarize(predp, evalp, outdir):
    inp={r["id"]:r for r in (json.loads(x) for x in evalp.open(encoding="utf-8") if x.strip())}
    rows=[]
    for line in predp.open(encoding="utf-8"):
        if line.strip():
            p=json.loads(line); rows.append({**inp.get(p["id"],{}), **p})
    outdir.mkdir(parents=True, exist_ok=True)
    write_group(rows, [], outdir/"overall_metrics.csv")
    write_group(rows, ["domain"], outdir/"domain_metrics.csv")
    write_group(rows, ["dataset"], outdir/"dataset_metrics.csv")
    write_group(rows, ["domain","subdomain"], outdir/"subdomain_metrics.csv")
    features=sorted({f for r in rows for f in set((r.get("speech_metadata") or {}).get("core_features") or []) | set((r.get("speech_metadata") or {}).get("speech_sensitive_reasons") or [])})
    with (outdir/"feature_metrics.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f); w.writerow(["feature","count","correct","accuracy","invalid_or_error"])
        for feat in features:
            rs=[r for r in rows if feat in (set((r.get("speech_metadata") or {}).get("core_features") or []) | set((r.get("speech_metadata") or {}).get("speech_sensitive_reasons") or []))]
            c=len(rs); cor=sum(1 for r in rs if r.get("is_correct") is True); inv=sum(1 for r in rs if r.get("parse_status") in {"invalid_prediction","api_error"})
            w.writerow([feat,c,cor,f"{cor/c:.6f}",inv])
    with (outdir/"error_cases.jsonl").open("w",encoding="utf-8") as f:
        for r in rows:
            if r.get("is_correct") is not True: f.write(json.dumps(r,ensure_ascii=False)+"\n")
    n_correct=sum(1 for r in rows if r.get("is_correct") is True); print(f"rows={len(rows)} correct={n_correct} accuracy={(n_correct/len(rows) if rows else 0):.6f}")

def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd", required=True)
    p=sub.add_parser("prepare"); p.add_argument("--input",type=Path,required=True); p.add_argument("--output",type=Path,required=True); p.add_argument("--invalid-output",type=Path,required=True)
    r=sub.add_parser("run"); r.add_argument("--eval-input",type=Path,required=True); r.add_argument("--output",type=Path,required=True); r.add_argument("--invalid-output",type=Path,required=True); r.add_argument("--model",default="qwen3-8b"); r.add_argument("--base-url",default="https://dashscope.aliyuncs.com/compatible-mode/v1"); r.add_argument("--api-key-env",default="DASHSCOPE_API_KEY"); r.add_argument("--limit",type=int); r.add_argument("--offset",type=int,default=0); r.add_argument("--shuffle",action="store_true"); r.add_argument("--seed",type=int,default=42); r.add_argument("--sleep",type=float,default=0.2); r.add_argument("--timeout",type=int,default=120); r.add_argument("--retries",type=int,default=3); r.add_argument("--temperature",type=float,default=0.0); r.add_argument("--top-p",type=float,default=1.0); r.add_argument("--max-tokens",type=int,default=32); r.add_argument("--disable-qwen-thinking",action="store_true"); r.add_argument("--resume",action="store_true")
    s=sub.add_parser("summarize"); s.add_argument("--predictions",type=Path,required=True); s.add_argument("--eval-input",type=Path,required=True); s.add_argument("--output-dir",type=Path,required=True)
    a=ap.parse_args()
    if a.cmd=="prepare": prepare(a.input,a.output,a.invalid_output)
    elif a.cmd=="run": run_eval(a)
    else: summarize(a.predictions,a.eval_input,a.output_dir)
if __name__=="__main__": main()
