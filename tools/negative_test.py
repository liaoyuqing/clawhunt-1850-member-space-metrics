# -*- coding: utf-8 -*-
"""反证实验：把 IR-03 定义里的「首年」删掉，校验器第 13 项应 FAIL 且退出码 1。

同时把正常校验输出按 UTF-8 落盘 tools/validate_metrics.out，供正文逐字粘贴。
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SEED = ROOT / "dash" / "metrics" / "seed.yaml"
VAL = ROOT / "tools" / "validate_metrics.py"
TMP = ROOT / "tools" / "_seed_mutated.yaml"


def run(args):
    env = {"PYTHONIOENCODING": "utf-8", "PATH": __import__("os").environ.get("PATH", "")}
    p = subprocess.run([sys.executable] + args, capture_output=True, env=env)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def main():
    code, out, _ = run([str(VAL)])
    out = out.replace("\r\n", "\n").replace("\r", "\n")
    (ROOT / "tools" / "validate_metrics.out").write_text(out, encoding="utf-8", newline="\n")
    print("normal: exit=%d lines=%d" % (code, len(out.rstrip().splitlines())))

    text = SEED.read_text(encoding="utf-8")
    idx = text.index("- id: IR-03")
    end = text.index("- id: IR-04")
    block = text[idx:end]
    if "首年" not in block:
        raise SystemExit("IR-03 定义块里找不到「首年」，反证无法进行")
    TMP.write_text(text[:idx] + block.replace("首年", "年度") + text[end:], encoding="utf-8")
    code2, out2, _ = run([str(VAL), "--seed", str(TMP)])
    (ROOT / "tools" / "negative_test.out").write_text(out2.replace("\r\n", "\n"), encoding="utf-8", newline="\n")
    fails = [l for l in out2.splitlines() if "FAIL" in l]
    body = "\n".join(["mutated: exit=%d fails=%d" % (code2, len(fails))] + ["  " + l for l in fails])
    (ROOT / "tools" / "negative_summary.txt").write_text(body + "\n", encoding="utf-8", newline="\n")
    TMP.unlink()
    print("restored: exit=%d" % run([str(VAL)])[0])


if __name__ == "__main__":
    main()