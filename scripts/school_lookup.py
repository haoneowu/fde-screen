#!/usr/bin/env python3
"""2025学校榜单离线精确查询；只返回院校排名证据，不作录用决定。

Owner: APU Workshop
Updated: 2026-10-11
Change Log: 2026-10-11 Apply CN100/QS150 thresholds and neutral status names.
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
    cutoff = 100 if scope == "domestic" else 150
    base = {"cutoff": cutoff, "input": school, "scope": scope, "ranking_year": 2025,
            "source_file": str(path), "g1": "待核验", "ranking_status": "unmatched",
            "note": "仅单榜证据；单榜超门槛不能判整体fail；还需检查其余就读学校。"}
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
    low, high = rank_bounds(row["rank"])
    if low is None:
        base.update(ranking_status="rank_unresolved", reason="无法解析名次；不得通过。")
    elif high <= cutoff:
        base.update(ranking_status="within_cutoff", reason="2025本榜名次符合；不等于所有已列学历学校及无专科条件均通过。")
    elif low > cutoff:
        base.update(ranking_status="outside_cutoff",
                    reason="本榜超过门槛；须检查另一榜，不能据此单独判G1不通过。")
    else:
        base.update(ranking_status="rank_unresolved", reason="排名区间跨越本榜门槛；待核验，不自动通过。")
    return base


def lookup_either(school):
    # 只用表内同一条学校记录提供的官方中英文名跨表查询，不猜译名。
    names = {school}
    for scope in ("domestic", "overseas"):
        match = lookup(scope, school).get("match", {})
        names.update(match[k] for k in ("name", "name_en") if match.get(k))
    evidence = []
    for scope in ("domestic", "overseas"):
        results = [lookup(scope, name) for name in sorted(names)]
        matched = [r for r in results if "match" in r]
        if len({r["match"]["name"] for r in matched}) > 1 or any(r["ranking_status"] == "ambiguous" for r in results):
            result = lookup(scope, school)
            result.update(ranking_status="ambiguous", reason="存在同名或跨表实体歧义，须人工核验。")
        else:
            result = matched[0] if matched else results[0]
        evidence.append(result)
    statuses = {r["ranking_status"] for r in evidence}
    status = ("ambiguous" if "ambiguous" in statuses else
              "within_cutoff" if "within_cutoff" in statuses else
              "outside_both_cutoffs" if statuses == {"outside_cutoff"} else "pending_verification")
    return {"input": school, "ranking_year": 2025, "ranking_status": status,
            "g1": "不通过（确认实际就读实体匹配时）" if status == "outside_both_cutoffs" else "待核验",
            "evidence": evidence,
            "note": "软科前100或QS前150仅满足该校排名项；逐校核验已列本科/硕士/博士，出现本人专科直接不通过，只认实际就读实体，不继承合作方/授予方排名。未匹配不等于已证实两榜均不达标。"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=["either", "domestic", "overseas"], default="either",
                        help="默认either查双榜；domestic/overseas仅保留单榜证据查询，不作地域限制")
    parser.add_argument("schools", nargs="+", help="学校完整名称；多个校名分别加引号")
    args = parser.parse_args()
    print(json.dumps([lookup_either(school) if args.scope == "either" else lookup(args.scope, school)
                      for school in args.schools], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
