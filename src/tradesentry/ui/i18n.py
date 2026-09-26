"""화면 문구 표(한국어·영어)와 이름표.

화면(경보 목록·사례 검토·결정 기록, 로딩 창·조사 중 표시)의 문구 전부를 키 → {"ko", "en"}로 둔다. 문구는 사용자 승인 디자인
v2(scratchpad HTML 목업 `Main2`·`Loading2`·`Main2_running`·`CaseDetail2`·`Assist2`와 `_en` 판)를 따른다(UI3). 판정은
평이한 이름("검토 유지·모니터링·자료 보류", EN "Keep under review·Monitor·Data hold")으로만 보이고 상태 코드(MAINTAIN 등)는
화면 문구에 넣지 않는다. 두 언어의 키 집합이 같고 빈 값이 없으며 자리표시({name})가 같음을 시험이 강제한다
(tests/test_ui_pages.py). streamlit을 import하지 않는다.
"""
import csv
from pathlib import Path

LANGS = ("ko", "en")
DEFAULT_LANG = "ko"
LANG_NAMES = {"ko": "한국어", "en": "English"}
LANG_SHORT = {"ko": "한국어", "en": "EN"}  # 머리 띠의 언어 전환
COUNTRY_MAP = Path("data") / "reference" / "country_map.csv"

# 품목 이름(UI2 지시서 용어표). 용어표에 없는 코드만 코드로 보인다.
HS6_NAMES = {
    "850431": {"ko": "계기용 변압기 (소용량)", "en": "Transformers ≤ 1 kVA (incl. instrument transformers)"},
    "850432": {"ko": "계기용 변압기 (중용량) · 전압 조정기", "en": "Transformers 1–16 kVA · voltage regulators"},
    "850450": {"ko": "인덕터 (기타)", "en": "Inductors, other"},
    "850490": {"ko": "변압기·전원장치 부분품", "en": "Parts of transformers & power supplies"},
}

MONTH_EN = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
MONTH_EN_FULL = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
                 "November", "December")
FIXTURE_PARTNERS = ("XA", "XB", "XC")  # 합성 픽스처의 가상 상대국 코드 → STRINGS["partner.XA"] 등의 이름

STRINGS: dict[str, dict[str, str]] = {
    # ---- 공통 · 머리 띠 ------------------------------------------------------------------------------------------
    "app.subtitle": {"ko": "수입통계 경보 검토", "en": "Import-statistics alert review"},
    "app.lang_label": {"ko": "언어 / Language", "en": "언어 / Language"},
    "app.snapshot_none": {
        "ko": "data/snapshots/ 아래 정본 빌드(snapshot_build.sqlite)가 있는 스냅샷이 없습니다. 합성 픽스처는 "
              "`uv run --locked python -c \"from tradesentry.snapshot import fixture; fixture.materialize()\"`로 만듭니다.",
        "en": "No snapshot with a canonical build (snapshot_build.sqlite) exists under data/snapshots/. Create the synthetic "
              "fixture with `uv run --locked python -c \"from tradesentry.snapshot import fixture; fixture.materialize()\"`."},
    "app.no_data": {"ko": "볼 수 있는 통계 자료가 없습니다. 관리자에게 문의하세요.",
                    "en": "No statistics are available to show. Please contact the administrator."},
    "app.data_line": {"ko": "자료: 관세청 수입통계 {start} ~ {end}",
                      "en": "Data: Korea Customs Service import statistics, {start} – {end}"},
    "app.error_read": {"ko": "기록을 읽지 못했습니다({name}).", "en": "Could not read the record ({name})."},
    "nav.home": {"ko": "경보 목록", "en": "Alerts"},
    "nav.case": {"ko": "사례 검토", "en": "Case review"},
    "nav.assist": {"ko": "결정 기록", "en": "Decision"},
    "nav.admin": {"ko": "관리자 화면", "en": "Admin view"},
    "admin.snapshot_label": {"ko": "담당자 화면 자료(스냅샷)", "en": "Data for the analyst screens (snapshot)"},
    "admin.snapshot_note": {"ko": "시험·시연용입니다. 담당자 화면(경보 목록·사례 검토·결정 기록)이 이 자료를 씁니다.",
                            "en": "For testing and demos. The analyst screens (alerts, case review, decision) use this data."},
    "foot.terms": {
        "ko": "kg당 단가 = 수입금액 ÷ 순중량. 점유율 = 그 품목 전체 수입 가운데 그 나라의 비중. 조사 결과의 제안은 참고용이며 "
              "기관 승인이나 통관 조치가 아닙니다.",
        "en": "Unit value = import value ÷ net weight. Share = the partner's part of Korea's total imports of that product. "
              "Suggestions are guidance only, not an institutional approval or a customs action."},
    "foot.admin": {"ko": "관리자 화면", "en": "Admin view"},
    # ---- 판정 --------------------------------------------------------------------------------------------------
    "verdict.MAINTAIN": {"ko": "검토 유지", "en": "Keep under review"},
    "verdict.MONITOR": {"ko": "모니터링", "en": "Monitor"},
    "verdict.HOLD": {"ko": "자료 보류", "en": "Data hold"},
    "verdict.none": {"ko": "—", "en": "—"},
    "verdict_lc.MAINTAIN": {"ko": "검토 유지", "en": "keep under review"},
    "verdict_lc.MONITOR": {"ko": "모니터링", "en": "monitoring"},
    "verdict_lc.HOLD": {"ko": "자료 보류", "en": "data hold"},
    "meaning.MAINTAIN": {"ko": "변동이 설명되지 않아 검토를 계속하는 것이 좋습니다.",
                         "en": "The change is not explained; continued review is advised."},
    "meaning.MONITOR": {"ko": "하위품목 구성 변화로 설명되어 다음 달 같은 사례를 다시 확인하는 것이 좋습니다.",
                        "en": "Explained by a change in product mix; re-checking the same case next month is advised."},
    "meaning.HOLD": {"ko": "검증할 자료가 모자라 다음 통계 갱신 뒤 다시 확인하는 것이 좋습니다.",
                     "en": "Data needed for verification is missing; re-checking after the next statistics update is advised."},
    "define.MAINTAIN": {"ko": "변동이 설명되지 않아 검토를 계속합니다.", "en": "unexplained change; keep reviewing."},
    "define.MONITOR": {"ko": "구성 변화로 설명되어 다음 달 다시 확인합니다.", "en": "explained by a mix change; re-check next month."},
    "define.HOLD": {"ko": "자료가 모자라 다음 통계 갱신 뒤 다시 봅니다.", "en": "data is incomplete; re-check after the next statistics update."},
    "signal.unit_change": {"ko": "단가 {value}%", "en": "unit value {value}%"},
    "signal.share_change": {"ko": "점유율 {value}%p", "en": "share {value} pp"},
    # ---- 경보 목록: 요약 카드 --------------------------------------------------------------------------------------
    "home.count": {"ko": "{n}건", "en": "{n}"},
    "sum.title": {"ko": "{month} 요약", "en": "{month} at a glance"},
    "sum.desc": {"ko": "전년 같은 달과 비교해 크게 바뀐 품목·국가 조합. 경보는 조사의 시작점이며 위법·부정을 뜻하지 않습니다.",
                 "en": "Product–partner pairs that moved sharply against the same month a year earlier. An alert starts an "
                       "investigation; it does not imply wrongdoing."},
    "sum.total": {"ko": "이번 달 경보", "en": "Alerts this month"},
    "sum.last_month": {"ko": "지난달 {n}건", "en": "last month {n}"},
    "sum.last_month_none": {"ko": "지난달은 비교 자료가 없음", "en": "no comparable earlier month"},
    "sum.unit": {"ko": "단가가 크게 바뀐 것", "en": "Big unit-value moves"},
    "sum.unit_updown": {"ko": "오른 것 {up} · 내린 것 {down}", "en": "{up} up · {down} down"},
    "sum.share": {"ko": "점유율이 크게 바뀐 것", "en": "Big share moves"},
    "sum.share_stopped": {"ko": "수입이 끊긴 나라 {n}", "en": "{n} partner(s) stopped importing"},
    "sum.share_updown": {"ko": "늘어난 것 {up} · 줄어든 것 {down}", "en": "{up} up · {down} down"},
    "sum.investigated": {"ko": "조사 완료", "en": "Investigated"},
    "sum.v.MAINTAIN": {"ko": "검토 유지 제안 {n}", "en": "{n} suggest keeping under review"},
    "sum.v.MONITOR": {"ko": "모니터링 제안 {n}", "en": "{n} suggest monitoring"},
    "sum.v.HOLD": {"ko": "자료 보류 제안 {n}", "en": "{n} suggest a data hold"},
    "sum.running": {"ko": "조사 중 {n}", "en": "{n} running"},
    "sum.none_yet": {"ko": "아직 조사한 사례 없음", "en": "none investigated yet"},
    "sum.awaiting": {"ko": "내 결정을 기다리는 사례", "en": "Waiting for my decision"},
    "sum.awaiting_sub": {"ko": "조사는 끝났고 결정만 남음", "en": "investigated, not yet decided"},
    # ---- 경보 목록: 조회 조건 --------------------------------------------------------------------------------------
    "flt.month": {"ko": "월", "en": "Month"},
    "flt.signal": {"ko": "바뀐 것", "en": "What moved"},
    "flt.signal.all": {"ko": "전체", "en": "All"},
    "flt.signal.unit_value": {"ko": "단가", "en": "Unit value"},
    "flt.signal.share": {"ko": "점유율", "en": "Import share"},
    "flt.progress": {"ko": "진행 상태", "en": "Progress"},
    "flt.progress.all": {"ko": "전체", "en": "All"},
    "flt.progress.not_started": {"ko": "조사 전", "en": "Not investigated"},
    "flt.progress.running": {"ko": "조사 중", "en": "Investigating"},
    "flt.progress.awaiting": {"ko": "조사 완료 · 결정 대기", "en": "Investigated · awaiting decision"},
    "flt.progress.decided": {"ko": "결정 완료", "en": "Decided"},
    "flt.sort": {"ko": "정렬", "en": "Sort"},
    "flt.sort.change": {"ko": "변화 큰 순", "en": "Largest change"},
    "flt.sort.item": {"ko": "품목", "en": "Product"},
    "flt.sort.partner": {"ko": "상대국", "en": "Partner"},
    "flt.sort.progress": {"ko": "진행 상태", "en": "Progress"},
    "flt.find": {"ko": "찾기", "en": "Find"},
    "flt.find_ph": {"ko": "품목 또는 국가", "en": "Product or partner"},
    # ---- 경보 목록: 표 -----------------------------------------------------------------------------------------------
    "col.item": {"ko": "품목", "en": "Product"},
    "col.partner": {"ko": "상대국", "en": "Partner"},
    "col.details": {"ko": "변화내용", "en": "Change details"},
    "col.change": {"ko": "변화", "en": "Change"},
    "col.progress": {"ko": "진행 상태", "en": "Progress"},
    "col.action": {"ko": "동작", "en": "Action"},
    "chg.unit": {"ko": "kg당 단가 {a} → {b} USD", "en": "Unit value {a} → {b} USD/kg"},
    "chg.share": {"ko": "점유율 {a}% → {b}%", "en": "Share {a}% → {b}%"},
    "chg.share_stopped": {"ko": "점유율 {a}% → {b}% — {month}에 수입이 없었습니다", "en": "Share {a}% → {b}% — no imports in {month}"},
    "chg.unit_na": {"ko": "단가는 비교할 수 없음", "en": "Unit value not comparable"},
    "chg.share_na": {"ko": "점유율 값 없음", "en": "Share not available"},
    "chg.pp": {"ko": "{v}%p", "en": "{v} pp"},
    "chg.na": {"ko": "비교 불가", "en": "n/a"},
    "prog.not_started": {"ko": "조사 전", "en": "Not investigated"},
    "prog.running": {"ko": "조사 중 · {time}", "en": "Investigating · {time}"},
    "prog.awaiting": {"ko": "조사 완료 · {verdict} 제안", "en": "Investigated · {verdict} suggested"},
    "prog.awaiting_sub": {"ko": "내 결정 대기", "en": "awaiting my decision"},
    "prog.decided": {"ko": "결정 완료 · {decision}", "en": "Decided · {decision}"},
    "prog.review_required": {"ko": "재검토 필요", "en": "Review required"},
    "prog.review_required_sub": {"ko": "근거 보고서가 바뀌었습니다", "en": "the underlying report changed"},
    "prog.failed": {"ko": "조사 실패", "en": "Investigation failed"},
    "home.btn_start": {"ko": "조사 시작", "en": "Investigate"},
    "home.btn_view": {"ko": "결과 보기", "en": "View result"},
    "home.btn_running": {"ko": "조사 중", "en": "Running"},
    "home.locked_running": {"ko": "진행 중인 조사가 끝난 뒤 시작할 수 있습니다", "en": "You can start once the current investigation finishes"},
    "home.cannot_run": {"ko": "조사 모델 연결이 설정되지 않아 지금은 이 사례의 조사를 시작할 수 없습니다. 관리자에게 문의하세요.",
                        "en": "The investigation model connection is not set up, so this case cannot be investigated now. "
                              "Please contact the administrator."},
    "home.no_alerts": {"ko": "이 자료에는 경보가 없습니다.", "en": "There are no alerts in this data."},
    "home.filtered_empty": {"ko": "조건에 맞는 경보가 없습니다.", "en": "No alerts match the filters."},
    "home.error_alerts": {"ko": "경보 목록을 만들지 못했습니다({name}).", "en": "Could not build the alert list ({name})."},
    # ---- 로딩 창 · 조사 중 표시 ---------------------------------------------------------------------------------------
    "load.title": {"ko": "조사 중입니다", "en": "Investigating…"},
    "load.case": {"ko": "{partner}산 {item} · {month} 경보", "en": "{item} from {partner} · {month} alert"},
    "load.case_unknown": {"ko": "사례", "en": "Case"},
    "load.step.check": {"ko": "자료 상태 확인 — 기준월·비교월 자료가 모두 있는지", "en": "Checking the data — are both months available?"},
    "load.step.compare": {"ko": "이력과 다른 상대국 비교", "en": "History and comparison with other partners"},
    "load.step.decompose": {"ko": "하위품목 구성 변화 확인", "en": "Checking for a change in product mix"},
    "load.step.critic": {"ko": "검수자의 반대 설명 점검과 수정", "en": "Critic checks for counter-explanations; one revision"},
    "load.step.verify": {"ko": "숫자를 원본 통계와 대조", "en": "Verifying every figure against the source statistics"},
    "load.expect": {"ko": "보통 30초에서 90초가 걸립니다. 끝나면 결과 화면이 바로 열립니다.",
                    "en": "Usually takes 30–90 seconds. The result opens automatically when done."},
    "load.back": {"ko": "목록으로", "en": "Back to list"},
    "load.retrying": {"ko": "응답이 늦어 다시 요청하는 중입니다.", "en": "Slow response; requesting again."},
    "load.footnote": {
        "ko": "조사가 실패하면(연결 지연 등) 여기서 알려 주고 \"다시 시도\" 버튼이 나옵니다. 조사자와 검수자는 정해진 조회 도구로 "
              "통계 원본만 조회합니다.",
        "en": "If the investigation fails (e.g. a slow connection), you will see it here with a \"Try again\" button. The "
              "investigator and critic query only the source statistics through fixed lookup tools."},
    "load.footnote_replay": {
        "ko": "이 조사는 저장해 둔 모델 응답을 다시 쓰는 시연 실행(재생)이라 외부 모델을 부르지 않습니다. 조사가 실패하면 여기서 "
              "알려 주고 \"다시 시도\" 버튼이 나옵니다.",
        "en": "This is a demo run that reuses stored model responses (replay), so no external model is called. If the "
              "investigation fails, you will see it here with a \"Try again\" button."},
    "load.failed_title": {"ko": "조사가 끝나지 못했습니다", "en": "The investigation did not finish"},
    "load.failed": {"ko": "연결 지연 같은 문제로 조사가 끝나지 못했습니다. 다시 시도하거나 닫을 수 있습니다. 이전 결과는 그대로 남아 있습니다.",
                    "en": "The investigation stopped because of a problem such as a slow connection. You can try again or "
                          "close this. Earlier results are kept."},
    "load.timeout": {"ko": "제한 시간 안에 끝나지 않아 조사를 멈췄습니다. 다시 시도하거나 닫을 수 있습니다. 이전 결과는 그대로 남아 있습니다.",
                     "en": "The investigation did not finish within the time limit and was stopped. You can try again or "
                           "close this. Earlier results are kept."},
    "load.retry": {"ko": "다시 시도", "en": "Try again"},
    "load.close": {"ko": "닫기", "en": "Close"},
    "pill.case": {"ko": "{partner}산 {item}", "en": "{item} · {partner}"},
    "pill.running": {"ko": "● 조사 중 · {case} · {step}/{total}단계 · {time} ›", "en": "● Investigating · {case} · step {step}/{total} · {time} ›"},
    "pill.done": {"ko": "✓ 조사 완료 · {case} · 결과 보기 ›", "en": "✓ Investigation done · {case} · View result ›"},
    "pill.failed": {"ko": "! 조사 실패 · {case} · 다시 시도 ›", "en": "! Investigation failed · {case} · Try again ›"},
    # ---- 사례 검토 ----------------------------------------------------------------------------------------------
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
    "case.title_unknown": {"ko": "이 사례의 조사 결과", "en": "Investigation result for this case"},
    "band.near_half": {"ko": "절반 가까이", "en": "by roughly half"},
    "band.large": {"ko": "크게", "en": "substantially"},
    "band.notable": {"ko": "눈에 띄게", "en": "noticeably"},
    "band.double": {"ko": "두 배 넘게", "en": "more than twofold"},
    "chip.alert_month": {"ko": "경보 {month}", "en": "Alert: {month}"},
    "chip.baseline": {"ko": "비교 기준 {month}", "en": "Baseline: {month}"},
    "chip.investigated": {"ko": "조사 {time}", "en": "Investigated {time}"},
    "chip.pos_latest": {"ko": "(최신, {n}회 중)", "en": "(latest of {n})"},
    "chip.pos_older": {"ko": "({k}번째, {n}회 중)", "en": "({k} of {n})"},
    "chip.verified": {"ko": "숫자 확인 완료", "en": "Figures verified"},
    "chip.findings": {"ko": "숫자 확인 기록 {n}건", "en": "{n} verification note(s)"},
    "chip.not_completed": {"ko": "조사가 끝나지 않음", "en": "Not completed"},
    "case.crumb_home": {"ko": "경보 목록", "en": "Alerts"},
    "case.next_step": {"ko": "다음 업무 제안", "en": "Suggested next step"},
    "case.btn_record": {"ko": "내 결정 기록하기", "en": "Record my decision"},
    "case.sec_what": {"ko": "무슨 일이 있었나", "en": "What happened"},
    "case.unit_label": {"ko": "kg당 수입단가 · 1년 전 대비", "en": "Unit value (USD/kg) · vs. a year earlier"},
    "case.threshold_hit": {"ko": "기준({thr}%)을 넘어 경보", "en": "Above the {thr}% threshold → alert"},
    "case.threshold_miss": {"ko": "기준({thr}%) 미만, 경보 아님", "en": "Below the {thr}% threshold → no alert"},
    "case.threshold_unknown": {"ko": "경보 기준과 비교한 기록 없음", "en": "no comparison with the threshold recorded"},
    "case.share_label": {"ko": "{partner}의 수입 점유율", "en": "{partner}'s import share"},
    "case.share_hit": {"ko": "{d}%p, 기준({thr}%p) 이상 → 경보", "en": "{d} pp, at or above the {thr} pp threshold → alert"},
    "case.share_miss": {"ko": "{d}%p, 기준({thr}%p) 미만, 경보 아님", "en": "{d} pp, below the {thr} pp threshold → no alert"},
    "case.value_missing": {"ko": "값 없음", "en": "no value"},
    "case.not_comparable": {"ko": "비교 불가", "en": "not comparable"},
    "case.sec_found": {"ko": "조사에서 확인한 것", "en": "What the investigation found"},
    "case.decomp_head.MONITOR": {"ko": "하위품목 구성이 바뀐 것으로 설명됩니다.", "en": "Explained by a change in product mix."},
    "case.decomp_head.MAINTAIN": {"ko": "하위품목 구성이 바뀐 탓만으로는 설명되지 않습니다.",
                                  "en": "A change in product mix alone does not explain it."},
    "case.decomp_head.HOLD": {"ko": "하위품목 구성효과를 판정할 자료가 모자랍니다.",
                              "en": "Data to judge the mix effect is insufficient."},
    "case.decomp_head.other": {"ko": "단가 변화를 하위품목 단위로 나누어 보았습니다.",
                               "en": "The unit-value change was split by sub-heading."},
    "case.decomp_body": {
        "ko": "같은 하위품목 안에서 단가가 움직인 몫이 {within} USD/kg이고, 하위품목 구성이 바뀌어 생긴 몫은 {mix} USD/kg, "
              "나머지는 {residual} USD/kg입니다.",
        "en": "Prices within the same sub-headings moved by {within} USD/kg, the shift in mix added {mix} USD/kg, and "
              "{residual} USD/kg is the remainder."},
    "case.compare_head": {"ko": "다른 상대국과 비교하면", "en": "Compared with other partners"},
    "case.compare_item": {"ko": "같은 품목의 {partner}산 kg당 단가는 같은 기간 {value}% {dir}.",
                          "en": "Over the same period, the unit value of the same product from {partner} {dir} by {value}%."},
    "case.compare_share_item": {"ko": "{partner}의 점유율 변화는 {value}%p입니다.", "en": "{partner}'s import share changed by {value} pp."},
    "case.compare_value_item": {"ko": "{partner}: {value} {unit}", "en": "{partner}: {value} {unit}"},
    "case.compare_note": {"ko": "시장 전체 요인일 가능성을 열어 두어야 합니다.", "en": "A market-wide factor cannot be ruled out."},
    "dir.down": {"ko": "내렸습니다", "en": "fell"},
    "dir.up": {"ko": "올랐습니다", "en": "rose"},
    "dir.flat": {"ko": "변하지 않았습니다", "en": "was flat"},
    "case.share_head.NOT_TRIGGERED": {"ko": "점유율은 크게 움직이지 않았습니다.", "en": "The import share barely moved."},
    "case.share_head.other": {"ko": "점유율이 기준 이상으로 움직였습니다.", "en": "The import share moved beyond the threshold."},
    "case.share_body": {"ko": "{s0}%에서 {s1}%로, 기준({thr}%p)에 {rel}.",
                        "en": "From {s0}% to {s1}%, {rel} the threshold ({thr} pp)."},
    "rel.below": {"ko": "미치지 않습니다", "en": "below"},
    "rel.at_or_above": {"ko": "이르거나 넘습니다", "en": "at or above"},
    "case.sub_head": {"ko": "하위품목별 단가 변화율", "en": "Unit-value change by sub-heading"},
    "case.sub_item": {"ko": "하위품목 {n}: {value}%", "en": "Sub-heading {n}: {value}%"},
    "case.data_head": {"ko": "자료 상태", "en": "Data status"},
    "case.data_item": {"ko": "{partner} {period}: {status}", "en": "{partner} {period}: {status}"},
    "dstat.OBSERVED": {"ko": "관측됨", "en": "observed"},
    "dstat.NOT_COLLECTED": {"ko": "미수집", "en": "not collected"},
    "dstat.REQUEST_FAILED": {"ko": "요청 실패", "en": "request failed"},
    "dstat.UNRESOLVED_ZERO": {"ko": "응답에 행 없음", "en": "no rows in the response"},
    "dstat.CONFIRMED_NO_TRADE": {"ko": "무거래 확정", "en": "confirmed no trade"},
    "dstat.other": {"ko": "확인되지 않은 상태", "en": "unrecognised status"},
    "case.found_empty": {"ko": "이 보고서에는 확인된 사실 주장이 없습니다.", "en": "This report has no verified factual claims."},
    "case.sec_alt": {"ko": "다른 설명 가능성", "en": "Other possible explanations"},
    "case.alt_note": {"ko": "조사자가 제시한 가설, 통계로 확인된 것은 아님", "en": "raised by the investigator, not confirmed by the statistics"},
    "case.alt_empty": {"ko": "조사자가 제시한 가설이 없습니다.", "en": "The investigator raised no hypotheses."},
    "case.korean_original": {"ko": "(원문)", "en": "(Korean original)"},
    "case.sec_conclusion": {"ko": "결론 — {verdict}", "en": "Conclusion — {verdict}"},
    "case.conclusion_not_completed": {"ko": "조사가 끝나지 않아 제안이 없습니다.",
                                      "en": "The investigation did not finish, so there is no suggestion."},
    "case.narrative_quote": {"ko": "조사 보고서 요약 원문 보기", "en": "Show the report summary (Korean original)"},
    "case.sec_meaning": {"ko": "제안이 뜻하는 것", "en": "What each suggestion means"},
    "case.this_case": {"ko": "(이 사례)", "en": "(this case)"},
    "case.sec_basis": {"ko": "근거로 삼은 것", "en": "What this relied on"},
    "basis.data": {"ko": "자료", "en": "Data"},
    "basis.data_value": {"ko": "관세청 수입통계 {start} ~ {end}", "en": "Korea Customs Service import statistics, {start} – {end}"},
    "basis.data_value_na": {"ko": "관세청 수입통계(한 시점에 고정한 자료)", "en": "Korea Customs Service import statistics (fixed at one point in time)"},
    "basis.rule": {"ko": "기준", "en": "Baseline"},
    "basis.rule_value": {"ko": "전년 같은 달과 비교. 단가 {u}%, 점유율 {s}%p", "en": "Same month a year earlier. Thresholds: unit value {u}%, share {s} pp"},
    "basis.method": {"ko": "방법", "en": "Method"},
    "basis.method_value": {"ko": "조사자와 검수자가 통계 원본만 조회. 외부 자료 없음",
                           "en": "Investigator and critic queried the source statistics only. No external data"},
    "basis.verify": {"ko": "확인", "en": "Verified"},
    "basis.verify_value": {"ko": "보고서의 숫자 {n}개를 통계 원본과 대조해 모두 일치", "en": "{n} figures in the report matched the source statistics"},
    "basis.verify_findings": {"ko": "보고서의 숫자 {n}개, 확인 기록 {m}건", "en": "{n} figures in the report, {m} verification note(s)"},
    "case.sec_caution": {"ko": "읽을 때 유의할 점", "en": "Please note"},
    "case.caution": {
        "ko": "단가 변화는 부정·위법·원산지 조작의 증거가 아닙니다. 제안은 참고용이며 기관 승인이나 통관 조치가 아닙니다.",
        "en": "A change in unit value is not evidence of fraud, illegality or origin manipulation. The suggestion is "
              "guidance, not an institutional approval or a customs action."},
    "case.admin_link": {"ko": "조사 과정을 자세히 보려면 관리자 화면 ›", "en": "Investigation details in the admin view ›"},
    "case.none_selected": {"ko": "검토할 사례가 선택되지 않았습니다. 경보 목록에서 \"결과 보기\"를 누르거나 아래에서 고릅니다.",
                           "en": "No case is selected. Choose \"View result\" in the alert list, or pick one below."},
    "case.not_investigated": {"ko": "이 사례는 아직 조사 결과가 없습니다. 경보 목록에서 \"조사 시작\"을 누릅니다.",
                              "en": "This case has no investigation result yet. Use \"Investigate\" in the alert list."},
    "case.pick_label": {"ko": "조사 완료된 사례 고르기", "en": "Choose an investigated case"},
    "case.pick_open": {"ko": "열기", "en": "Open"},
    "case.pick_none": {"ko": "이 자료에는 조사 완료된 사례가 없습니다.", "en": "There are no investigated cases in this data."},
    "case.run_pick": {"ko": "조사 시각", "en": "Investigated at"},
    "case.run_latest": {"ko": "{time} (최신)", "en": "{time} (latest)"},
    # ---- 결정 기록 ----------------------------------------------------------------------------------------------
    "assist.suggested": {"ko": "제안: {verdict}", "en": "Suggested: {verdict}"},
    "assist.none": {"ko": "사례가 선택되지 않았습니다. 경보 목록이나 아래에서 사례를 고릅니다.",
                    "en": "No case is selected. Choose one in the alert list or below."},
    "step.1": {"ko": "경보 발생", "en": "Alert raised"},
    "step.1_desc": {"ko": "{month} 통계 · {signal}", "en": "{month} statistics · {signal}"},
    "step.1_desc_plain": {"ko": "{month} 통계", "en": "{month} statistics"},
    "step.2": {"ko": "조사 완료", "en": "Investigated"},
    "step.2_desc": {"ko": "{time} · 제안 {verdict}", "en": "{time} · suggested: {verdict}"},
    "step.2_pending": {"ko": "아직 조사 결과가 없음", "en": "no investigation result yet"},
    "step.3": {"ko": "내 결정 (지금)", "en": "My decision (now)"},
    "step.3_done": {"ko": "내 결정", "en": "My decision"},
    "step.3_desc": {"ko": "제안을 따를지, 다르게 볼지", "en": "Follow the suggestion, or see it differently"},
    "step.4": {"ko": "사후 확인", "en": "Follow-up"},
    "step.4_desc": {"ko": "다음 달 통계가 갱신되면 열립니다", "en": "Opens when next month's statistics arrive"},
    "decide.question": {"ko": "이 사례를 어떻게 다루겠습니까?", "en": "How will you handle this case?"},
    "decide.follow": {"ko": "제안대로 {verdict}", "en": "Follow the suggestion — {verdict}"},
    "decide.opt.MAINTAIN": {"ko": "검토 유지로", "en": "Keep under review instead"},
    "decide.opt.MONITOR": {"ko": "모니터링으로", "en": "Monitor instead"},
    "decide.opt.HOLD": {"ko": "자료 보류로", "en": "Data hold instead"},
    "decide.desc.MAINTAIN": {"ko": "내 검토 목록에 남겨 둡니다.", "en": "Stays on my review list."},
    "decide.desc.MONITOR": {"ko": "시장 전체 요인으로 보고 다음 달 다시 봅니다.", "en": "Treat it as market-wide and re-check next month."},
    "decide.desc.HOLD": {"ko": "자료가 미심쩍어 다음 통계 갱신 뒤 다시 확인합니다.", "en": "The data looks doubtful; re-check after the next update."},
    "decide.memo": {"ko": "이유 (선택)", "en": "Reason (optional)"},
    "decide.memo_ph": {"ko": "예: 미국산 단가도 비슷하게 내려가 시장 전체 요인으로 보임", "en": "e.g. US prices fell similarly — looks market-wide"},
    "decide.reviewer": {"ko": "담당자 이름", "en": "Analyst name"},
    "decide.reviewer_ph": {"ko": "예: 무역통계 담당 A", "en": "e.g. Trade statistics analyst A"},
    "decide.save": {"ko": "결정 저장", "en": "Save decision"},
    "decide.after_note": {"ko": "저장되면 이 사례는 \"결정 완료\"로 바뀝니다. 근거 보고서가 바뀌면 \"재검토 필요\"로 표시됩니다.",
                          "en": "The case becomes \"Decided\". If the underlying report changes, it is marked \"review required\"."},
    "decide.saved": {"ko": "결정을 저장했습니다. 이 사례는 \"결정 완료\"로 표시됩니다.", "en": "Decision saved. The case is now shown as \"Decided\"."},
    "decide.reject_not_completed": {"ko": "끝나지 않은 조사에는 결정을 기록할 수 없습니다.", "en": "A decision cannot be recorded for an unfinished investigation."},
    "decide.error": {"ko": "결정을 저장하지 못했습니다({name}).", "en": "Could not save the decision ({name})."},
    "decide.no_run": {"ko": "조사 결과가 없어 결정을 기록할 수 없습니다.", "en": "There is no investigation result, so a decision cannot be recorded."},
    "reinv.title": {"ko": "다시 조사하기", "en": "Investigate again"},
    "reinv.desc": {"ko": "같은 절차가 다시 돌고 새 결과가 이 사례에 붙습니다(1~2분). 이전 결과는 그대로 남습니다.",
                   "en": "The same procedure runs again and the new result is attached to this case (1–2 minutes). Earlier results are kept."},
    "reinv.reason1": {"ko": "통계가 갱신되어 값이 달라졌을 수 있음", "en": "The statistics were updated; values may differ"},
    "reinv.reason2": {"ko": "다른 나라와 더 비교해 보고 싶음", "en": "I want more comparison with other countries"},
    "reinv.reason3": {"ko": "하위품목별로 다시 나누어 보고 싶음", "en": "I want the breakdown by sub-heading again"},
    "reinv.button": {"ko": "다시 조사", "en": "Investigate again"},
    "reinv.cannot": {"ko": "조사 모델 연결이 설정되지 않아 지금은 이 사례를 다시 조사할 수 없습니다.",
                     "en": "The investigation model connection is not set up, so this case cannot be investigated again now."},
    "followup.title": {"ko": "사후 확인", "en": "Follow-up"},
    "followup.desc": {"ko": "다음 달 통계가 갱신되면 여기서 \"변동이 계속됨 / 해소됨 / 자료 정정으로 사라짐\"을 기록합니다. 지금은 열리지 않습니다.",
                      "en": "When next month's statistics arrive, record here whether the change persisted, reversed, or "
                            "disappeared after a data correction. Not open yet."},
    "history.title": {"ko": "이 사례의 기록", "en": "History of this case"},
    "history.alert": {"ko": "{month} — 경보 발생({signal})", "en": "{month} — alert raised ({signal})"},
    "history.alert_plain": {"ko": "{month} — 경보 발생", "en": "{month} — alert raised"},
    "history.run": {"ko": "{time} — 조사 완료, 제안 \"{verdict}\"", "en": "{time} — investigated, suggested \"{verdict}\""},
    "history.run_failed": {"ko": "{time} — 조사가 끝나지 못함", "en": "{time} — investigation did not finish"},
    "history.decision": {"ko": "{time} — 내 결정 \"{decision}\"{reviewer} [{validity}]",
                         "en": "{time} — my decision \"{decision}\"{reviewer} [{validity}]"},
    "history.by": {"ko": " ({reviewer})", "en": " ({reviewer})"},
    "history.no_decision": {"ko": "내 결정 — 아직 없음", "en": "My decision — none yet"},
    "validity.VALID": {"ko": "유효", "en": "valid"},
    "validity.REVIEW_REQUIRED": {"ko": "재검토 필요", "en": "review required"},
    "glossary.title": {"ko": "용어", "en": "Terms"},
    "glossary.unit": {"ko": "kg당 단가", "en": "Unit value"},
    "glossary.unit_desc": {"ko": "수입금액을 순중량으로 나눈 값", "en": "Import value divided by net weight"},
    "glossary.share": {"ko": "점유율", "en": "Import share"},
    "glossary.share_desc": {"ko": "그 품목 수입에서 한 나라가 차지하는 비중", "en": "One country's part of Korea's imports of that product"},
    "glossary.mix": {"ko": "구성 변화", "en": "Mix change"},
    "glossary.mix_desc": {"ko": "비싼·싼 하위품목의 비중이 바뀌어 평균 단가가 움직인 몫",
                          "en": "The part of the average price move caused by shifting between dearer and cheaper sub-headings"},
    "ask.line": {"ko": "문의할 때 사례 번호: {case_id}", "en": "Case reference for enquiries: {case_id}"},
    "partner.XA": {"ko": "가상국 A", "en": "Synthetic partner A"},
    "partner.XB": {"ko": "가상국 B", "en": "Synthetic partner B"},
    "partner.XC": {"ko": "가상국 C", "en": "Synthetic partner C"},
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


def _period(period: object) -> tuple[str, int] | None:
    if not isinstance(period, str) or len(period) != 6 or not period.isdigit() or not 1 <= int(period[4:]) <= 12:
        return None
    return period[:4], int(period[4:])


def month_long(period: object, lang: str = DEFAULT_LANG) -> str:
    """`YYYYMM` → 한국어 "2024년 12월", 영어 "December 2024"(제목·칩·경로용). 형식이 다르면 원문 그대로다."""
    parsed = _period(period)
    if parsed is None:
        return str(period)
    year, month = parsed
    return f"{MONTH_EN_FULL[month - 1]} {year}" if lang == "en" else f"{year}년 {month}월"


def month_name(period: object, lang: str = DEFAULT_LANG) -> str:
    """`YYYYMM` → 달 이름만: 한국어 "12월", 영어 "December"."""
    parsed = _period(period)
    if parsed is None:
        return str(period)
    return MONTH_EN_FULL[parsed[1] - 1] if lang == "en" else f"{parsed[1]}월"


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
    """관세청 국가코드 → 국가 이름(data/reference/country_map.csv: ko는 kcs_country_name, en은 baci_country_name)과 합성
    픽스처 가상 상대국 이름. 표를 읽지 못하면 가상 상대국 이름만 남는다."""
    column = "baci_country_name" if lang == "en" else "kcs_country_name"
    names = {code: t(f"partner.{code}", lang) for code in FIXTURE_PARTNERS}  # 합성 픽스처의 가상 상대국
    try:
        with (repo_root / COUNTRY_MAP).open(encoding="utf-8", newline="") as fh:
            names.update({row["cntyCd"]: row[column] for row in csv.DictReader(fh) if row.get("cntyCd") and row.get(column)})
    except (OSError, KeyError, csv.Error):
        pass
    return names


def partner_label(partner: object, countries: dict[str, str]) -> str:
    """상대국 표시: 이름이 있으면 이름, 없으면 코드(합성 픽스처)."""
    return countries.get(partner, str(partner)) if isinstance(partner, str) else str(partner)
