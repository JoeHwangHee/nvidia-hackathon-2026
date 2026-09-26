"""화면 문구 표(한국어·영어)와 이름표.

화면(담당자 홈·사례 검토·결정 기록·도움)의 문구 전부를 키 → {"ko", "en"}로 둔다. 한국어는 디자인 정본(scratchpad HTML 목업)
의 문구를 그대로 옮겼고, 영어는 UI2 지시서의 용어표를 따른다. 상태값·코드(MAINTAIN 등)는 번역하지 않고 자료 계약의 글자
그대로 쓴다. 두 언어의 키 집합이 같고 빈 값이 없으며 자리표시({name})가 같음을 시험이 강제한다(tests/units/UI/).
streamlit을 import하지 않는다.
"""
import csv
from pathlib import Path

LANGS = ("ko", "en")
DEFAULT_LANG = "ko"
LANG_NAMES = {"ko": "한국어", "en": "English"}
COUNTRY_MAP = Path("data") / "reference" / "country_map.csv"

# 품목 이름(UI2 지시서 용어표). 합성 픽스처 품목은 HS6 코드만 보인다.
HS6_NAMES = {
    "850431": {"ko": "계기용 변압기 (소용량)", "en": "Transformers ≤ 1 kVA (incl. instrument transformers)"},
    "850432": {"ko": "계기용 변압기 (중용량) · 전압 조정기", "en": "Transformers 1–16 kVA · voltage regulators"},
    "850450": {"ko": "인덕터 (기타)", "en": "Inductors, other"},
    "850490": {"ko": "변압기·전원장치 부분품", "en": "Parts of transformers & power supplies"},
}

MONTH_EN = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

STRINGS: dict[str, dict[str, str]] = {
    # ---- 공통 --------------------------------------------------------------------------------------------------
    "app.title": {"ko": "TradeSentry", "en": "TradeSentry"},
    "app.subtitle": {"ko": "수입통계 경보 검토 · 담당자용", "en": "Import statistics alert review · for analysts"},
    "app.lang_label": {"ko": "언어 / Language", "en": "언어 / Language"},
    "app.snapshot_label": {"ko": "스냅샷", "en": "Snapshot"},
    "app.snapshot_none": {
        "ko": "data/snapshots/ 아래 정본 빌드(snapshot_build.sqlite)가 있는 스냅샷이 없습니다. 합성 픽스처는 "
              "`uv run --locked python -c \"from tradesentry.snapshot import fixture; fixture.materialize()\"`로 만듭니다.",
        "en": "No snapshot with a canonical build (snapshot_build.sqlite) exists under data/snapshots/. Create the synthetic "
              "fixture with `uv run --locked python -c \"from tradesentry.snapshot import fixture; fixture.materialize()\"`."},
    "app.data_line": {"ko": "자료: 관세청 수입통계 {start} ~ {end} (고정 스냅샷 {snapshot_id})",
                      "en": "Data: Korea Customs Service import statistics {start} – {end} (frozen snapshot {snapshot_id})"},
    "app.disclaimer": {
        "ko": "다음 업무 제안(검토 유지 · 모니터링 · 자료 보류)은 담당자 참고용이며 기관 승인이나 통관 조치가 아닙니다.",
        "en": "The suggested next step (Keep under review · Monitor · Data hold) is for the analyst's reference only; it is "
              "not an institutional approval or a customs action."},
    "app.error_read": {"ko": "기록을 읽지 못했습니다({name}).", "en": "Could not read the record ({name})."},
    "app.admin_link": {"ko": "관리자용 조사 기록 보기", "en": "Open the admin investigation log"},
    "nav.home": {"ko": "담당자 홈", "en": "Analyst home"},
    "nav.case": {"ko": "사례 검토", "en": "Case review"},
    "nav.assist": {"ko": "결정 기록 · 도움", "en": "Decision · help"},
    "nav.admin": {"ko": "관리자용 조사 기록", "en": "Investigation log (admin)"},
    # ---- 상태·판정 ----------------------------------------------------------------------------------------------
    "status.NOT_INVESTIGATED": {"ko": "조사 전", "en": "Not investigated"},
    "status.INVESTIGATED": {"ko": "조사 완료", "en": "Investigated"},
    "status.FAILED": {"ko": "조사 실패", "en": "Investigation failed"},
    "verdict.MAINTAIN": {"ko": "검토 유지", "en": "Keep under review"},
    "verdict.MONITOR": {"ko": "모니터링", "en": "Monitor"},
    "verdict.HOLD": {"ko": "자료 보류", "en": "Data hold"},
    "verdict.NOT_TRIGGERED": {"ko": "미발동", "en": "Not triggered"},
    "verdict.PRE_INVESTIGATION": {"ko": "조사 전 경보", "en": "Alert, not yet investigated"},
    "verdict.none": {"ko": "—", "en": "—"},
    "meaning.MAINTAIN": {"ko": "변동이 설명되지 않아 담당자의 검토가 계속 필요합니다.",
                         "en": "The change is not explained, so the analyst's review continues."},
    "meaning.MONITOR": {"ko": "하위품목 구성 변화로 설명되어 다음 달 같은 사례를 다시 확인합니다.",
                        "en": "Explained by a change in sub-heading mix; the same case is re-checked next month."},
    "meaning.HOLD": {"ko": "검증할 자료가 모자라 다음 통계 현행화 뒤 자료를 다시 확인합니다.",
                     "en": "Data needed for verification is missing; re-check after the next monthly statistics revision."},
    "define.MAINTAIN": {"ko": "필수 비교를 마쳤는데 변동이 설명되지 않거나 설명이 서로 충돌할 때. 담당자가 검토를 계속합니다.",
                        "en": "Required comparisons were made but the change is unexplained or explanations conflict. "
                              "The analyst keeps reviewing."},
    "define.MONITOR": {"ko": "하위품목 구성 변화로 설명되고 개별 변동이 기준 안일 때. 다음 달 같은 사례를 다시 확인합니다.",
                       "en": "Explained by a change in sub-heading mix, with individual changes within the thresholds. "
                             "The same case is re-checked next month."},
    "define.HOLD": {"ko": "필요한 달·단위·분모·구성자료가 없어 검증할 수 없을 때. 다음 통계 현행화 뒤 자료를 다시 확인합니다.",
                    "en": "Required months, units, denominator or composition data are missing, so verification is "
                          "impossible. Re-check after the next monthly statistics revision."},
    "signal.unit_value": {"ko": "단가", "en": "unit value"},
    "signal.share": {"ko": "점유율", "en": "import share"},
    "signal.unit_change": {"ko": "단가 {value}%", "en": "unit value {value}%"},
    "signal.share_change": {"ko": "점유율 {value}%p", "en": "import share {value} pp"},
    "signal.none": {"ko": "값 없음", "en": "no value"},
    # ---- 담당자 홈 ----------------------------------------------------------------------------------------------
    "home.month_alerts": {"ko": "{month} 경보", "en": "Alerts for {month}"},
    "home.count": {"ko": "{n}건", "en": "{n}"},
    "home.month_label": {"ko": "경보 월", "en": "Alert month"},
    "home.intro": {
        "ko": "전년 같은 달({baseline})과 비교해 kg당 수입단가가 {u}% 이상 또는 상대국 점유율이 {s}%p 이상 바뀐 품목·국가 "
              "조합입니다. 경보는 조사의 시작점이며, 위법·부정을 뜻하지 않습니다.",
        "en": "Product–partner combinations whose unit value (USD/kg) changed by {u}% or more, or whose import share "
              "changed by {s} percentage points or more, compared with the same month a year earlier ({baseline}). "
              "An alert is the starting point of an investigation; it does not imply wrongdoing."},
    "home.kpi_unit": {"ko": "단가 변화 경보", "en": "Unit-value alerts"},
    "home.kpi_share": {"ko": "점유율 변화 경보", "en": "Import-share alerts"},
    "home.kpi_done": {"ko": "조사 완료", "en": "Investigated"},
    "home.kpi_total": {"ko": "최근 24개월 경보 합계", "en": "Alerts, all 24 months"},
    "home.filter_label": {"ko": "보기", "en": "Show"},
    "home.filter_all": {"ko": "전체", "en": "All"},
    "home.filter_unit": {"ko": "단가 변화", "en": "Unit value"},
    "home.filter_share": {"ko": "점유율 변화", "en": "Import share"},
    "home.filter_status": {"ko": "상태", "en": "Status"},
    "home.search": {"ko": "품목·국가 찾기", "en": "Find product or partner"},
    "home.col_item": {"ko": "품목 (HS6)", "en": "Product (HS6)"},
    "home.col_partner": {"ko": "상대국", "en": "Partner"},
    "home.col_unit": {"ko": "kg당 단가 · {baseline} → {month}", "en": "Unit value (USD/kg) · {baseline} → {month}"},
    "home.col_share": {"ko": "점유율 · {baseline} → {month}", "en": "Import share · {baseline} → {month}"},
    "home.col_status": {"ko": "상태", "en": "Status"},
    "home.col_next": {"ko": "다음 업무 제안", "en": "Suggested next step"},
    "home.col_action": {"ko": "동작", "en": "Action"},
    "home.no_import": {"ko": "{month} 수입 없음", "en": "no imports in {month}"},
    "home.not_comparable": {"ko": "비교 불가", "en": "not comparable"},
    "home.btn_start": {"ko": "조사 시작", "en": "Investigate"},
    "home.btn_view": {"ko": "결과 보기", "en": "View result"},
    "home.footer1": {
        "ko": "단가는 수입금액(USD) ÷ 순중량(kg). 점유율은 해당 품목의 전체 수입금액 가운데 그 나라의 비중. 값은 관세청 공개 "
              "통계에서 계산한 것입니다.",
        "en": "Unit value = import value (USD) ÷ net weight (kg). Import share = the partner's share of Korea's total "
              "import value for that product. Values are computed from published Korea Customs Service statistics."},
    "home.no_alerts": {"ko": "이 스냅샷에는 경보가 없습니다.", "en": "This snapshot has no alerts."},
    "home.filtered_empty": {"ko": "조건에 맞는 경보가 없습니다.", "en": "No alerts match the filters."},
    "home.running": {"ko": "조사 실행 중… 사례당 최대 {s}초까지 기다립니다. 버튼은 잠깁니다.",
                     "en": "Investigation running… waits up to {s} seconds per case. Buttons are locked."},
    "home.run_failed": {"ko": "조사 실행이 끝났지만 새 실행 폴더를 찾지 못했습니다(종료 코드 {code}).",
                        "en": "The run finished but no new run folder was found (exit code {code})."},
    "home.cannot_run": {
        "ko": "이 프로세스 환경에 NVIDIA_API_KEY가 없고 이 사례의 재생 파일도 없어 지금은 조사를 시작할 수 없습니다. "
              "관리자용 화면이나 CLI(`tradesentry run-case`)로 돌린 뒤 새로 고칩니다.",
        "en": "NVIDIA_API_KEY is not in this process environment and this case has no replay file, so the investigation "
              "cannot start now. Run it from the admin screen or the CLI (`tradesentry run-case`) and refresh."},
    "home.replay_note": {"ko": "키 없이 재생 파일로 돕니다(재생 실행, 점수표 근거 아님).",
                         "en": "Runs from the replay file without a key (replay run; not scorecard evidence)."},
    "home.error_alerts": {"ko": "경보 목록을 만들지 못했습니다({name}).", "en": "Could not build the alert list ({name})."},
    # ---- 사례 검토 ----------------------------------------------------------------------------------------------
    "case.crumb_month": {"ko": "{month} 경보", "en": "{month} alerts"},
    "case.title_down": {"ko": "{partner}산 {item}의 kg당 수입단가가 1년 전보다 {band} 낮아졌습니다",
                        "en": "The unit value (USD/kg) of {item} imported from {partner} has fallen {band} from a year earlier"},
    "case.title_up": {"ko": "{partner}산 {item}의 kg당 수입단가가 1년 전보다 {band} 높아졌습니다",
                      "en": "The unit value (USD/kg) of {item} imported from {partner} has risen {band} from a year earlier"},
    "case.title_flat": {"ko": "{partner}산 {item}의 kg당 수입단가가 1년 전과 거의 같습니다",
                        "en": "The unit value (USD/kg) of {item} imported from {partner} is about the same as a year earlier"},
    "case.title_na": {"ko": "{partner}산 {item}의 kg당 수입단가를 1년 전과 비교할 수 없습니다",
                      "en": "The unit value (USD/kg) of {item} imported from {partner} cannot be compared with a year earlier"},
    "case.title_share_up": {"ko": "{partner}의 {item} 수입 점유율이 1년 전보다 크게 높아졌습니다",
                            "en": "{partner}'s import share of {item} is substantially higher than a year earlier"},
    "case.title_share_down": {"ko": "{partner}의 {item} 수입 점유율이 1년 전보다 크게 낮아졌습니다",
                              "en": "{partner}'s import share of {item} is substantially lower than a year earlier"},
    "case.title_share_na": {"ko": "{partner}의 {item} 수입 점유율을 1년 전과 비교할 수 없습니다",
                            "en": "{partner}'s import share of {item} cannot be compared with a year earlier"},
    "band.near_half": {"ko": "절반 가까이", "en": "by roughly half"},
    "band.large": {"ko": "크게", "en": "substantially"},
    "band.notable": {"ko": "눈에 띄게", "en": "noticeably"},
    "band.double": {"ko": "두 배 넘게", "en": "more than twofold"},
    "chip.alert_month": {"ko": "경보 월 {month}", "en": "Alert month {month}"},
    "chip.baseline": {"ko": "비교 기준 {month} (전년 같은 달)", "en": "Baseline {month} (same month a year earlier)"},
    "chip.hs6": {"ko": "HS6 {hs6} · 상대국 {partner}", "en": "HS6 {hs6} · partner {partner}"},
    "chip.investigated": {"ko": "조사 완료 {time}", "en": "Investigated {time}"},
    "chip.verified": {"ko": "보고서 검증 통과", "en": "report verified against source rows"},
    "chip.findings": {"ko": "검증기 기록 {n}건", "en": "{n} validator finding(s)"},
    "chip.not_completed": {"ko": "실행 상태 {status}", "en": "Execution status {status}"},
    "case.next_step": {"ko": "다음 업무 제안", "en": "Suggested next step"},
    "case.btn_record": {"ko": "내 결정 기록하기", "en": "Record my decision"},
    "case.sec_what": {"ko": "무슨 일이 있었나", "en": "What happened"},
    "case.unit_label": {"ko": "kg당 수입단가 · 전년 같은 달 대비", "en": "Unit value (USD/kg) · vs. same month a year earlier"},
    "case.threshold_hit": {"ko": "기준 {thr}% 이상 변화 → 경보 발동", "en": "Change of {thr}% or more → alert triggered"},
    "case.threshold_miss": {"ko": "기준 {thr}% 미만 → 경보 아님", "en": "Below the {thr}% threshold → no alert"},
    "case.threshold_unknown": {"ko": "발동 여부 기록 없음", "en": "no trigger record"},
    "case.share_label": {"ko": "{partner}의 수입 점유율 · {baseline} → {month}",
                         "en": "{partner}'s import share · {baseline} → {month}"},
    "case.share_hit": {"ko": "{d}%p, 기준 {thr}%p 이상 → 경보 발동", "en": "{d} pp, at or above the {thr} pp threshold → alert triggered"},
    "case.share_miss": {"ko": "{d}%p, 기준 {thr}%p 미만 → 경보 아님", "en": "{d} pp, below the {thr} pp threshold → no alert"},
    "case.value_missing": {"ko": "값 없음", "en": "no value"},
    "case.sec_found": {"ko": "조사에서 확인한 것", "en": "What the investigation confirmed"},
    "case.found_note": {"ko": "숫자는 모두 원본 통계와 대조해 통과한 값", "en": "All figures were checked against the source statistics"},
    "case.decomp_head.MONITOR": {"ko": "하위품목 구성이 바뀐 것으로 설명됩니다.", "en": "Explained by a change in sub-heading mix."},
    "case.decomp_head.MAINTAIN": {"ko": "하위품목 구성이 바뀐 탓만으로는 설명되지 않습니다.",
                                  "en": "Not explained by a change in sub-heading mix alone."},
    "case.decomp_head.HOLD": {"ko": "하위품목 구성효과를 판정할 자료가 모자랍니다.",
                              "en": "Data to judge the mix effect is insufficient."},
    "case.decomp_head.other": {"ko": "단가 변화를 하위품목 단위로 나누어 보았습니다.",
                               "en": "The unit-value change was decomposed by sub-heading."},
    "case.decomp_body": {
        "ko": "단가 변화를 나누어 보면, 같은 하위품목 안에서 단가가 움직인 몫이 {within} USD/kg이고, 하위품목 구성이 바뀌어 생긴 "
              "몫은 {mix} USD/kg, 나머지는 {residual} USD/kg입니다.",
        "en": "Splitting the change: {within} USD/kg comes from price moves within the same sub-headings, {mix} USD/kg "
              "from a shift in the sub-heading mix, and {residual} USD/kg is the remainder."},
    "case.compare_head": {"ko": "다른 상대국과 비교하면", "en": "Compared with other partners"},
    "case.compare_item": {"ko": "같은 품목의 {partner}산 kg당 단가는 같은 기간 {value}% {dir}.",
                          "en": "Over the same period, the unit value of the same product from {partner} {dir} by {value}%."},
    "case.compare_share_item": {"ko": "{partner}의 점유율 변화는 {value}%p입니다.", "en": "{partner}'s import share changed by {value} pp."},
    "case.compare_value_item": {"ko": "{partner}: {metric} {value} {unit}", "en": "{partner}: {metric} {value} {unit}"},
    "case.compare_note": {"ko": "시장 전체 요인일 가능성을 열어 두어야 합니다.", "en": "A market-wide factor cannot be ruled out."},
    "dir.down": {"ko": "내렸습니다", "en": "fell"},
    "dir.up": {"ko": "올랐습니다", "en": "rose"},
    "dir.flat": {"ko": "변하지 않았습니다", "en": "was flat"},
    "case.share_head.NOT_TRIGGERED": {"ko": "점유율은 크게 움직이지 않았습니다.", "en": "Import share did not move much."},
    "case.share_head.other": {"ko": "점유율이 기준 이상으로 움직였습니다.", "en": "Import share moved beyond the threshold."},
    "case.share_body": {"ko": "{s0}%에서 {s1}%로, 정책 기준({thr}%p)에 {rel}.",
                        "en": "From {s0}% to {s1}%, {rel} the policy threshold ({thr} pp)."},
    "rel.below": {"ko": "미치지 않습니다", "en": "below"},
    "rel.at_or_above": {"ko": "이르거나 넘습니다", "en": "at or above"},
    "case.sub_head": {"ko": "하위품목(HS10)별 단가 변화율", "en": "Unit-value change by sub-heading (HS10)"},
    "case.sub_item": {"ko": "{code}: {value}%", "en": "{code}: {value}%"},
    "case.data_head": {"ko": "자료 상태", "en": "Data status"},
    "case.data_item": {"ko": "{partner} {period}: {status}", "en": "{partner} {period}: {status}"},
    "case.found_empty": {"ko": "이 보고서에는 검증된 사실 주장이 없습니다.", "en": "This report has no verified factual claims."},
    "case.sec_alt": {"ko": "다른 설명 가능성", "en": "Other possible explanations"},
    "case.alt_note": {"ko": "조사자가 제시한 가설, 통계로 확인된 것은 아님",
                      "en": "Hypotheses raised by the investigator; not confirmed by the statistics"},
    "case.alt_empty": {"ko": "조사자가 제시한 가설이 없습니다.", "en": "The investigator raised no hypotheses."},
    "case.korean_original": {"ko": "(원문)", "en": "(Korean original)"},
    "case.sec_conclusion": {"ko": "결론 — {verdict}", "en": "Conclusion — {verdict}"},
    "case.conclusion_not_completed": {"ko": "조사가 완료되지 않았습니다(실행 상태 {status}). 최종 판정이 없습니다.",
                                      "en": "The investigation did not complete (execution status {status}). There is no final decision."},
    "case.narrative_quote": {"ko": "조사 보고서 요약 원문:", "en": "Investigation report summary (verbatim):"},
    "case.narrative_empty": {"ko": "보고서 요약이 없습니다.", "en": "The report has no summary."},
    "case.sec_meaning": {"ko": "판정이 뜻하는 것", "en": "What each decision means"},
    "case.this_case": {"ko": "← 이 사례", "en": "← this case"},
    "case.sec_basis": {"ko": "이 조사가 근거로 삼은 것", "en": "What this investigation relied on"},
    "basis.data": {"ko": "자료", "en": "Data"},
    "basis.data_value": {"ko": "관세청 수입통계 고정 스냅샷 {snapshot_id}",
                         "en": "Frozen snapshot of Korea Customs Service import statistics: {snapshot_id}"},
    "basis.rule": {"ko": "비교 기준", "en": "Comparison rule"},
    "basis.rule_value": {"ko": "전년 같은 달. 단가 {u}% · 점유율 {s}%p (정책 {policy})",
                         "en": "Same month a year earlier. Unit value {u}% · import share {s} pp (policy {policy})"},
    "basis.method": {"ko": "조사 방식", "en": "Method"},
    "basis.method_value": {"ko": "조사자와 검수자가 정해진 조회 도구로 원본 통계만 조회. 외부 자료 없음",
                           "en": "An investigator and a separate critic queried only the source statistics with fixed lookup tools. No external data"},
    "basis.verify": {"ko": "검증", "en": "Verification"},
    "basis.verify_value": {"ko": "보고서의 사실 주장 {n}개를 원본 통계 행과 대조해 통과",
                           "en": "{n} factual claims in the report were checked against source rows and passed"},
    "basis.verify_findings": {"ko": "사실 주장 {n}개, 검증기 기록 {m}건", "en": "{n} factual claims, {m} validator findings"},
    "basis.rows": {"ko": "근거 행", "en": "Source rows"},
    "basis.rows_value": {"ko": "원본 통계 행 보기 (관리자용 화면)", "en": "View source rows (admin screen)"},
    "case.sec_caution": {"ko": "읽을 때 유의할 점", "en": "Please note"},
    "case.caution": {
        "ko": "단가 변화는 부정·위법·원산지 조작의 증거가 아닙니다. 다음 업무 제안은 담당자 참고용이며 기관 승인이나 통관 조치가 "
              "아닙니다. 위 \"다른 설명 가능성\"은 통계로 확인되지 않은 가설입니다.",
        "en": "A unit-value change is not evidence of wrongdoing or origin manipulation. The suggested next step is for the "
              "analyst's reference only, not an institutional approval or customs action. The \"other possible explanations\" "
              "above are hypotheses not confirmed by the statistics."},
    "case.btn_report": {"ko": "보고서 전문 보기", "en": "Full report"},
    "case.btn_admin": {"ko": "조사 과정 (관리자용)", "en": "Investigation process (admin)"},
    "case.report_full": {"ko": "보고서 전문(한국어 원문, 주장·설명·가설·검증기 기록)", "en": "Full report (Korean original: claims, narrative, hypotheses, validator findings)"},
    "case.none_selected": {"ko": "검토할 사례가 선택되지 않았습니다. 담당자 홈에서 \"결과 보기\"를 누릅니다.",
                           "en": "No case is selected. Choose \"View result\" on the analyst home."},
    "case.not_investigated": {"ko": "이 사례({case_id})는 아직 조사 결과가 없습니다. 담당자 홈에서 \"조사 시작\"을 누릅니다.",
                              "en": "This case ({case_id}) has no investigation result yet. Use \"Start investigation\" on the analyst home."},
    "case.run_label": {"ko": "실행 폴더", "en": "Run folder"},
    "case.pick_label": {"ko": "조사 완료된 사례 고르기", "en": "Choose an investigated case"},
    "case.pick_open": {"ko": "열기", "en": "Open"},
    "case.pick_none": {"ko": "이 스냅샷에는 조사 완료된 실행이 없습니다.", "en": "This snapshot has no completed investigation runs."},
    "case.run_pick": {"ko": "이 사례의 조사 결과({n}개, 새 것부터)", "en": "Investigation results for this case ({n}, newest first)"},
    # ---- 결정 기록 · 재조사 · 도움 -------------------------------------------------------------------------------
    "assist.case": {"ko": "사례", "en": "Case"},
    "assist.suggested": {"ko": "제안: {verdict}", "en": "Suggested: {verdict}"},
    "assist.none": {"ko": "사례가 선택되지 않았습니다. 담당자 홈에서 사례를 고릅니다.", "en": "No case is selected. Choose one on the analyst home."},
    "step.1": {"ko": "경보 발생", "en": "Alert raised"},
    "step.1_desc": {"ko": "{month} 통계 · {signal}", "en": "{month} statistics · {signal}"},
    "step.2": {"ko": "조사 완료", "en": "Investigation completed"},
    "step.2_desc": {"ko": "{time} · {verify} · 제안 {verdict}", "en": "{time} · {verify} · suggested {verdict}"},
    "step.2_pending": {"ko": "아직 조사 결과가 없음", "en": "no investigation result yet"},
    "step.3": {"ko": "담당자 결정 ← 지금", "en": "Analyst decision ← now"},
    "step.3_desc": {"ko": "제안을 따를지, 다르게 볼지 기록", "en": "Record whether you follow the suggestion or see it differently"},
    "step.4": {"ko": "사후 확인", "en": "Follow-up check"},
    "step.4_desc": {"ko": "다음 달 통계 현행화(매월 15일경) 뒤 열림", "en": "Opens after next month's statistics revision (around the 15th)"},
    "decide.title": {"ko": "담당자 결정", "en": "Analyst decision"},
    "decide.question": {"ko": "이 사례를 어떻게 다루겠습니까?", "en": "How will you handle this case?"},
    "decide.follow": {"ko": "제안대로 {verdict}", "en": "Follow the suggestion: {verdict}"},
    "decide.opt.MAINTAIN": {"ko": "검토 유지로", "en": "Keep under review"},
    "decide.opt.MONITOR": {"ko": "모니터링으로", "en": "Monitor"},
    "decide.opt.HOLD": {"ko": "자료 보류로", "en": "Data hold"},
    "decide.desc.MAINTAIN": {"ko": "설명되지 않는 변동. 내 검토 목록에 남겨 둡니다.", "en": "Unexplained change. Keep it on my review list."},
    "decide.desc.MONITOR": {"ko": "시장 전체 요인으로 보고 다음 달 같은 사례를 다시 봅니다.",
                            "en": "Treat it as a market-wide factor and re-check the same case next month."},
    "decide.desc.HOLD": {"ko": "자료가 미심쩍어 다음 통계 현행화 뒤 다시 확인합니다.",
                         "en": "The data looks doubtful; re-check after the next statistics revision."},
    "decide.memo": {"ko": "이유 메모 (선택)", "en": "Reason (optional)"},
    "decide.reviewer": {"ko": "담당자 표시 이름 (계정·권한 없음, 기록에만 남음)",
                        "en": "Analyst display name (no accounts or permissions; stored in the record only)"},
    "decide.save": {"ko": "기록 저장", "en": "Save record"},
    "decide.saved_with": {"ko": "함께 저장: 결정 · 시각 · 보고서 해시 · 스냅샷 ID · 정책 버전",
                          "en": "Also saved: decision · time · report hash · snapshot ID · policy version"},
    "decide.review_note": {
        "ko": "보고서나 자료가 뒤에 바뀌면 이 기록은 지워지지 않고 \"재검토 필요\"로 표시됩니다. 완료되지 않은 조사는 기록할 수 없습니다.",
        "en": "If the report or data changes later, this record is kept and marked \"review required\". An incomplete "
              "investigation cannot be recorded."},
    "decide.saved": {"ko": "기록을 저장했습니다: {path}", "en": "Record saved: {path}"},
    "decide.reject_not_completed": {"ko": "완료되지 않은 조사는 기록할 수 없습니다(실행 상태 {status}).",
                                    "en": "An incomplete investigation cannot be recorded (execution status {status})."},
    "decide.error": {"ko": "기록을 저장하지 못했습니다({name}).", "en": "Could not save the record ({name})."},
    "decide.no_run": {"ko": "조사 결과가 없어 결정을 기록할 수 없습니다.", "en": "There is no investigation result, so a decision cannot be recorded."},
    "reinv.title": {"ko": "재조사 요청", "en": "Request re-investigation"},
    "reinv.desc": {"ko": "같은 조사 절차가 다시 돌고 새 보고서가 이 사례에 붙습니다(보통 1~2분). 이전 보고서는 그대로 남습니다.",
                   "en": "The same investigation procedure runs again and a new report is attached to this case (usually 1–2 "
                         "minutes). The previous report is kept."},
    "reinv.reason1": {"ko": "통계가 현행화되어(정정 반영) 값이 달라졌을 수 있음", "en": "The statistics may have been revised (corrections applied)"},
    "reinv.reason2": {"ko": "다른 상대국과의 비교를 더 보고 싶음", "en": "I want more comparison with other partners"},
    "reinv.reason3": {"ko": "하위품목(HS10) 단위로 다시 나누어 보고 싶음", "en": "I want the breakdown by sub-heading (HS10) again"},
    "reinv.button": {"ko": "재조사 요청", "en": "Request re-investigation"},
    "reinv.replay_note": {"ko": "이 프로세스 환경에 NVIDIA_API_KEY가 없어 재생 파일이 있는 합성 사례만 다시 돌 수 있습니다(재생 실행, 점수표 근거 아님).",
                          "en": "NVIDIA_API_KEY is not in this process environment, so only synthetic cases with a replay file "
                                "can be re-run (replay run; not scorecard evidence)."},
    "reinv.cannot": {"ko": "키가 없고 이 사례의 재생 파일도 없어 지금은 재조사할 수 없습니다.",
                     "en": "There is no key and no replay file for this case, so re-investigation is not possible now."},
    "reinv.done": {"ko": "재조사가 끝났습니다. 새 실행 폴더: {run}", "en": "Re-investigation finished. New run folder: {run}"},
    "reinv.failed": {"ko": "재조사 실행이 실패했습니다(종료 코드 {code}).", "en": "The re-investigation run failed (exit code {code})."},
    "reinv.not_score": {"ko": "화면에서 시작한 실행은 점수표 근거가 아닙니다.", "en": "Runs started from the screen are not scorecard evidence."},
    "followup.title": {"ko": "사후 확인 기록", "en": "Follow-up record"},
    "followup.locked": {"ko": "다음 달 통계 현행화 뒤 열립니다", "en": "Opens after next month's statistics revision"},
    "followup.question": {"ko": "다음 달에 확인한 결과", "en": "Result seen next month"},
    "followup.opt1": {"ko": "변동이 계속됨", "en": "Change persists"},
    "followup.opt2": {"ko": "변동이 해소됨", "en": "Change resolved"},
    "followup.opt3": {"ko": "자료 정정으로 경보가 사라짐", "en": "Alert removed by a data correction"},
    "followup.desc": {"ko": "사후 확인 결과는 사례에 붙어 쌓이고, 나중에 경보 기준과 조사 지침을 손보는 근거가 됩니다.",
                      "en": "Follow-up results accumulate on the case and later inform changes to alert thresholds and "
                            "investigation guidance."},
    "followup.demo": {"ko": "이 데모는 자료 갱신이 없어 사후 확인을 저장하지 않습니다.",
                      "en": "This demo has no data updates, so follow-up records are not saved."},
    "history.title": {"ko": "이 사례의 기록", "en": "History of this case"},
    "history.alert": {"ko": "{month} 통계 — {signal}", "en": "{month} statistics — {signal}"},
    "history.alert_unit": {"ko": "단가 {value}%로 경보 발동", "en": "unit value {value}%, alert triggered"},
    "history.alert_share": {"ko": "점유율 {value}%p로 경보 발동", "en": "import share {value} pp, alert triggered"},
    "history.alert_other": {"ko": "경보 발동", "en": "alert triggered"},
    "history.run": {"ko": "{time} — 조사 완료, {verify}, 제안 \"{verdict}\" ({run})",
                    "en": "{time} — investigated, {verify}, suggested \"{verdict}\" ({run})"},
    "history.run_failed": {"ko": "{time} — 조사 실행 {status} ({run})", "en": "{time} — run {status} ({run})"},
    "history.decision": {"ko": "{time} — 담당자 결정 \"{decision}\"{reviewer} [{validity}]",
                         "en": "{time} — analyst decision \"{decision}\"{reviewer} [{validity}]"},
    "history.by": {"ko": " ({reviewer})", "en": " ({reviewer})"},
    "history.no_decision": {"ko": "담당자 결정 — 아직 없음", "en": "Analyst decision — none yet"},
    "validity.VALID": {"ko": "유효", "en": "valid"},
    "validity.REVIEW_REQUIRED": {"ko": "재검토 필요", "en": "review required"},
    "glossary.title": {"ko": "용어 도움", "en": "Glossary"},
    "glossary.unit": {"ko": "kg당 단가", "en": "Unit value (USD/kg)"},
    "glossary.unit_desc": {"ko": "한 달 수입금액(USD)을 순중량(kg)으로 나눈 값. 품목 안 구성이 바뀌면 함께 움직입니다.",
                           "en": "Monthly import value (USD) divided by net weight (kg). It moves when the mix within the product changes."},
    "glossary.share": {"ko": "점유율", "en": "Import share"},
    "glossary.share_desc": {"ko": "그 품목 전체 수입금액 가운데 한 나라의 비중(%). %p는 두 비중의 차이입니다.",
                            "en": "One partner's share (%) of the total import value of the product. pp (percentage points) is the difference between two shares."},
    "glossary.yoy": {"ko": "전년 같은 달", "en": "Same month a year earlier"},
    "glossary.yoy_desc": {"ko": "계절 요인을 피하려고 12개월 전 같은 달과 비교합니다.",
                          "en": "Compared with the same month 12 months earlier to avoid seasonal effects."},
    "glossary.mix": {"ko": "구성효과", "en": "Mix effect"},
    "glossary.mix_desc": {"ko": "비싼·싼 하위품목의 비중이 바뀌어 평균 단가가 움직인 몫. 이것으로 설명되면 \"모니터링\"입니다.",
                          "en": "The part of the average unit-value change caused by a shift between expensive and cheap sub-headings. "
                                "If it explains the change, the next step is \"Monitor\"."},
    "glossary.hs6": {"ko": "HS6", "en": "HS6"},
    "glossary.hs6_desc": {"ko": "국제 품목분류 6자리 코드. {hs6}는 {item}입니다.",
                          "en": "The 6-digit international product classification code. {hs6} is {item}."},
    "ask.title": {"ko": "더 물어볼 곳", "en": "Where to ask"},
    "ask.desc": {"ko": "조사 과정이 궁금하면 관리자에게 사례 ID를 알려 주세요:",
                 "en": "To ask about the investigation process, give the administrator this case ID:"},
    "ask.admin_link": {"ko": "관리자용 조사 기록 화면에서 이 사례 열기", "en": "Open this case in the admin investigation log"},
}


def t(key: str, lang: str = DEFAULT_LANG, **fields: object) -> str:
    """문구 하나. 없는 키는 키 이름 그대로 돌려준다(빈 화면 대신 키가 보이게). fields가 있으면 자리표시를 채운다."""
    entry = STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(lang) or entry.get(DEFAULT_LANG) or key
    return text.format(**fields) if fields else text


def verdict_label(code: object, lang: str = DEFAULT_LANG) -> str:
    """판정 상태 코드의 이름표. 모르는 값은 원문 그대로다(고쳐 적지 않는다)."""
    if code is None:
        return t("verdict.none", lang)
    key = f"verdict.{code}"
    return t(key, lang) if key in STRINGS else str(code)


def month_label(period: object, lang: str = DEFAULT_LANG) -> str:
    """`YYYYMM` → 한국어 "2024년 12월", 영어 "Dec 2024". 형식이 다르면 원문 그대로다."""
    if not isinstance(period, str) or len(period) != 6 or not period.isdigit() or not 1 <= int(period[4:]) <= 12:
        return str(period)
    year, month = period[:4], int(period[4:])
    if lang == "en":
        return f"{MONTH_EN[month - 1]} {year}"
    return f"{year}년 {month}월"


def month_short(period: object) -> str:
    """`YYYYMM` → "YYYY-MM"(칩·표 머리용, 언어 공통)."""
    if isinstance(period, str) and len(period) == 6 and period.isdigit():
        return f"{period[:4]}-{period[4:]}"
    return str(period)


def hs6_name(hs6: object, lang: str = DEFAULT_LANG) -> str | None:
    """품목 이름. 용어표에 없는 코드(합성 픽스처)는 None이다."""
    entry = HS6_NAMES.get(hs6) if isinstance(hs6, str) else None
    return entry.get(lang) or entry.get(DEFAULT_LANG) if entry else None


def item_label(hs6: object, lang: str = DEFAULT_LANG) -> str:
    """품목 표시: 이름이 있으면 이름, 없으면 HS6 코드."""
    return hs6_name(hs6, lang) or f"HS6 {hs6}"


def load_country_names(repo_root: Path, lang: str = DEFAULT_LANG) -> dict[str, str]:
    """관세청 국가코드 → 국가 이름(data/reference/country_map.csv: ko는 kcs_country_name, en은 baci_country_name).
    읽지 못하면 빈 표다."""
    column = "baci_country_name" if lang == "en" else "kcs_country_name"
    try:
        with (repo_root / COUNTRY_MAP).open(encoding="utf-8", newline="") as fh:
            return {row["cntyCd"]: row[column] for row in csv.DictReader(fh) if row.get("cntyCd") and row.get(column)}
    except (OSError, KeyError, csv.Error):
        return {}


def partner_label(partner: object, countries: dict[str, str]) -> str:
    """상대국 표시: 이름이 있으면 이름, 없으면 코드(합성 픽스처)."""
    return countries.get(partner, str(partner)) if isinstance(partner, str) else str(partner)
