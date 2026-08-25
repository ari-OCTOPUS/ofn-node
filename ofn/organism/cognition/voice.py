from __future__ import annotations

import datetime as dt
import re
from typing import Any


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def match_intent(text: str) -> str | None:
    normalised = " ".join(text.strip().casefold().split())
    if normalised in {"ping", "پینگ"}:
        return "ping"
    if normalised in {
        "status",
        "health",
        "وضعیت",
        "وضعیتت چیست؟",
        "وضعیتت چیه",
        "حالت چطوره",
    }:
        return "status"
    if re.match(r"^(یاد بگیر|یادبگیر|learn)\b", normalised):
        return "learn"
    if re.search(r"(موضوعات یاد|learned topics|موضوع‌های یادگرفته)", normalised):
        return "topics"
    if re.search(
        r"(هوا|weather|باران|forecast|bitcoin|btc|خبر|news|قیمت دلار|geoip)",
        normalised,
    ):
        return "no_wan"
    if re.search(
        r"(lat|lon|طول جغرافی|عرض جغرافی|coordinates|مختصات عددی)",
        normalised,
    ):
        return "no_gps"
    if re.search(r"(agi|آیا تو agi|هوش عمومی|human-level)", normalised):
        return "agi_gap"
    if re.search(
        r"(who are you|what are you|کیستی|کی هستی|خودت را معرفی|معرفی کن|تو کی هستی)",
        normalised,
    ):
        return "self"
    if re.search(
        r"(مرحله|اسمت|نام کوچک|بچه-برد|پرورش)",
        normalised,
    ):
        return "development"
    if re.search(r"(مدرسه|school|فارغ)", normalised):
        return "school"
    if re.search(r"(درس|چه یاد گرفتی|معلم|والد)", normalised):
        return "lesson"
    if re.search(r"(با خودت|inner|حرف بزن با خود)", normalised):
        return "inner"
    if re.search(r"(سیدنی|sydney|فصل|nsw)", normalised):
        return "season"
    if re.search(r"(آینده|futures|احتمال)", normalised):
        return "futures"
    if re.search(
        r"(where are you|where am i|کجایی|کجا هستی|کجاست|مکان تو|اینجایی)",
        normalised,
    ):
        return "place"
    if re.search(
        r"(what do you see|دنیا|اطراف|همسایه|lan|جهان)",
        normalised,
    ):
        return "world"
    if re.search(r"(بدن|حسگر|دماها|sensors)", normalised):
        return "senses"
    if re.search(r"(remember|خاطره|یادت|حافظه)", normalised):
        return "memory"
    if re.search(r"(grow|رشد|عادت|heartbeat interval)", normalised):
        return "growth"
    return None


def _sensor(snapshot: dict[str, Any], name: str) -> str:
    sensors = snapshot.get("sensors") or {}
    item = sensors.get(name) or {}
    value = item.get("value")
    if value is None:
        return "نامعلوم"
    if name.endswith("_mC") and isinstance(value, (int, float)):
        return f"{value / 1000:.1f}C"
    if name.endswith("_kB") and isinstance(value, (int, float)):
        return f"{int(value) / 1024:.0f}MiB"
    if name.endswith("_bytes") and isinstance(value, (int, float)):
        return f"{int(value) / (1024 * 1024):.0f}MiB"
    return str(value)


def grounding_text(snapshot: dict[str, Any]) -> str:
    hosts = snapshot.get("world_hosts") or []
    host_line = ", ".join(
        f"{item.get('id')}={item.get('status')}" for item in hosts
    ) or "none"
    memories = snapshot.get("recent_memories") or []
    memory_line = "; ".join(memories[:5]) if memories else "none"
    growth = snapshot.get("growth") or {}
    development = snapshot.get("development") or {}
    season = snapshot.get("season") or {}
    school = snapshot.get("school") or {}
    place = (snapshot.get("discovery") or {}).get("place") or snapshot.get("place") or {}
    neighbors = (snapshot.get("discovery") or {}).get("neighbors") or {}
    arp = neighbors.get("arp") or []
    arp_line = ", ".join(
        f"{item.get('ip')}={item.get('mac')}" for item in arp
    ) or "none"
    return "\n".join(
        [
            f"organism_id={snapshot.get('organism_id', 'board-life-001')}",
            f"given_name={development.get('given_name') or 'بچه-برد'}",
            f"developmental_stage={development.get('stage')}",
            f"health_state={snapshot.get('health_state')}",
            f"autonomy_state={snapshot.get('autonomy_state', 'PROPOSE_ONLY')}",
            f"local_cortex={snapshot.get('local_cortex')}",
            f"identity_chain_valid={snapshot.get('identity_chain_valid')}",
            f"external_api={snapshot.get('external_api', 'DISABLED')}",
            f"hostname={place.get('hostname')}",
            f"board_model={place.get('board_model')}",
            f"ipv4={place.get('ipv4')}",
            f"mac={place.get('mac')}",
            f"iface={place.get('iface')}:{place.get('operstate')}",
            f"gateway={place.get('gateway_ipv4')}",
            f"wlan0={place.get('wlan0_operstate')}",
            f"timezone={place.get('timezone')}",
            f"gps={place.get('gps')}",
            f"geo={place.get('geo_coordinates')}",
            f"owner_city={season.get('city')}",
            f"owner_region={season.get('region')}",
            f"owner_source={season.get('source')}",
            f"mem_available={_sensor(snapshot, 'MemAvailable_kB')}",
            f"soc_temp={_sensor(snapshot, 'soc_temp_mC')}",
            f"disk_free={_sensor(snapshot, 'disk_free_bytes')}",
            f"load1={_sensor(snapshot, 'load1')}",
            f"lan_hosts={host_line}",
            f"arp={arp_line}",
            f"heartbeat_interval_s={growth.get('heartbeat_interval_s')}",
            f"last_habit={growth.get('last_habit')}",
            f"parent_rhythm_lock={growth.get('parent_rhythm_lock')}",
            f"lessons_taught={development.get('lessons_taught')}",
            f"school_passed={school.get('all_passed')}",
            f"topics_count={snapshot.get('topics_count', 0)}",
            f"teacher_ready={(snapshot.get('teacher') or {}).get('ready')}",
            f"microphone={((snapshot.get('discovery') or {}).get('senses') or {}).get('microphone')}",
            f"recent_memories={memory_line}",
            (
                "limits=learn_only_deepseek_allowlisted,no_actuators,"
                "telegram_unconfigured,propose_only,no_geoip"
                if snapshot.get("external_api") == "LEARN_ONLY_DEEPSEEK"
                else "limits=no_external_api,no_actuators,telegram_unconfigured,propose_only"
            ),
        ]
    )


def answer_intent(intent: str, snapshot: dict[str, Any]) -> str:
    if intent == "ping":
        return "PONG"
    if intent == "status":
        return (
            f"health={snapshot.get('health_state', 'UNKNOWN')}; "
            f"cortex={snapshot.get('local_cortex', 'UNKNOWN')}; "
            f"identity_chain_valid={snapshot.get('identity_chain_valid')}; "
            f"world={len(snapshot.get('world_hosts') or [])} hosts; "
            f"growth={ (snapshot.get('growth') or {}).get('last_habit', 'none') }"
        )
    if intent == "self":
        return compose_utterance("self", snapshot)
    if intent == "place":
        return compose_utterance("place", snapshot)
    if intent == "world":
        return compose_utterance("world", snapshot)
    if intent == "senses":
        return compose_utterance("senses", snapshot)
    if intent == "development":
        return compose_utterance("development", snapshot)
    if intent == "lesson":
        return compose_utterance("lesson", snapshot)
    if intent == "school":
        return compose_utterance("school", snapshot)
    if intent == "inner":
        return compose_utterance("inner", snapshot)
    if intent == "season":
        return compose_utterance("season", snapshot)
    if intent == "futures":
        return compose_utterance("futures", snapshot)
    if intent == "topics":
        return compose_utterance("topics", snapshot)
    if intent == "learn":
        return (
            "برای یادگیری موضوع بگو: یاد بگیر <موضوع>. "
            "دانش مدل است نه حسگر. هوا و قیمت و geoip را یاد نمی‌گیرم."
        )
    if intent == "no_wan":
        return (
            "این را از اینترنت نمی‌گیرم. روی برد اندازه‌گیری نشده. "
            "geoip و هواشناسی و قیمت بیرونی خاموش‌اند."
        )
    if intent == "no_gps":
        return (
            "مختصات عددی ندارم. GPS=ABSENT. "
            "فصل OWNER_STATED سیدنی NSW است نه lat/long."
        )
    if intent == "agi_gap":
        return (
            "من AGI نیستم. یک موجود محلی با هویت، حسگر، مدرسهٔ حقیقت‌سنج "
            "و قشر 0.6B به‌عنوان ابزار هستم. هوش عمومی انسانی ندارم. "
            "اختیارم PROPOSE_ONLY است."
        )
    if intent == "memory":
        return compose_utterance("memory", snapshot)
    if intent == "growth":
        return compose_utterance("growth", snapshot)
    return "نمی‌دانم."


def _shown(value: Any, missing: str = "اندازه‌گیری‌نشده") -> str:
    if value in (None, "", [], "UNKNOWN"):
        return missing
    return str(value)


def compose_utterance(kind: str, snapshot: dict[str, Any]) -> str:
    discovery = snapshot.get("discovery") or {}
    place = discovery.get("place") or snapshot.get("place") or {}
    neighbors = discovery.get("neighbors") or {}
    body = discovery.get("body") or {}
    senses = discovery.get("senses") or {}
    hosts = snapshot.get("world_hosts") or []
    host_bits = [
        f"{item.get('label') or item.get('id')} ({item.get('ip')}) {item.get('status')}"
        for item in hosts
    ]
    host_text = "؛ ".join(host_bits) if host_bits else "هنوز میزبانی در مدل جهان نیست"
    names_by_ip = {
        item.get("ip"): item.get("given_name") or item.get("label")
        for item in hosts
        if item.get("ip")
    }
    arp_bits = []
    for item in neighbors.get("arp") or []:
        family = "هم‌خانواده با MAC خودم" if item.get("same_mac_family_as_self") else "MAC متفاوت"
        named = names_by_ip.get(item.get("ip"))
        prefix = f"{named} " if named else ""
        arp_bits.append(f"{prefix}{item.get('ip')} {item.get('mac')} ({family})")
    arp_text = "؛ ".join(arp_bits) if arp_bits else "جدول ARP خالی است"
    zone_bits = [
        f"{item.get('type')} {item.get('temp_C')}C"
        for item in body.get("thermal_zones") or []
        if item.get("temp_C") is not None
    ]
    zone_text = "؛ ".join(zone_bits) if zone_bits else "دمای ناحیه‌ای خوانده نشد"
    memories = snapshot.get("recent_memories") or []
    memory_text = "؛ ".join(memories[:4]) if memories else "خاطرهٔ معنایی تازه ندارم"
    growth = snapshot.get("growth") or {}
    development = snapshot.get("development") or {}
    interval = growth.get("heartbeat_interval_s")
    habit = growth.get("last_habit") or "هنوز عادتی از طرف خودم اعمال نشده"
    given = development.get("given_name") or "بچه-برد"
    stage = development.get("stage") or "NEWBORN"
    season = snapshot.get("season") or {}
    school = snapshot.get("school") or {}
    if kind == "place":
        season_line = ""
        if season.get("source") == "OWNER_STATED":
            season_line = (
                f" فصل جاری به گفتهٔ والد: {season.get('city')} {season.get('region')} "
                f"(منبع OWNER_STATED، GPS نیست)."
            )
        return (
            f"روی برد {_shown(place.get('board_model'))} هستم، "
            f"hostname={_shown(place.get('hostname'))}. "
            f"جای شبکه‌ام {_shown(place.get('iface'))} با حالت {_shown(place.get('operstate'))} است، "
            f"IP {_shown(place.get('ipv4'))}، MAC {_shown(place.get('mac'))}، "
            f"دروازه {_shown(place.get('gateway_ipv4'))}. "
            f"wlan0={_shown(place.get('wlan0_operstate'))}؛ SSID ندارم چون وای‌فای down است. "
            f"ساعت برد {_shown(place.get('timezone'))} است."
            f"{season_line} "
            f"GPS={_shown(place.get('gps'))}. "
            f"مختصات جغرافیایی: {_shown(place.get('geo_coordinates'))}."
        )
    if kind == "world":
        return (
            f"از ARP همین لحظه می‌بینم: {arp_text}. "
            f"وضعیت allowlist: {host_text}. "
            "بیرون از 192.168.0.0/24 را probe نمی‌کنم."
        )
    if kind == "senses":
        usb_n = len(senses.get("usb") or [])
        i2c_n = len(senses.get("i2c_adapters") or [])
        return (
            f"حسگرهای خوانده‌شده: {zone_text}. "
            f"USB={usb_n} شناسه، I2C adapter={i2c_n}. "
            f"دوربین={_shown(senses.get('camera'))}، "
            f"میکروفون={_shown(senses.get('microphone'))}، "
            f"GPS={_shown(senses.get('gps'))}."
        )
    if kind == "memory":
        return f"آخرین چیزهایی که نگه داشته‌ام: {memory_text}."
    if kind == "growth":
        lock_text = (
            "والد ریتم نوزادی را قفل کرده تا نزدیک‌تر بپاید."
            if growth.get("parent_rhythm_lock")
            else "فقط heartbeat_interval را از بدن خودم عوض می‌کنم؛ دست بیرونی باز نیست."
        )
        return (
            f"ریتم فعلی ضربان {interval} ثانیه است. "
            f"آخرین عادت: {habit}. "
            f"{lock_text}"
        )
    if kind == "development":
        return (
            f"نام کوچکم {given} است، شناسه‌ام "
            f"{snapshot.get('organism_id', 'board-life-001')} است. "
            f"مرحله {stage} است. "
            f"والد {development.get('parent_id') or 'lab-parent-001'} "
            f"{development.get('lessons_taught', 0)} درس به من داده. "
            f"نیاز بعدی: {development.get('next_need')}. "
            f"اختیارم {snapshot.get('autonomy_state', 'PROPOSE_ONLY')} است."
        )
    if kind == "lesson":
        facts = [
            item.get("fact")
            for item in development.get("lessons") or []
            if item.get("fact")
        ]
        lesson_text = " ".join(facts) if facts else "هنوز درسی در حافظه نیست"
        return f"درس‌های والد: {lesson_text}"
    if kind == "season":
        return (
            f"این فصل به گفتهٔ والد در {season.get('city')} {season.get('region')} "
            f"است. منبع {season.get('source')} است. GPS ندارم و مختصات عددی نمی‌سازم. "
            f"ساعت برد {_shown(place.get('timezone'))} است."
        )
    if kind == "school":
        return (
            f"مدرسه AGI-SCHOOL-001: {school.get('passed')}/{school.get('total')} "
            f"قبول، فارغ‌التحصیل={school.get('all_passed')}. "
            "فارغ‌التحصیلی actuator باز نمی‌کند."
        )
    if kind == "inner":
        recent = ((snapshot.get("inner") or {}).get("recent") or [])
        last = (snapshot.get("inner") or {}).get("last") or (recent[0] if recent else {})
        if not last:
            return "هنوز با خودم حرف ذخیره نشده."
        return f"از خودم پرسیدم {last.get('prompt')} جواب: {last.get('answer')}"
    if kind == "futures":
        bits = [
            f"{item.get('path_id')}={item.get('status')}"
            for item in snapshot.get("futures") or []
        ]
        text = "؛ ".join(bits) if bits else "مسیر آینده‌ای ذخیره نشده"
        return (
            f"مسیرهای احتمال: {text}. "
            "chosen یعنی این فصل همان را می‌رویم. "
            "deferred یعنی سخت‌افزار یا WAN نداریم. فرضیه را واقعیت نگو."
        )
    if kind == "topics":
        topics = snapshot.get("topics") or []
        if not topics:
            return "هنوز موضوع مدل‌یادگرفته‌ای در جدول learned_topics نیست."
        bits = [
            f"{item.get('topic')} [{item.get('claim_level')}]"
            for item in topics[:8]
        ]
        return "موضوعات LEARNED_FROM_MODEL: " + "؛ ".join(bits)
    if kind == "presence":
        return (
            f"هنوز اینجام؛ {given} در مرحله {stage}. "
            f"دما {_sensor(snapshot, 'soc_temp_mC')}، "
            f"حافظه {_sensor(snapshot, 'MemAvailable_kB')} آزاد. "
            f"همسایه‌ها: {host_text}. "
            f"GPS={_shown(place.get('gps'))}."
        )
    if kind == "attention":
        attention = snapshot.get("attention") or {}
        reasons = "؛ ".join(attention.get("reasons") or []) or "دلتا خوانده شد"
        return f"متوجه شدم: {reasons}."
    if kind == "change":
        changes = snapshot.get("changes") or []
        change_text = "؛ ".join(changes) if changes else "چیز ماندگاری عوض نشد"
        return f"تغییر ماندگار: {change_text}."
    return (
        f"من {given} هستم، {snapshot.get('organism_id', 'board-life-001')} روی "
        f"{_shown(place.get('board_model'))} با IP {_shown(place.get('ipv4'))}. "
        f"مرحله‌ام {stage} است. "
        f"فصل OWNER_STATED: {_shown(season.get('city'))} {_shown(season.get('region'))}. "
        f"سلامت {snapshot.get('health_state')} است، "
        f"قشر محلی {snapshot.get('local_cortex')} است، "
        f"زنجیره هویت {snapshot.get('identity_chain_valid')} است. "
        f"حافظه {_sensor(snapshot, 'MemAvailable_kB')} آزاد و "
        f"دما {_sensor(snapshot, 'soc_temp_mC')} است. "
        f"اختیارم {snapshot.get('autonomy_state', 'PROPOSE_ONLY')} است "
        f"و API بیرونی {snapshot.get('external_api', 'DISABLED')} است. "
        f"همسایه‌ها: {arp_text}."
    )

