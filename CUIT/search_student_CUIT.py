# -*- coding: utf-8 -*-
"""
成都信息工程大学 竞赛报名系统 - 学生查询
依赖：pip install requests beautifulsoup4
用法：
  python search_student_CUIT.py            # 交互输入姓名
  python search_student_CUIT.py 陈嘉瑞      # 命令行直接带姓名
"""

import json
import os
import sys
import time

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

URL = "https://scxy.cuit.edu.cn/xkjs/CompetitionStudent/Apply/SearchStudentPageList"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36 Edg/156.0.0.0",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://scxy.cuit.edu.cn",
    "Referer": "https://scxy.cuit.edu.cn/xkjs/CompetitionStudent/Apply/Modify/ea0a1d11-2432-40bc-84f9-4ce7b73c577e",
    "Cookie": COOKIE,
}

MAX_PAGES = 2       # 最多翻几页
SLEEP_SEC = 1       # 每页间隔秒数

# 空页占位文本，出现即视为没有数据
EMPTY_TEXTS = {"暂无数据", "暂无记录", "没有数据", "无数据", "没有找到相关数据"}


def parse_table(html: str):
    """从返回的 HTML 片段里解析表格数据行"""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", id="c-app-page-ResultStudentPageList-table")
    if not table:
        return []

    thead = table.find("thead")
    headers = [th.get_text(strip=True) for th in thead.find_all("th")] if thead else []

    rows = []
    tbody = table.find("tbody")
    if not tbody:
        return rows

    for tr in tbody.find_all("tr"):
        # 占位行通常是 colspan 撑满整行的单个单元格
        if tr.find("td", colspan=True):
            continue

        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if not cells:
            continue
        if cells[0] in EMPTY_TEXTS:
            continue
        if len(cells) < len(headers):
            continue

        rows.append(dict(zip(headers, cells)))

    return rows


def search_by_name(name: str):
    all_records = []
    for page in range(1, MAX_PAGES + 1):
        form = {
            "PageIndex": str(page),
            "XueYuanCode": "",
            "ZhuanYeCode": "",
            "UserName": name,
            "UserAccount": "",
            "Grade": "",
        }

        try:
            resp = requests.post(URL, data=form, headers=HEADERS, timeout=15)
        except requests.RequestException as e:
            print(f"[网络错误] 第 {page} 页请求失败：{e}")
            break

        records = parse_table(resp.text)
        if not records:
            print(f"第 {page} 页无数据，停止。")
            break

        all_records.extend(records)
        print(f"第 {page} 页：{len(records)} 条，累计 {len(all_records)} 条")

        if page < MAX_PAGES:
            time.sleep(SLEEP_SEC)

    return all_records


if __name__ == "__main__":
    if not COOKIE:
        print("没有找到 Cookie：请在同目录新建 cookie.txt 写入整段 Cookie，"
              "或设置环境变量 CUIT_COOKIE。")
        raise SystemExit(1)

    name = sys.argv[1].strip() if len(sys.argv) > 1 else input("请输入姓名：").strip()
    if not name:
        raise SystemExit(1)

    records = search_by_name(name)

    print(f"\n共拿到 {len(records)} 条")
    print(json.dumps(records, ensure_ascii=False, indent=2))

    out_file = os.path.join(BASE_DIR, f"search_{name}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"\n已保存到 {out_file}")
