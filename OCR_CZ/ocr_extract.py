#!/usr/bin/env python3
"""批量提取证书信息 -> Excel + 待人工审核清单（跨平台版）。

用法:
    python ocr_extract.py <证书图片目录> [<目录2> ...]
    （不带参数则提示用法；所有路径通过命令行传入，不绑定机器目录）

输出（写在脚本所在目录）:
    证书信息.xlsx      成功解析的记录
    待人工审核.txt     解析失败的文件列表
"""
import sys
from pathlib import Path

import pandas as pd

from cert_ocr import create_ocr, ocr_lines, parse

OUT_DIR = Path(__file__).resolve().parent
OUT_XLSX = OUT_DIR / "证书信息.xlsx"
OUT_FAIL = OUT_DIR / "待人工审核.txt"


def main():
    dirs = [Path(a) for a in sys.argv[1:]]
    if not dirs:
        sys.exit("用法: python ocr_extract.py <证书图片目录> [<目录2> ...]")
    for d in dirs:
        if not d.is_dir():
            sys.exit(f"目录不存在: {d}")

    imgs = sorted(p for d in dirs for p in d.glob("*.jpg"))
    print(f"共 {len(imgs)} 张证书待识别")
    if not imgs:
        return

    ocr = create_ocr()
    rows, fails = [], []
    for i, img in enumerate(imgs, 1):
        # 级别以所在路径为准（路径含"省赛"则为省赛，否则为国赛）
        level = "省赛" if "省赛" in str(img) else "国赛"
        info = parse("\n".join(ocr_lines(ocr, img)))
        if info:
            info["级别"] = level
            info["来源文件"] = img.name
            rows.append(info)
            print(f"[{i}/{len(imgs)}] OK   {img.name} -> {info['姓名']} {info['奖项']}", flush=True)
        else:
            fails.append(img)
            print(f"[{i}/{len(imgs)}] FAIL {img.name}", flush=True)

    df = pd.DataFrame(rows, columns=["姓名", "赛道", "组别", "级别", "奖项", "指导老师", "证书编号", "来源文件"])
    df.to_excel(OUT_XLSX, index=False)
    print(f"\n已写出: {OUT_XLSX} ({len(rows)} 条)")

    if fails:
        OUT_FAIL.write_text("\n".join(str(f) for f in fails), encoding="utf-8")
        print(f"解析失败 {len(fails)} 张，清单见: {OUT_FAIL}")


if __name__ == "__main__":
    main()
