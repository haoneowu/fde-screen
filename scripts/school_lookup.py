#!/usr/bin/env python3
"""2025学校榜单离线精确查询；只返回院校排名证据，不作录用决定。

Owner: APU Workshop
Updated: 2026-10-07
Change Log: 2026-10-07 Initial exact-match lookup, fail-closed routing.
"""
import argparse
import csv
import json
import re
import unicodedata
from pathlib import Path

REFERENCE = Path(__file__).resolve().parents[1] / "references"


def normalize(name):
    # 不删除“学院/校区”等实体区分词，不做包含、拼音或相似度匹配。
    return " ".join(unicodedata.normalize("NFKC", name).split()).casefold()


def rank_bounds(rank):
    text = rank.strip().lstrip("=").replace("–", "-")
    if re.fullmatch(r"\d+", text):
        return int(text), int(text)
    if re.fullmatch(r"\d+\+", text):
        return int(text[:-1]), float("inf")
    if re.fullmatch(r"\d+-\d+", text):
        low, high = map(int, text.split("-"))
        return (low, high) if low <= high else (None, None)
    return None, None


def lookup(scope, school):
    path = REFERENCE / ("schools-2025-cn.csv" if scope == "domestic" else "schools-2025-qs.csv")
    base = {"input": school, "scope": scope, "ranking_year": 2025,
            "source_file": str(path), "g1": "待核验", "ranking_status": "unmatched",
            "note": "仅学校排名查询；G1仍需确认初始高等教育路径、就读实体及榜单归属。"}
    if not normalize(school):
        base["reason"] = "学校名为空；不得通过。"
        return base
    if not path.exists():
        base.update(ranking_status="data_unavailable", reason="离线表缺失；不得通过或用其他年份替代。")
        return base
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    key = normalize(school)
    matches = [r for r in rows if key in {normalize(r.get("name", "")), normalize(r.get("name_en", ""))}]
    if len(matches) != 1:
        base.update(ranking_status="ambiguous" if matches else "unmatched",
                    reason="未唯一精确匹配；核全称/原文校名/历史更名/校区，不继承母体排名，不进通过名单。")
        return base
    row = matches[0]
    base["match"] = row
    if scope == "overseas":
        country = normalize(row.get("country", ""))
        if country in {"china", "mainland china", "china (mainland)", "中国", "中国大陆"}:
            base.update(ranking_status="wrong_scope", reason="国内院校须查国内主榜，不能凭QS绕过国内门槛。")
            return base
        if not country or any(x in country for x in ["hong kong", "macao", "macau", "taiwan", "香港", "澳门", "台湾"]):
            base.update(ranking_status="scope_review", reason="港澳台或归属不明；按现行G1先请使用者确认，不自动归入海外。")
            return base
    low, high = rank_bounds(row["rank"])
    if low is None:
        base.update(ranking_status="rank_unresolved", reason="无法解析名次；不得通过。")
    elif high <= 150:
        base.update(ranking_status="within_top150", reason="2025榜单名次符合；不等于G1已通过，需核初始路径及实际就读实体。")
    elif low > 150:
        base.update(ranking_status="outside_top150", g1="不通过（确认初始本科实体匹配时）",
                    reason="2025指定榜单明确超过150；列入确认不符队列，不用工作经验或后续学历补偿。")
    else:
        base.update(ranking_status="rank_unresolved", reason="排名区间跨越150边界；待核验，不自动通过。")
    return base


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=["domestic", "overseas"], required=True)
    parser.add_argument("schools", nargs="+", help="学校完整名称；多个校名分别加引号")
    args = parser.parse_args()
    print(json.dumps([lookup(args.scope, school) for school in args.schools], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
