#!/usr/bin/env python3
"""OCR 公共配置：轻量模型 + 字段解析正则（macOS / Windows 通用）。"""
import re

from paddleocr import PaddleOCR

# PP-OCRv5_mobile：移动端轻量模型，证书等规整印刷体识别足够，内存约为 medium 的 1/3
# 关闭文档方向分类/矫正/文本行方向三个辅助模型，进一步省内存（证书都是正向拍摄的）
OCR_KWARGS = dict(
    lang="ch",
    text_detection_model_name="PP-OCRv5_mobile_det",
    text_recognition_model_name="PP-OCRv5_mobile_rec",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
)

RE_NAME = re.compile(r"成都信息工程大学\s*(\S{2,4})")
RE_AWARD = re.compile(r"荣获(.+?)\s*([A-Za-z])组\s*(省赛|国赛)[:：]\s*(\S+等奖|优秀奖)")
RE_TEACHER = re.compile(r"指导老师[:：]\s*(\S+)")
RE_CERTNO = re.compile(r"证书编号[:：]?\s*([A-Za-z0-9]+)")


def create_ocr() -> PaddleOCR:
    return PaddleOCR(**OCR_KWARGS)


def ocr_lines(ocr: PaddleOCR, img) -> list[str]:
    """兼容 paddleocr 3.x (dict) 与 2.x (list) 返回格式，取识别文本行。"""
    result = ocr.ocr(str(img))
    if not result:
        return []
    page = result[0]
    if isinstance(page, dict):  # 3.x
        return page.get("rec_texts", [])
    return [line[1][0] for line in page] if page else []  # 2.x


def parse(text: str) -> dict | None:
    name = RE_NAME.search(text)
    award = RE_AWARD.search(text)
    teacher = RE_TEACHER.search(text)
    certno = RE_CERTNO.search(text)
    if not (name and award and teacher and certno):
        return None
    return {
        "姓名": name.group(1),
        "赛道": award.group(1),
        "组别": award.group(2),
        "级别": award.group(3),
        "奖项": award.group(4),
        "指导老师": teacher.group(1),
        "证书编号": certno.group(1),
    }
