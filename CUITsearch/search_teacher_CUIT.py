# -*- coding: utf-8 -*-
"""
成都信息工程大学 竞赛报名系统 - 教师查询（只查第一页，单次请求）
依赖：pip install requests beautifulsoup4
用法：
  python search_teacher_CUIT.py            # 交互输入姓名
  python search_teacher_CUIT.py 巩远发      # 命令行直接带姓名
"""

import json
import os
import sys

import requests
from bs4 import BeautifulSoup

# 输出目录：固定为本脚本所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_cookie() -> str:
    """Cookie 不写进代码，避免泄到公开仓库。
    优先读环境变量 CUIT_COOKIE，其次读同目录下的 cookie.txt（已被 .gitignore 忽略）。
    """
    env = os.environ.get("CUIT_COOKIE", "").strip()
    if env:
        return env
    path = os.path.join(BASE_DIR, "cookie.txt")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


COOKIE = load_cookie()

URL = "https://scxy.cuit.edu.cn/xkjs/CompetitionStudent/Apply/SearchTeacherPageList"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36 Edg/156.0.0.0",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://scxy.cuit.edu.cn",
    "Referer": "https://scxy.cuit.edu.cn/xkjs/CompetitionStudent/Apply/Modify/ea0a1d11-2432-40bc-84f9-4ce7b73c577e",
    "Cookie": COOKIE,
}

TABLE_ID = "c-app-page-ResultTeacherPageList-table"

# 教师接口是模糊/前缀匹配：查「王伟」会带出「王伟业」。
# EXACT_ONLY = True 时只保留姓名完全一致的记录；被过滤掉的名字会打印出来，不会悄悄丢掉。
EXACT_ONLY = True

# 单元格 data-name -> 输出字段名
FIELD_MAP = {
    "UserID": "教师ID",
    "UserName": "教师姓名",
    "UserAccount": "教师账号",
    "XueYuanName": "学院",
}


def attr(tag, key: str) -> str:
    """读取标签属性并统一成字符串。
    bs4 的 Tag.get 类型存根返回 str | None（实际还可能是 list），
    直接传给 dict.get / setdefault 会让 PyCharm 报类型重载不匹配。
    """
    value = tag.get(key)
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return " ".join(str(v) for v in value)
    return str(value)


def parse_table(html: str):
    """解析教师表格，优先读单元格的 data-value（未被格式化的原始值）"""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", id=TABLE_ID)
    if not table:
        # 兜底：服务端改过 table id 时取第一个带 thead/tbody 的表格
        table = soup.find("table")
    if not table:
        return []

    thead = table.find("thead")
    headers = [th.get_text(strip=True) for th in thead.find_all("th")] if thead else []

    rows = []
    tbody = table.find("tbody")
    if not tbody:
        return rows

    for tr in tbody.find_all("tr"):
        # 占位行：colspan 撑满整行的单个单元格
        if tr.find("td", colspan=True):
            continue

        cells = tr.find_all("td")
        if not cells:
            continue

        record = {}
        for idx, td in enumerate(cells):
            name = attr(td, "data-name")
            if name:
                key = FIELD_MAP.get(name, name)
                val = attr(td, "data-value") or td.get_text(strip=True)
            else:
                # 无 data-name 的列（序号、操作）按表头位置取名
                key = headers[idx] if idx < len(headers) else f"列{idx + 1}"
                val = td.get_text(strip=True)

            if key == "操作":      # 按钮列，没有数据
                continue
            record[key] = val

        # 主键：整行的 data-value 就是 UserID
        row_id = attr(tr, "data-value")
        if row_id:
            record.setdefault("教师ID", row_id)

        if not record.get("教师姓名"):
            continue

        rows.append(record)

    return rows


def search_teacher(name: str):
    """只查第一页，单次请求"""
    form = {
        "PageIndex": "1",
        "UserName": name,
    }

    resp = requests.post(URL, data=form, headers=HEADERS, timeout=15)
    return parse_table(resp.text)


if __name__ == "__main__":
    if not COOKIE:
        print("没有找到 Cookie：请在同目录新建 cookie.txt 写入整段 Cookie，"
              "或设置环境变量 CUIT_COOKIE。")
        raise SystemExit(1)

    name = sys.argv[1].strip() if len(sys.argv) > 1 else input("请输入教师姓名：").strip()
    if not name:
        raise SystemExit(1)

    records = search_teacher(name)

    if EXACT_ONLY:
        exact = [r for r in records if r.get("教师姓名") == name]
        others = [r.get("教师姓名") for r in records if r.get("教师姓名") != name]
        if others:
            print(f"[提示] 模糊匹配带出以下非完全一致的结果，已过滤：{others}")
        records = exact

    print(f"\n共拿到 {len(records)} 条")
    print(json.dumps(records, ensure_ascii=False, indent=2))

    out_file = os.path.join(BASE_DIR, f"output/teacher_{name}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"\n已保存到 {out_file}")
