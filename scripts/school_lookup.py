#!/usr/bin/env python3
"""2025学校榜单离线精确查询；只返回院校排名证据，不作录用决定。

Owner: APU Workshop
Updated: 2026-10-11
Change Log: 2026-10-11 Add domestic outside-CN100 / QS-unmatched policy evidence.
"""
import argparse
import csv
import hashlib
import io
import json
import re
import unicodedata
from pathlib import Path

REFERENCE = Path(__file__).resolve().parents[1] / "references"
DATA_HASHES = {
    "domestic": "5a29751540f8ed69a9742eb96dc97d6cddd30b7a0824f6fc9124643dcc4d0ee9",
    "overseas": "1da69f0adbd32100390ec58ad30ccc525f28f970c84fca6b14feab050029158c",
}


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
            "note": "仅单榜证据；国内须结合另一榜，海外实体已确认时按QS150；还需检查其余就读学校。"}
    if not normalize(school):
        base["reason"] = "学校名为空；不得通过。"
        return base
    if not path.exists():
        base.update(ranking_status="data_unavailable", reason="离线表缺失；不得通过或用其他年份替代。")
        return base
    try:
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != DATA_HASHES[scope]:
            raise ValueError("离线表完整性校验失败")
        rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    except (OSError, UnicodeError, ValueError, csv.Error):
        base.update(ranking_status="data_unavailable", reason="离线表读取或完整性校验失败；待核验，不视为未命中。")
        return base
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
                    reason="本榜超过门槛；国内须结合另一榜，海外实体已确认时QS超过150可判排名项不通过。")
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
    qs_country = evidence[1].get("match", {}).get("country", "")
    overseas_outside = (evidence[1]["ranking_status"] == "outside_cutoff"
                        and qs_country and qs_country != "China (Mainland)")
    status = ("ambiguous" if "ambiguous" in statuses else
              "within_cutoff" if "within_cutoff" in statuses else
              "outside_both_cutoffs" if statuses == {"outside_cutoff"} else
              "overseas_outside_qs" if overseas_outside else
              "domestic_outside_qs_unmatched" if evidence[0]["ranking_status"] == "outside_cutoff"
              and evidence[1]["ranking_status"] == "unmatched" else "pending_verification")
    return {"input": school, "ranking_year": 2025, "ranking_status": status,
            "g1": "不通过（确认实际就读实体匹配时）" if status in {"outside_both_cutoffs", "domestic_outside_qs_unmatched", "overseas_outside_qs"} else "待核验",
            "evidence": evidence,
            "note": "国内软科超过100且QS150未命中按规则否；须确认实体明确、表正常读取。海外按QS150，不因缺软科而否。逐校核验已列学历、专科直接否。本工具只查校名，空输入不证明简历未写学校；须完整读取后由审阅者判定。"}


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
