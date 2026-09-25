"""단위 K1(contract_types) 계약 대조 시험.

K1은 커널이라 진입 함수와 골든 쌍이 없다(test_golden.py는 건너뛴다). 대신 이 시험이 K1의 상수를 자료 계약
docs/rules/DATA_CONTRACT_V1.md의 원문 블록·표와 글자까지 대조한다. 계약 문서가 바뀌면 이 시험이 먼저 깨진다.
"""
import re
import unittest
from decimal import Decimal
from pathlib import Path

from tradesentry.contract import types

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = (ROOT / "docs" / "rules" / "DATA_CONTRACT_V1.md").read_text(encoding="utf-8")
LINES = CONTRACT.splitlines()
TICK_RE = re.compile(r"`([^`]*)`")


def line_starting(prefix: str) -> str:
    """prefix로 시작하는 첫 줄."""
    for line in LINES:
        if line.startswith(prefix):
            return line
    raise AssertionError(f"계약에 {prefix!r}로 시작하는 줄이 없다")


def line_after(marker: str) -> str:
    """marker 줄 다음의 첫 빈 줄 아닌 줄."""
    index = LINES.index(marker)
    return next(line for line in LINES[index + 1:] if line.strip())


def ticked(line: str) -> list[str]:
    return TICK_RE.findall(line)


def top_ticked(line: str) -> list[str]:
    """괄호 안 설명을 뺀 백틱 조각(예: "`flow`(`import` 또는 `export`)"에서 flow만)."""
    return ticked(re.sub(r"\([^()]*\)", "", line))


def bar_values(line: str, position: int = -1) -> tuple[str, ...]:
    """줄의 백틱 조각 하나를 `|`로 나눈 값."""
    return tuple(part.strip() for part in ticked(line)[position].split("|"))


def comma_values(text: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in text.split(","))


def section(start: str, end: str) -> list[str]:
    """start로 시작하는 제목 줄부터 end로 시작하는 줄 앞까지."""
    begin = next(i for i, line in enumerate(LINES) if line.startswith(start))
    stop = next(i for i, line in enumerate(LINES) if i > begin and line.startswith(end))
    return LINES[begin:stop]


def table_cells(lines: list[str]) -> list[list[str]]:
    """표 본문 행(머리와 구분 줄 뺌)의 칸 목록."""
    rows = [[cell.strip() for cell in line.strip().strip("|").split("|")] for line in lines if line.startswith("|")]
    return [row for row in rows[2:]] if rows else []


class OriginalBlockTest(unittest.TestCase):
    """명세 §4.x 원문 블록과 값 집합이 글자까지 같다."""

    def test_status_values(self):
        self.assertEqual(types.SIGNAL_TRIGGERS, bar_values(line_starting("- 신호 발동 여부 `signal_trigger`:")))
        self.assertEqual(types.SIGNAL_STATUSES, bar_values(line_starting("- 신호별 판정 `signal_status`:")))
        self.assertEqual(types.SIGNALS, tuple(ticked(line_starting("- 신호 코드는 "))))
        self.assertEqual(types.EXECUTION_STATUSES, bar_values(line_after("**명세 §4.2 원문**")))
        self.assertEqual(types.OBSERVATION_STATUSES, bar_values(line_after("**명세 §4.3 원문**"), 0))
        self.assertEqual(types.REVIEW_STATUSES, types.SIGNAL_STATUSES[:3])
        rows = table_cells(section("**명세 §4.1 원문**", "- 신호 코드는"))
        self.assertEqual({ticked(row[0])[0]: row[1] for row in rows}, types.STATUS_LABELS_KO)
        self.assertIn(f'`{types.PRE_INVESTIGATION}`(표기 "{types.PRE_INVESTIGATION_LABEL_KO}")', CONTRACT)
        self.assertIn("우선순위는 `" + " > ".join(types.CASE_STATUS_PRIORITY) + "`다", CONTRACT)

    def test_names(self):
        self.assertEqual(types.MODES, bar_values(line_starting("- 모드: ")))
        self.assertEqual(types.SOURCE_KINDS, bar_values(line_starting("- 출처 종류 `source_kind`: ")))
        self.assertEqual(types.DATASETS, tuple(ticked(line_starting("- 데이터셋: "))))
        self.assertEqual((types.REAL_SNAPSHOT_ID,), tuple(ticked(line_starting("- 스냅샷: "))))
        self.assertEqual(types.POLICY_V1, ticked(line_starting("- 정책: "))[0])
        self.assertEqual(types.GROUPING_VERSIONS, tuple(ticked(line_starting("- 비교 대상: "))))
        self.assertEqual((types.RULEBOOK_VERSION,), tuple(ticked(line_starting("- 룰북: "))))
        self.assertEqual(types.APPROVAL_STATUSES, bar_values(line_starting("- 승인 유효 상태: ")))
        self.assertEqual((types.EVIDENCE_ID_FORMAT,), tuple(ticked(line_starting("- 근거 ID: "))))
        self.assertTrue(types.EVIDENCE_ID_FORMAT.startswith(types.EVIDENCE_ID_PREFIX + ":"))
        self.assertIn(f"`{types.FIXTURE_SNAPSHOT_ID}`", line_starting("| `controlled_fixture_v0` |"))
        sealed = [row for row in table_cells(section("### 12.2 기록 형식", "- 목록에 있는 파일이")) if row[0] == "`dataset`"]
        self.assertEqual(types.SEALED_DATASETS, tuple(ticked(sealed[0][2])))

    def test_envelope_and_tools(self):
        self.assertEqual(types.ENVELOPE_KEYS, comma_values(ticked(line_after("**명세 §4.6 원문**"))[0]))
        self.assertEqual(types.TOOLS, tuple(ticked(line_starting("- 도구 5개: "))))

    def test_claims_outcomes_records(self):
        self.assertEqual(types.CLAIM_FIELDS, comma_values(ticked(line_starting("- 필드: `claim_id"))[0]))
        self.assertEqual(types.CLAIM_TYPES, bar_values(line_starting("- `claim_type`: ")))
        self.assertEqual(types.DIRECTIONS, bar_values(line_starting("- `direction`: ")))
        self.assertEqual(types.CLAIM_OUTCOMES, bar_values(line_after("**명세 §4.9 원문**"), 0))
        self.assertEqual(types.RUN_RECORD_KEYS, comma_values(ticked(line_after("**명세 §4.10 원문**"))[0]))
        self.assertEqual(types.REPORT_KEYS, comma_values(ticked(line_after("**명세 §4.10-1 원문**"))[0]))
        self.assertEqual(types.CLAIM_RECORD_KEYS, comma_values(ticked(line_after("**명세 §4.10-2 원문**"))[0]))
        self.assertEqual(types.CLAIM_RECORD_SOURCES, bar_values(line_starting("- `source`: "), 1))
        self.assertEqual(types.APPROVAL_RECORD_KEYS, tuple(ticked(line_starting("- 필드: `reviewer_label`"))))
        self.assertLessEqual(set(types.RUN_RECORD_SCORER_KEYS), set(types.RUN_RECORD_KEYS))
        hash_line = line_starting("1. `claims`, `narrative`, `hypotheses`, `evidence_ids` 네 키만")
        self.assertEqual(types.REPORT_HASH_KEYS, tuple(ticked(hash_line)))
        manifest = table_cells(section("### 12.2 기록 형식", "- 목록에 있는 파일이"))
        self.assertEqual(types.SEALED_MANIFEST_FILE_KEYS, tuple(ticked(row[0])[0] for row in manifest))


class ObjectKeyTest(unittest.TestCase):
    """§2.3 객체 표의 v1 키와 기존 열."""

    def keys_of(self, start: str, end: str, column: int) -> tuple[str, ...]:
        keys: list[str] = []
        for row in table_cells(section(start, end)):
            keys += ticked(row[column])
        return tuple(keys)

    def test_object_keys(self):
        self.assertEqual(types.SNAPSHOT_KEYS, self.keys_of("#### 2.3.1", "- `hs_version`의 v2 대응", 1))
        self.assertEqual(types.OBSERVATION_KEYS, self.keys_of("#### 2.3.2", "- 기존 열:", 1))
        self.assertEqual(types.COLLECTION_RECEIPT_KEYS, self.keys_of("#### 2.3.3", "- 기존 열:", 1))
        self.assertEqual(types.METRIC_KEYS, self.keys_of("#### 2.3.4", "- 원문 필드에는", 1))
        self.assertEqual(types.CASE_KEYS, self.keys_of("#### 2.3.5", "- 사례는 코드가", 1))
        peer = self.keys_of("#### 2.3.6", "- 원문 예시값", 0)
        self.assertEqual(tuple(k for k in types.PEER_GROUP_KEYS if k != "baci_country_code"), peer)
        self.assertIn("`baci_country_code` 열에 따로 둔다", CONTRACT)
        self.assertIn(f"값은 `{types.PEER_ENTITY_TYPE}`(수출국)다", CONTRACT)

    def test_existing_columns(self):
        obs_extra = [line for line in section("#### 2.3.2", "**행 규칙**") if line.startswith("- 기존 열:")][0]
        self.assertEqual(types.OBSERVATION_EXTRA_COLUMNS, tuple(top_ticked(obs_extra)))
        rec_extra = [line for line in section("#### 2.3.3", "#### 2.3.4") if line.startswith("- 기존 열:")][0]
        self.assertEqual(types.COLLECTION_RECEIPT_EXTRA_COLUMNS, tuple(top_ticked(rec_extra.split(" [")[0])))
        self.assertEqual(set(types.OBSERVATION_COLUMNS), set(types.OBSERVATION_KEYS) | set(types.OBSERVATION_EXTRA_COLUMNS))
        self.assertEqual(set(types.COLLECTION_RECEIPT_COLUMNS),
                         set(types.COLLECTION_RECEIPT_KEYS) | set(types.COLLECTION_RECEIPT_EXTRA_COLUMNS))
        self.assertIn("(`" + "`, `".join(types.OBSERVATION_PRIMARY_KEY) + "`)", line_starting("1. 관측 단위:"))
        self.assertIn(f"`{types.PARTNER_NAMESPACE}`", CONTRACT)
        month_row = line_starting("| month | `month` |")
        self.assertIn(f"월 행은 `YYYYMM`, 총계 행(", month_row)
        self.assertIn(f"은 `{types.TOTAL_ROW_MONTH}`", month_row)
        self.assertTrue(types.TOTAL_ROW_MONTH.startswith(types.RAW_MONTH_PREFIX))
        self.assertEqual(types.RECEIPT_STATUSES, tuple(ticked(line_starting("| 성공·오류·미수집 |"))[1:3]))
        self.assertIn("| `OK` 또는 `FAILED` |", line_starting("| 성공·오류·미수집 |"))

    def test_collector_table_matches_columns(self):
        """스냅샷 SQLite 열 순서는 기존 수집기의 표 정의와 같다."""
        source = (ROOT / "src" / "tradesentry" / "ingest.py").read_text(encoding="utf-8")
        for table, columns in (("observation", types.OBSERVATION_COLUMNS),
                               ("collection_receipt", types.COLLECTION_RECEIPT_COLUMNS)):
            body = re.search(r"CREATE TABLE IF NOT EXISTS " + table + r"\((.*?)\);", source, re.S).group(1)
            names = [part.split()[0] for part in body.replace("\n", " ").split(",")
                     if part.strip() and not part.strip().startswith("PRIMARY KEY") and "(" not in part.split()[0]]
            self.assertEqual(tuple(names[:len(columns)]), columns, table)


class MetricTableTest(unittest.TestCase):
    """§11.2 단위, §11.3 표시 자릿수, §9.4 신호 계열, §6.2 HS10 기호."""

    def symbol(self, cell: str) -> list[str]:
        return [token.replace("@<HS10 코드>", "") for token in ticked(cell)]

    def test_units(self):
        found: dict[str, str] = {}
        for row in table_cells(section("### 11.2 지표 기호와 단위", "- `r_U`, `s`, `w@<HS10 코드>`는")):
            for name in self.symbol(row[0]):
                found[name] = ticked(row[-1])[0]
        self.assertEqual(found, types.METRIC_UNITS)
        self.assertEqual(set(types.METRIC_SYMBOLS) | {"w"}, set(found))

    def test_display_decimals(self):
        words = {"정수": 0, "소수 1자리": 1, "소수 2자리": 2}
        found: dict[str, int] = {}
        for row in table_cells(section("### 11.3 표시 자릿수와 반올림", "- `U@<HS10 코드>`")):
            for name in self.symbol(row[0]):
                found[name] = words[row[2]]
        self.assertEqual(found, types.DISPLAY_DECIMALS)

    def test_signal_families_and_hs10_symbols(self):
        found = {}
        for row in table_cells(section("| 신호 계열 | 드는 `metric` |", "- `data_status` 주장은 값이")):
            found[ticked(row[0])[0]] = tuple(token.replace("<HS10 코드>", "") for token in ticked(row[1]))
        self.assertEqual(found, types.SIGNAL_FAMILY_METRICS)
        hs10_line = [line for line in LINES if "정의한 것은 `U@<HS10 코드>`" in line][0]
        bases = [token.split("@")[0] for token in ticked(hs10_line)
                 if token.endswith("@<HS10 코드>") and not token.startswith("<")]
        self.assertEqual(tuple(dict.fromkeys(bases)), types.HS10_METRIC_BASES)

    def test_metric_helpers(self):
        self.assertEqual(types.parse_metric("r_U"), ("r_U", None))
        self.assertEqual(types.parse_metric("w@8504501000"), ("w", "8504501000"))
        self.assertEqual(types.parse_metric("observation_status@8504501000"), ("observation_status", "8504501000"))
        self.assertEqual(types.metric_unit("U@8504501000"), "USD/kg")
        self.assertEqual(types.metric_unit("d_s"), "pp")
        self.assertIsNone(types.metric_unit("observation_status"))
        self.assertEqual(types.metric_display_decimals("r_U@8504501000"), 1)
        self.assertEqual(types.metric_display_decimals("V"), 0)
        self.assertEqual(types.signal_family("w@8504501000"), ("unit_value",))
        self.assertEqual(types.signal_family("d_s"), ("share",))
        self.assertEqual(types.signal_family("V"), ())
        for bad in ("w", "within_effect@8504501000", "U@85045010", "r_u", "", "V@8504501000"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                types.parse_metric(bad)

    def test_formats(self):
        self.assertTrue(types.MONTH_RE.fullmatch("202401"))
        for bad in ("202413", "202400", "2024-01", "20241", "RAW:총계"):
            self.assertIsNone(types.MONTH_RE.fullmatch(bad), bad)
        self.assertTrue(types.RUN_ID_RE.fullmatch("run_case-260925143015"))
        for bad in ("Run_case-260925143015", "run-case-260925143015", "run_case-2609251430"):
            self.assertIsNone(types.RUN_ID_RE.fullmatch(bad), bad)
        self.assertEqual(types.SCHEMA_VERSION, 2)
        self.assertIn("`schema_version=2`", CONTRACT)  # 2026-09-25(금) 사용자 결정(v2로 올림). 코드 상수와 계약 본문이 같다
        self.assertEqual(types.Number, int | Decimal)


if __name__ == "__main__":
    unittest.main()
