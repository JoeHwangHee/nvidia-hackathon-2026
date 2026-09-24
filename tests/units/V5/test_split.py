"""단위 V5(datagen_split) 동작 시험: 순위 값 형식, 개수와 HS6 층별 배정, 결정성, 입력 검사, 수집 설정 도우미.

- 합성 키만 쓴다(실제 품목·국가가 아니다): HS6은 99로 시작하는 6자리, 상대국은 X로 시작하는 두 글자(XK는 뺐다).
  실제 64개 시계열로 run을 부르는 곳은 골든 쌍(input.json·expected.json, test_golden.py)뿐이다.
- 순위 값과 그 순서의 기대치는 이 모듈의 코드가 아니라 shasum -a 256으로 따로 계산해 적었다.
- 수집 설정 시험(CollectionPlanTest)은 추적 파일 configs/collection_plan.json과 골든 입력만 읽고 run은 부르지 않는다.
"""
import json
import unittest
from decimal import Decimal
from pathlib import Path
from unittest import mock

from eval.datagen import split

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SNAPSHOT = "synthetic_split_v0"
RATIO = {"real_dev": 1, "real_sealed": 2}
HS6_CODES = ["990001", "990002", "990003", "990004"]
PARTNERS = ["XA", "XB", "XC", "XD", "XE", "XF", "XG", "XH", "XI", "XJ", "XL", "XM", "XN", "XO", "XP", "XQ"]


def grid(hs6_codes: list[str], partners: list[str]) -> list[dict[str, str]]:
    return [{"hs6": hs6, "partner": partner} for hs6 in hs6_codes for partner in partners]


def make_input(series: list[dict[str, str]], seed: int = 7, ratio: dict[str, int] | None = None,
               snapshot_id: str = SNAPSHOT) -> dict[str, object]:
    return {"snapshot_id": snapshot_id, "seed": seed, "ratio": dict(ratio or RATIO), "series": series}


def keyset(items: list[dict[str, str]]) -> set[tuple[str, str]]:
    return {(item["hs6"], item["partner"]) for item in items}


def per_hs6(items: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        counts[item["hs6"]] = counts.get(item["hs6"], 0) + 1
    return counts


class DigestTest(unittest.TestCase):
    """순위 값의 메시지 형식을 고정한다."""

    def test_message_format_is_pinned(self):
        # shasum -a 256 으로 계산: printf '%s' '7:synthetic_split_v0:990001:XA' | shasum -a 256
        self.assertEqual(split.series_digest(7, SNAPSHOT, "990001", "XA"),
                         "f1173c637467881b309aec5cff51aa60a899f9dd8034aae50e23c02c9a4a03ff")


class AllocationTest(unittest.TestCase):
    """개수(내림), HS6 층별 비례 배정(최대 나머지), 남은 자리의 순서, 층 안 순위."""

    def test_single_stratum_takes_the_smallest_digests(self):
        # seed 7, 990003 × XA~XF의 순위 값 오름차순(shasum): XB, XE, XF, XD, XA, XC. 6개 중 real_dev는 2개다.
        out = split.run(make_input(grid(["990003"], ["XA", "XB", "XC", "XD", "XE", "XF"])))
        self.assertEqual(out["real_dev"], [{"hs6": "990003", "partner": "XB"}, {"hs6": "990003", "partner": "XE"}])
        self.assertEqual(keyset(out["real_sealed"]),
                         {("990003", "XA"), ("990003", "XC"), ("990003", "XD"), ("990003", "XF")})

    def test_leftover_seat_goes_to_the_stratum_with_the_smaller_next_digest(self):
        # 2 × 2 키, 1:2면 real_dev는 1개. 두 층의 몫은 0이고 나머지가 같아, 층마다 1번째 키의 순위 값이 작은 쪽이 가진다.
        # seed 7(shasum): 990001의 1번째 XB 8efb…, 990002의 1번째 XB 01c0… → 990002 XB
        # seed 8(shasum): 990001의 1번째 XB 02e9…, 990002의 1번째 XB 38cf… → 990001 XB
        series = grid(["990001", "990002"], ["XA", "XB"])
        self.assertEqual(split.run(make_input(series, seed=7))["real_dev"], [{"hs6": "990002", "partner": "XB"}])
        self.assertEqual(split.run(make_input(series, seed=8))["real_dev"], [{"hs6": "990001", "partner": "XB"}])

    def test_total_is_rounded_down_for_real_dev(self):
        keys = grid(HS6_CODES, PARTNERS)
        for total, n_dev in ((3, 1), (4, 1), (5, 1), (6, 2), (16, 5), (18, 6), (64, 21)):
            with self.subTest(total=total):
                out = split.run(make_input(keys[:total]))
                self.assertEqual((len(out["real_dev"]), len(out["real_sealed"])), (n_dev, total - n_dev))

    def test_equal_strata_like_the_real_grid(self):
        # 합성 4 × 16 = 64개. real_dev 21개를 층마다 5.25씩 → 5, 5, 5, 6. seed와 관계없다.
        for seed in range(10):
            with self.subTest(seed=seed):
                out = split.run(make_input(grid(HS6_CODES, PARTNERS), seed=seed))
                self.assertEqual(sorted(per_hs6(out["real_dev"]).values()), [5, 5, 5, 6])
                self.assertEqual(sorted(per_hs6(out["real_sealed"]).values()), [10, 11, 11, 11])

    def test_unequal_strata_use_the_largest_remainder(self):
        # 층 크기 10·7·3, 합 20 → real_dev 6개. 몫 3·2·0, 나머지 0·2·18(단위 1/20) → 남은 1자리는 크기 3인 층.
        series = (grid(["990001"], PARTNERS[:10]) + grid(["990002"], PARTNERS[:7]) + grid(["990003"], PARTNERS[:3]))
        for seed in range(5):
            with self.subTest(seed=seed):
                out = split.run(make_input(series, seed=seed))
                self.assertEqual(per_hs6(out["real_dev"]), {"990001": 3, "990002": 2, "990003": 1})

    def test_other_ratio(self):
        # 1:1, 층 크기 3·3 → real_dev 3개, 몫 1·1과 나머지가 같은 남은 1자리 → 층별 1과 2
        out = split.run(make_input(grid(["990001", "990002"], ["XA", "XB", "XC"]),
                                   ratio={"real_dev": 1, "real_sealed": 1}))
        self.assertEqual(len(out["real_dev"]), 3)
        self.assertEqual(sorted(per_hs6(out["real_dev"]).values()), [1, 2])

    def test_output_is_a_sorted_partition_of_the_input(self):
        series = grid(HS6_CODES, PARTNERS)
        out = split.run(make_input(series))
        dev, sealed = keyset(out["real_dev"]), keyset(out["real_sealed"])
        self.assertEqual(dev & sealed, set())
        self.assertEqual(dev | sealed, keyset(series))
        for name in ("real_dev", "real_sealed"):
            pairs = [(item["hs6"], item["partner"]) for item in out[name]]
            self.assertEqual(pairs, sorted(pairs), name)
            self.assertEqual(len(pairs), len(set(pairs)), name)


class DeterminismTest(unittest.TestCase):
    """같은 입력이면 같은 출력, 입력 순서와 무관, seed·snapshot_id가 배정을 바꾼다, 출력 모양."""

    def test_same_input_same_output(self):
        inp = make_input(grid(HS6_CODES, PARTNERS))
        self.assertEqual(split.run(inp), split.run(json.loads(json.dumps(inp))))

    def test_input_order_does_not_matter(self):
        series = grid(HS6_CODES, PARTNERS)
        base = split.run(make_input(series))
        for reordered in (list(reversed(series)), series[17:] + series[:17], series[1::2] + series[::2]):
            self.assertEqual(split.run(make_input(reordered)), base)

    def test_seed_and_snapshot_id_change_the_assignment(self):
        series = grid(HS6_CODES, PARTNERS)
        base = keyset(split.run(make_input(series, seed=7))["real_dev"])
        self.assertNotEqual(keyset(split.run(make_input(series, seed=8))["real_dev"]), base)
        self.assertNotEqual(keyset(split.run(make_input(series, snapshot_id="synthetic_split_v1"))["real_dev"]), base)

    def test_output_shape_and_echo(self):
        out = split.run(make_input(grid(HS6_CODES, PARTNERS), seed=0))
        self.assertEqual(list(out), ["snapshot_id", "seed", "ratio", "method", "real_dev", "real_sealed"])
        self.assertEqual(out["snapshot_id"], SNAPSHOT)
        self.assertIs(type(out["seed"]), int)
        self.assertEqual(out["seed"], 0)
        self.assertEqual(out["ratio"], {"real_dev": 1, "real_sealed": 2})
        self.assertTrue(all(type(v) is int for v in out["ratio"].values()))
        self.assertEqual(out["method"], "hs6_stratified_sha256_rank")
        for item in out["real_dev"] + out["real_sealed"]:
            self.assertEqual(list(item), ["hs6", "partner"])

    def test_input_is_not_modified(self):
        inp = make_input(grid(HS6_CODES, PARTNERS))
        snapshot = json.dumps(inp)
        split.run(inp)
        self.assertEqual(json.dumps(inp), snapshot)


class ValidationTest(unittest.TestCase):
    """형식이 틀린 입력은 ValueError다. 메시지에 입력 값을 넣지 않는다."""

    def assert_rejected(self, inp: object) -> ValueError:
        with self.assertRaises(ValueError) as caught:
            split.run(inp)
        return caught.exception

    def test_top_level_shape(self):
        good = make_input(grid(["990001"], ["XA", "XB", "XC"]))
        self.assert_rejected([good])
        self.assert_rejected(None)
        for missing in ("snapshot_id", "seed", "ratio", "series"):
            with self.subTest(missing=missing):
                self.assert_rejected({k: v for k, v in good.items() if k != missing})
        self.assert_rejected(dict(good, extra=1))

    def test_snapshot_id(self):
        for bad in ("", "Kcs_v2", "a:b", "../x", "kcs v2", "kcs-v2", "1kcs", "kcs_v2\n", 5, None):
            with self.subTest(bad=bad):
                self.assert_rejected(make_input(grid(["990001"], ["XA", "XB", "XC"]), snapshot_id=bad))

    def test_seed(self):
        for bad in (True, False, -1, "7", 7.0, Decimal("7"), None):
            with self.subTest(bad=bad):
                self.assert_rejected(make_input(grid(["990001"], ["XA", "XB", "XC"]), seed=bad))

    def test_ratio(self):
        series = grid(["990001"], ["XA", "XB", "XC"])
        for bad in ({"real_dev": 1}, {"real_dev": 1, "real_sealed": 2, "extra": 1}, {"real_dev": 0, "real_sealed": 2},
                    {"real_dev": 1, "real_sealed": -2}, {"real_dev": True, "real_sealed": 2},
                    {"real_dev": 1, "real_sealed": "2"}, {"real_dev": Decimal("1.0"), "real_sealed": 2}):
            with self.subTest(bad=bad):
                inp = make_input(series)
                inp["ratio"] = bad
                self.assert_rejected(inp)
        inp = make_input(series)
        inp["ratio"] = [1, 2]
        self.assert_rejected(inp)

    def test_series_items(self):
        bad_items = [
            {"hs6": "990001"}, {"hs6": "990001", "partner": "XA", "month": "202401"}, ["990001", "XA"],
            {"hs6": "99000", "partner": "XA"}, {"hs6": "9900011", "partner": "XA"}, {"hs6": "99000a", "partner": "XA"},
            {"hs6": "990001\n", "partner": "XA"}, {"hs6": "９９０００１", "partner": "XA"},
            {"hs6": 990001, "partner": "XA"}, {"hs6": "990001", "partner": "ALL"}, {"hs6": "990001", "partner": "xa"},
            {"hs6": "990001", "partner": "X1"}, {"hs6": "990001", "partner": "XAA"}, {"hs6": "990001", "partner": "X"},
            {"hs6": "990001", "partner": "ＸＡ"}, {"hs6": "990001", "partner": None},
        ]
        for bad in bad_items:
            with self.subTest(bad=bad):
                self.assert_rejected(make_input(grid(["990002"], ["XA", "XB", "XC"]) + [bad]))
        inp = make_input(grid(["990001"], ["XA", "XB", "XC"]))
        inp["series"] = tuple(inp["series"])
        self.assert_rejected(inp)

    def test_all_partner_message(self):
        error = self.assert_rejected(make_input(grid(["990001"], ["XA", "XB"]) + [{"hs6": "990001", "partner": "ALL"}]))
        self.assertIn("ALL", str(error))

    def test_duplicate_keys(self):
        self.assert_rejected(make_input(grid(["990001"], ["XA", "XB", "XC"]) + [{"hs6": "990001", "partner": "XB"}]))

    def test_both_sets_must_be_non_empty(self):
        # real_dev가 0개가 되는 입력을 거부한다. real_sealed는 내림 때문에 키가 하나라도 있으면 늘 1개 이상이다.
        self.assert_rejected(make_input([]))
        self.assert_rejected(make_input(grid(["990001"], ["XA"])))
        self.assert_rejected(make_input(grid(["990001"], ["XA", "XB"])))  # 2 × 1 ÷ 3 = 0
        self.assertEqual(len(split.run(make_input(grid(["990001"], ["XA", "XB", "XC"])))["real_dev"]), 1)
        out = split.run(make_input(grid(["990001"], ["XA", "XB"]), ratio={"real_dev": 100, "real_sealed": 1}))
        self.assertEqual((len(out["real_dev"]), len(out["real_sealed"])), (1, 1))

    def test_messages_do_not_echo_input_values(self):
        error = self.assert_rejected(make_input(grid(["990001"], ["XA", "XB", "XC"]), snapshot_id="zz:unexpected_text"))
        self.assertNotIn("unexpected_text", str(error))
        error = self.assert_rejected(make_input(grid(["990001"], ["XA", "XB"]) + [{"hs6": "odd_text", "partner": "XC"}]))
        self.assertNotIn("odd_text", str(error))
        self.assertIn("series[2]", str(error))


class CollectionPlanTest(unittest.TestCase):
    """수집 설정 도우미와 골든 입력의 출처. 이 클래스는 run을 부르지 않는다."""

    def load_plan(self) -> dict[str, object]:
        return json.loads((ROOT / "configs" / "collection_plan.json").read_text(encoding="utf-8"))

    def test_tracked_config_gives_64_partner_series(self):
        plan = self.load_plan()
        self.assertEqual(plan["snapshot_id"], "kcs_202201_202412_v2")
        series = split.series_from_collection_plan(plan)
        self.assertEqual(len(series), 64)
        self.assertEqual(len(keyset(series)), 64)
        self.assertEqual({item["hs6"] for item in series}, {"850450", "850431", "850432", "850490"})
        self.assertEqual({item["partner"] for item in series}, set(plan["partners"]))
        self.assertEqual(len(set(plan["partners"])), 16)
        self.assertNotIn("ALL", {item["partner"] for item in series})

    def test_golden_input_comes_from_the_tracked_config(self):
        golden_input = json.loads((HERE / "input.json").read_text(encoding="utf-8"))
        self.assertEqual(golden_input["ratio"], {"real_dev": 1, "real_sealed": 2})  # real_dev:real_sealed = 1:2
        rebuilt = split.input_from_collection_plan(self.load_plan(), golden_input["seed"], golden_input["ratio"])
        self.assertEqual(golden_input, rebuilt)

    def test_helper_does_not_split(self):
        with mock.patch.object(split, "_dev_keys", side_effect=AssertionError("분할을 부르면 안 된다")):
            inp = split.input_from_collection_plan(self.load_plan(), 1, RATIO)
        self.assertEqual(len(inp["series"]), 64)

    def test_helper_uses_only_top_level_codes(self):
        plan = {"snapshot_id": SNAPSHOT, "hs6": ["990001", "990002"], "partners": ["XA", "XB"],
                "_alternate": {"hs6": ["990009"], "partners": ["XZ"]}, "hs4_scan": ["9900", "9901"]}
        inp = split.input_from_collection_plan(plan, 3, RATIO)
        self.assertEqual(inp, {"snapshot_id": SNAPSHOT, "seed": 3, "ratio": RATIO,
                               "series": grid(["990001", "990002"], ["XA", "XB"])})

    def test_helper_rejects_bad_plans(self):
        good = {"snapshot_id": SNAPSHOT, "hs6": ["990001"], "partners": ["XA", "XB", "XC"]}
        bad_plans = [
            [good], dict(good, partners=["XA", "ALL"]), dict(good, hs6=[]), dict(good, partners=[]),
            {"snapshot_id": SNAPSHOT, "hs6": ["990001"]}, {"hs6": ["990001"], "partners": ["XA", "XB", "XC"]},
            dict(good, partners=["XA", "XB", "XA"]), dict(good, hs6=["99000"]), dict(good, snapshot_id="Bad"),
        ]
        for bad in bad_plans:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    split.input_from_collection_plan(bad, 1, RATIO)
        with self.assertRaises(ValueError):
            split.input_from_collection_plan(good, True, RATIO)
        with self.assertRaises(ValueError):
            split.input_from_collection_plan(good, 1, {"real_dev": 1})


if __name__ == "__main__":
    unittest.main()
