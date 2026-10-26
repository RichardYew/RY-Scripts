#!/usr/bin/env python3
"""单张/多张证书 OCR 测试，打印原始识别文本 + 解析结果。

用法:
    python ocr_test.py 证书1.jpg [证书2.jpg ...]
"""
import sys
from pathlib import Path

from cert_ocr import create_ocr, ocr_lines, parse


def main():
    if len(sys.argv) < 2:
        sys.exit("用法: python ocr_test.py 证书.jpg [更多.jpg ...]")
    ocr = create_ocr()
    for img in sys.argv[1:]:
        lines = ocr_lines(ocr, img)
        print(f"===== {Path(img).name} =====")
        print("\n".join(lines))
        print("----- 解析结果 -----")
        info = parse("\n".join(lines))
        if info:
            for k, v in info.items():
                print(f"{k}: {v}")
        else:
            print("解析失败: 关键字段未匹配")
        print()


if __name__ == "__main__":
    main()
