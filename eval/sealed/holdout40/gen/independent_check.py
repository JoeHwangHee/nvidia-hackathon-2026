"""holdout40 독립 자체 검산(병렬 개발 규칙 §6.6의 1). 봉인 폴더 안에만 둔다.

표준 라이브러리만 쓴다. 생성 스크립트(generate.py), 저장소 생성 도구(eval/datagen/dev20.py), 런타임 모듈(tradesentry.*)을
import하지 않는다. 생성된 응답 XML·수집 계획·요청 결과 기록·비교국 표만 다시 읽어, 자료 계약 §2.3.2 행 규칙과 §11.2
공식, configs/policy_v1.json 기준값(최소 기준 U2, 정확값 비교와 경계 포함 U3, 반올림 불안정 U4, U1=θ)으로 모든 계열·달의
단가 변화율과 점유율 변화를 계산해 정답표와 대조한다. 부모 원본 계열 ID는 생성 규칙의 기본 값과 흔들림 식(명세 §6,
생성 규칙 noise)을 따로 구현해 다시 계산하고, 사건이 닿지 않은 모든 (계열, 달)에서 그 기본 값이 응답 XML과 같은지로
생성 자료에 묶는다.

사용: python independent_check.py --bundle <holdout40 폴더> --repo <저장소 작업 폴더> [--verbose]
출력: 건수와 검사 이름·통과 여부(JSON). --verbose일 때만 위반 내용(값 포함)을 표준 오류에 쓴다.
종료 코드: 모두 통과 0, 하나라도 실패 1.
"""
import argparse
import csv
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path

MARGIN = Fraction(5, 100)
HALF = Fraction(1, 2)
CLASS_ALLOCATION = {1: 6, 2: 6, 3: 4, 4: 4, 5: 4, 6: 4, 7: 4, 8: 4, 9: 2, 10: 2}
RULE_TABLE = {
    "unit_value": {
        "composition_explained": ("MONITOR", ["parent_child_match_V_and_Q", "weight_share_decomposition",
                                              "per_child_unit_value_stable", "comparability_ok"]),
        "unexplained": ("MAINTAIN", ["parent_child_match_V_and_Q", "weight_share_decomposition",
                                     "partner_comparison_done", "comparability_ok"]),
        "hold_missing": ("HOLD", ["missingness_listed", "failure_vs_not_collected_distinguished", "no_zero_fill"]),
        "hold_inconsistent": ("HOLD", ["parent_child_match_V_and_Q", "comparability_ok", "no_zero_fill"]),
        "rounding_unstable": ("HOLD", ["precision_sensitivity_shown"]),
    },
    "share": {
        "unexplained": ("MAINTAIN", ["country_and_world_change_shown", "partner_comparison_done",
                                     "comparability_ok"]),
        "hold_missing": ("HOLD", ["missingness_listed", "failure_vs_not_collected_distinguished", "no_zero_fill"]),
        "hold_inconsistent": ("HOLD", ["country_and_world_change_shown", "comparability_ok", "no_zero_fill"]),
    },
}


def shift(month, delta):
    index = int(month[:4]) * 12 + int(month[4:]) - 1 + delta
    return f"{index // 12}{index % 12 + 1:02d}"


def months_between(start, end):
    out, m = [], start
    while m <= end:
        out.append(m)
        m = shift(m, 1)
    return out


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


class Checker:
    def __init__(self, bundle, repo, verbose):
        self.bundle, self.repo, self.verbose = Path(bundle), Path(repo), verbose
        self.results = []

    def check(self, name, ok, detail=None, count=None):
        self.results.append({"name": name, "ok": bool(ok), **({"count": count} if count is not None else {})})
        if not ok and self.verbose and detail:
            print(f"[{name}] {detail}", file=sys.stderr)

    # ------------------------------------------------------------------ 원천 읽기
    def read_source(self):
        src = self.bundle / "input" / "source"
        self.manifest = load(src / "manifest.json")
        log = load(src / "collection_log.json")
        failed, not_collected = set(log["FAILED"]), set(log["NOT_COLLECTED"])
        config = self.manifest["config"]
        self.hs6 = list(config["hs6"])
        self.partners = list(config["partners"])
        self.months = months_between(config["period"]["start"], config["period"]["end"])
        raw_dir = src / "raw"
        present = sorted(p.name for p in raw_dir.glob("*.xml"))
        # raw 결합 해시(shasum -a 256 raw/*.xml | shasum -a 256)
        lines = "".join(f"{hashlib.sha256((raw_dir / n).read_bytes()).hexdigest()}  raw/{n}\n" for n in present)
        combined = hashlib.sha256(lines.encode("utf-8")).hexdigest()
        recorded = load(src / "snapshot_hash.json")
        self.check("raw_combined_hash", combined == recorded["raw_combined_sha256"]
                   and len(present) == recorded["raw_files"])
        self.raw_combined = combined
        ok_ids = {r["request_id"] for r in self.manifest["requests"]} - failed - not_collected
        self.check("raw_files_match_ok_requests", set(present) == {f"{r}.xml" for r in ok_ids})
        self.parent, self.children, self.child_missing, self.world = {}, {}, {}, {}
        world_rank = {}
        conflicts = 0
        for req in self.manifest["requests"]:
            rid, params, purpose = req["request_id"], req["params"], req["purpose"]
            partner, code = params.get("cntyCd", "ALL"), params["hsSgn"]
            status = "FAILED" if rid in failed else "NOT_COLLECTED" if rid in not_collected else "OK"
            items = []
            if status == "OK":
                root = ET.fromstring((raw_dir / f"{rid}.xml").read_bytes())
                if root.findtext("header/resultCode") != "00":
                    self.check("result_code", False, rid)
                for item in root.iter("item"):
                    items.append({child.tag: (child.text or "") for child in item})
            seen = set()
            for item in items:
                month = item["year"].replace(".", "")
                if not (len(month) == 6 and month.isdigit()):
                    continue  # 총계 행
                seen.add(month)
                hs = item.get("hsCd") or item.get("hsCode")
                pair = (int(item["impDlr"]), int(item["impWgt"]))
                if purpose == "hs4_partner_monthly":
                    self.parent[(hs, partner, month)] = pair
                elif purpose == "hs6_partner_monthly":
                    self.children.setdefault((code, partner, month), {})[hs[6:]] = pair
                else:
                    held = self.world.setdefault((hs[:6], month), {})
                    if hs in held and held[hs] != pair:
                        conflicts += 1
                    if world_rank.get((hs, month), -1) <= len(code):
                        held[hs] = pair
                        world_rank[(hs, month)] = len(code)
            if purpose == "hs6_partner_monthly":
                for month in req["months"]:
                    if status != "OK":
                        self.child_missing[(code, partner, month)] = \
                            "REQUEST_FAILED" if status == "FAILED" else "NOT_COLLECTED"
                    elif month not in seen:
                        self.child_missing[(code, partner, month)] = "UNRESOLVED_ZERO"
        self.check("all_duplicate_rows_agree", conflicts == 0, count=conflicts)
        missing_parent = sum(1 for h in self.hs6 for p in self.partners for m in self.months
                             if (h, p, m) not in self.parent)
        self.check("no_missing_parent_rows", missing_parent == 0, count=missing_parent)
        missing_world = sum(1 for h in self.hs6 for m in self.months if not self.world.get((h, m)))
        self.check("no_missing_world_rows", missing_world == 0, count=missing_world)

    # ------------------------------------------------------------------ 지표
    def uv(self, h, p, m):
        v, q = self.parent[(h, p, m)]
        return None if q == 0 else Fraction(v, q)

    def world_value(self, h, m):
        rows = self.world.get((h, m))
        return None if not rows else sum(v for v, _ in rows.values())

    def r_u(self, h, p, t):
        u0, u1 = self.uv(h, p, shift(t, -12)), self.uv(h, p, t)
        return None if u0 is None or u1 is None or u0 == 0 else (u1 / u0 - 1) * 100

    def d_s(self, h, p, t):
        b = shift(t, -12)
        w0, w1 = self.world_value(h, b), self.world_value(h, t)
        if not w0 or not w1:
            return None
        return (Fraction(self.parent[(h, p, t)][0], w1) - Fraction(self.parent[(h, p, b)][0], w0)) * 100

    def decompose(self, h, p, t):
        b = shift(t, -12)
        if any((h, p, m) in self.child_missing for m in (b, t)):
            return {"ok": False, "reason": "child_missing"}
        k0, k1 = self.children.get((h, p, b), {}), self.children.get((h, p, t), {})
        if not k0 or set(k0) != set(k1):
            return {"ok": False, "reason": "code_set_changed"}
        for m, kids in ((b, k0), (t, k1)):
            v, q = self.parent[(h, p, m)]
            if sum(x for x, _ in kids.values()) != v:
                return {"ok": False, "reason": "amount_mismatch"}
            if abs(sum(y for _, y in kids.values()) - q) > self.tol * (len(kids) + 1):
                return {"ok": False, "reason": "weight_mismatch"}
            if any(y == 0 for _, y in kids.values()):
                return {"ok": False, "reason": "zero_weight_child"}
        q0, q1 = sum(y for _, y in k0.values()), sum(y for _, y in k1.values())
        u0 = {c: Fraction(x, y) for c, (x, y) in k0.items()}
        u1 = {c: Fraction(x, y) for c, (x, y) in k1.items()}
        w0 = {c: Fraction(y, q0) for c, (_, y) in k0.items()}
        w1 = {c: Fraction(y, q1) for c, (_, y) in k1.items()}
        within = sum((w0[c] + w1[c]) / 2 * (u1[c] - u0[c]) for c in u0)
        mix = sum((u0[c] + u1[c]) / 2 * (w1[c] - w0[c]) for c in u0)
        delta = self.uv(h, p, t) - self.uv(h, p, b)
        return {"ok": True, "within": within, "mix": mix, "residual": delta - within - mix,
                "U0": self.uv(h, p, b), "child_r": {c: (u1[c] / u0[c] - 1) * 100 for c in u0}}

    def rounding(self, h, p, t):
        (v0, q0), (v1, q1) = self.parent[(h, p, shift(t, -12))], self.parent[(h, p, t)]
        if q0 - HALF <= 0 or q1 - HALF <= 0:
            return True, None
        r = self.r_u(h, p, t)
        if r >= 0:
            low = ((Fraction(v1) / (q1 + HALF)) / (Fraction(v0) / (q0 - HALF)) - 1) * 100
            return low < self.theta_u, abs(low - self.theta_u)
        high = ((Fraction(v1) / (q1 - HALF)) / (Fraction(v0) / (q0 + HALF)) - 1) * 100
        return high > -self.theta_u, abs(high + self.theta_u)

    # ------------------------------------------------------------------ 검사
    def run(self):
        policy = load(self.repo / "configs" / "policy_v1.json")
        self.theta_u = Fraction(policy["thresholds"]["unit_value"])
        self.theta_s = Fraction(policy["thresholds"]["share"])
        self.min_amount, self.min_weight = policy["min_amount"], policy["min_weight"]
        self.tol = Fraction(str(policy["tolerance"]["weight_rounding_kg"]))
        self.read_source()
        cases_doc = load(self.bundle / "input" / "cases.json")
        answers = load(self.bundle / "answers" / "answers.json")
        ids_doc = load(self.bundle / "answers" / "parent_series_ids.json")
        rules = load(self.bundle / "answers" / "generation_rules.json")
        build = load(self.bundle / "input" / "source" / "snapshot_build.json")
        self.check("dataset_fields", cases_doc["dataset"] == answers["dataset"] == "holdout40"
                   and cases_doc["snapshot_id"] == answers["snapshot_id"] == "holdout40"
                   and cases_doc["policy_version"] == answers["policy_version"] == rules["policy_version"]
                   == "policy_v1")
        self.check("schema_version_matches_policy_file", len({cases_doc["schema_version"], answers["schema_version"],
                   ids_doc["schema_version"], rules["schema_version"], build["schema_version"],
                   policy["schema_version"]}) == 1)
        self.check("normalized_sha256_matches_build",
                   cases_doc.get("snapshot_normalized_sha256") == build["normalized_sha256"]
                   and build["raw_sha256"] == self.raw_combined)
        self.check("thresholds_match_policy", answers.get("thresholds") == {
            "unit_value": policy["thresholds"]["unit_value"], "share": policy["thresholds"]["share"]})
        cases = {(c["hs6"], c["partner"], c["month"]): c for c in cases_doc["cases"]}
        by_id = {a["case_id"]: a for a in answers["cases"]}
        self.check("case_ids_match", set(by_id) == {c["case_id"] for c in cases_doc["cases"]}
                   and len(by_id) == len(answers["cases"]) == len(cases_doc["cases"])
                   and all(c["case_id"] == f"{c['hs6']}-{c['partner']}-{c['month']}" for c in cases_doc["cases"]))
        self.check("cases_sorted_by_id", [c["case_id"] for c in cases_doc["cases"]]
                   == sorted(c["case_id"] for c in cases_doc["cases"]))

        # 1) 모든 계열·달의 발동 계산(최소 기준 적용), 기준 거리
        triggered, near, below_min_exceed = {}, [], 0
        nearest = None
        for h in self.hs6:
            for p in self.partners:
                for t in self.months:
                    b = shift(t, -12)
                    if b not in self.months:
                        continue
                    r, d = self.r_u(h, p, t), self.d_s(h, p, t)
                    for fam, val, theta in (("unit_value", r, self.theta_u), ("share", d, self.theta_s)):
                        if val is None:
                            continue
                        gap = abs(abs(val) - theta)
                        nearest = gap if nearest is None else min(nearest, gap)
                        if gap < MARGIN:
                            near.append((h, p, t, fam))
                        if abs(val) >= theta:
                            if fam == "unit_value":
                                (v0, q0), (v1, q1) = self.parent[(h, p, b)], self.parent[(h, p, t)]
                                if min(v0, v1) < self.min_amount or min(q0, q1) < self.min_weight:
                                    below_min_exceed += 1
                                    continue
                            triggered.setdefault((h, p, t), set()).add(fam)
        extra = sorted(set(triggered) - set(cases))
        self.check("no_alert_outside_cases", not extra, extra[:5], count=len(extra))
        self.check("unit_exceedance_below_minimum_zero", below_min_exceed == 0, count=below_min_exceed)
        self.check("margin_all_values", not near, near[:5], count=len(near))

        # 2) 사례별 발동 여부와 규칙별 자료 불변식
        peers = {}
        with open(self.bundle / "input" / "source" / "peer_group_holdout40.csv", encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                peers.setdefault((row["scope_id"], row["entity_id"]), []).append((int(row["peer_rank"]),
                                                                                 row["peer_id"]))
        # 비교국 표 재계산(g0: 기준연도 부모 금액 상위 k, 같으면 코드순)
        k, year = rules["world"]["peer_k"], str(rules["world"]["peer_source_year"])
        peer_ok = True
        for h in self.hs6:
            for p in self.partners:
                sums = {q: sum(self.parent[(h, q, m)][0] for m in self.months if m.startswith(year))
                        for q in self.partners if q != p}
                want = sorted(sums, key=lambda q: (-sums[q], q))[:k]
                got = [q for _, q in sorted(peers.get((h, p), []))]
                peer_ok &= got == want
        self.check("peer_table_recomputed", peer_ok)

        mismatched_signals, invariant_bad, unstable_bad, interval_near = [], [], [], []
        class_count = {}
        for key, case in cases.items():
            h, p, t = key
            b = shift(t, -12)
            ans = by_id[case["case_id"]]
            klass = ans["scenario_class"]
            class_count[klass] = class_count.get(klass, 0) + 1
            got = {f: ("TRIGGERED" if f in triggered.get(key, set()) else "NOT_TRIGGERED")
                   for f in ("unit_value", "share")}
            if got != ans["expected"]["signals"]:
                mismatched_signals.append(case["case_id"])
                continue
            # 기대 판정이 규칙표와 맞는지
            rule = ans["rule"]
            for fam in ("unit_value", "share"):
                if (rule[fam] is None) != (got[fam] == "NOT_TRIGGERED"):
                    invariant_bad.append((case["case_id"], "rule_vs_signal", fam))
                elif rule[fam] is not None and ans["expected"]["signal_status"][fam] != RULE_TABLE[fam][rule[fam]][0]:
                    invariant_bad.append((case["case_id"], "status", fam))
            peer_list = [q for _, q in sorted(peers.get((h, p), []))]
            peers_obs = all((h, q, m) in self.parent for q in peer_list for m in (b, t)) and peer_list
            u_rule, s_rule = rule["unit_value"], rule["share"]
            if got["unit_value"] == "TRIGGERED":
                unstable, gap = self.rounding(h, p, t)
                if unstable != (u_rule == "rounding_unstable"):
                    unstable_bad.append(case["case_id"])
                if gap is not None and gap < MARGIN:
                    interval_near.append(case["case_id"])
                dec = self.decompose(h, p, t)
                theta_frac = self.theta_u / 100
                if u_rule == "composition_explained":
                    ok = dec["ok"] and dec["within"] == 0 and dec["residual"] == 0 \
                        and all(r == 0 for r in dec["child_r"].values())
                elif u_rule == "unexplained":
                    ok = dec["ok"] and abs(dec["within"] + dec["residual"]) >= (theta_frac + MARGIN / 100) * dec["U0"] \
                        and any(abs(r) >= self.theta_u + MARGIN for r in dec["child_r"].values()) and peers_obs
                elif u_rule == "hold_missing":
                    ok = any(self.child_missing.get((h, p, m)) in ("REQUEST_FAILED", "NOT_COLLECTED") for m in (b, t))
                elif u_rule == "hold_inconsistent":
                    ok = not dec["ok"] and dec["reason"] in ("code_set_changed", "amount_mismatch", "weight_mismatch",
                                                             "zero_weight_child") \
                        and not any((h, p, m) in self.child_missing for m in (b, t))
                else:  # rounding_unstable
                    ok = True
                if not ok:
                    invariant_bad.append((case["case_id"], "unit_rule", u_rule, dec.get("reason")))
            if got["share"] == "TRIGGERED":
                totals = [self.world_value(h, m) for m in (b, t)]
                covered = [sum(self.parent[(h, q, m)][0] for q in self.partners) for m in (b, t)]
                if s_rule == "unexplained":
                    ok = all(w >= c for w, c in zip(totals, covered)) and peers_obs
                elif s_rule == "hold_inconsistent":
                    ok = any(w < self.parent[(h, p, m)][0] for w, m in zip(totals, (b, t)))
                else:
                    ok = False
                if not ok:
                    invariant_bad.append((case["case_id"], "share_rule", s_rule))
            if klass == 3:
                target = self.r_u(h, p, t)
                moves = [self.r_u(h, q, t) for q in peer_list]
                if not moves or any(r is None or r * target <= 0 or abs(r) * 2 < self.theta_u for r in moves):
                    invariant_bad.append((case["case_id"], "class3_peers"))
            if klass in (7, 8):
                r = self.r_u(h, p, t)
                if r is None or abs(r) >= self.theta_u:
                    invariant_bad.append((case["case_id"], "class78_unit"))
            if klass == 9:
                sums = [(sum(self.parent[(g, p, m)][0] for g in self.hs6), sum(self.parent[(g, p, m)][1]
                                                                                for g in self.hs6)) for m in (b, t)]
                ratio = (Fraction(*sums[1]) / Fraction(*sums[0]) - 1) * 100
                if abs(ratio) * 2 >= self.theta_u:
                    invariant_bad.append((case["case_id"], "class9_hs4"))
            if klass == 10:
                st = ans["expected"]["signal_status"]
                if not (got["unit_value"] == got["share"] == "TRIGGERED" and st["unit_value"] != st["share"]):
                    invariant_bad.append((case["case_id"], "class10"))
        self.check("case_signals_equal_expected", not mismatched_signals, mismatched_signals[:5],
                   count=len(mismatched_signals))
        self.check("rule_invariants", not invariant_bad, invariant_bad[:5], count=len(invariant_bad))
        self.check("rounding_unstable_only_for_rule", not unstable_bad, unstable_bad[:5], count=len(unstable_bad))
        self.check("rounding_interval_margin", not interval_near, interval_near[:5], count=len(interval_near))
        self.check("class_counts", class_count == CLASS_ALLOCATION and len(cases) == 40, class_count,
                   count=len(cases))

        # 3) 부모 원본 계열 ID 재계산(생성 규칙의 기본 값 + 흔들림 식)과 생성 자료 묶기
        world = rules["world"]
        noise = world["noise"]

        def rnd(x):
            return int(x + HALF)

        def digest(*parts):
            return int(hashlib.sha256(":".join(str(p) for p in parts).encode("utf-8")).hexdigest(), 16)

        def noisy(level, *key):
            v, q = level
            qp, pp = noise["quantity_permille"], noise["price_permille"]
            qf = 1 + Fraction(digest(noise["seed"], "q", *key) % (2 * qp + 1) - qp, 1000)
            pf = 1 + Fraction(digest(noise["seed"], "p", *key) % (2 * pp + 1) - pp, 1000)
            if q == 0:
                return rnd(v * pf), 0
            qq = rnd(q * qf)
            return rnd(Fraction(v, q) * pf * qq), qq

        base = {}
        for h in self.hs6:
            owners = [(p, world["series"][h][p]) for p in self.partners] + [("ROW", world["rest_of_world"][h])]
            for who, levels in owners:
                for m in self.months:
                    base[(h, who, m)] = {s: noisy(tuple(levels[s]), h, who, s, m) for s in sorted(levels)}
        touched_series, touched_world, touched_parent = set(), set(), set()
        for c in rules["cases"]:
            h, p = c["hs6"], c["partner"]
            for ev in c["events"]:
                kind = ev["type"]
                if kind == "request":
                    for m in self.months:
                        if m.startswith(ev["strtYymm"][:4]):
                            touched_series.add((ev["hsSgn"], ev["cntyCd"], m))
                    continue
                m = ev["month"]
                if kind in ("exact", "children"):
                    touched_series.add((h, p, m))
                    touched_world.add((h, m))
                elif kind == "scale":
                    for who in ev["who"]:
                        touched_series.add((h, who, m))
                    touched_world.add((h, m))
                elif kind == "parent":
                    touched_parent.add((h, p, m))
                elif kind == "world":
                    touched_world.add((h, m))
        diff_child, diff_parent, diff_world, compared = 0, 0, 0, 0
        for h in self.hs6:
            for m in self.months:
                for p in self.partners:
                    key = (h, p, m)
                    if key in touched_series:
                        continue
                    compared += 1
                    kids = {s: tuple(v) for s, v in self.children.get(key, {}).items()}
                    if kids != base[key]:
                        diff_child += 1
                    if key not in touched_parent:
                        want = (sum(v for v, _ in base[key].values()), sum(q for _, q in base[key].values()))
                        if self.parent[key] != want:
                            diff_parent += 1
                if (h, m) not in touched_world:
                    acc = {}
                    for who in self.partners + ["ROW"]:
                        for s, (v, q) in base[(h, who, m)].items():
                            a = acc.setdefault(h + s, [0, 0])
                            a[0] += v
                            a[1] += q
                    if {c: tuple(x) for c, x in acc.items()} != {c: tuple(x) for c, x in self.world[(h, m)].items()}:
                        diff_world += 1
        self.check("base_series_reproduce_xml_on_untouched_months", diff_child == diff_parent == diff_world == 0
                   and compared > 0, (diff_child, diff_parent, diff_world), count=compared)
        recomputed = {}
        for c in rules["cases"]:
            h, p = c["hs6"], c["partner"]
            suffixes = sorted(world["series"][h][p])
            doc = {"children": {s: [list(base[(h, p, m)][s]) for m in self.months] for s in suffixes},
                   "parent": [[sum(base[(h, p, m)][s][i] for s in suffixes) for i in (0, 1)] for m in self.months],
                   "period": {"start": world["period"]["start"], "end": world["period"]["end"]}}
            text = json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            recomputed[c["case_id"]] = "ps_" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        id_bad = [cid for cid, pid in recomputed.items() if by_id[cid]["parent_series_id"] != pid]
        self.check("parent_series_ids_recomputed", not id_bad and set(recomputed) == set(by_id), id_bad[:5],
                   count=len(recomputed))
        self.check("parent_series_ids_file", ids_doc["parent_series_ids"] == sorted(set(recomputed.values()))
                   and ids_doc["dataset"] == "holdout40")
        # 사례 목록의 사례가 생성 규칙의 사례와 같은지
        self.check("rules_cases_match", {c["case_id"] for c in rules["cases"]} == set(by_id))

        # 4) dev20과 겹침·구조 구별
        dev_ids = set(load(self.repo / "eval/dev/dev20/answers/parent_series_ids.json")["parent_series_ids"])
        overlap = len(dev_ids & set(recomputed.values()))
        self.check("dev20_parent_id_overlap_zero", overlap == 0, count=overlap)
        dev_rules = load(self.repo / "eval/dev/dev20/answers/generation_rules.json")

        def shapes(levels_by_owner):
            out = set()
            for levels in levels_by_owner:
                tv = sum(v for v, _ in levels.values())
                tq = sum(q for _, q in levels.values())
                shape = tuple(sorted((round(float(Fraction(v, q) / Fraction(tv, tq)), 2) if q else None,
                                      round(q / tq, 2)) for v, q in levels.values()))
                out.add(shape)
            return out

        dev_levels = [lv for h in dev_rules["world"]["series"].values() for lv in h.values()]
        hold_levels = [lv for h in world["series"].values() for lv in h.values()]
        dev_suffix_sets = {tuple(sorted(lv)) for lv in dev_levels}
        hold_suffix_sets = {tuple(sorted(lv)) for lv in hold_levels}
        same_shape = len(shapes(dev_levels) & shapes(hold_levels))
        self.check("structure_distinct_from_dev20", not (dev_suffix_sets & hold_suffix_sets) and same_shape == 0,
                   count=same_shape)
        self.check("holdout_series_ids_distinct", len(set(recomputed.values())) == len(recomputed))
        dev_partners = set(dev_rules["world"]["partners"])
        self.check("partners_distinct_from_dev20", not (dev_partners & set(self.partners)))

        # 5) 합성 상대국 코드가 실제 국가코드 목록에 없다
        strings = set()

        def walk(x):
            if isinstance(x, str):
                strings.add(x.strip())
            elif isinstance(x, list):
                for y in x:
                    walk(y)
            elif isinstance(x, dict):
                for kk, y in x.items():
                    walk(kk)
                    walk(y)

        walk(load(self.repo / "data/reference/kcs_country_codes.json"))
        with open(self.repo / "data/reference/country_map.csv", encoding="utf-8", newline="") as fh:
            for row in csv.reader(fh):
                strings.update(cell.strip() for cell in row)
        clash = sorted(set(self.partners) & strings)
        self.check("partners_not_real_country_codes", not clash and "XK" not in self.partners
                   and all(len(p) == 2 and p[0] == "X" for p in self.partners), count=len(clash))

        return {"ok": all(r["ok"] for r in self.results), "cases": len(cases),
                "class_counts": {str(k2): class_count.get(k2, 0) for k2 in sorted(CLASS_ALLOCATION)},
                "alerts_outside_cases": len(extra), "dev20_overlap": overlap,
                "min_distance_at_least_0_05": nearest is not None and nearest >= MARGIN and not interval_near,
                "checks": self.results}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)
    report = Checker(args.bundle, args.repo, args.verbose).run()
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
