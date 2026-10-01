#!/usr/bin/env python3
"""(AT-1) Token attributions for the small checkers on matched dose pairs (GPU if available; CPU smoke).

Models (--models): mc_roberta (MiniCheck-RoBERTa-Large), mc_ft5 (MiniCheck-Flan-T5-Large), as_large
(AlignScore-large, nli head), optional mc_deberta, as_base.  Inputs follow each checker's own format
(MiniCheck: evidence + eos + claim, Flan-T5 "predict: " prefix and the 3/209 label tokens; AlignScore:
(evidence, claim) pair, softmax(tri)[entail]); AlignScore is rebuilt from the checkpoint state_dict
(RobertaModel + tri_layer, no pytorch_lightning needed).  The single-pass score is compared with
the paper's stored score of the same instance (`score_stored`) as a reproduction check.

Items (main DOSE card bases): C0, INV-claim (correct unit conversion), E1-unit-claim (x1000 unit swap,
same numeral), E1-claim x10 (value edit), E1-unit-evid (swap in the evidence).
Per item:
  * Integrated gradients (target = support log-odds; baseline = pad embeddings with special tokens
    kept; --steps alphas, completeness gap logged) -> |attribution| share of token groups:
    claim/evidence x {number, unit, drug, other}; numbers/units = the dose spans' numeral / unit
    characters, drug = lexicon / suffix match.
  * Attention rollout (encoders only; eager attention) -> same group shares.
  * Occlusion (score space): claim unit removed, claim number removed, claim drug -> "the drug",
    evidence unit removed; delta prob and delta log-odds vs the intact item.
Output: results/journal2/attribution/attr_<model>.jsonl (resumable by item id) + run manifest.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT / "src", ROOT / "analysis", ROOT / "scripts", ROOT / "scripts/journal", HERE):
    sys.path.insert(0, str(p))

from unit_norm_fix import find_spans  # noqa: E402

OUTD = ROOT / "results/journal2/attribution"
CONDS = {("C0", None): "C0", ("INV-claim", "unit_conversion"): "INV-conv", ("E1-unit-claim", "x1000"): "swap-claim",
         ("E1-claim", "x10"): "value-x10", ("E1-unit-evid", "x1000"): "swap-evid"}
MODELS = {
    "mc_roberta": {"kind": "mc", "repo": "lytang/MiniCheck-RoBERTa-Large", "stored": "t6a_minicheck_roberta"},
    "mc_deberta": {"kind": "mc", "repo": "lytang/MiniCheck-DeBERTa-v3-Large", "stored": "t6a_minicheck_deberta"},
    "mc_ft5": {"kind": "ft5", "repo": "lytang/MiniCheck-Flan-T5-Large", "stored": "v2a_minicheck"},
    "as_large": {"kind": "as", "ckpt": "AlignScore-large.ckpt", "backbone": "roberta-large", "stored": "v3_alignscore"},
    "as_base": {"kind": "as", "ckpt": "AlignScore-base.ckpt", "backbone": "roberta-base", "stored": "t6a_alignscore_base"},
}
AS_REV = "8509e78d25bb914939fc585c626500c9b2944249"
_NUMPART = re.compile(r"^\s*(?:\d[\d,]*(?:\.\d+)?|\.\d+)(?:\s*(?:-|–|—|to)\s*(?:\d[\d,]*(?:\.\d+)?|\.\d+))?")


def drug_regex():
    try:
        from rd_fetch_labels import LEXICON
    except Exception:  # noqa: BLE001
        LEXICON = []
    from text_utils import DRUG_RE

    lex = re.compile(r"\b(?:%s)\b" % "|".join(re.escape(w) for w in sorted(LEXICON, key=len, reverse=True)), re.I) if LEXICON else None
    sfx = re.compile(r"\b\w{3,}(?:olol|pril|sartan|statin|cillin|mycin|cycline|prazole|dipine|oxetine|parin|gliptin|formin|"
                     r"azole|floxacin|vir|mab|nib|semide|thiazide|triptan|zepam|zolam|done|pine|profen|caine|olone|asone)\b", re.I)
    return [x for x in (lex, sfx, DRUG_RE) if x is not None]


DRUG_RES = None


def char_groups(text: str) -> list:
    """List of (start, end, group) over `text`: number / unit (dose spans) and drug mentions."""
    global DRUG_RES
    if DRUG_RES is None:
        DRUG_RES = drug_regex()
    out = []
    for s in find_spans(text):
        m = _NUMPART.match(s.text)
        k = m.end() if m else 0
        out.append((s.start, s.start + k, "number"))
        out.append((s.start + k, s.end, "unit"))
    for rx in DRUG_RES:
        for m in rx.finditer(text):
            if not any(a < m.end() and m.start() < b for a, b, _ in out):
                out.append((m.start(), m.end(), "drug"))
    return out


def group_of(a: int, b: int, groups: list) -> str:
    for s, e, g in groups:
        if a < e and s < b:
            return g
    return "other"


# ------------------------------------------------------------------ model wrappers
def _hf_load(fn, repo, **kw):
    """Local caches first (hub cache, then HF_HOME root as used by MiniCheck's cache_dir), online last."""
    hf = os.environ.get("HF_HOME")
    hub = os.environ.get("HUGGINGFACE_HUB_CACHE") or (hf + "/hub" if hf else None)
    caches = [c for c in (hub, hf) if c]
    last = None
    for local, cache in [(True, c) for c in caches] + [(True, None)] + [(False, caches[0] if caches else None)]:
        try:
            return fn(repo, cache_dir=cache, local_files_only=local, **kw)
        except Exception as exc:  # noqa: BLE001
            last = exc
    raise last


def check_tokenizer(tok, name: str) -> None:
    ids = tok("cefazolin 500 mg twice daily", add_special_tokens=False)["input_ids"]
    unk = tok.unk_token_id
    if not ids or (unk is not None and sum(i == unk for i in ids) > len(ids) // 2):
        raise RuntimeError("tokenizer for %s looks broken (ids=%s); incomplete cache?" % (name, ids))


class Wrapper:
    encoder_only = True

    def __init__(self, name: str, device):
        import torch

        self.torch = torch
        self.name, self.device = name, device
        spec = MODELS[name]
        self.kind = spec["kind"]
        from transformers import AutoTokenizer

        if self.kind == "mc":
            from transformers import AutoModelForSequenceClassification

            self.tok = _hf_load(AutoTokenizer.from_pretrained, spec["repo"], use_fast=True)
            self.model = _hf_load(AutoModelForSequenceClassification.from_pretrained, spec["repo"], attn_implementation="eager")
        elif self.kind == "ft5":
            from transformers import AutoModelForSeq2SeqLM

            self.tok = _hf_load(AutoTokenizer.from_pretrained, spec["repo"])
            self.model = _hf_load(AutoModelForSeq2SeqLM.from_pretrained, spec["repo"])
            self.encoder_only = False
        else:
            from huggingface_hub import hf_hub_download
            from transformers import AutoConfig, RobertaModel

            ckpt = None
            for local in (True, False):
                try:
                    ckpt = hf_hub_download("yzha/AlignScore", spec["ckpt"], revision=AS_REV, local_files_only=local,
                                           cache_dir=os.environ.get("HUGGINGFACE_HUB_CACHE"))
                    break
                except Exception:  # noqa: BLE001
                    continue
            bb = spec["backbone"]
            cfg = None
            for rid in (bb, "FacebookAI/" + bb):
                try:
                    cfg = _hf_load(AutoConfig.from_pretrained, rid)
                    self.tok = _hf_load(AutoTokenizer.from_pretrained, rid)
                    break
                except Exception:  # noqa: BLE001
                    continue
            cfg._attn_implementation = "eager"
            sd = torch.load(ckpt, map_location="cpu", weights_only=True)["state_dict"]
            enc = RobertaModel(cfg, add_pooling_layer=True)
            missing, unexpected = enc.load_state_dict({k[len("base_model."):]: v for k, v in sd.items() if k.startswith("base_model.")},
                                                      strict=False)
            missing = [m for m in missing if "position_ids" not in m]
            if missing:
                raise RuntimeError("AlignScore backbone keys missing: %s" % missing[:5])
            tri = torch.nn.Linear(cfg.hidden_size, 3)
            tri.load_state_dict({"weight": sd["tri_layer.weight"], "bias": sd["tri_layer.bias"]})
            self.model = torch.nn.ModuleDict({"enc": enc, "tri": tri})
        check_tokenizer(self.tok, name)
        self.model.to(device).eval()
        for p_ in self.model.parameters():
            p_.requires_grad_(False)

    # -- encoding: returns (enc dict, list of (segment, start, end) per token in its own text, claim, evidence)
    def encode(self, claim: str, evidence: str):
        tok = self.tok
        if self.kind == "as":
            enc = tok(evidence, claim, truncation="only_first", max_length=512, return_offsets_mapping=True, return_tensors="pt")
            seq = enc.sequence_ids(0)
            segs = []
            for (a, b), sid in zip(enc["offset_mapping"][0].tolist(), seq):
                segs.append(("special", 0, 0) if sid is None else (("evidence" if sid == 0 else "claim"), a, b))
        else:
            sep = tok.eos_token if self.kind == "mc" else "</s>"
            prefix = "predict: " if self.kind == "ft5" else ""
            text = prefix + evidence + sep + claim
            enc = tok(text, truncation=True, max_length=512, return_offsets_mapping=True, return_tensors="pt")
            e0, e1 = len(prefix), len(prefix) + len(evidence)
            c0 = e1 + len(sep)
            segs = []
            for (a, b) in enc["offset_mapping"][0].tolist():
                if a == b:
                    segs.append(("special", 0, 0))
                elif a >= c0:
                    segs.append(("claim", a - c0, b - c0))
                elif a >= e0 and b <= e1:
                    segs.append(("evidence", a - e0, b - e0))
                else:
                    segs.append(("special", 0, 0))
        enc.pop("offset_mapping")
        return {k: v.to(self.device) for k, v in enc.items()}, segs

    def embed(self, ids):
        emb = self.model["enc"].embeddings.word_embeddings if self.kind == "as" else self.model.get_input_embeddings()
        return emb(ids)

    def logodds_from_embeds(self, embeds, attn, output_attentions=False):
        torch = self.torch
        if self.kind == "mc":
            out = self.model(inputs_embeds=embeds, attention_mask=attn, output_attentions=output_attentions)
            lo = out.logits[:, 1] - out.logits[:, 0]
            return lo, getattr(out, "attentions", None)
        if self.kind == "ft5":
            dec = torch.zeros((embeds.size(0), 1), dtype=torch.long, device=embeds.device)
            out = self.model(inputs_embeds=embeds, attention_mask=attn, decoder_input_ids=dec)
            lg = out.logits[:, 0, :]
            return lg[:, 209] - lg[:, 3], None
        out = self.model["enc"](inputs_embeds=embeds, attention_mask=attn, output_attentions=output_attentions)
        tri = self.model["tri"](out.pooler_output)
        lp = torch.log_softmax(tri, dim=-1)
        p0 = lp[:, 0]
        return p0 - torch.log1p(-torch.exp(p0).clamp(max=1 - 1e-7)), getattr(out, "attentions", None)

    def prob(self, claim: str, evidence: str) -> tuple:
        torch = self.torch
        enc, _ = self.encode(claim, evidence)
        with torch.no_grad():
            lo, _ = self.logodds_from_embeds(self.embed(enc["input_ids"]), enc["attention_mask"])
        lo = float(lo[0])
        return 1 / (1 + math.exp(-lo)), lo


def integrated_gradients(w: Wrapper, enc: dict, steps: int, chunk: int = 16):
    torch = w.torch
    ids, attn = enc["input_ids"], enc["attention_mask"]
    x = w.embed(ids).detach()
    pad_id = w.tok.pad_token_id if w.tok.pad_token_id is not None else 0
    special = torch.tensor([[i in set(w.tok.all_special_ids) for i in ids[0].tolist()]], device=ids.device)
    base_ids = torch.where(special, ids, torch.full_like(ids, pad_id))
    x0 = w.embed(base_ids).detach()
    alphas = [(k + 0.5) / steps for k in range(steps)]  # midpoint rule
    total = torch.zeros_like(x)
    for off in range(0, steps, chunk):
        al = torch.tensor(alphas[off:off + chunk], device=x.device, dtype=x.dtype).view(-1, 1, 1)
        xs = (x0 + al * (x - x0)).requires_grad_(True)
        lo, _ = w.logodds_from_embeds(xs, attn.expand(xs.size(0), -1))
        g, = torch.autograd.grad(lo.sum(), xs)
        total += g.sum(0, keepdim=True)
    attr = ((x - x0) * total / steps).sum(-1)[0]
    with torch.no_grad():
        f1, _ = w.logodds_from_embeds(x, attn)
        f0, _ = w.logodds_from_embeds(x0, attn)
    gap = float(attr.sum() - (f1 - f0)[0])
    return attr.detach().float().cpu().tolist(), float(f1[0]), float(f0[0]), gap


def rollout(w: Wrapper, enc: dict):
    torch = w.torch
    if not w.encoder_only:
        return None
    with torch.no_grad():
        _, atts = w.logodds_from_embeds(w.embed(enc["input_ids"]), enc["attention_mask"], output_attentions=True)
    if not atts:
        return None
    n = atts[0].size(-1)
    r = torch.eye(n, device=atts[0].device)
    for a in atts:
        a = a[0].mean(0)
        a = a + torch.eye(n, device=a.device)
        a = a / a.sum(-1, keepdim=True)
        r = a @ r
    return r[0].float().cpu().tolist()  # CLS row


def shares(vals, segs, claim, evidence):
    cg, eg = char_groups(claim), char_groups(evidence)
    agg, cnt = {}, {}
    tot = 0.0
    for v, (seg, a, b) in zip(vals, segs):
        if seg == "special":
            continue
        g = seg + "_" + group_of(a, b, cg if seg == "claim" else eg)
        agg[g] = agg.get(g, 0.0) + abs(v)
        cnt[g] = cnt.get(g, 0) + 1
        tot += abs(v)
    return {"share": {k: v / tot for k, v in agg.items()} if tot else {}, "n_tokens": cnt,
            "signed_claim": {k: sum(v for v, (s, a, b) in zip(vals, segs) if s == "claim" and group_of(a, b, cg) == k)
                             for k in ("number", "unit", "drug", "other")}}


def occlusions(w: Wrapper, row: dict) -> dict:
    claim, ev = row["claim"], row["evidence"]
    p0, l0 = w.prob(claim, ev)
    out = {}

    def edit(text, span, part):
        if not span:
            return None
        j = text.find(span)
        if j < 0:
            return None
        m = _NUMPART.match(span)
        k = m.end() if m else 0
        if part == "unit":
            new = span[:k].rstrip()
        else:
            new = span[k:].lstrip()
        return text[:j] + new + text[j + len(span):]

    variants = {"claim_unit_removed": (edit(claim, row.get("claim_span"), "unit"), ev),
                "claim_number_removed": (edit(claim, row.get("claim_span"), "number"), ev),
                "evid_unit_removed": (claim, edit(ev, row.get("evidence_span"), "unit"))}
    drugs = [(s, e) for s, e, g in char_groups(claim) if g == "drug"]
    if drugs:
        t = claim
        for s, e in sorted(drugs, reverse=True):
            t = t[:s] + "the drug" + t[e:]
        variants["claim_drug_masked"] = (t, ev)
    for k, (c, e) in variants.items():
        if c is None or e is None:
            continue
        p, l_ = w.prob(c, e)
        out[k] = {"dprob": p - p0, "dlogodds": l_ - l0}
    return out


def load_items(limit_bases: int = 0) -> list:
    import paper_numbers_final as pnf  # noqa: F401  (loader side effects: none)
    from t15_card_report import T7, load_main_dose_instances
    from analyze import read_jsonl

    rows = list(load_main_dose_instances()) + [r for r in read_jsonl(T7) if r.get("valid", True)]
    items = []
    for r in rows:
        c = CONDS.get((r.get("condition"), r.get("magnitude") if r.get("condition") != "C0" else None))
        if c:
            items.append(dict(r, at_cond=c))
    bases = sorted({r["base_id"] for r in items if r["at_cond"] == "swap-claim"})
    if limit_bases:
        # smoke: prefer bases that have every condition
        full = [b for b in bases if {r["at_cond"] for r in items if r["base_id"] == b} >= set(CONDS.values())]
        bases = (full + [b for b in bases if b not in full])[:limit_bases]
    keep = set(bases)
    return [r for r in items if r["base_id"] in keep]


def stored_scores(slug: str) -> dict:
    try:
        import jr_threshold_robustness as J

        return J.score_map(slug)[0]
    except Exception as exc:  # noqa: BLE001
        print("stored scores unavailable for %s: %s" % (slug, exc))
        return {}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="mc_roberta,mc_ft5,as_large")
    ap.add_argument("--steps", type=int, default=128)
    ap.add_argument("--limit-bases", type=int, default=0, help="smoke: first N bases with all conditions")
    ap.add_argument("--outdir", default=str(OUTD))
    ap.add_argument("--device", default=os.environ.get("MEDVERIF_AT_DEVICE", "auto"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    items = load_items(args.limit_bases)
    from collections import Counter

    plan = {"items": len(items), "bases": len({r["base_id"] for r in items}), "by_cond": dict(Counter(r["at_cond"] for r in items)),
            "models": args.models.split(","), "steps": args.steps}
    print(json.dumps({"at_plan": plan}), flush=True)
    if args.dry_run:
        return
    import torch

    dev = torch.device("cuda" if (args.device == "auto" and torch.cuda.is_available()) else
                       (args.device if args.device != "auto" else "cpu"))
    outd = Path(args.outdir)
    outd.mkdir(parents=True, exist_ok=True)
    for name in [m for m in args.models.split(",") if m]:
        out = outd / ("attr_%s.jsonl" % name)
        done = set()
        if out.is_file():
            done = {json.loads(l)["item_id"] for l in out.open() if l.strip()}
        todo = [r for r in items if r["instance_id"] not in done]
        print(json.dumps({"at_model": name, "todo": len(todo), "done": len(done), "device": str(dev)}), flush=True)
        if not todo:
            continue
        t0 = time.time()
        w = Wrapper(name, dev)
        stored = stored_scores(MODELS[name]["stored"])
        with out.open("a", encoding="utf-8") as fh:
            for i, r in enumerate(todo, 1):
                enc, segs = w.encode(r["claim"], r["evidence"])
                ig, f1, f0, gap = integrated_gradients(w, enc, args.steps)
                ro = rollout(w, enc)
                ids = enc["input_ids"][0].tolist()
                rec = {"item_id": r["instance_id"], "model": name, "base_id": r["base_id"], "cond": r["at_cond"],
                       "claim": r["claim"], "claim_span": r.get("claim_span"), "evidence_span": r.get("evidence_span"),
                       "prob": 1 / (1 + math.exp(-f1)), "logodds": f1, "logodds_baseline": f0, "ig_completeness_gap": gap,
                       "score_stored": stored.get(r["instance_id"]), "n_tokens": len(ids),
                       "ig": shares(ig, segs, r["claim"], r["evidence"]),
                       "rollout": shares(ro, segs, r["claim"], r["evidence"]) if ro else None,
                       "occlusion": occlusions(w, r),
                       # claim-token heatmap material (only claim tokens, to keep files small)
                       "claim_tokens": [[w.tok.convert_ids_to_tokens(t), round(v, 5), a, b] for t, v, (s, a, b) in zip(ids, ig, segs)
                                        if s == "claim"]}
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                fh.flush()
                if i == 1 or i % 25 == 0 or i == len(todo):
                    print(json.dumps({"at_model": name, "n": i, "of": len(todo), "s_per_item": round((time.time() - t0) / i, 2)}), flush=True)
        del w
        if dev.type == "cuda":
            torch.cuda.empty_cache()
    (outd / "run_manifest.json").write_text(json.dumps(dict(plan, device=str(dev), torch=torch.__version__,
                                                             finished=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                                                             slurm_job=os.environ.get("SLURM_JOB_ID", "local")), indent=1) + "\n")


if __name__ == "__main__":
    main()
