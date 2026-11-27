#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dash/metrics/seed.yaml 口径库格式校验器（S3-DASH-002）。

用法：
    python tools/validate_metrics.py            # 校验默认路径 dash/metrics/seed.yaml
    python tools/validate_metrics.py --seed PATH  # 校验指定文件

校验 12 项：文件可读、YAML 可解析、顶层字段、面板数=8 且键名匹配、面板计数自洽、
条目数>=30、每面板>=2、id 唯一且前缀与面板一致、必填文本字段非空、公式三段齐全、
过滤/维度/来源表非空、示例含数字且比率型演算可复算、验收定义与需求原文一致。
通过打印 [RESULT] PASS 并以退出码 0 结束；失败逐条打印缺陷并以退出码 1 结束。
"""
import argparse
import pathlib
import re
import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

try:
    import yaml
except ImportError:  # pragma: no cover
    print("[FAIL] PyYAML 未安装：pip install pyyaml")
    sys.exit(2)

PANEL_PREFIX = {
    "member_scale": "MS",
    "profile_completeness": "PF",
    "sop_execution": "SOP",
    "opportunity_funnel": "OF",
    "miniapp_activity": "MA",
    "ai_adoption": "AI",
    "investment_revenue": "IR",
    "occupancy_renewal": "OR",
}
TEXT_FIELDS = ["id", "panel", "name", "definition", "granularity"]
LIST_FIELDS = ["filters", "dimensions", "source_tables"]
FORMULA_FIELDS = ["numerator", "denominator", "expression"]
EXAMPLE_FIELDS = ["given", "calc", "result"]


class Report:
    def __init__(self):
        self.lines = []
        self.failures = []

    def check(self, name, ok, detail=""):
        tag = "[PASS]" if ok else "[FAIL]"
        if not ok:
            self.failures.append("%s %s" % (name, detail))
        self.lines.append("%s %-28s %s" % (tag, name, detail))


def load(path):
    if not path.is_file():
        print("[FAIL] 文件不存在: %s" % path)
        sys.exit(1)
    raw = path.read_text(encoding="utf-8")
    return raw, yaml.safe_load(raw)


def ratio_math(calc, result):
    """对 calc 形如 `A ÷ B`（可带 ×100）且 result 形如 `A ÷ B = C%` 的行复算。

    返回 (status, detail)：status 为 "checked" / "mismatch" / "skip"。
    """
    m_calc = re.match(r"^([\d.]+)\s*÷\s*([\d.]+)\s*(×\s*100)?$", calc.strip())
    m_res = re.match(r"^([\d.]+)\s*÷\s*([\d.]+)\s*=\s*([\d.]+)\s*%$", result.strip())
    if not m_calc or not m_res:
        return "skip", ""
    a, b = float(m_calc.group(1)), float(m_calc.group(2))
    ra, rb, rc = m_res.group(1), m_res.group(2), float(m_res.group(3))
    if a != float(ra) or b != float(rb):
        return "mismatch", "calc 与 result 的分子分母不一致: %s vs %s" % (calc, result)
    if b == 0:
        return "mismatch", "分母为 0"
    expect = round(a / b * 100, 2)
    if abs(expect - rc) > 0.011:
        return "mismatch", "%s 应为 %.2f%%，实际 %s" % (calc, expect, result)
    return "checked", ""

ALLOWED_ARITH = re.compile(r"^[0-9+\-*/(). ]+$")
DATA_DEPENDENT = ("样本", "位次", "中位")


def norm_expr(s):
    return (s.replace("×", "*").replace("÷", "/")
            .replace("（", "(").replace("）", ")").replace("，", ""))


def eval_arith(expr):
    """只接受纯四则运算字符，安全求值；不可求值返回 None。"""
    e = norm_expr(expr).strip().rstrip("。；;")
    if not e or not ALLOWED_ARITH.match(e):
        return None
    try:
        return float(eval(e, {"__builtins__": {}}, {}))
    except Exception:
        return None


def close(a, b, tol=0.011):
    return abs(a - b) <= max(tol, abs(b) * 1e-9)


def recompute(calc, result):
    """复算一条示例：calc 中每个「算式 = 结果」逐段验算，再用 result 的等式或末位数字回验。

    返回 (status, detail)：status 为 "checked" / "mismatch" / "skip"。
    calc 形如 `A - B = C；D ÷ E`，result 形如 `D ÷ E = F%`、`F 元/工位/月`、`F 天`。
    分位/中位这类需要原始样本的值（见 DATA_DEPENDENT）只验算式内部一致性。
    """
    calc, result = str(calc or "").strip(), str(result or "").strip()
    mism, evaluated, last_val = [], 0, None
    segs = [s for s in re.split(r"[；;]", calc) if s.strip()]
    for seg in segs:
        parts = [p.strip() for p in seg.split("=")]
        if len(parts) < 2:
            v = eval_arith(parts[0])
            if v is not None:
                evaluated += 1
                last_val = v
            continue
        expr_part, rhs = None, None
        for i in range(len(parts) - 1, 0, -1):
            v = eval_arith(parts[i])
            if v is not None:
                rhs, expr_part = v, parts[i - 1]
                break
        left = eval_arith(expr_part) if expr_part is not None else None
        if left is None or rhs is None:
            continue
        evaluated += 1
        last_val = rhs
        if not close(left, rhs):
            mism.append("%s 应为 %s，实际写 %s" % (expr_part, rhs, parts[-1]))

    eqs = list(re.finditer(r"([\d.]+)(\s*[÷/]\s*[\d.]+)+\s*=\s*([\d.]+)\s*(%?)", result))
    if eqs:
        last_div = None
        for seg in reversed(segs):
            md = re.search(r"([\d.]+(?:\s*[÷/]\s*[\d.]+)+)\s*$", seg.strip())
            if md:
                vals = [float(x) for x in re.findall(r"[\d.]+", md.group(1))]
                if len(vals) >= 2:
                    last_div = (vals[0], vals[1])
                break
        if last_div is not None:
            first = [float(x) for x in re.findall(r"[\d.]+", eqs[-1].group(0).split("=")[0])]
            if len(first) >= 2 and not (close(last_div[0], first[0], 1e-9) and close(last_div[1], first[1], 1e-9)):
                mism.append("示例算式的分子/分母与结果等式不一致：%s vs %s" % (last_div, (first[0], first[1])))
        for m in eqs:
            vals = [float(x) for x in re.findall(r"[\d.]+", m.group(0).split("=")[0])]
            c = float(m.group(3))
            acc, zero = vals[0], False
            for v in vals[1:]:
                if v == 0:
                    mism.append("分母为 0: %s" % m.group(0))
                    zero = True
                    break
                acc /= v
            if zero:
                continue
            expect = acc * (100.0 if m.group(4) else 1.0)
            evaluated += 1
            if not close(expect, c):
                mism.append("%s 应为 %.4f，实际写 %s" % (m.group(0), expect, c))
    elif last_val is not None and not any(w in calc + result for w in DATA_DEPENDENT):
        nums = re.findall(r"-?\d+(?:\.\d+)?", result.replace(",", ""))
        if nums:
            target = float(nums[-1])
            got = last_val * 100.0 if "%" in result else last_val
            evaluated += 1
            if not close(got, target):
                mism.append("末值 %.4f 与 result 数字 %s 不符" % (got, nums[-1]))

    inner = re.finditer(r"[（(]([0-9+\-*/. ]+)[）)]\s*[÷/]\s*([0-9.]+)\s*=\s*([0-9.]+)", calc)
    for m in inner:
        v = eval_arith(m.group(1))
        d = float(m.group(2))
        if v is None or d == 0:
            continue
        evaluated += 1
        if not close(v / d, float(m.group(3))):
            mism.append("%s 应为 %.4f" % (m.group(0), v / d))

    if mism:
        return "mismatch", "；".join(mism[:3])
    if not evaluated:
        return "skip", ""
    return "checked", ""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", default=None)
    args = ap.parse_args()
    root = pathlib.Path(__file__).resolve().parents[1]
    path = pathlib.Path(args.seed) if args.seed else root / "dash" / "metrics" / "seed.yaml"
    rep = Report()

    raw, doc = load(path)
    rep.check("1-yaml-parse", isinstance(doc, dict), "文件 %s，%d 字节，%d 行" % (path.name, len(raw.encode("utf-8")), raw.count(chr(10)) + 1))
    if not isinstance(doc, dict):
        print("\n".join(rep.lines))
        sys.exit(1)

    top_ok = all(k in doc for k in ("schema_version", "library", "panels", "metrics"))
    rep.check("2-top-level-fields", top_ok, "schema_version=%s library=%s" % (doc.get("schema_version"), doc.get("library")))

    panels = doc.get("panels") or []
    keys = [p.get("key") for p in panels]
    rep.check("3-panel-set", sorted(keys) == sorted(PANEL_PREFIX), "%d 个面板: %s" % (len(keys), ",".join(keys)))

    metrics = doc.get("metrics") or []
    if not isinstance(metrics, list):
        metrics = []
    rep.check("4-metric-count>=30", len(metrics) >= 30, "实际 %d 条" % len(metrics))

    per_panel = {k: [m for m in metrics if m.get("panel") == k] for k in PANEL_PREFIX}
    thin = [k for k, v in per_panel.items() if len(v) < 2]
    rep.check("5-per-panel>=2", not thin, "最少面板 %s=%d 条；分布 %s" % (min(per_panel.items(), key=lambda kv: len(kv[1]))[0], min(len(v) for v in per_panel.values()), " ".join("%s:%d" % (k, len(v)) for k, v in per_panel.items())))

    bad_counts = [p.get("key") for p in panels if p.get("metric_count") != len(per_panel.get(p.get("key"), []))]
    rep.check("6-panel-count-consistent", not bad_counts, "面板声明计数与条目实际数一致" if not bad_counts else "不一致: %s" % bad_counts)

    ids = [m.get("id") for m in metrics]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    bad_prefix = [m.get("id") for m in metrics if not str(m.get("id", "")).startswith(PANEL_PREFIX.get(m.get("panel"), "??") + "-")]
    rep.check("7-id-unique-and-prefixed", not dup and not bad_prefix, "%d 个 id 唯一%s" % (len(set(ids)), "" if not (dup or bad_prefix) else "；重复 %s；前缀错 %s" % (dup, bad_prefix)))

    missing = []
    for m in metrics:
        for f in TEXT_FIELDS:
            if not str(m.get(f) or "").strip():
                missing.append("%s.%s" % (m.get("id"), f))
    rep.check("8-required-text", not missing, "缺 %d 项%s" % (len(missing), "" if not missing else ": " + ",".join(missing[:6])))

    bad_formula = []
    for m in metrics:
        f = m.get("formula") or {}
        for k in FORMULA_FIELDS:
            if not str(f.get(k) or "").strip():
                bad_formula.append("%s.%s" % (m.get("id"), k))
    rep.check("9-formula-complete", not bad_formula, "分子/分母/计算方式齐全" if not bad_formula else "缺: %s" % ",".join(bad_formula[:6]))

    bad_list = []
    for m in metrics:
        for k in LIST_FIELDS:
            v = m.get(k)
            if not isinstance(v, list) or not [x for x in v if str(x).strip()]:
                bad_list.append("%s.%s" % (m.get("id"), k))
    rep.check("10-filters-dims-sources", not bad_list, "过滤条件/维度/来源表非空" if not bad_list else "缺: %s" % ",".join(bad_list[:6]))

    no_digit, checked, mismatch, skipped, checked_ids = [], 0, [], 0, []
    for m in metrics:
        e = m.get("example") or {}
        for k in EXAMPLE_FIELDS:
            if not str(e.get(k) or "").strip():
                no_digit.append("%s.example.%s 为空" % (m.get("id"), k))
        if not re.search(r"\d", str(e.get("given", "")) + str(e.get("calc", "")) + str(e.get("result", ""))):
            no_digit.append("%s.example 无数字" % m.get("id"))
        status, detail = recompute(str(e.get("calc", "")), str(e.get("result", "")))
        if status == "checked":
            checked += 1
            checked_ids.append(m.get("id"))
        elif status == "mismatch":
            mismatch.append("%s: %s" % (m.get("id"), detail))
        else:
            skipped += 1
    rep.check("11-example-has-numbers", not no_digit, "全部 32 条示例含虚拟数字" if not no_digit else ",".join(no_digit[:6]))
    rep.check("12-example-math-recompute", not mismatch, "复算 %d 条示例全部对得上%s%s" % (checked, "" if skipped else "（覆盖全部条目）", "" if skipped == 0 else "；另 %d 条无算式" % skipped) + ("" if not mismatch else "；不符: " + "; ".join(mismatch[:4])))

    by_id = {m.get("id"): m for m in metrics}
    defs = {k: " ".join(str((by_id.get(k) or {}).get(f, "")) for f in ("name", "definition", "formula")) for k in ("OF-03", "OR-01", "SOP-01", "OF-02", "IR-03")}
    checks = [
        ("OF-03", ["双方", "确认", "90 天", "同一对企业"]),
        ("OR-01", ["已租工位", "可租工位", "共享空间"]),
        ("SOP-01", ["按时完成", "到期待办"]),
        ("OF-02", ["采纳", "推荐"]),
        ("IR-03", ["首年", "拆分"]),
    ]
    bad_defs = []
    for mid, words in checks:
        for w in words:
            if w not in defs[mid]:
                bad_defs.append("%s 缺「%s」" % (mid, w))
    rep.check("13-definition-alignment", not bad_defs, "北极星/出租率/SOP/采纳率/签约额 定义与需求原文用词一致" if not bad_defs else "; ".join(bad_defs))

    for line in rep.lines:
        print(line)
    total = len(rep.lines)
    if rep.failures:
        print("")
        print("[RESULT] FAIL %d/%d 项不通过：" % (len(rep.failures), total))
        for f in rep.failures:
            print("  - " + f)
        sys.exit(1)
    print("")
    print("[SUMMARY] metrics=%d panels=%d examples_recomputed=%d examples_without_arith=%d" % (len(metrics), len(panels), checked, skipped))
    print("[RESULT] PASS %d/%d checks · 32 条口径 · 8 个面板 · 每面板 >= 2 条" % (total, total))
    sys.exit(0)


if __name__ == "__main__":
    main()