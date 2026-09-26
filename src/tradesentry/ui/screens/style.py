"""담당자 화면 v2의 CSS(디자인 캔버스 v2의 색·간격). 위치를 고정할 요소는 key를 준 Streamlit 요소의 `.st-key-<key>` 클래스로
고른다(streamlit 1.64). 이 파일은 streamlit을 import하지 않는다(문자열만)."""

CSS = """
<style>
:root{--ts-bg:#f4f2ec;--ts-card:#ffffff;--ts-line:#d9d5cb;--ts-band:#ebe8df;--ts-blue:#1f5a8a;--ts-deep:#174670;
--ts-light:#e3eef9;--ts-text:#1c2430;--ts-muted:#5b6470;--ts-green:#2e7d4f;--ts-up:#fbecd4;--ts-upt:#7a4b00;--ts-down:#e3eef9;
--ts-downt:#174670;--ts-sh:#ece6f6;--ts-sht:#4a3a78}
header[data-testid="stHeader"]{display:none}
[data-testid="stMainBlockContainer"]{padding:0 40px 32px !important;max-width:1520px}
[data-testid="stAppViewContainer"]{background:var(--ts-bg)}
body{font-variant-numeric:tabular-nums}
/* 머리 띠 */
.st-key-ts_header{background:#fff;border-bottom:1px solid var(--ts-line);margin:0 -40px 4px;padding:8px 40px;width:calc(100% + 80px) !important;max-width:none !important}
[data-testid="stElementContainer"]:has(style){display:none}
.st-key-ts_header [data-testid="stPageLink"] a{padding:6px 14px;border-radius:8px}
.st-key-ts_header [data-testid="stPageLink-NavLink"]{padding:6px 12px;border-radius:8px;white-space:nowrap}
.st-key-ts_nav{flex-wrap:nowrap !important}
.ts-brand{display:flex;align-items:baseline;gap:10px;white-space:nowrap}
.ts-brand b{font-family:"Noto Serif KR",Georgia,serif;font-size:20px;letter-spacing:.02em}
.ts-brand span,.ts-dataline{font-size:13px;color:var(--ts-muted)}
.ts-dataline{text-align:right;white-space:nowrap;padding-top:6px}
/* 영역 */
.st-key-ts_summary{background:var(--ts-band);border-radius:14px;padding:16px 20px}
.st-key-ts_filters,.st-key-ts_table{background:#fff;border:1px solid var(--ts-line);border-radius:14px;padding:12px 20px}
.st-key-ts_table{padding:4px 20px 8px}
.ts-sum-title{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
.ts-sum-title .h{margin:0;padding:0;font-family:"Noto Serif KR",Georgia,serif;font-size:22px}
.ts-sum-title span{font-size:13px;color:var(--ts-muted)}
.ts-kpi{background:#fff;border-radius:10px;padding:14px 16px;min-height:122px;box-sizing:border-box;border:1px solid transparent}
.ts-kpi.ts-kpi-accent{border:1px solid var(--ts-deep)}
.ts-kpi .l{font-size:12px;color:var(--ts-muted)} .ts-kpi .v{font-size:28px;font-weight:700;line-height:1.3}
.ts-kpi .v small{font-size:15px;font-weight:400;color:var(--ts-muted)} .ts-kpi .s{font-size:12px;color:var(--ts-muted)}
.ts-kpi.ts-kpi-accent .v{color:var(--ts-deep)}
.ts-th{font-size:12px;color:var(--ts-muted);font-weight:600;padding:8px 0 2px}
.ts-row{border-top:1px solid #ecebe5}
.ts-cell{font-size:14px;line-height:1.45}
.ts-cell small{display:block;font-size:12px;color:var(--ts-muted)}
.ts-badge{display:inline-block;padding:2px 8px;border-radius:6px;font-size:12px;font-weight:700}
.ts-badge.up{background:var(--ts-up);color:var(--ts-upt)} .ts-badge.down{background:var(--ts-down);color:var(--ts-downt)}
.ts-badge.sh{background:var(--ts-sh);color:var(--ts-sht)} .ts-badge.na{background:#ecebe5;color:var(--ts-muted)}
.ts-prog-done{color:var(--ts-deep);font-weight:600}
.ts-prog-run{color:var(--ts-deep);font-weight:600}
.ts-prog-fail{color:#9a3412;font-weight:600}
.ts-awaiting{background:#f4f8fc;margin:0 -20px;padding:0 20px}
.ts-foot{display:flex;gap:24px;font-size:12px;color:var(--ts-muted);align-items:baseline}
/* 카드 */
.ts-card{background:#fff;border:1px solid var(--ts-line);border-radius:14px;padding:18px 22px}
.ts-chip{display:inline-block;padding:3px 10px;border:1px solid var(--ts-line);border-radius:999px;font-size:13px;margin:0 6px 6px 0;background:#fff}
.ts-chip.ok{background:var(--ts-light);border-color:#c3d6ea;color:var(--ts-deep)}
.ts-crumb{font-size:13px;color:var(--ts-muted);padding-top:10px}
.ts-title{font-family:"Noto Serif KR",Georgia,serif;font-size:28px;font-weight:700;line-height:1.3;margin:6px 0 10px}
.ts-verdict{display:inline-block;padding:4px 14px;border-radius:999px;background:var(--ts-light);color:var(--ts-deep);font-weight:700;font-size:16px}
.ts-verdict.MONITOR{background:#fbf1dc;color:#7a4b00} .ts-verdict.HOLD{background:var(--ts-sh);color:var(--ts-sht)}
.ts-mean{border-radius:8px;padding:8px 10px;margin:6px 0;background:#f8f7f3;font-size:13px}
.ts-mean.cur{background:var(--ts-light);border:1px solid #c3d6ea}
.ts-kv{display:grid;grid-template-columns:72px 1fr;gap:6px 10px;font-size:13px}
.ts-kv .k{color:var(--ts-muted)}
.ts-caution{border:1px dashed var(--ts-line);border-radius:14px;padding:14px 18px;font-size:13px;background:#f8f7f3}
.ts-small-link{font-size:12px;text-align:right}
.st-key-case_what,.st-key-case_found,.st-key-case_alt,.st-key-case_next,.st-key-case_meaning,.st-key-case_basis,
.st-key-as_form,.st-key-as_reinv,.st-key-as_hist,.st-key-as_terms{background:#fff;border:1px solid var(--ts-line);border-radius:14px;padding:18px 22px}
.st-key-case_conc{background:var(--ts-light);border:1px solid #c3d6ea;border-radius:14px;padding:18px 22px}
.st-key-as_follow{border:1px dashed var(--ts-line);border-radius:14px;padding:18px 22px;background:#f8f7f3}
.ts-what{background:#f8f7f3;border-radius:10px;padding:14px 16px}
.ts-what .l{font-size:12px;color:var(--ts-muted)} .ts-what .v{font-size:28px;font-weight:700;color:var(--ts-deep)}
.ts-what .s{font-size:13px;color:var(--ts-muted)}
.ts-sec{font-weight:700;font-size:17px;margin:0 0 8px}
.ts-sec small{font-weight:400;font-size:13px;color:var(--ts-muted)}
.st-key-as_steps{background:var(--ts-band);border-radius:14px;padding:14px 20px}
.ts-stepbox{display:flex;gap:10px;align-items:flex-start}
.ts-stepbox .n{width:26px;height:26px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:13px;flex-shrink:0;border:1px solid var(--ts-line);background:#fff}
.ts-stepbox .n.done{background:var(--ts-green);color:#fff;border-color:var(--ts-green)}
.ts-stepbox .n.now{background:var(--ts-deep);color:#fff;border-color:var(--ts-deep)}
.ts-stepbox b{font-size:14px} .ts-stepbox b.now{color:var(--ts-deep)} .ts-stepbox div small{display:block;font-size:12px;color:var(--ts-muted)}
.ts-hist{font-size:13px;margin:0;padding-left:20px} .ts-hist li{margin:4px 0;font-size:13px} .ts-hist li.muted{color:#8a9099}
/* 로딩 창 */
.st-key-ts_overlay{position:fixed !important;inset:0;z-index:1000000;background:rgba(40,44,52,.32);backdrop-filter:blur(1.5px);
display:flex !important;align-items:center;justify-content:center;width:100vw !important;height:100vh}
.st-key-ts_overlay>div{width:640px !important;max-width:calc(100vw - 32px);flex:0 0 auto}
.st-key-ts_modal{width:640px !important;max-width:calc(100vw - 32px);background:#fff;border-radius:16px;padding:32px 36px 28px;
box-shadow:0 16px 48px rgba(28,36,48,.22);box-sizing:border-box;gap:14px}
.st-key-ts_overlay, .st-key-ts_overlay *, [class*="st-key-ts_pill_"], [class*="st-key-ts_pill_"] *{opacity:1 !important;transition:none !important}
.ts-load-head{display:flex;align-items:center;gap:14px}
.ts-load-title{flex-grow:1}.ts-h{font-size:22px;font-weight:700}.ts-sub{font-size:14px;color:#3a424d}
.ts-clock{font-size:22px;font-weight:700;color:var(--ts-deep)}
.ts-spin{width:44px;height:44px;border-radius:50%;border:4px solid #e3eef9;border-top-color:var(--ts-blue);box-sizing:border-box;
display:inline-block;animation:ts-rot 1s linear infinite;flex-shrink:0}
.ts-fail{width:44px;height:44px;border-radius:50%;background:#fde8dc;color:#9a3412;font-weight:700;font-size:22px;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0}
@keyframes ts-rot{to{transform:rotate(360deg)}}
.ts-steps{list-style:none;margin:6px 0 14px;padding:0}
.ts-step{display:flex;align-items:center;gap:12px;margin:0 0 10px;font-size:14px;color:#5b6470}
.ts-dot{width:24px;height:24px;border-radius:50%;border:2px solid #d9d5cb;box-sizing:border-box;display:inline-flex;align-items:center;justify-content:center;font-size:12px;color:#fff}
.ts-step-done{color:var(--ts-text)} .ts-step-done .ts-dot{background:var(--ts-green);border-color:var(--ts-green)}
.ts-step-current{color:var(--ts-deep);font-weight:700} .ts-step-current .ts-dot{border:3px solid var(--ts-deep)}
.ts-bar{height:8px;border-radius:4px;background:#ecebe5;overflow:hidden}.ts-bar span{display:block;height:8px;background:var(--ts-deep);border-radius:4px}
.ts-note{font-size:13px;color:var(--ts-muted);flex-grow:1}
.st-key-ts_load_actions{justify-content:space-between}
.ts-footnote{font-size:12px;color:var(--ts-muted);background:#f8f7f3;border-radius:8px;padding:10px 12px}
.ts-failbox{font-size:14px;background:#fdf1ea;border-radius:8px;padding:12px 14px;color:#7c2d12}
/* 조사 중 표시 */
[class*="st-key-ts_pill_"]{position:fixed !important;right:40px;bottom:18px;width:470px !important;max-width:calc(100vw - 32px);z-index:999999;gap:0}
.st-key-ts_pill,.st-key-ts_pill>div{width:100% !important}
[class*="st-key-ts_pill_"] button>div{justify-content:flex-start;width:100%}
[class*="st-key-ts_pill_"] button{width:100%;height:44px;border-radius:999px;background:#fff;border:1px solid #c3d6ea;
box-shadow:0 4px 14px rgba(28,36,48,.14);justify-content:flex-start;padding:0 16px;color:var(--ts-deep)}
[class*="st-key-ts_pill_"] button p{font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.st-key-ts_pill_done button{border-color:#b7d8c4;color:var(--ts-green)}
.st-key-ts_pill_failed button{border-color:#f3c7ae;color:#9a3412}
.ts-pillbar{position:absolute;left:16px;right:16px;bottom:5px;height:3px;border-radius:2px;background:#ecebe5;pointer-events:none}
.ts-pillbar span{display:block;height:3px;border-radius:2px;background:var(--ts-blue)}
[class*="st-key-ts_pill_"] [data-testid="stElementContainer"]:has(.ts-pillbar){position:absolute;inset:0;pointer-events:none}
.ts-flabel{font-size:12px;color:var(--ts-muted);white-space:nowrap}
.ts-found{margin:0;padding-left:20px;font-size:14px;line-height:1.6}.ts-found li{margin:0 0 6px;font-size:14px}
.ts-minispin{width:12px;height:12px;border-radius:50%;border:2px solid #c3d6ea;border-top-color:var(--ts-blue);box-sizing:border-box;
display:inline-block;margin-right:8px;vertical-align:-1px;animation:ts-rot 1s linear infinite}
.ts-kv-wide{grid-template-columns:92px 1fr}
[class*="st-key-ts_row_"],[class*="st-key-ts_rowaw_"]{border-top:1px solid #ecebe5;padding:6px 0;gap:0}
[class*="st-key-ts_rowaw_"]{background:#f4f8fc;margin:0 -20px;padding:6px 20px;width:calc(100% + 40px) !important;max-width:none !important}
.st-key-month_prev button,.st-key-month_next button{padding:0 10px;min-width:34px}.st-key-month_prev button p,.st-key-month_next button p{font-size:20px;line-height:1}
[data-testid="stMarkdownContainer"]:has(> [class^="ts-"]){margin-bottom:0}
.st-key-ts_filters [data-testid="stSelectbox"] [role="group"],.st-key-ts_filters [data-testid="stTextInputRootElement"],
.st-key-as_form [data-testid="stTextInputRootElement"],.st-key-as_form [data-testid="stTextAreaRootElement"],
[data-testid="stSelectbox"] [role="group"]{border:1px solid var(--ts-line) !important;border-radius:8px;background:#fff !important}
[class*="st-key-ts_small_"] button{min-height:0;padding:0}
[class*="st-key-ts_small_"] button p{font-size:12px;color:var(--ts-blue);text-decoration:underline}
.ts-v-MAINTAIN{color:var(--ts-deep)} .ts-v-MONITOR{color:#7a4b00} .ts-v-HOLD{color:var(--ts-sht)}
.st-key-as_ask{gap:4px}
.st-key-as_form [role="radiogroup"]{gap:8px;width:100%}
.st-key-as_form [role="radiogroup"]>label{border:1px solid var(--ts-line);border-radius:10px;padding:10px 14px;width:100%;box-sizing:border-box;margin:0}
.st-key-as_form [role="radiogroup"]>label:has(input:checked){background:var(--ts-light);border-color:#8fb3d6}
@media (max-width:760px){[data-testid="stMainBlockContainer"]{padding:0 16px 32px !important}
.st-key-ts_header{margin:0 -16px 8px;padding:10px 16px}[class*="st-key-ts_pill_"]{right:16px;left:16px;width:auto !important}}
</style>
"""
