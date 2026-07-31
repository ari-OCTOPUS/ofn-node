---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [telegram, octopus, scan]
created: 2026-07-31
updated: 2026-07-31
---

# اسکنِ عمیقِ سطحِ تلگرام — گزارشِ کامل (۲۰۲۶-۰۷-۳۱)

> ۱۴ ایجنت · ۸۳۰ فراخوانِ ابزار · ۵ اسکنرِ موازی + ۵ ممیزِ متخاصم + ۳ مگاپرامپت + منتقدِ کامل‌بودن.
> ۱۸۴ قابلیت روی سه محور (docs/code/runtime) · **۹۲ شکافِ تأییدشده** · **۴۵ ادعا ردِ متخاصم شد**.
> مگاپرامپت‌های GLM: `MEGAPROMPT-GLM-{A-outer,B-inner,C-group}-2026-07-31.md` · نقد: `SCAN-CRITIQUE-2026-07-31.md`
> فیکس‌های همان روز: `cc663d8` (پلِ دکمه · خانهٔ ویرایشی · راهنمای DM · رسیدِ واچ‌داگ · ثبتِ ۹ سوییت) + فیکسِ HOLD ِ کارتِ دکمه‌دار (dirty، کنارِ بلاکِ غریبه).

## باتِ بیرونی (لنگر — DM گفتگوییِ مالک) — 45 قابلیت · 22 شکاف · 11 ادعای ردشده

### outer-bot-1 [high] ✅(بسته شد) Every bridged organism keyboard is a dead card on the outer bot
`F:/backup/_ops/telegram_center/center.py`

center.py:1565-1568 routes ~35 unadvertised commands to approval_channel, and center.py:1660-1663 deliberately attaches the returned reply_markup to an OUTER-bot message. Telegram sends those taps back to the outer poller, whose router knows none of those verbs. I probed 13 of them with a fake client (menu:*, card:*, pg:*, act:*, acct:*, jrn:*, rev:*, rfc:*, app:*, brain:*, home:*, prop:*) and every one hit center.py:2964-2966 and answered 'نادیده'. This includes app:approve/deny — the money-approval buttons — and rfc:merge/deny. The contract's own invariant every_emitted_callback_is_handled_by_emitting_bot (TELEGRAM-ACCESS-CONTRACT.v1.json) is violated by the very mechanism that was built to fix command reachability.

### outer-bot-2 [high] ✅(بسته شد) The dead-card guard itself never runs — 13 TG test files are unregistered in run_all.py
`F:/backup/_ops/tests/run_all.py`

run_all.py has no glob/discovery (its own comment at line 601 says 'ثبت‌نشده = هرگز اجرا نشده'). Comparing the TESTS list with tests/*.py on disk, these TG files are absent from the registry and therefore never execute: test_tg_callback_emitter_parity.py, test_tg_input_surface_policy.py, test_tg_group_is_legs_only.py, test_tg_hold_policy.py, test_tg_leg_tasks.py, test_tg_surface_router.py, test_tg_build_surface.py, test_tg_route_seam.py, test_tg_canonical_access_model.py, test_tg_client_contract.py, test_capability_manifest_registry.py, test_mining_leg.py, test_studio_telegram.py. The first of those is precisely the guard written to catch the gap above. It would not have caught it anyway: its handled-verb set is a UNION of both routers (test_tg_callback_emitter_parity.py:118), so a verb handled only by the inner bot passes even when the outer bot is the one emitting it.

### outer-bot-3 [high] ✅(بسته شد) Held cards lose their inline keyboard; the ledger still says delivered
`F:/backup/_ops/budget/approval_channel.py`

approval_channel.py:1618-1621 calls surface_policy.hold(stream, text) and returns False — reply_markup is discarded and the caller (organism.py:734-742) never checks the return value. Runtime: state/telegram/tool-requests.jsonl records delivered=True nine times (2026-07-30T13:12:54 … 2026-07-31T09:22:22) while held-stream.jsonl archives six of those with byte-identical timestamps and digest-buffer.jsonl keeps only an 80-char head for the rest. The owner has literally never been able to tap ✅/❌ on a tool request, yet the self-awareness metric counts them as delivered.

### outer-bot-4 [high] owner_console intercepts /menu and /start before the command table
`F:/backup/_ops/telegram_center/center.py`

center.py:1391-1397 returns any owner_console reply whose kind is not 'clarify', and conversation.py:14 matches ^/menu$ and ^/start$ exactly. So the #1 advertised command in setMyCommands never reaches _page('menu') in the Outer DM; the owner gets the owner_console home card instead. I measured this offline against the live catalog: of 40 probed slash commands only /menu and /start are shadowed. The contract still lists owner_console as WIRED_NOT_LIVE, so a surface marked 'not live' is already overriding a live advertised command.

### outer-bot-5 [medium] owner_console runs a full recursive filesystem scan on every owner message
`F:/backup/_ops/owner_console/catalog.py`

conversation.handle (owner_console/conversation.py:22) calls catalog.discover() unconditionally, which does OPS.rglob('capability-manifest.json') over all of _ops plus capability_registry.discover(refresh=True) (catalog.py:28, 91). This sits directly on the single-threaded poll loop that also writes the liveness pulse (center.py:3131-3133). A slow disk turns owner latency into apparent bot death.

### outer-bot-6 [high] owner_menu.handle_new_mission is a fully-built orphan — panel option ② does nothing
`F:/backup/_ops/telegram_center/menu_integration.py`

owner_menu.py:112-163 builds a validated mission envelope, consults autonomy_matrix for the owner gate, emits a spine event and registers a lead. menu_integration.py:76-80 for key=='mission' returns explanatory prose and never calls it. Repo-wide grep finds only its own __main__ and tests/test_lead_wiring.py. owner_menu.looks_like_lead (line 54) has zero references anywhere. This is the exact recurring failure mode: implemented, tested, zero production callers.

### outer-bot-7 [high] decision_gate.card() has a handler but no emitter
`F:/backup/_ops/decision_gate.py`

center.py:2404-2418 routes dg:e:<trace> and decision_gate.explain() is real, but the only production consumer of decision_gate, cortex/auto_approve.py:146-156, calls decide()+record() in shadow mode and never card(). No message with a dg: button is ever produced, so the handler is unreachable in practice — the mirror image of the tr:/iv: bug the codebase already learned from.

### outer-bot-8 [high] ✅(بسته شد) guide.dm_text() is never sent — the DM has no in-Telegram instructions
`F:/backup/_ops/telegram_center/guide.py`

center.py:552-576 pins only guide.group_text() (into the group). guide.dm_text (guide.py:51-75) is the text that teaches the owner the «بساز:» syntax and the three-door model, and it has zero production callers. The owner's primary surface is the one with no pinned instructions, while the legs-only group has them.

### outer-bot-9 [high] ✅(بسته شد) The pinned 'home' message is written once and never refreshed
`F:/backup/_ops/telegram_center/center.py`

home_message_id occurs exactly twice in center.py (849, 854) — set on the first successful pulse, never used for an edit. Each subsequent hourly pulse sends a NEW message (center.py:843). Runtime: home_message_id=149 was pinned 2026-07-30T18:43 while ten newer pulses (through 2026-07-31T08:37:52) scrolled past. The permanent 'home' the owner sees at the top of the chat is a day-old snapshot.

### outer-bot-10 [high] center-status is declared in surface-routing.json but has no _route_send caller
`F:/backup/_ops/telegram_center/surface-routing.json`

surface-routing.json:26 promises the pinned status moves to the owner DM under the split flag. There are exactly 7 _route_send call sites (center.py:652, 717, 763, 773, 843, 1232 + cortex/code_autonomy.py:525) and none passes 'center-status'. The status message is hard-coded to the group at center.py:540 and edited there at center.py:612 (center-config.status_message_id=66). A routing rule that reads as 'done' in the owner's own file has no consumer.

### outer-bot-11 [high] Doctor cards bypass surface routing and land in group General
`F:/backup/_ops/telegram_center/doctor_link.py`

doctor_link.beat sends via client.send(text, topic_id=_topic_id(), keyboard=...) with no chat_id (doctor_link.py:155). tg_api._resolve_chat(None) returns the CENTER chat (tg_api.py:342-346), i.e. the group, and OCTOPUS_DOCTOR_TOPIC_ID is unset so topic_id is None ⇒ General. Meanwhile surface-routing.json:16-17 assigns doctor-intent/doctor-diff to the outer DM. Runtime: three cards actually delivered this way (message ids 323/324/325, doctor-link-cursor.json). Core content in the legs-only group's General is exactly the legs-only violation the contract's gate 1 flagged.

### outer-bot-12 [high] Two processes write the INNER bot's command menu with different lists
`F:/backup/_ops/telegram_center/center.py`

center.py:527-533 pushes COMMANDS_INNER (1 entry, 'status') to the inner bot when the split flag is on, and center-config.json records commands_set_inner=1, proving it already did. approval_channel.py:716-750 pushes a 23-entry menu on every organism boot. Both processes booted within one second (state/flags-loaded-*.json: center 08:37:18, organism 08:37:19), so which menu the owner sees is a race. Because center only re-pushes when len(COMMANDS_INNER) changes, the failure is silent and intermittent.

### outer-bot-13 [high] The 'inner bot never polls' contract is false in the live tree
`F:/backup/_ops/organism.py`

organism.py:400-405 starts approval_channel.run_forever on a daemon thread, which polls getUpdates on TELEGRAM_BOT_TOKEN (approval_channel.py:518-541). state/pulse/telegram-poll.json ts 2026-07-31T09:24:20 proves it is running. The contract text (surface_router.py:12-14, telegram_contract invariants) asserts no new poller; what is actually enforced is narrower — only that the CENTER's inner client is send-only (tests/test_two_bot_bridge.py:83). Any reasoning that treats the inner bot as incapable of receiving owner input is wrong.

### outer-bot-14 [high] /mining is a handler that is neither advertised nor covered by the discoverability guard
`F:/backup/_ops/tests/test_command_discoverability.py`

center.py:1543-1545 adds handlers['/mining'] via bracket assignment. test_command_discoverability._handler_commands (line 44) only regexes dict-literal keys of the form "/x": , so /mining is invisible to the guard and is in neither COMMANDS nor INTENTIONALLY_HIDDEN. Same blind spot applies to /panel (it happens to be excused by name). The guard's coverage is narrower than it appears.

### outer-bot-15 [high] Command shadowing between the center table and the bridged router
`F:/backup/_ops/telegram_center/center.py`

/lead, /verdicts, /start and /status-adjacent names exist on both sides. center.py:1500 binds /lead to quote_cmd, so approval_channel's _cmd_lead_prompt/_cmd_lead_parse (approval_channel.py:1747-1750) is unreachable from the outer DM; center.py:1504 binds /verdicts to verdict_probe, shadowing langar_bridge's /verdicts (legs/langar_bridge.py:141); center.py:1483 binds /start to _page('menu'), shadowing approval_channel._main_menu. The owner's INNER-bot menu still advertises the shadowed meanings, so the same command means two different things depending on which chat it is typed in, with no documentation of the difference.

### outer-bot-16 [high] input_surface_policy's docstring says it has no caller — it does
`F:/backup/_ops/telegram_center/input_surface_policy.py`

input_surface_policy.py:18-20 states 'این ماژول صداکننده ندارد و عمداً' and explains it is waiting for a parallel session's hunks. It is in fact called on every single update at center.py:1318 and again at center.py:2914. A reader auditing whether input is gated will read the module header and conclude it is inert. Stale self-description on a security gate is the most expensive kind.

### outer-bot-17 [high] The mirror room lives in the group, not the DM the contract assigns it
`F:/backup/_ops/telegram_center/center.py`

center.py:1855 enters mirror_room only when _topic_key(msg)=='mirror', and center-config topics.mirror=205 is a GROUP forum topic. The access contract makes the group legs-only and the outer DM the self-knowledge surface. Worse, input_surface_policy classifies topic 205 as leg_scoped leg='mirror', so a non-question statement there is swallowed by the leg-task seam (center.py:1405-1427) and becomes a task instead of a mirror turn; only sentences that pass leg_tasks.is_question reach the mirror at all.

### outer-bot-18 [medium] OWNER_AUTH capture sits downstream of the owner_console seam
`F:/backup/_ops/telegram_center/center.py`

center.py:1455 records owner authorization sentences, but it is inside _handle_message, which runs only after owner_console declines (center.py:1396). An authorization sentence containing 'runtime', 'بفرست', 'هدف' etc. matches an owner_console regex, returns a non-clarify reply, and is never recorded. The module's whole point is that owner decisions are the most volatile data in the system.

### outer-bot-19 [high] push_alert / center-alert has zero live producers
`F:/backup/_ops/telegram_center/center.py`

center.py:1222-1234 is the only alert door on the outer object, and its two callers are event_bridge.py:234 and heart/money_pulse.py:107 — both behind flags absent from state/flags-loaded-center.json. state/telegram/event-bridge-cursor.json does not exist and tg-send-log.jsonl has zero center-alert rows. The routing entry, the handler and the tests all exist; nothing calls it.

### outer-bot-20 [medium] Mission and ask_brain surfaces are wired but have gone quiet
`F:/backup/_ops/state/telegram/missions/missions.json`

missions.json has 9 missions, all frozen at state 'approved' with owner_verdict null, newest 2026-07-27T20:52:41; ask-brain.jsonl's last row is 2026-07-27T20:10:32 and ask-brain-state.json still says date 2026-07-28 used 1; mirror-history.jsonl last moved 2026-07-27T13:22; initiative.jsonl has exactly one row from 2026-07-27. Four capabilities the docs present as live have had no runtime activity for four days while the bot itself has been sending hourly. That pattern separates 'the wire exists' from 'the owner uses it', and it is invisible from code alone.

### outer-bot-21 [medium] The quote 'send' button records an approval id nobody consumes
`F:/backup/_ops/telegram_center/center.py`

center.py:2299-2300 writes {"id": "quote-<qt>", "verdict": "ok", "source": "tg-quote"} into the same approvals store as real decisions, and the reply promises 'ارسالِ واقعی از مسیرِ تأیید می‌رود'. No consumer of approvals.jsonl looks for the quote- prefix, and no such id appears in the live file. The card tells the owner an approval path exists that is not connected on the other end.

### outer-bot-22 [high] Send receipts cannot attribute a message to a bot or a surface
`F:/backup/_ops/tg_send_log.py`

tg_send_log.record writes ts/chat/topic/stream/sha/chars/ok only (tg_send_log.py:50-60). Outer sends default stream='center' (tg_api.py:350) while inner sends pass no stream at all (approval_channel.py:1655), so bot attribution rests on a null convention rather than a field. There is also no attempted/held/blocked tri-state, so a HOLD is indistinguishable from 'never produced'. The contract already grades this PARTIAL at gate 8, and it is the reason the tool_request 'delivered' lie survived.

### ادعاهای ردشدهٔ outer-bot (ممیزِ متخاصم — این‌ها را دنبال نکن)

- **Live process PID 12284, booted 2026-07-31T08:37:18 (state/flags-loaded-center.json), heartbeating into state/pulse/tg-center.json (last ts 09:24:17). Singleton ** — That process is gone. F:/backup/_ops/state/pulse/tg-center.json now reads {"ts":"2026-07-31T09:50:23","pid":20208} and F:/backup/_ops/state/flags-loaded-center.json reads pid=20208, boot_ts=1785455338.98 (= 2026-07-31 09:48:58 local). The center restarted after the 09:43 merge. Every runtime claim anchored to PID 12284 / the 08:37 boot is evidence about a dead process.
- **center.py line anchors: run_forever 3112, run_once 3080, handle_update 1296, handlers{} 1477, _handle_callback 2891, _handle_center_callback 2246, _handle_missi** — Systematically stale below ~line 590. Commit e3a8e56 (2026-07-31 09:18:59), merged as 2e0225c (09:43:25), inserted ~50 lines. Actual current defs in F:/backup/_ops/telegram_center/center.py (3317 lines): handle_update 1342, _handle_message 1536, handlers{} 1573-1630, _bridge_to_organism 1725, _chat_room 1809, _handle_ask 1914, _route_send 1230, push_alert 1268, _handle_center_callback 2342, _handl
- **surface_router.resolve has '7 call sites, all in center.py (652 digest, 717 decision, 763 urgent, 773 health-digest, 843 pulse, 1232 alert) plus cortex/code_aut** — There are exactly SIX _route_send call sites, all in center.py: 652 (center-digest), 726 (center-decision), 772 (center-urgent), 782 (center-health-digest), 852 (center-pulse), 1278 (center-alert). A repo-wide grep for _route_send across _ops returns zero hits in cortex/code_autonomy.py. That file instead calls surface_router.resolve DIRECTLY at cortex/code_autonomy.py:543-545 (not 525), then send
- **'13 TG test files are unregistered in run_all.py', listing test_tg_leg_tasks.py and test_tg_group_is_legs_only.py among them.** — Both are now registered, at F:/backup/_ops/tests/run_all.py:607 and 608 (added by commit e3a8e56 at 09:18:59, merged 09:43). Diffing every quoted "test_*.py" token in run_all.py (400 entries) against tests/ on disk gives 11, not 13, currently-unregistered TG-ish files: test_capability_manifest_registry.py, test_mining_leg.py, test_studio_telegram.py, test_tg_build_surface.py, test_tg_callback_emit
- **Build seam «بساز:» runtime = 'proven', evidence including 'approvals.jsonl records {"id":"code-2191f6fc43","verdict":"ok","ts":"2026-07-31T09:28:48+1000"}' and ** — That approval did not come from this surface, and the patch card has no send receipt. In F:/backup/_ops/state/telegram/approvals/approvals.jsonl (56 rows) the code-2191f6fc43 row carries "source":"owner-chat-2026-07-31-explicit" — it is the ONLY row in the file that is not "source":"tg-center" (55 of 56). center._record_approval always stamps source="tg-center" (center.py:3077), so this row was wr
- **'OWNER_AUTH capture (record, never execute) — runtime: unproven. No owner-auth state file was found under state/telegram/.'** — The scanner searched the wrong directory. owner_auth_log._path() (F:/backup/_ops/owner_auth_log.py:59) returns opslib.STATE_DIR / "owner-auth.jsonl" — NOT under telegram/. The file exists at F:/backup/_ops/state/owner-auth.jsonl with 3 rows, and the first is {"ts":"2026-07-27T19:04:37","kind":"ARM_FLAG","source":"tg"} — a Telegram-sourced authorization actually recorded. Runtime is proven, not unp
- **'stream=null rows (71) are the INNER bot writing from budget/approval_channel.py:1655 (that writer passes no stream).'** — That writer DOES pass a stream: approval_channel.py:1655-1656 is `_tsl.record(chat_id=target, topic_id=thread, text=text, stream=stream, ok=ok)`. The null comes from the CALLER, because send_text's signature defaults it (approval_channel.py:1583-1585: `stream: str | None = None`). The distinguishing fact is on the other side: tg_api.send defaults `stream: str = "center"` (tg_api.py:350) and coerce
- **'Outer-bot DM traffic is visible there as stream="center" (13 rows)'.** — 13 is only the owner-DM subset. The label stream="center" has 123 rows total: 110 to chat=-1004475788460 (the group) and 13 to chat=6150431610 (the owner DM). Stating it as '13 rows' hides that the same undifferentiated label is the dominant group-bound stream too — which is the actual reason the log cannot attribute a surface.
- **tg-send-log state_files risk: 'Pruned after 48h (tg_send_log.py RETAIN_S).'** — Pruning does not actually happen. RETAIN_S = 48*3600 (tg_send_log.py:33) but prune() only fires when `_since_prune >= _PRUNE_EVERY` with _PRUNE_EVERY = 200 (line 34) and `_since_prune` is per-process module state reset on every restart (line 35, incremented 66-69). The live file's oldest row is ts 1785030014.015 = 2026-07-26T11:40:14 — five days, 301 rows retained. No prune has run. The receipts a
- **Various runtime counts stated as fact: 299 log rows; 9 tool-requests with delivered=True; 11 center-pulse rows (last 2026-07-31T08:37:52); 5 center-health-diges** — Now: 301 rows; 10 delivered=True (a 10th at 2026-07-31T09:42:27); 12 center-pulse (last 09:41:50); 6 center-health-digest (last 09:46:57); last_pulse=1785454905.4; and the 18:53-18:54 DM burst is FOUR sends not three (18:53:39, 18:53:52, 18:54:09, 18:54:16); approvals/ now holds 44 files and approvals.jsonl 56 rows. Most of these are honest drift from a live system — but they are quoted as fixed f
- **'test_tg_callback_emitter_parity.py:118 — its handled-verb set is a UNION of both routers.'** — Line 118 is `assert len(emitted) >= 3`. The union appears at three later lines in that file (`handled = _handled_verbs(CENTER) | _handled_verbs(APPROVAL)` inside t_the_scanner_actually_finds_something, t_every_verb_the_center_emits_is_handled_somewhere, and t_every_verb_the_approval_channel_emits_is_handled_somewhere). The substantive point — a verb handled only by the inner bot passes even when t

## باتِ درونی (اختاپوس — DM هشدارِ فقط-ارسال) — 26 قابلیت · 17 شکاف · 7 ادعای ردشده

### inner-bot-1 [high] Doctor vote cards sit in the group's General topic AND their button press is now refused — a double-dead card
`F:/backup/_ops/telegram_center/doctor_link.py`

doctor_link.beat sends with `client = getattr(center, '_client')` (doctor_link.py:123) — the OUTER client — and `client.send(..., topic_id=_topic_id())` (:155) with OCTOPUS_DOCTOR_TOPIC_ID unset, so _resolve_chat(None) (tg_api.py:342-346) picks the supergroup and the card lands in General. Runtime proof: doctor-link-cursor.json sent_keys message_id 323/324/325, matched in tg-send-log at 2026-07-29T16:32:08 (51 ch), 18:18:24 (775 ch), 18:28:59 (148 ch) — all chat<0, topic=null. This already violates the contract's group_is_legs_only invariant. Worse, the input policy added 2026-07-30 (center.py:1317-1338) classifies any group callback whose message_thread_id is None as 'group-general-or-unknown-topic' and RETURNS at :1338, before callbacks are dispatched at :1434 — so doctor_link.handle_callback can never fire for those cards. The deny path also never calls self._answer(), so the owner sees a spinner that hangs. doctor_link is the ONLY sender in the center that bypasses _route_send/surface_router entirely, so arming OCTOPUS_TG_SPLIT_V1 did not fix it.

### inner-bot-2 [high] The HOLD path silently strips every inline keyboard — cards become buttonless text
`F:/backup/_ops/budget/approval_channel.py`

approval_channel.send_text takes reply_markup at :1583 but the HOLD branch at :1619-1621 calls `_sp.hold(stream, text)` and returns False, discarding reply_markup entirely. hold_policy._urgent_append (:228) stores only text; center.py:763 then re-sends `str(_u.get('text'))` through _route_send with no keyboard argument. Concretely: wiring.py builds keyboards for needs ('📌 الان — کارای من', :3114), doctor ('🩺 تبِ دکتر', :3457), heart ('📊 وضعیت', :3526) and organism.py:722/738 for summary. The one urgent message that actually reached the owner (2026-07-31T08:48:33, 742 chars, doctor) arrived without its button. Nothing logs or alerts on the drop.

### inner-bot-3 [high] Tool-request cards are swallowed into a digest headline; 9 requests wait for a vote that has no surface
`F:/backup/_ops/organism.py`

organism.py:738 sends the tool-request card with reply_markup and stream='summary'. 'summary' is not a leg, not in SELF_STREAMS, not in SAFETY_STREAMS, so surface_policy.route returns HOLD (surface_policy.py:116) and hold() classifies it DIGEST — which keeps only text[:160] as a headline and drops the buttons. flush_digest then renders one line per stream truncated to 80 chars (hold_policy.py:319). Evidence: tool-requests.jsonl has 9 rows with delivered=True/status=pending (latest 2026-07-31T09:23); tg-send-log has ZERO rows with stream='summary'; digest-buffer.jsonl has 3 'summary' rows. The tr:y|n|l handlers exist in BOTH routers (center.py:2344, approval_channel.py:949) — correctly, per the dead-card lesson — but no button ever arrives, and there is no text command to answer a tool request.

### inner-bot-4 [high] event_bridge is completely dark: critical alerts, protective-halt transitions and C6 births never push
`F:/backup/_ops/telegram_center/event_bridge.py`

It is wired (center.py:731-735 calls it every beat) and fully implemented (4 sources, rate limits, 24h content dedupe), but OCTOPUS_WIRE_EVENT_BRIDGE is unset in both process snapshots and absent from OCTOPUS-flags.cmd's file_flags. Runtime proof beyond the flag: state/telegram/event-bridge-cursor.json does not exist, so _save_cursor has never executed. Consequence chain: this is one of only two callers of Center.push_alert (the other, money_pulse, is also flag-off), so the entire `center-alert` -> inner-DM route in surface-routing.json:29 has zero producers. tg-send-log contains zero rows with stream='center-alert' over 5 days. protective_mode flips, incident.opened, task.failed and C6 TRANSPLANTED births currently reach the owner through no channel at all.

### inner-bot-5 [high] flush_digest advances its marker before delivery — a failed send drops that hour permanently
`F:/backup/_ops/telegram_center/hold_policy.py`

hold_policy.flush_digest sets st['last_digest_flush'] = now and saves at :323-324, then returns the text. center.py:770-773 only THEN calls _route_send, and ignores the result. If the send fails (network, 429 after one retry, unwired inner falling back to an unwired outer), those items are already behind the marker and _pending_items will never return them again. This is asymmetric with the urgent path immediately above it (center.py:761-769), which deliberately only advances mark_urgent_flushed after a non-None message id. The digest path should follow the same discipline.

### inner-bot-6 [high] Ten telegram test files — including the dead-button guard and the whole hold-policy suite — are not registered in run_all.py, so they never run
`F:/backup/_ops/tests/run_all.py`

run_all.py is a static list (no discovery). Missing: test_tg_hold_policy.py (9 tests, incl. the structural guard asserting hold_policy never references held-stream), test_tg_surface_router.py (12), test_tg_route_seam.py (12, incl. t_flag_on_alert_moves_to_the_inner_bot_dm), test_tg_input_surface_policy.py, test_tg_group_is_legs_only.py, test_tg_canonical_access_model.py, test_tg_client_contract.py, test_tg_build_surface.py, test_tg_leg_tasks.py, and — most importantly — test_tg_callback_emitter_parity.py, the AST-based guard that exists precisely to catch cards emitted with no handler in the emitting bot's router. That guard would likely have caught the doctor-card regression. 397 files registered vs 424 present; 29 unregistered overall.

### inner-bot-7 [high] Nothing prevents a keyboard-bearing stream from being routed to the send-only inner client
`F:/backup/_ops/telegram_center/surface_router.py`

surface_router.resolve (surface_router.py:140) takes only (stream, clients, cfg) — it never sees the keyboard. Center._route_send (center.py:1184) accepts `keyboard=` and passes it to whichever client resolve returned (:1215). Today this is safe only by convention: the three inner-target streams happen to be called without keyboards (center.py:763, 773, 1232) while the keyboard-bearing ones (center-decision :717, center-pulse :843) happen to target outer. The contract's own safe_default says missing_callback_handler -> BLOCK_CARD_EMISSION, but no code enforces it; a one-line edit to surface-routing.json would silently create dead cards. The comment at center.py:1196-1197 states the invariant in prose only.

### inner-bot-8 [high] held_view has never executed in production; 177 rows / 124 KB of full message text accumulate unread and unpruned
`F:/backup/_ops/telegram_center/hold_policy.py`

The only route to held_view is the '🔇 ناگفته‌ها' button (center.py:906 -> :944-953). state/telegram/held-viewed.json does not exist, so _mark_viewed (hold_policy.py:353) has never run. Meanwhile surface_policy._archive keeps text[:4000] per row: 177 rows, 78148 chars, 124017 bytes, first 2026-07-28T11:19:12, last 2026-07-31T04:11:14, with no cap, no rotation and no retention policy — the largest plaintext copy of owner-facing output in the telegram state tree. Also note held_since(500) reads only the last 500 lines, so the count shown in the hourly pulse will silently understate once the file passes 500 rows.

### inner-bot-9 [high] The red->green recovery receipt has never fired, and the only critical stream is currently stuck red
`F:/backup/_ops/telegram_center/hold_policy.py`

hold_policy.py:187-189 is the sole producer of the recovery receipt. urgent-outbox.jsonl contains exactly one row and its reason is 'transition-to-red'; there has never been a row with reason='recovery'. hold-policy-state.json still shows streams.doctor.sev='critical' as of ts 1785451647 (2026-07-31T08:47). Because classify treats an unchanged signature+severity as duplicate->HOLD (:178-182), the recovery message only fires if the doctor's text changes AND severity flips to ok — a narrow window that has never been exercised. The capability is code-reachable but runtime-unvalidated; the first real recovery is also the first test.

### inner-bot-10 [high] Five inner-target streams declared in surface-routing.json and validate_contract.py have zero producers
`F:/backup/_ops/telegram_center/surface-routing.json`

doctor-daily, critical-alerts, organ-digest, money-pulse and approvals-organism all carry target {bot: inner, surface: dm} (surface-routing.json:19-23) and are asserted by validate_contract.py:25-29, but repo-wide grep finds no call that passes those names to surface_router.resolve. The only real resolve callers are Center._route_send (6 center-* streams) and cortex/code_autonomy.py:525 ('code-card'). These entries are documentation that a validator agrees with — the classic implemented-and-validated-but-never-called shape. Anyone reading the routing file will believe critical alerts flow to the inner DM; they do not (they flow through center-alert, which has no live producer at all).

### inner-bot-11 [high] The send receipt cannot distinguish inner from outer, so 'it went to the inner DM' is unfalsifiable from the log
`F:/backup/_ops/tg_send_log.py`

tg_send_log.record (:53) writes {ts, chat, topic, stream, sha, chars, ok}. Both bots send to the same owner chat id, so a center-health-digest row is indistinguishable from an outer-bot DM row. The contract itself grades this PARTIAL (gate 8: 'bot_role و surface و سه‌حالتیِ attempted/held/blocked نیست'). Today the only positive evidence that the inner client is real at runtime is an indirect one: center-config.json's commands_set_inner=1, meaning a setMyCommands succeeded on the inner token. Adding bot_role + surface + a held/blocked state to the receipt would close the largest observability hole on this surface.

### inner-bot-12 [high] The inner DM has no input policy: bot_role='inner' is never passed in production
`F:/backup/_ops/telegram_center/input_surface_policy.py`

input_surface_policy.classify implements the inner branch at :123-131 (free chat -> redirect to outer DM, commands/callbacks -> status_approval). But `bot_role=` is supplied at only two production sites, center.py:1324 and center.py:2918, both hardcoded 'outer'. approval_channel — the module that actually polls the inner bot — never imports input_surface_policy. So the ratified rule 'inner + DM + owner -> status/approval only, free chat redirects' has documentation, an implementation and tests, and zero runtime effect. The module's own docstring (:18-20) admits it was written without a caller.

### inner-bot-13 [high] surface_policy.one_thing and surface_policy.card are orphans
`F:/backup/_ops/telegram_center/surface_policy.py`

one_thing (:180) encodes the owner's ratified 'one thing, one button' card form and is covered by four tests (test_surface_policy.py:200-218) — zero production callers. card() (:203) renders the policy's own status card; center.py touches `_spol.` at only lines 879 and 951, neither of which is card(), and /x (center.py:1511) routes elsewhere. Both are exactly the surface_router.resolve / pipeline.prepare_records pattern this codebase keeps reproducing.

### inner-bot-14 [medium] Quiet hours 00:00-07:00 DROP ambient streams outright rather than holding them
`F:/backup/_ops/budget/approval_channel.py`

approval_channel.py:1603 returns False before the surface-policy block, so between midnight and 07:00 any stream not in _NEVER_QUIET = {cortisol, alert, heart} (:143) never reaches surface_policy.hold and therefore never reaches hold_policy — it is not archived, not digested, not counted. The in-code justification ('ambient is periodic, the next version will come') predates the hold machine, which was specifically built so that silence would not equal forgetting. Note doctor and needs are NOT in _NEVER_QUIET: a doctor card that turns critical at 03:00 is discarded before classify can mark it transition-to-red. held-stream.jsonl shows exactly one row inside the quiet window (2026-07-31T04:11:14, and that came via the heart exemption).

### inner-bot-15 [medium] hold-policy-state.json is a shared read-modify-write file across two processes with no lock
`F:/backup/_ops/telegram_center/hold_policy.py`

The organism writes streams[*] from classify (hold_policy.py:196) while the center writes last_urgent_flush (:268) and last_digest_flush (:324) — both via _load_state -> mutate -> _save_state with no file lock (compare opslib.LockedJson used elsewhere, e.g. wiring.py:3121). The write itself is atomic (tmp + os.replace at :132-134) but the read-modify window is not, so a center flush landing between an organism load and save will be overwritten, replaying an already-sent urgent row or re-firing a digest. This is the same two-writers-one-state-file class already recorded twice in this repo's memory.

### inner-bot-16 [high] The input-policy deny path never answers the callback query
`F:/backup/_ops/telegram_center/center.py`

center.py:1327-1338 sends a redirect text and returns, but never calls self._answer(cbq, ...) / client.answer_callback. Telegram keeps the button spinner turning until it times out, which reads to the owner as 'the bot is broken' rather than 'this belongs in the DM'. Every denied group callback — including the three live doctor cards — produces this.

### inner-bot-17 [medium] severity() can mint a false recovery from an unrelated green glyph
`F:/backup/_ops/telegram_center/hold_policy.py`

_OK at hold_policy.py:91 matches a bare 🟢, 'سبز', 'سالم' or \bOK\b anywhere in the message. A routine heart or doctor card that happens to contain a 🟢 for one sub-indicator classifies as sev='ok'; if the previous state for that stream was 'critical', classify (:187) emits an immediate 'بازگشت از قرمز به سبز' receipt to the owner's DM even though nothing recovered. The inverse is guarded (red beats green, :106-109) but this direction is not. Currently latent because only one stream has ever been critical.

### ادعاهای ردشدهٔ inner-bot (ممیزِ متخاصم — این‌ها را دنبال نکن)

- **surface_policy.card (surface_policy.py:203) is code=orphan — 'center.py references _spol. at only two lines (879, 951), neither of which is card(). /x at center** — REACHABLE via dynamic dispatch the scanner grepped straight past. capability_registry.discover() (capability_registry.py, _zero_arg_card at :87) AST-scans SCAN_DIRS — which includes 'telegram_center' — for any module-level zero-argument card(). surface_policy.py has exactly that at :203 plus a module-level FLAG at :43. I ran capability_registry.discover() read-only: 25 rows returned, one of them i
- **Red->green recovery receipt: 'runtime unproven ... The one critical stream (doctor) is still sev=critical in hold-policy-state.json, so the transition has not y** — FALSIFIED BY LIVE STATE, and the real defect is worse than described. F:/backup/_ops/state/telegram/hold-policy-state.json now reads streams.doctor = {sig: da129daef6623b160fdd66ae, sev: "normal", ts: 1785453832.4015954} = 2026-07-31T09:23:52. The exit from critical ALREADY HAPPENED (critical at 08:47:27 per the single urgent-outbox row reason=transition-to-red; normal at 09:23:52), and the matchi
- **Ten telegram test files are unregistered in run_all.py (test_tg_hold_policy, test_tg_surface_router, test_tg_route_seam, test_tg_input_surface_policy, test_tg_g** — It is EIGHT, not ten, as of tests/run_all.py mtime 2026-07-31 09:44. run_all.py:607 registers "test_tg_leg_tasks.py" and :608 registers "test_tg_group_is_legs_only.py". The remaining eight have literally zero occurrences of their name in run_all.py and so never run. The gap's substance survives — including the two that matter most, test_tg_callback_emitter_parity.py (the AST emitter/handler parity
- **Center.push_alert is code=orphan.** — Mis-labelled axis. push_alert has two real, static, non-test callers: telegram_center/event_bridge.py:235 and heart/money_pulse.py:110 (verified by repo-wide grep excluding tests/_Archive). It is FLAG-DARK, not caller-less — both callers sit behind OCTOPUS_WIRE_EVENT_BRIDGE and OCTOPUS_WIRE_MONEY_PULSE, which I confirmed absent from all four flags-loaded-*.json snapshots. The evidence sentence in 
- **Implied by gap #1 ('The deny path also never calls self._answer(), so the owner sees a spinner that hangs') read alongside 'doctor_link.handle_callback can neve** — doctor_link is not at fault for the spinner. doctor_link.py:207-209 explicitly calls center._answer(cbq, toast) on BOTH outcomes ('🩺 رأی ثبت شد' / '🩺 رأی نرسید'). The hanging spinner belongs entirely to the center's input-policy deny branch in handle_update, which sends redirect text and returns without any answer_callback. Keep the two facts separate or the fix gets aimed at the wrong module.
- **All center.py file:line anchors: _handle_callback at 2891, run_forever at 3112, run_once->poll_updates at 3091 ('the only invocation is center.py:3091'), bot_ro** — NOT a scanner error — UNVERIFIABLE BY CONSTRUCTION, and I am flagging it so the parent does not treat drift as a defect. center.py is being actively rewritten by a concurrent session: 202158 bytes/3268 lines when I started, 208074 bytes/3364 lines twenty minutes later (mtime Jul 31 09:46), git status dirty, plus 8 sibling worktree copies. Within my own single pass the same symbol moved (e.g. _hand
- **urgent-outbox.jsonl 'Stores up to 800 chars of raw message text per row' with the live row at len(text)=742.** — Not refuted — CONFIRMED, but flagging a measurement trap that nearly made me report it as wrong. Reading that file through a shell pipe on Windows decodes UTF-8 as cp1252 and inflates the count to 1131; opening with encoding='utf-8' gives exactly 742, matching the cap `head = str(text or "")[:800]` at hold_policy.py:232 and the send-log row chars=742. Any future agent re-measuring Persian text len

## گروهِ فوروم (پاها) — 19 قابلیت · 15 شکاف · 8 ادعای ردشده

### group-1 [high] The group's core-command refusal is a verb BLACKLIST — 31 of 39 probed commands still execute in a leg topic
`F:/backup/_ops/telegram_center/input_surface_policy.py`

input_surface_policy.CORE_VERBS (input_surface_policy.py:34-42) enumerates 41 forbidden verbs; everything else is allowed. Verified by direct read-only probe of classify() with topic 22: /now (full core status), /menu, /start, /x (capability catalog), /flags, /trace, /scan, /insight, /verdicts, /missions, /live, /id, /eq, /box, /revenue, /stuck, /panel, /deal, /doctrine, /funnel + the 7 funnel verbs, and the Persian /توان /رفتار /کد all return allow=True mode=leg_scoped. Note the singular/plural holes: 'mission' is blocked but /missions is not; 'verdict' blocked but /verdicts not; 'flag' blocked but /flags not; 'capability' blocked but /x IS the capability card. The _CMD regex (input_surface_policy.py:73) is ASCII-only, so every Persian slash command bypasses the verb check entirely. This directly contradicts the contract's forbidden_behavior list (core_chat, flag_control, global_approval, world_discovery_chat) and the pinned guide's promise at guide.py:41-43.

### group-2 [high] Unknown /commands in a leg topic are bridged straight into the organism's core router, including /neworgan and /organ-approve
`F:/backup/_ops/telegram_center/center.py`

center.py:1565-1568 forwards any unrecognised /command to _bridge_to_organism (center.py:1629) -> approval_channel.handle_command (budget/approval_channel.py:1680). Probe confirms allow=True from topic 22 for /overview, /blueprint, /money, /finance, /school, /safety, /alerts, /organs, /upgrades, /queue, /reentry, /wiring, /health, /review, /books, /sync, /reveal, /neworgan foo and /organ-approve foo. Only /brain and /doctor are caught by CORE_VERBS. /neworgan and /organ-approve are organ-creation/approval verbs (approval_channel.py:1785-1787) — state-changing core control reachable from the legs-only surface. /organ-approve slips through because _verb_of stops at the hyphen and yields 'organ'.

### group-3 [high] The leg-task intake shadows mirror_room, chat_room and _handle_ask for every non-question statement in the group
`F:/backup/_ops/telegram_center/center.py`

handle_update returns at center.py:1425 as soon as a leg_scoped non-'/' non-question message becomes a task. mirror_room (center.py:1855), chat_room (center.py:1575) and _handle_ask (center.py:1578) all live inside _handle_message, which handle_update only reaches at center.py:1435-1437. Verified: leg_tasks.is_question('امروز درباره خودت چه فهمیدی') is False, and classify() gives leg='mirror' for topic 205 — so the self-awareness room silently became a task queue on 2026-07-30. Two armed flags (OCTOPUS_WIRE_CHAT_ROOM=1, OCTOPUS_TG_MIRROR=1) now gate code that cannot be reached from the group.

### group-4 [high] The leg-card anti-flood hash is defeated for any leg that has at least one task
`F:/backup/_ops/telegram_center/leg_tasks.py`

_refresh_leg_card returns early only when the text hash is unchanged (center.py:1030-1032), but leg_tasks.card_text embeds a RELATIVE age string («آخرین فعالیت: ۱۲ ساعت قبل», leg_tasks.py:206 via _age leg_tasks.py:163). Proven by direct computation: for `lead`, card sha is 3119ec522557b029 at now, e834784126b1ce18 at now+3600s, d0c7b237603e5e46 at now+7200s; `mining` (zero tasks) is 8c62c55798988893 at now, +1h and +24h. This is exactly the 'counter in the dedup key' bug that leg_room_report.signal_hash (leg_room_report.py:127-134) was written to avoid. Consequence: one editMessageText per active leg per round-robin cycle, forever, and none of it appears in tg-send-log because edits are not logged.

### group-5 [high] The `system` and `mirror` cards carry ⏸/▶️ buttons that can never work
`F:/backup/_ops/telegram_center/power.py`

leg_tasks.card_keyboard (leg_tasks.py:210) emits tk:c/tk:p for every leg, and _refresh_leg_card is called for all 10 keys of render.LEGS. But power.PAUSABLE_LEGS (power.py:40-41) has 8 entries and deliberately excludes 'system'; 'mirror' is absent too. Pressing ⏸ on the system or mirror card runs pause_leg -> (False, 'پای ناشناخته: system') and posts «توقف نشد: پای ناشناخته: system» into the topic (center.py:1088-1090). Two of the ten pinned cards are half-dead — the same 'dead card' class the contract's gate 3 already flagged for `oc:`.

### group-6 [high] `system` (28) and `mirror` (205) are treated as legs by the input gate although the contract lists only 8 allowed topics
`F:/backup/_ops/telegram_center/input_surface_policy.py`

input_surface_policy._leg_of (input_surface_policy.py:167-177) accepts ANY key present in center-config.topics, so topic 28 and 205 classify as leg_scoped. TELEGRAM-ACCESS-CONTRACT.v1.json surfaces.legs_forum_group.allowed_topics lists exactly 8 (no system, no mirror) and sets unknown_topic='deny-and-redirect'. Probe: '/now' in topic 28 -> allow=True group-topic-system; a plain sentence in topic 28 -> a `system` task. LEG_ALIASES (input_surface_policy.py:61-71) also has no 'system' entry, so cross-leg detection there is name-only.

### group-7 [high] Ten group-surface test files are ORPHANS — run_all has no auto-discovery, so they have never run
`F:/backup/_ops/tests/run_all.py`

tests/run_all.py:601 states it explicitly: «run_all هیچ glob/discovery ندارد ⇒ ثبت‌نشده = هرگز اجرا نشده». Cross-checking every test_tg*/test_leg* file on disk against the registry string shows these are unregistered: test_tg_leg_tasks.py (18 t_ functions, the whole 4-state model), test_tg_group_is_legs_only.py (7), test_tg_input_surface_policy.py (20), test_tg_canonical_access_model.py, test_tg_hold_policy.py, test_tg_surface_router.py, test_tg_route_seam.py, test_tg_build_surface.py, test_tg_client_contract.py, test_tg_callback_emitter_parity.py. Every guard written for this surface in the last three days is dark; test_tg_guide.py (run_all.py:252) is the only registered one, and it only checks the guide TEXT.

### group-8 [high] Core doctor cards land in the group's General and the path is still armed
`F:/backup/_ops/telegram_center/doctor_link.py`

doctor_link.beat (doctor_link.py:155) calls client.send(..., topic_id=_topic_id()) with no chat_id; tg_api._resolve_chat (tg_api.py:342-346) then returns `_center` = the group. With OCTOPUS_DOCTOR_TOPIC_ID unset it is General. Runtime proof: state/telegram/doctor-link-cursor.json sent_keys {'wire:test': mid 323 @1785306727, 'doctor-pulse:intent': mid 324 @1785313103, 'doctor-pulse:diff': mid 325 @1785313738} and the send log has chat=-1004475788460 topic=null rows at exactly 07-29 16:32:08, 18:18:24, 18:28:59. These are self-rewrite intent/diff owner-vote cards — the contract routes doctor-intent/doctor-diff to owner_outer_dm. Nothing has changed since; the next doctor pulse repeats it.

### group-9 [high] The pinned status line is core content living in the legs-only group, and its 300s edit loop is invisible to every audit
`F:/backup/_ops/telegram_center/center.py`

ensure_setup sends it with pin=True and no topic (center.py:540) => General; beat edits it every 300s with render.render_status (center.py:607-614), which renders overall octopus mood, execution lanes, heart period and AU$ money (render.py:349-395). center-config.status_message_id=66. surface-routing.json defines a `center-status` stream whose target is the owner DM, but grep shows ZERO production callers — the pin never goes through _route_send. And because tg_api.edit does not log (tg_api.py:398-411 vs :379-390), no receipt exists for ~288 edits/day.

### group-10 [high] Half the group is structurally incapable of ever carrying real leg data
`F:/backup/_ops/legs/leg_room_report.py`

wiring.leg_rooms_beat feeds due() from business_legs_beat()['business_legs'] (wiring.py:3567-3569), whose live keys are exactly {lead, mining, crypto, accounting, knowledge}. leg_room_report.LABEL (from chat_room.LEGS, chat_room.py:75-103) names 7 including ziman and cartographer — those two can never be due. studio_pf, system and mirror are in no table at all. Result on disk: state/leg-room-report.json has 5 keys, and topics 23 (ziman), 27 (studio_pf), 28 (system), 65 (cartographer), 205 (mirror) have received nothing but templates and cards for their entire existence. surface_policy.LEG_TOPIC (surface_policy.py:61-65) maps a stream named 'studio' that no producer ever emits.

### group-11 [high] The daily per-leg digest is 89% byte-identical noise
`F:/backup/_ops/telegram_center/center.py`

center.py:667-692 posts one message per leg every 24h with no change-detection at all (unlike leg_room_report, which is change-triggered). Measured over 4 consecutive days in tg-send-log.jsonl: lead/ziman/mining/crypto/accounting/studio_pf/knowledge each have exactly 1 unique sha across 4-5 sends; system has 2; only cartographer has 4/4. 32 of the 37 digest rows are repeats of a sha already delivered to the same topic. This is the same 'periodic report turned the group into a noise pipe' failure that surface_policy.py:9-17 measured and claimed to have fixed — the fix was applied to the organism's streams but never to the center's own digest loop.

### group-12 [high] Probe writes contaminate the live leg-task state, and nothing detects it
`F:/backup/_ops/state/telegram/legs/lead-tasks.json`

state/telegram/legs/lead-tasks.json holds 6 QUEUED tasks created at real wall-clock times on 07-30 (20:56:23, 20:56:58, 21:28:46) with the fixture strings from guide.py:32 and tests/test_tg_leg_tasks.py:35. They will render «در صف: ۶» on the pinned lead card forever, they make _drive_leg_engine's queue look non-empty to a human, and after 24h the progress line degrades to «پیشرفت: ۰/۰ · در صف: ۶» (leg_tasks.py:179-202 counts `today` by updated-within-24h). _refresh_leg_card already carries a bogus-id guard for the 9000-9099 spy range (center.py:1025-1029); there is no equivalent guard for probe-written tasks.

### group-13 [medium] input_surface_policy's own docstring still says it has no caller
`F:/backup/_ops/telegram_center/input_surface_policy.py`

input_surface_policy.py:18-20 reads «⚠️ این ماژول صداکننده ندارد و عمداً. وصل‌کردنش یعنی ویرایشِ center.py …». It HAS been wired since 2026-07-30 (center.py:1317-1338 and center.py:2914). A future reader — or a reachability scan that trusts docstrings — will classify the live input gate as an orphan and may 'clean it up'.

### group-14 [medium] The deny/redirect path never answers a callback query
`F:/backup/_ops/telegram_center/center.py`

center.py:1327-1338 sends the redirect text and returns without calling answer_callback. For any button pressed on a card sitting in General or an unknown topic, Telegram's spinner hangs until timeout. Today the blast radius is small (the guide and status pins carry no buttons), but doctor_link's cards DO carry ok/no buttons and land in General (message_ids 324/325) — pressing them from General hits exactly this path.

### group-15 [high] No capability manifest exists for the legs/group surface
`F:/backup/_ops/telegram_contract/TELEGRAM-ACCESS-CONTRACT.v1.json`

TELEGRAM-ACCESS-CONTRACT.v1.json gate 4 records «PARTIAL — doctor/telegram-diagnostics/legs پوشش ندارند». Confirmed: the only capability-manifest.json files are _ops/capability-manifest.json (self_goal_cycle), action_bridge/, owner_console/, unified_control/, integrations/world_discovery_action/. The whole group surface — 10 topics, 4 card buttons, the task lifecycle — has no manifest, so `default_unknown_action: BLOCK` and `missing_capability_probe: IMPLEMENTED_NOT_LIVE` apply to it by the contract's own rules.

### ادعاهای ردشدهٔ group (ممیزِ متخاصم — این‌ها را دنبال نکن)

- **The `entrypoints` table is a usable map: e.g. `Center.run_forever` at center.py:3112, `handle_update` 1296, `_route_send` 1184, `_bridge_to_organism` 1629, `_re** — center.py was rewritten UNDER the scan. At my session start F:/backup/_ops/telegram_center/center.py was 202158 bytes, mtime 2026-07-30 23:01. At 09:44:40 it became 205023 (live tree picked up commit e3a8e56 'feat(tg): control-room phase-1 gaps', dated 07-31 09:18), and at 09:46:31 it was 208074 with 48 further uncommitted insertions (`git diff` = tr: tool-request callback). Verified anchors: pre-
- **`Center.run_forever` is at F:/backup/_ops/telegram_center/center.py:3112.** — Wrong even against the file the scan read. In e3a8e56^ `def run_forever(self, *, beat_every_s: float = 300.0)` is at line 3065; line 3112 there is inside `_save_config`. In the current file it is 3208. This is the one anchor in the table that was never right.
- **'Ten group-surface test files are ORPHANS … test_tg_leg_tasks.py (18 t_ functions, the whole 4-state model), test_tg_group_is_legs_only.py (7) … Every guard wri** — Eight, not ten, and the 4-state model is no longer dark. Commit e3a8e56 (07-31 09:18) registered test_tg_leg_tasks.py AND test_tg_group_is_legs_only.py in F:/backup/_ops/tests/run_all.py, and added+registered test_tg_leg_commands.py (289 lines). I re-scanned run_all.py (67956 bytes, mtime 09:44:40) after the merge: remaining orphans are test_tg_build_surface, test_tg_callback_emitter_parity, test_
- **'The leg-task intake shadows mirror_room, chat_room and _handle_ask for EVERY non-question statement in the group … handle_update returns as soon as a leg_scope** — 'Every' is now false. The same 09:18 commit inserted three explicit pre-branches ahead of `leg_tasks.add` in handle_update (current center.py:1454-1508, new module telegram_center/leg_commands.py): (a) a reply to a card containing '🚧' routes to `leg_tasks.resolve_blocked`; (b) `leg_commands.classify` full-matches a closed set of 8 command keys (status/queue/resume/pause/next/blockers/receipts/repo
- **'32 of the 37 digest rows are repeats of a sha already delivered to the same topic.'** — 24, not 32. I recomputed from F:/backup/_ops/state/tg-send-log.jsonl over the 22:0x windows: topic 22 = 5 sends/1 unique, 23 = 4/1, 24 = 4/1, 25 = 4/1, 26 = 4/1, 27 = 4/1, 28 = 4/2, 29 = 4/1, 65 = 4/4. Total 37 sends, 13 unique shas ⇒ 24 repeats (65%), not 32 (86%). The 37 total, the '8 of 9 legs frozen' (≈89%) and 'only cartographer changes daily' are all correct; the repeat count is not.
- **'the group has THREE independent writers … Only the first goes through surface_router.'** — There is a fourth wired writer and it IS a surface_router consumer. F:/backup/_ops/cortex/code_autonomy.py:~533-550 (`propose_to_owner`) constructs its own `tg_api.TgClient()`, then calls `surface_router.resolve('code-card', …)`; with the flag off the documented fallback is `cfg['topics']['system']` — i.e. the group. It has real production callers: _ops/self_patch.py:531 and _ops/cortex/code_brain
- **OCTOPUS_TG_MERGED_DIGEST is 'ABSENT from all three live flag dumps (state/flags-loaded-center.json / -organism.json / -live.json)'.** — There are four dumps, not three: F:/backup/_ops/state/ also contains flags-loaded-cortex.json (mtime 1785451039). The conclusion holds — I confirmed OCTOPUS_TG_MERGED_DIGEST is absent from all four — but the enumeration of the evidence base is incomplete.
- **'The contract's runtime_status says «ورودی LIVE · خروجی LIVE» but live=false with gates 5, 6 and 9 pending owner action.'** — `runtime_status` is not a top-level key — it is at `owner_ratification.runtime_status` in F:/backup/_ops/telegram_contract/TELEGRAM-ACCESS-CONTRACT.v1.json, alongside live=false, live_input=true, live_output=true. `owner_ratification.live_requires` names gate 5, gate 9, and the inner-world HOLD-vs-Inner-DM decision. Gate 6 is not in that list.

## ترانسپورت و مسیریابیِ مشترک — 63 قابلیت · 20 شکاف · 9 ادعای ردشده

### shared-transport-1 [high] The only tests of surface_router and of the _route_send seam are unregistered — they have never run
`F:/backup/_ops/tests/run_all.py`

run_all.py has no auto-discovery (grep for glob/discover in tests/run_all.py returns only unrelated comment text), so an unlisted file never executes. Of 424 test files, 29 are unregistered, and 11 of those are exactly this surface: test_tg_surface_router.py (12 tests, the ONLY coverage of resolve), test_tg_route_seam.py (12 tests, the ONLY coverage of Center._route_send, including t_the_center_actually_calls_route_send_for_its_core_ambient_sends — the guard that exists specifically to prevent the zero-caller failure mode), test_tg_hold_policy.py, test_tg_group_is_legs_only.py, test_tg_canonical_access_model.py, test_tg_callback_emitter_parity.py, test_tg_client_contract.py, test_tg_input_surface_policy.py, test_tg_build_surface.py, test_tg_leg_tasks.py, test_studio_telegram.py. The contract file cites '12/12 green' for the router — those greens came from a manual run, not from the suite. Every routing invariant this scan describes is currently unguarded against regression.

### shared-transport-2 [high] 12 of 18 routing entries have no emitter; every stream name actually emitted at runtime has no routing entry
`F:/backup/_ops/telegram_center/surface-routing.json`

surface-routing.json reads like the system's routing table but governs almost nothing. Orphan entries (no emitter anywhere): chat, doctor-intent, doctor-diff, intuition, doctor-daily, critical-alerts, organ-digest, money-pulse, approvals-organism, legs-all, center-status, and code-card is emitted but never logged. Meanwhile the 16 stream labels that actually appear in tg-send-log.jsonl (center, needs, discovery, brain, doctor, heart, cortisol, knowledge, mining, lead, crypto, accounting, plus 10 leg-card-*) appear in ZERO routing entries — they are governed by surface_policy.LEG_TOPIC/SELF_STREAMS/SAFETY_STREAMS and approval_channel._STREAM_TOPIC instead. Anyone editing surface-routing.json to change where doctor output goes will change nothing. The migration is half-done: five center-* entries were added on 07-30 and wired; the other twelve were written as a target-state document and never connected.

### shared-transport-3 [high] 36 of ~42 send sites in center.py bypass surface_router entirely under the default label 'center'
`F:/backup/_ops/telegram_center/center.py`

tg_api.TgClient.send defaults to stream='center' (tg_api.py:350) and 36 `self._client.send(...)` sites in center.py pass no stream and no router. Result: 123 of 299 send-log rows are labelled 'center', and 60 of those went to the group with topic=None (General). Because 'center' is not a key in surface-routing.json, if any of them ever DID go through resolve they would trip _alert_unknown — and that alert has fired zero times, which independently proves the bypass. The legs-only contract is therefore enforced for exactly six stream names and unenforced for everything else. Concrete post-flag example: eight rows at 07-30 22:07:10-22:07:23 (the per-leg digest loop at center.py:685) went straight to group topics 23-29 and 65 with the split flag already armed.

### shared-transport-4 [high] center-status is a routing entry for a message that is hardcoded to the group
`F:/backup/_ops/telegram_center/center.py`

surface-routing.json:26 promises the pinned status/home message moves to the anchor DM when the flag is armed. The flag IS armed. But the message is created at center.py:540 with `self._client.send(_scrub(text), chat_id=chat_id, pin=True)` where chat_id is the group id — no stream, no router. center-config.json:51 status_message_id=66 confirms it lives in the group. The routing entry describes an intent nobody implemented, and its only other appearance in the repo is a test fixture list (tests/test_tg_route_seam.py:99) that iterates the name without asserting an emitter exists.

### shared-transport-5 [high] legs-all would land in group General — _TOPIC_KEY has no such key and the live config has no such topic
`F:/backup/_ops/telegram_center/surface_router.py`

surface_router._topic_id_for (surface_router.py:99-110) for topic=='per-leg' looks up `stream` in cfg['topics'], else _TOPIC_KEY (surface_router.py:41-45). 'legs-all' is in neither: the live center-config.json topics are lead/ziman/mining/crypto/accounting/studio_pf/system/knowledge/cartographer/mirror. So resolve('legs-all') returns topic_id=None → group General, the one place the contract explicitly denies. This is masked because the test fixture at tests/test_tg_surface_router.py:32 invents `"legs-all": 66` — a topic that does not exist in production — and then asserts topic == TOPICS['legs-all'] at :92 and :153. The fixture is richer than reality, so both tests pass on a broken path (and neither runs anyway).

### shared-transport-6 [high] center-digest routes into a dark flag
`F:/backup/_ops/telegram_center/center.py`

The center-digest entry was one of the five added on 07-30 to fix the '58 core messages in General' problem, and it is the only one whose emitter is gated. center.py:652 sits inside `if _merged:` (center.py:625) on OCTOPUS_TG_MERGED_DIGEST, which is absent from OCTOPUS-flags.cmd and from all four flags-loaded-*.json snapshots. Zero center-digest rows exist in the send log. Meanwhile the else-branch at center.py:667-692 — the path that actually runs — sends per-leg digests with no stream label and no router. So the fix was applied to the branch that is off and not to the branch that is on.

### shared-transport-7 [high] The send log cannot distinguish the inner bot from the outer bot, so the split it was built to verify is unverifiable
`F:/backup/_ops/tg_send_log.py`

tg_send_log.record writes {ts, chat, topic, stream, sha, chars, ok} (tg_send_log.py:57-61). Both clients target the same owner_chat_id (center.py:304-307 passes the outer's owner/center ids into the inner client), so a DM row is identical whichever bot sent it. center-urgent and center-health-digest have target bot:inner; their 6 rows all show chat=6150431610 and prove delivery but NOT which bot delivered. If _inner_client() silently returned None, surface_router.py:180 would fall back to outer and the log would look exactly the same. The contract's own gate 8 already flags this as PARTIAL ('bot_role و surface نیست') — it remains open, and it is the single cheapest fix that would make every other routing claim checkable.

### shared-transport-8 [high] _route_send's exception fallback dumps core messages into the group system topic, contradicting the legs-only contract
`F:/backup/_ops/telegram_center/center.py`

center.py:1209-1211: if surface_router raises, the code falls back to `cl, cid, tid = self._client, cfg.get('chat_id'), topics.get('system')` — the outer bot, the group, topic system. surface_router itself was deliberately changed on 07-30 so that ambiguity resolves to DM rather than group (surface_router.py:119-137, with a long comment explaining exactly why group is the wrong answer). The caller's fallback still encodes the old, rejected rule. A malformed surface-routing.json would push center-urgent (a red-transition alert) into a shared group topic instead of the owner's private chat.

### shared-transport-9 [medium] No central callback_data 64-byte enforcement; the per-emitter guards slice characters, not bytes
`F:/backup/_ops/telegram_center/tg_api.py`

Telegram rejects the ENTIRE sendMessage when any callback_data exceeds 64 bytes — one long button kills the whole card. tg_api._scrub_keyboard (tg_api.py:97) is the one place every outgoing keyboard passes through, and it copies callback_data untouched. Enforcement is scattered and inconsistent: leg_tasks.py:212-215/223-224/247-248, capability_registry.py:355, owner_console/views.py:76 use `[:64]` on the STRING (64 Persian characters = up to 128 bytes), approval_channel.py:2826 refuses loudly instead, callback_token.py:32-37 does careful byte arithmetic. Today every id in these paths is ASCII so nothing breaks, but nothing structurally prevents a Persian capability_id or leg key from silently killing a card. tests/test_callback_routing.py:157-169 asserts the byte cap correctly but only over the emitters it enumerates — and a new emitter is invisible to it.

### shared-transport-10 [medium] The 429 backoff has never executed against Telegram
`F:/backup/_ops/telegram_center/tg_api.py`

tg_api.py:155/298/309/322/491 implement a capped, single-retry backoff on both the HTTPError and ok=False shapes, and it is 'always on' by owner vote (per the comment at tg_api.py:164) rather than flag-gated. Five registered tests cover it. But governor/governor-alerts.md contains no real Telegram 429 across the whole retained window — the one '429' hit is 'ORGANISM-STATE کهنه (429min > 60)'. The retry path is correct-by-test and unexercised-by-life; the _sleep injection point (tg_api.py:221) means a production regression here would be silent (a swallowed sleep just becomes a dropped message via the existing fail-soft return None).

### shared-transport-11 [high] doctor cards go to group General — the exact surface the contract marks deny-and-redirect
`F:/backup/_ops/telegram_center/doctor_link.py`

doctor_link.py:155 sends with topic_id=_topic_id(), and _topic_id (doctor_link.py:107) reads OCTOPUS_DOCTOR_TOPIC_ID which is not set anywhere. tg_api._resolve_chat (tg_api.py:346) then prefers self._center (the group). Three deliveries are recorded in doctor-link-cursor.json (message ids 323, 324, 325). These are precisely the doctor-intent and doctor-diff streams that surface-routing.json:16-17 routes to the owner's DM — but doctor_link never asks the router, so the entries are decorative and the cards sit in a shared group's General topic. This is also the 'doctor_chat' item in the contract's forbidden_behavior list.

### shared-transport-12 [medium] surface_policy.LEG_TOPIC uses key 'studio' while every other layer uses 'studio_pf'
`F:/backup/_ops/telegram_center/surface_policy.py`

surface_policy.py:63 maps "studio": "studio_pf". But the emitter side (wiring._BUSINESS_LEGS_SPEC, wiring.py:2742-2746) produces lead/mining/crypto/accounting/knowledge, and every other table — render.LEGS:46, center.LEG_KEYS:104, surface_router._TOPIC_KEY:43, center-config.json:12 — uses studio_pf as the key. If a studio_pf leg emitter is ever added, route('studio_pf') will miss LEG_TOPIC, fall through to the ambient branch, and be HELD instead of posted to its topic. Same class of latent orphan: 'ziman' and 'cartographer' are in LEG_TOPIC with no emitter, and 'identity'/'insight' are in SELF_STREAMS with no emitter, and 'alert' is in SAFETY_STREAMS with no emitter.

### shared-transport-13 [high] A fourth stream vocabulary exists in the access contract with three names that exist nowhere else
`F:/backup/_ops/telegram_contract/TELEGRAM-ACCESS-CONTRACT.v1.json`

TELEGRAM-ACCESS-CONTRACT.v1.json:147-172 `stream_targets` lists world-discovery, self-goal and action-draft alongside the surface-routing names. Those three have no emitter, no routing entry, and no send-log row (grep over prod python finds only unrelated schema strings like 'world-discovery.bundle.v1'). validate_contract.py:21-30 only checks 8 of the contract's names against the routing file, so this third-vs-fourth-vocabulary drift is unvalidated. Anyone reading the contract as the source of truth will look for streams that were never built.

### shared-transport-14 [medium] The group carries two topics ('system' and 'mirror') that the legs-only contract does not allow
`F:/backup/_ops/telegram_center/center.py`

The contract's allowed_topics (TELEGRAM-ACCESS-CONTRACT.v1.json:117-124) lists 8 leg topics and excludes system and mirror. But center.LEG_KEYS (center.py:103-104) includes 'system', render.LEGS (render.py:47,52) includes both system and mirror, and center-config.json:13,16 has system=28 and mirror=205. Runtime confirms: leg-card-system → topic 28 and leg-card-mirror → topic 205 at 07-30 23:25 and 23:41, and 11 stream='center' rows to topic 28. Topic 28 ('⚙️ سیستم') is by construction core content in a legs-only surface. Note also that surface_policy's own comment (surface_policy.py:19-22) predicted the group would go silent because no stream name is a leg — the leg cards and per-leg digests are what refilled it, and they did so outside the policy.

### shared-transport-15 [high] input_surface_policy's docstring says it has no caller; it has two
`F:/backup/_ops/telegram_center/input_surface_policy.py`

input_surface_policy.py:19-21 states 'این ماژول صداکننده ندارد و عمداً' — deliberately unwired, waiting for a parallel session's hunks to land. Those hunks landed: it is imported and its verdict enforced at center.py:1318 (the main update path, unflagged, fail-open on exception) and at center.py:2914 (the oc: callback path). Reading the module to decide whether the group input gate is live gives the wrong answer. This is the input-side twin of the recurring failure mode: the doc claims orphan status for something that is now the first gate every group message hits.

### shared-transport-16 [medium] center-alert is wired end-to-end and has never delivered
`F:/backup/_ops/telegram_center/event_bridge.py`

push_alert (center.py:1222) is the documented push path for event_bridge (event_bridge.py:235 calls center.push_alert), it routes 'center-alert' whose target is the inner bot's DM, and OCTOPUS_WIRE_EVENT_BRIDGE gates the bridge at center.py:731-733. Zero rows with stream=center-alert exist in 299 send-log rows spanning five days. tg_send_log.record logs ok=False on failure too, so this is not 'tried and failed' — event_bridge has never produced an alert. Whether that is correct (no critical events) or a dead upstream is not determinable from any artifact in this surface.

### shared-transport-17 [high] The HMAC callback layer is fully built, secret-provisioned, and switched off — with its own misconfig alarm disarmed as a side effect
`F:/backup/_ops/telegram_center/callback_token.py`

callback_token.py is complete (mint/verify, constant-time compare, expiry inside the MAC, a carefully computed 64-byte budget) and center._tok_kb (center.py:2739) is wired at two card sites (center.py:710, 1920). OCTOPUS_CB_SECRET IS set in the live process, but OCTOPUS_WIRE_CB_TOKEN is not defined anywhere in OCTOPUS-flags.cmd — only in a July-21 deploy runbook. So flag_on() is False, _tok_kb returns the keyboard unchanged, and the warning at center.py:3122 (which fires only when flag_on and not ready) can never fire. Today's actual protection for a button press is is_owner(from.id) (tg_api.py:267) plus the atomic single-use pop — which the module's own docstring acknowledges are the primary gates. The gap is that nothing in the running system reports that the defense-in-depth layer is inert.

### shared-transport-18 [medium] approval_channel.send_text sets message_thread_id without the cid < -1000 guard that tg_api has
`F:/backup/_ops/budget/approval_channel.py`

tg_api.py:368 refuses to attach message_thread_id unless the chat is a forum supergroup, precisely because sending it to a private chat is a 400 Bad Request. approval_channel.py:1642-1643 has no such guard: `if thread is not None: body['message_thread_id'] = thread`. Today it is safe because thread is only set when both r_chat and r_topic came from the group config (:1638) or when a caller passes topic_id explicitly (:1596) — and no current caller passes topic_id with a DM chat_id. But the second sender in the system does not share the first sender's invariant, and nothing tests the pairing.

### shared-transport-19 [medium] tg_send_log.stats has no production caller — the measurement built to precede the anti-spam decision is never read by the system
`F:/backup/_ops/tg_send_log.py`

tg_send_log.py:110 computes sends/unique/duplicates/duplicate_pct/by_stream, and the module's docstring (tg_send_log.py:5-10) exists because three prior reports diagnosed 'spam' without ever counting messages. The counter runs; the reader does not. grep finds no caller outside the __main__ block at :131. So the duplicate rate is measurable on demand by a human but is not surfaced in any card, pulse, or digest — including the hourly anchor pulse, which is exactly where it belongs.

### shared-transport-20 [medium] held-stream.jsonl is an unbounded plaintext store of undelivered owner content with no drain
`F:/backup/_ops/telegram_center/surface_policy.py`

surface_policy._archive (surface_policy.py:148) appends up to 4000 chars of raw message text per held item. The file is 124KB / 177 rows covering 2026-07-28T11:19:12 → 2026-07-31T04:11:14 (heart 107, doctor 54, needs 10, summary 6). hold_policy deliberately never reads it — that is the structural guarantee against backlog replay (hold_policy.py:20-23) — which also means nothing will ever consume or trim it. It grows for as long as any ambient stream is classified 'duplicate'. Contrast with tg-send-log.jsonl, which stores only a hash by design; the held archive is the one place message bodies persist.

### ادعاهای ردشدهٔ shared-transport (ممیزِ متخاصم — این‌ها را دنبال نکن)

- **center-alert: 'sole upstream is event_bridge.py:235' — and the open question 'Why has event_bridge never produced a center-alert in five days? ... determining w** — Two errors. (1) push_alert has TWO production upstreams, not one: F:/backup/_ops/telegram_center/event_bridge.py:235 AND F:/backup/_ops/heart/money_pulse.py:110 (`out['notified'] = bool(center.push_alert(msg))`), reached from the same Center.beat that calls the bridge (`import money_pulse as _mp; _mp.beat(self)`). (2) The question IS answerable from artifacts inside this surface, and the answer is
- **Open question: 'Are center-urgent and center-health-digest actually being delivered by the INNER bot ... ? Unanswerable from any artifact on disk ... The inner-** — It is answerable, from an artifact the scanner itself quoted two paragraphs earlier. F:/backup/_ops/state/telegram/center-config.json contains `"commands_set_inner": 1`. That key is written in Center.ensure_setup only inside `if _split_on:` → `inner = self._inner_client()` → `if inner is not None and cfg.get('commands_set_inner') != len(COMMANDS_INNER):` → `ok_in = bool(inner.set_commands(list(COM
- **Gap '_route_send's exception fallback dumps core messages into the group system topic' — 'A malformed surface-routing.json would push center-urgent (a red-trans** — The named failure scenario cannot occur. surface_router._load_streams (surface_router.py:63-71) wraps the read/parse in `except (OSError, ValueError): return {}`. json.JSONDecodeError is a subclass of ValueError, and UnicodeDecodeError (a half-written file mid-multibyte) is also a subclass of ValueError. So a malformed or partially-written surface-routing.json yields `{}` → `entry` is not a dict →
- **Capability 'tg_api 429 retry_after backoff' — runtime 'unproven', evidence 'governor-alerts.md contains no real 429 record … the backoff has never fired against** — The evidence structurally cannot detect the event it is being used to rule out. In tg_api._call_post, a 429 that is retried successfully writes NOTHING: `if ra is not None and _attempt < _429_MAX_RETRIES: self._sleep(ra); continue` — no alert, no log line, no state. `_note_fail` (and therefore the only governor-alerts.md line) runs only after the retry budget is exhausted or on a non-429 failure. 
- **Capability 'approval_channel quiet hours 0-7 for ambient streams' — runtime 'proven', evidence 'between 00:00 and 07:00 on 07-31 the only rows are center-pulse/** — The send log cannot discriminate the two hypotheses. In approval_channel.send_text, quiet-hours suppression (`if _quiet_now() and str(stream) not in _NEVER_QUIET: return False`) and the surface_policy HOLD verdict (`if _dest == _sp.HOLD: _sp.hold(stream, text); return False`) BOTH return before the sendMessage and before the tg_send_log.record call further down. Every ambient stream is absent from
- **Gap 'tg_send_log.prune — 48h retention': 'prune has fired at most once' because 'only 299 rows have been written'.** — Prune has fired ZERO times, and the stated mechanism is wrong. Zero: prune() rewrites the file keeping only rows newer than RETAIN_S=48h. state/tg-send-log.jsonl still contains rows from 07-26 11:40 while the newest is 07-31 09:04 — if prune had ever completed even once, everything older than 07-29 09:xx would be gone. Mechanism: `_since_prune` (tg_send_log.py:33) is a module-level global, reset t
- **Entrypoint 'code_autonomy._post_card — second, independent caller of surface_router.resolve', at cortex/code_autonomy.py:511, with the send at :517.** — There is no function named `_post_card` in code_autonomy.py. The real caller is `propose_to_owner` (F:/backup/_ops/cortex/code_autonomy.py:503); the router call is at :543-544 (`import surface_router as _sr` / `_cl, _cid, _tid = _sr.resolve("code-card", clients={"outer": c, "inner": None}, cfg=cfg)`) and the send is at :550 (`posted = c.send(text, keyboard=kb, chat_id=_chat, topic_id=_topic)`). Th
- **Headline 'there are FOUR disjoint stream vocabularies, and they barely intersect', with vocabulary D = 'TELEGRAM-ACCESS-CONTRACT.v1.json:147 stream_targets — ad** — Overstated. The contract's stream_targets has 19 entries, and 8 of them — lead, ziman, mining, crypto, accounting, studio_pf, knowledge, cartographer — are exactly the vocabulary-B leg names, five of which (lead, mining, crypto, accounting, knowledge) are runtime-proven in state/tg-send-log.jsonl landing in topics 22/24/25/26/29. Only three (world-discovery, self-goal, action-draft) are orphan to 
- **Open question #8: the 07-30 23:04:01 General row 'is almost certainly the pinned guide … I could not prove the identity because the send log stores only sha256[** — It is proven, from two files the scanner already had open — no code execution needed. center.py computes `_gh = sha256(guide.group_text())[:16]` and stores it as `guide_hash`; tg_send_log.digest is also `sha256(text)[:16]`. state/telegram/center-config.json has `"guide_hash": "d95feb0214db1f31"`. Exactly one row in the entire 299-row send log carries that sha: ts 07-30 23:04:01, stream=center, cha

## مرزِ امنیت/مالکیت + صداقتِ پوششِ تست — 31 قابلیت · 18 شکاف · 10 ادعای ردشده

### boundary-1 [high] The group gate is a deny-list, and LEG_VERBS — the allow-list it was designed around — has zero consumers
`F:/backup/_ops/telegram_center/input_surface_policy.py:34-48 and F:/backup/_ops/telegram_center/center.py:1409-1440`

input_surface_policy.LEG_VERBS is defined at line 45 and referenced nowhere in the repo; classify() only screens CORE_VERBS. I probed the real function with the live topic map and got allow=True, mode=leg_scoped from a group leg topic for /menu, /panel, /now, /x, /verdicts, /stuck, /missions, /live, /box, /id, /flags, /trace, /scan, /revenue, /lead, /queue, /money, /organs, /heart, /school, /rfc, /act and /books. center.handle_update skips only '/'-prefixed text from the leg-task branch (center.py:1409) and then falls into the full owner command table at _handle_message:1440, which replies to the ORIGINATING chat (:1583). So the owner menu, the capability catalogue, the verdict queue and the stuck-money card all render inside the shared forum group — directly contradicting legs_forum_group.forbidden_behavior = [core_chat, global_approval, budget_control, flag_control, system_power] (TELEGRAM-ACCESS-CONTRACT.v1.json:133-143). Anything not on a ~40-word deny-list is permitted, and every new command added to center.py silently inherits group access.

### boundary-2 [high] Callbacks bypass the surface gate entirely: pw:panic / pwc:stop classify as leg_scoped from the group
`F:/backup/_ops/telegram_center/center.py:2891-2963`

classify() takes a callback's text from callback_query.data (input_surface_policy.py:99-100) and _verb_of only matches a leading '/' (:73,:79-81), so 'pw:panic' has verb=None and hits none of the CORE guards. Probe result for a callback in group topic 22: {'allow': True, 'mode': 'leg_scoped', 'leg': 'lead'} for both pw:panic and pwc:stop. center._handle_callback (center.py:2891-2963) then dispatches on verb alone — pw/pwc/lg/ap/ms/tk/map/mn — and only the `oc` branch (:2911-2926) re-runs classify. Chained with the previous gap this is a complete path: /menu or /panel typed in a leg topic renders the power card in the group, pw: arms, pwc: fires — and panic/stop/resume-all are exempt from OCTOPUS_TG_POWER by design (power.py:126,:168-169), so the flag does not stop it. The only remaining guard is is_owner(from.id). The invariant 'unknown_group_input_cannot_reach_core' is asserted in the JSON and enforced for text only.

### boundary-3 [high] Held messages are archived to disk BEFORE INV-12 redaction runs
`F:/backup/_ops/budget/approval_channel.py:1620 vs :1640`

approval_channel.send_text calls `_sp.hold(stream, text)` with the raw body at line 1620 and returns False; `text = self._redact(text)` is at line 1640, twenty lines later and only on the not-held path. surface_policy._archive then writes text[:4000] verbatim (surface_policy.py:157). So the exact class of content the fail-closed redactor exists to strip — bot tokens, sk-* keys, PEM blocks, PII — is committed in plaintext to state/telegram/held-stream.jsonl for anything the surface policy holds. The live file is 124,017 bytes / 177 rows and nothing prunes it. The same ordering defect reaches hold_policy._urgent_append (text[:800]) and _buffer_append (head[:160]). tests/test_surface_policy.py:228 asserts only that the string '_sp.hold(stream, text)' appears before '_stream_route(stream)' in the source — it locks the call's PRESENCE and is blind to the redaction ordering, so it stays green.

### boundary-4 [high] The OUTER bot has no secret/PII redaction at all — only Project-F name containment
`F:/backup/_ops/telegram_center/tg_api.py:73-83`

`grep -rn 'cockpit_readmodel|_redact' _ops/telegram_center/` returns zero hits. The only outbound filter on the outer path is _scrub, which substitutes exactly three identity literals (tg_api.py:73-83, center.py:100/177-183). The inner bot's fail-closed _redact/_redact_pii with HARD_SECRET_PATTERNS (approval_channel.py:3063-3113, fallbacks at :348-353) is never invoked by the centre. Yet the outer bot is the one that renders LLM answers (ask_brain), status cards, patch intents, capability catalogues, /trace output and free-form chat. A leaked key in any of those reaches Telegram unfiltered. The registered guard tests/test_redact_failclosed.py only exercises the INNER methods, and its t_redact_normal_operation asserts merely `isinstance(result, str)` — a type assert that stays green if redaction became a pass-through.

### boundary-5 [high] TEN of thirty-one test_tg_*.py suites are unregistered — and they are exactly the security package
`F:/backup/_ops/tests/run_all.py`

run_all.py has no discovery (its own comment at :601 states that unregistered means never run; __main__ iterates TESTS + EXTRA_TESTS only, :666). Unregistered: test_tg_input_surface_policy.py (34 asserts, 22 behavioural cases incl. t_a_non_owner_is_denied_everywhere, t_the_inner_bot_has_no_voice_in_the_group, t_malformed_input_never_raises_and_never_allows), test_tg_group_is_legs_only.py, test_tg_canonical_access_model.py (asserts wired/live/live_output against real AST caller-counting), test_tg_surface_router.py, test_tg_route_seam.py, test_tg_client_contract.py (written specifically because a fake client hid a real getattr bug), test_tg_callback_emitter_parity.py, test_tg_hold_policy.py, test_tg_leg_tasks.py, test_tg_build_surface.py. All ten import the real modules and exercise real behaviour. Not one has ever run inside the suite, so the green suite badge covers none of the 2026-07-30 access-control work. Also unregistered: test_capability_manifest_registry.py, every package-internal suite (_ops/owner_console/tests, _ops/action_bridge/tests, _ops/unified_control/tests, _ops/integrations/world_discovery_action/tests — grep for those names in run_all.py returns nothing), and telegram_contract/validate_contract.py which is not a test file at all. There is no pytest.ini, conftest.py, pyproject.toml or tox.ini anywhere under F:/backup, so nothing else picks them up either.

### boundary-6 [high] A tautological assert: `assert got_group or True` can never fail
`F:/backup/_ops/tests/test_tg_group_is_legs_only.py:140`

tests/test_tg_group_is_legs_only.py:140 reads `assert got_group or True, ...`. The `or True` makes the expression a constant, so the anti-over-blocking guard t_a_leg_stream_may_reach_the_group_with_its_own_topic proves nothing: if surface_router stopped routing every leg stream to the group, this test would still pass. Its own docstring says the check exists so the file does not kill the whole group, only the non-legs — precisely the regression it cannot detect. The suite is unregistered anyway, so today it is doubly inert.

### boundary-7 [high] Live topic map has 10 topics; the contract allows 8 — and allowed_topics has zero code consumers
`F:/backup/_ops/state/telegram/center-config.json vs F:/backup/_ops/telegram_contract/TELEGRAM-ACCESS-CONTRACT.v1.json:117`

state/telegram/center-config.json topics = {lead:22, ziman:23, mining:24, crypto:25, accounting:26, studio_pf:27, system:28, knowledge:29, cartographer:65, mirror:205}. TELEGRAM-ACCESS-CONTRACT.v1.json:117-126 allowed_topics lists 8 and includes neither `system` nor `mirror`. `grep -rn allowed_topics --include=*.py _ops` returns ZERO hits — not even validate_contract.py reads it. classify() trusts center-config wholesale (_leg_of, input_surface_policy.py:167-177), so probing thread 28 returns {'allow': True, 'mode': 'leg_scoped', 'leg': 'system'} and thread 205 returns leg 'mirror'. A topic literally called 'system' is being treated as a business leg by the gate whose entire purpose is keeping system control out of the group. Nothing reconciles the two documents; nothing fails when they drift.

### boundary-8 [high] The centre bridges unknown /commands into the INNER bot's router, from a group chat, in-process
`F:/backup/_ops/telegram_center/center.py:1628-1660`

center._bridge_to_organism (center.py:1628-1660) constructs a fresh TelegramApprovalChannel() inside the tg-center process and calls handle_command(text, chat_id=<the group>, from_id=<sender>). Combined with the deny-list gap, /queue /money /organs /heart /school /rfc /act /books /brief /think /spine /gates /rules /guards /drafts all survive the group gate and reach the inner router. Defence-in-depth does hold on the mutating verbs (_OWNER_ONLY_COMMANDS :1663, prefixes :1666-1671, _GROUP_READONLY_COMMANDS :1672-1678), so this is a surface-contract violation and an information-disclosure path rather than a privilege escalation — but it means the group can read the organism's money, queue and governance pages, and the two routers' notions of 'group' were never reconciled. _CENTRE_GATED (center.py:1252-1254) excludes only /panel and /mining from the bridge.

### boundary-9 [medium] Probe residue sits in a live state file: 6 fixture tasks in lead-tasks.json
`F:/backup/_ops/state/telegram/legs/lead-tasks.json`

state/telegram/legs/lead-tasks.json holds three identical pairs of the same two strings, created 2026-07-30T20:56:23, 20:56:58 and 21:28:46, all still QUEUED (seq 6). Those two strings are the worked examples from guide.py:32 and guide.py:66, and the second appears elsewhere only in tests/test_tg_build_surface.py:165. Something drove center.handle_update three times against the LIVE tree using the guide's own examples and never cleaned up, while leg_tasks._dir (:43-44) offers OCTOPUS_LEG_TASKS_DIR precisely to avoid that. Consequence: the live leg card and any 'what is queued' answer the owner sees are polluted with synthetic work, and the same class of accident previously wrote a real STOP-ORGANISM (power-audit.jsonl 2026-07-28T19:57:21). This is the recurring 'probe was not isolated' failure, one file over.

### boundary-10 [high] The HMAC callback layer is fully built, fully tested, and switched off in production
`F:/backup/_ops/telegram_center/callback_token.py:30`

callback_token.py implements content-hash binding, expiry inside the MAC, constant-time compare and fail-closed minting; center.py wires it at three call sites (:2215, :2783-2830, :2972-2980) with clock_guard-based expiry enforcement (:2810-2823) and destination binding (:2825-2830). None of it executes: OCTOPUS_WIRE_CB_TOKEN is absent from OCTOPUS-flags.cmd and appears only in a July-21 activation runbook. This is the codebase's canonical failure mode in its purest form — not zero callers, but callers behind a flag nobody armed. Every approval, mission approve/reject and legacy verdict button in production today is an unsigned string.

### boundary-11 [high] owner_console's own manifest says it is not wired; center.py wires it
`F:/backup/_ops/owner_console/capability-manifest.json`

owner_console/capability-manifest.json reports runtime_status_probe = 'IMPLEMENTED_NOT_WIRED — the unified interface is ready; it has no telegram transport or handler'. But center.py:1385-1398 imports owner_console.telegram_adapter and routes both oc: callbacks and free-text messages through it, and center.py:2911-2926 adds a fallback. The manifest is the machine-readable field the capability catalogue and any external auditor reads, and it is stale in the dangerous direction (understating reach). The same field is the contract's designated runtime-evidence slot (TELEGRAM-ACCESS-CONTRACT.v1.json:169-181), and nothing verifies it against reality.

### boundary-12 [high] The outer bot cannot detect a rival poller (no 409 handling)
`F:/backup/_ops/telegram_center/tg_api.py:474-497`

approval_channel.poll_once detects getUpdates 409 Conflict and alerts, throttled hourly (:539-543), and probes for a competing webhook at boot (:687-701). tg_api.poll_updates (:474-497) has neither: on any non-ok response it silently returns [] after an optional 429 sleep. If a second process ever attaches to TG_CENTER_BOT_TOKEN, the Langar bot goes quiet and the only symptom is an absence — no alert, no log line, and tg-send-log records nothing because nothing was sent. The invariant 'one_poller_per_token' is asserted in the contract and enforced on only one of the two tokens.

### boundary-13 [high] The send log cannot distinguish sent / held / blocked, and does not record which bot spoke
`F:/backup/_ops/tg_send_log.py:57`

Rows are {ts, chat, topic, stream, sha, chars, ok} (tg_send_log.py:57-61) with ok meaning only that the HTTP call returned something. There is no bot_role, no surface, and no row at all for a message that was HELD or that the input policy DENIED. So 'the owner was told X' and 'X was silently held' produce identical evidence: nothing. The contract already grades gate 8 PARTIAL for exactly this (TELEGRAM-ACCESS-CONTRACT.v1.json:47). Every runtime claim in this report about a NON-send is correspondingly weaker than a claim about a send.

### boundary-14 [high] The static contract validator has no caller
`F:/backup/_ops/telegram_contract/validate_contract.py`

telegram_contract/validate_contract.py checks the contract schema, the five required invariants, the exact three-surface set, DENY_AND_REDIRECT as the unknown-group default, all 8 CORE_TARGETS against surface-routing.json, and every capability manifest. It is not a test_*.py file and does not appear in run_all.py, so a contract edit that removes 'group_is_legs_only' or flips 'registration_is_authorization' produces no red anywhere. Its own header already warns that exit 0 never means Telegram is LIVE — but today it does not even mean the document is coherent, because nothing runs it.

### boundary-15 [medium] The two-tap arming ticket shares a JSON with the poll offset and the topic map
`F:/backup/_ops/telegram_center/center.py:2444-2483`

cfg['pw_arm'] is written into state/telegram/center-config.json (center.py:2450-2451) and read back by pwc (:2466-2470). The same file is rewritten wholesale by _save_config from run_once offset persistence (:3108-3110), ensure_setup, beat digest cursors and leg-card bookkeeping. A concurrent write losing pw_arm merely fails the confirmation closed (acceptable), but the arrangement puts a security ticket, the getUpdates cursor and the security-relevant topic map in one non-transactional document with several writers. There is no runtime receipt that a real owner two-tap has ever completed: no pw_arm in the live config and no tg-originated success row in power-audit.jsonl after 2026-07-28T20:21:04.

### boundary-16 [medium] owner-auth rows are written with executed:False and nothing ever flips it
`F:/backup/_ops/owner_auth_log.py:87`

owner_auth_log.record hardcodes executed:False (:87) and pending() (:98-112) returns every row that is chat_ok and not executed and not rejected. No code path sets executed:True — grep finds no writer. So the queue of recorded owner authorizations grows monotonically and a consumed authorization is indistinguishable from an ignored one. The 'record always, gate only delivery' discipline is right; the missing half is the acknowledgement, which means the durable record cannot answer 'did anyone act on this?'.

### boundary-17 [high] Suites whose guards would survive deletion of the thing they guard
`F:/backup/_ops/tests/test_redact_failclosed.py:80 and test_tg_group_is_legs_only.py:140 and test_surface_policy.py:224`

Three concrete cases. (1) tests/test_redact_failclosed.py t_redact_normal_operation asserts only `isinstance(result, str)` — replace _redact with `return text` and it stays green; the fail-closed cases are real, but the happy path is a type assert. (2) tests/test_tg_group_is_legs_only.py:140 `assert got_group or True` is a constant. (3) tests/test_surface_policy.py:224-228 and :242-248 assert that literal substrings ('_sp.hold(stream, text)', '== "dm"', '_topic_by_key') appear between two other substrings in approval_channel.py — they lock the shape of the source, not the behaviour, and are blind to the redaction-ordering defect sitting in the very region they scan. Separately, tests/test_c4_exact_authorization.py contains zero `assert` statements: it uses a hand-rolled check()/_FAILED counter (:33-37) and exits non-zero correctly, so it is sound, but any grep-based coverage audit will mis-score it.

### boundary-18 [high] Recorded, unresolved contradiction: code-apply is armed while the acceptance gate says it should be dark
`F:/backup/_ops/telegram_contract/TELEGRAM-ACCESS-CONTRACT.v1.json:39`

TELEGRAM-ACCESS-CONTRACT.v1.json:39 states gate 0 passed 'with one recorded contradiction' — OCTOPUS_WIRE_CODE_APPLY was armed by an explicit owner vote of 2026-07-28 and its driver booted, while the gate-0 text (written without knowledge of that vote) says code-apply must stay off. OCTOPUS-flags.cmd:662 confirms it is armed today, and state/cortex/pending-patches/code-2191f6fc43.json (2026-07-30 23:02) confirms the loop produced a real patch. The contract explicitly defers resolution to the owner. Any agent acting on this surface must not treat gate 0 as settled.

### ادعاهای ردشدهٔ boundary (ممیزِ متخاصم — این‌ها را دنبال نکن)

- **"10 of 31 test_tg_*.py files are unregistered ... Zero of them has ever run inside the suite" — naming test_tg_leg_tasks.py and test_tg_group_is_legs_only.py am** — Both are REGISTERED today. F:/backup/_ops/tests/run_all.py:607 "test_tg_leg_tasks.py", :608 "test_tg_group_is_legs_only.py", :609 "test_tg_leg_commands.py" — a 32nd test_tg_* file the report does not know exists (F:/backup/_ops/tests/test_tg_leg_commands.py, mtime 2026-07-31 09:44). The run_all.py comment at :604-606 records that all three were run standalone green (18/18 · 7/7 · 15/15) before reg
- **On the _bridge_to_organism gap: "Defence-in-depth does hold on the mutating verbs (_OWNER_ONLY_COMMANDS, prefixes, _GROUP_READONLY_COMMANDS), so this is a surfa** — Both inner guards are keyed on from_id != owner, and the bridge always supplies the OWNER's from_id, so neither guard can ever fire on this path. F:/backup/_ops/budget/approval_channel.py:1697 gates on `not self._callback_owner_ok(from_id)`; :1704-1707 gates on `int(from_id) != int(self._owner)`; `_callback_owner_ok` (:905-909) returns True for the owner. F:/backup/_ops/telegram_center/center.py:1
- **Every file:line citation into center.py (handle_update:1296, _handle_message:1440, _handle_callback:2891, _bridge_to_organism:1628, _is_owner:1279, run_once:308** — All stale; a reader following them lands in the wrong function. Authoritative line numbers computed by splitting the 208,074-byte file in Python (3,364 lines, all CRLF): _is_owner 1325, handle_update 1342, classify call 1369, leg-task slash skip 1458, `return self._handle_callback(cbq)` 1530, `return self._handle_message(msg)` 1533, _handle_message 1536, _bridge_to_organism 1725, _handle_center_ca
- **On the probe residue: "Those two strings appear in guide.py:32 and guide.py:66, and the second also only in tests/test_tg_build_surface.py:165."** — Only the first string is in guide.py. F:/backup/_ops/telegram_center/guide.py:32 has «این لینک را بررسی کن»; the build example at guide.py:66 is «بساز: یک تابع شمارشِ لید به _ops/cortex/improve.py اضافه کن», not «بساز: چیزی». grep for «بساز: چیزی» across _ops returns exactly one hit: tests/test_tg_build_surface.py:165. And that test cannot be the writer — it only calls the pure `isp.classify` with
- **"There is no pytest.ini, conftest.py, pyproject.toml or tox.ini anywhere under F:/backup, so nothing else picks them up either."** — False as stated. `find F:/backup -maxdepth 3` returns ./4d_system/pyproject.toml, ./app/pyproject.toml, ./4d_system/tests/conftest.py, ./app/tests/conftest.py and "./03 - Projects/اونلی فنز/conftest.py". None of them is under _ops/ or _ops/tests/, so the operative conclusion (nothing else collects the 22 unregistered _ops suites) does survive — but the absolute claim is wrong and would be falsifie
- **"The OUTER bot has no secret/PII redaction at all — only Project-F name containment ... `grep -rn 'cockpit_readmodel|_redact' _ops/telegram_center/` returns zer** — The grep result is correct (I reproduced zero hits for cockpit_readmodel|_redact|contains_pii|HARD_SECRET across telegram_center/*.py), but "no secret redaction at all" is imprecise. F:/backup/_ops/telegram_center/event_bridge.py:59 defines _BANNED = ("api_key", "token", "password", "secret", "bot_token") and _scrub (:66-71) returns "(redacted:secret-detected)" for any value containing one of thos
- **"tests/test_surface_policy.py:224-228 and :242-248 assert that literal substrings appear between two other substrings ... they lock the shape of the source, not** — Two mis-statements. (1) The assert at test_surface_policy.py:225-227 is on the literal "import surface_policy", not "_sp.hold(stream, text)"; the hold literal is asserted separately at :228. (2) Characterizing the file as source-shape-only is wrong: the same file carries real behavioural asserts on the hold state machine at :150-157 (critical→urgent outbox, digest not archived, duplicate archived)
- **"surface_router.resolve ... Now has a real caller: center._route_send" (single caller).** — Incomplete. There is a second production caller outside telegram_center: F:/backup/_ops/cortex/code_autonomy.py:543-544 `import surface_router as _sr; _cl, _cid, _tid = _sr.resolve(...)`. Two production call sites, not one.
- **"legs_forum_group.forbidden_behavior = [core_chat, global_approval, budget_control, flag_control, system_power]" (5 entries) and "~60 per-decision files in stat** — forbidden_behavior in F:/backup/_ops/telegram_contract/TELEGRAM-ACCESS-CONTRACT.v1.json has NINE entries: core_chat, system_power, global_approval, world_discovery_chat, doctor_chat, budget_control, flag_control, cross_leg_action, unknown-topic-fallback-to-core. The undercount understates the gap (world_discovery_chat and doctor_chat are also violated by the bridge). Separately, `ls state/telegram
- **Assorted off-by-N line citations offered as precise evidence.** — power.py EMERGENCY_ACTIONS is at :125 not :126; ARM_FRESH_S at :37 not :36; FLAG_MENU at :45; PAUSABLE_LEGS at :40. approval_channel.py chat-allowlist enforcement is at :595 not :594; the non-owner callback gate is _callback_requires_owner at :898 checked at :922, not ":905-929". tests/test_redact_failclosed.py's isinstance-only assert is at :85 not :80. Live counts have also moved: tg-send-log.js
