# -*- coding: utf-8 -*-
"""
PTA (pintia.cn/competitions) 竞赛排行榜爬虫
示例：2026年CCPC网络预选赛 - 清华大学队伍数据

原理：直接请求 PTA 后台排名 API，无需逐个点击加载队员名。
API 返回 JSON 已包含 teamInfo.memberNames（三名队员）和每题详情。
"""

import json
import gzip
import os
import urllib.request
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


# ====== 1. 配置 ======
# 竞赛 ID：从排行榜 URL 中提取，例如
# https://pintia.cn/rankings/2099750481526394880
# https://pintia.cn/rankings/2094677389171486720
# https://pintia.cn/rankings/2097206296647036928
CONTEST_ID = "2099750481526394880"
# 要筛选的学校名称（留空则导出全部队伍）
SCHOOL_NAME = "清华大学"
# 输出目录：始终放在当前脚本所在目录下的 output 文件夹中
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# output这个目录写在.gitignore中
OUTPUT_DIR = os.path.join(_SCRIPT_DIR, "output")
OUTPUT_FILE = f"2026年CCPC网络预选赛-{SCHOOL_NAME}.xlsx"


# ====== 2. 请求 API ======
def fetch_rankings(contest_id: str) -> dict:
    """请求 PTA 公开排名 API，返回完整 JSON。"""
    url = (
        f"https://pintia.cn/api/competitions/{contest_id}/xcpc-rankings/public"
        "?filter=%7B%22groupFid%22%3A%22%22%2C%22teamExcluded%22%3A%22NO_FILTER%22%2C%22hideScoreboard%22%3Afalse%7D"
    )
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0",
        "Accept-Encoding": "gzip",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
        # API 返回 gzip 压缩数据，需解压
        if raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)
    return json.loads(raw.decode("utf-8"))


# ====== 3. 数据解析 ======
def fmt_time(minutes: int) -> str:
    """比赛分钟数 → m:ss（如 287 → 4:47）。"""
    m, s = divmod(minutes, 60)
    return f"{m}:{s:02d}"


def parse_problem(prob: dict):
    """
    解析单题状态。
    返回 (显示文本, 是否通过)：
      - 通过：acceptTime >= 0 → "m:ss (+n)"，n = 提交次数 - 1（罚时）
      - 未过：acceptTime == -1 → "(+n)"，n = 提交次数
      - 未提交：调用方传 None → ("", False)
    """
    if prob is None:
        return "", False
    accept = prob["acceptTime"]
    submits = prob["validSubmitCount"]
    if accept >= 0:
        return f"{fmt_time(accept)} (+{submits - 1})", True
    else:
        return f"(+{submits})", False


# ====== 4. 生成 Excel ======
def build_excel(teams: list, problem_letters: list, output_path: str):
    wb = Workbook()
    ws = wb.active
    ws.title = "排行榜"

    # 表头
    headers = (
        ["校内排名", "排名", "队伍名", "队员1", "队员2", "队员3", "过题数", "总用时"]
        + problem_letters
    )
    header_fill = PatternFill("solid", fgColor="17365D")
    header_font = Font(name="微软雅黑", bold=True, color="FFFFFF", size=11)
    center = Alignment(horizontal="center", vertical="center")

    for col, h in enumerate(headers, 1):
        c = ws.cell(row=1, column=col, value=h)
        c.fill = header_fill
        c.font = header_font
        c.alignment = center

    # 颜色
    green_fill = PatternFill("solid", fgColor="C6EFCE")   # 通过-浅绿底
    red_fill = PatternFill("solid", fgColor="FFC7CE")     # 未过-浅红底
    green_font = Font(name="Arial", color="006100", size=10)
    red_font = Font(name="Arial", color="9C0006", size=10)
    normal_font = Font(name="微软雅黑", size=10)
    left = Alignment(horizontal="left", vertical="center")
    thin = Side(style="thin", color="D9D9D9")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    # 逐行写入
    for idx, team in enumerate(teams, 1):
        row = idx + 1
        ti = team["teamInfo"]
        members = ti["memberNames"][:3]
        members += [""] * (3 - len(members))

        base_vals = [
            idx,                  # 校内排名序号
            team["rank"],         # 总排名
            ti["teamName"],       # 队伍名
            members[0], members[1], members[2],
            team["solvedCount"],  # 过题数
            team["solvingTime"],  # 总用时（分钟）
        ]
        for col, val in enumerate(base_vals, 1):
            c = ws.cell(row=row, column=col, value=val)
            c.font = normal_font
            c.border = border
            c.alignment = left if col in (3, 4, 5, 6) else center

        # 每题
        for j, pid in enumerate(team["_problem_ids"]):
            col = 9 + j
            c = ws.cell(row=row, column=col)
            c.border = border
            c.alignment = center
            text, solved = parse_problem(team["detailsByProblemSetProblemId"].get(pid))
            c.value = text
            if solved:
                c.fill = green_fill
                c.font = green_font
            elif text:
                c.fill = red_fill
                c.font = red_font

    # 列宽
    widths = {1: 8, 2: 8, 3: 28, 4: 10, 5: 10, 6: 10, 7: 8, 8: 8}
    for col, w in widths.items():
        ws.column_dimensions[get_column_letter(col)].width = w
    for j in range(len(problem_letters)):
        ws.column_dimensions[get_column_letter(9 + j)].width = 12

    ws.freeze_panes = "A2"  # 冻结表头
    wb.save(output_path)


# ====== 5. 主流程 ======
def main():
    data = fetch_rankings(CONTEST_ID)
    rankings = data["xcpcRankings"]["rankings"]

    # 题目 ID 按返回顺序对应 A、B、C…
    problem_ids = list(rankings[0]["detailsByProblemSetProblemId"].keys())
    problem_letters = [chr(ord("A") + i) for i in range(len(problem_ids))]

    # 筛选学校
    if SCHOOL_NAME:
        teams = [r for r in rankings if r["teamInfo"]["schoolName"] == SCHOOL_NAME]
    else:
        teams = rankings

    # 附上题目 ID 列表供逐题遍历
    for t in teams:
        t["_problem_ids"] = problem_ids

    print(f"共 {len(teams)} 支队伍，{len(problem_letters)} 道题（{problem_letters[0]}~{problem_letters[-1]}）")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    build_excel(teams, problem_letters, output_path)
    print(f"已保存: {output_path}")


if __name__ == "__main__":
    main()
