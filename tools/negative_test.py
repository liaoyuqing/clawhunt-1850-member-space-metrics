# -*- coding: utf-8 -*-
"""反证实验（两条）：①把 IR-03 定义的「首年」改成「年度」→ 13 项定义一致性应 FAIL；
②把 OR-04 示例的分子改错（14400000→14400001）→ 第 12 项复算应 FAIL。正常校验输出落 tools/validate_metrics.out。
"""
import pathlib
import subprocess
import sys
import os

ROOT = pathlib.Path(__file__).resolve().parents[1]
SEED = ROOT / "dash" / "metrics" / "seed.yaml"
VAL = ROOT / "tools" / "validate_metrics.py"


def run(args):
    env = {"PYTHONIOENCODING": "utf-8", "PATH": os.environ.get("PATH", "")}
    p = subprocess.run([sys.executable] + args, capture_output=True, env=env)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def mutate(tag, old, new, metric=None):
    text = SEED.read_text(encoding="utf-8")
    tmp = ROOT / "tools" / ("_seed_mutated_%s.yaml" % tag)
    if metric:
        i = text.index("- id: %s" % metric)
        j = text.index("- id: ", i + 5)
        block = text[i:j]
        if old not in block:
            raise SystemExit("反证失败：%s 块里找不到 %r" % (metric, old))
        text = text[:i] + block.replace(old, new) + text[j:]
    else:
        if old not in text:
            raise SystemExit("反证失败：源文件找不到 %r" % old)
        text = text.replace(old, new, 1)
    tmp.write_text(text, encoding="utf-8")
    code, out, _ = run([str(VAL), "--seed", str(tmp)])
    out = out.replace("\r\n", "\n")
    (ROOT / "tools" / ("negative_%s.out" % tag)).write_text(out, encoding="utf-8", newline="\n")
    tmp.unlink()
    fails = [l for l in out.splitlines() if l.startswith("[FAIL]")]
    return code, fails


def main():
    code, out, _ = run([str(VAL)])
    out = out.replace("\r\n", "\n")
    (ROOT / "tools" / "validate_metrics.out").write_text(out, encoding="utf-8", newline="\n")
    print("normal: exit=%d lines=%d" % (code, len(out.rstrip().splitlines())))

    c1, f1 = mutate("def", "首年", "年度", metric="IR-03")
    c2, f2 = mutate("math", "14400000 ÷ 18720000", "14400001 ÷ 18720000")
    lines = [
        "case1 定义反证（IR-03「首年」→「年度」）: exit=%d fails=%d" % (c1, len(f1))
    ] + ["  " + l for l in f1]
    lines += [
        "case2 算式反证（OR-04 分子 14400000→14400001）: exit=%d fails=%d" % (c2, len(f2))
    ] + ["  " + l for l in f2]
    lines.append("restored: exit=%d" % run([str(VAL)])[0])
    (ROOT / "tools" / "negative_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
