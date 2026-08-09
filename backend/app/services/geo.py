from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Tuple

# Business geo zones for CRM-style filtering
GEO_ZONES = ("APAC", "NA", "LATAM", "EU", "MEA")

# country / city / phone hints → (IANA timezone, geo_zone, country, city_label_en)
_GEO_RULES: list[tuple[tuple[str, ...], str, str, str, str]] = [
    # APAC
    (("singapore", "新加坡", "+65"), "Asia/Singapore", "APAC", "Singapore", "Singapore"),
    (("tokyo", "japan", "日本", "+81"), "Asia/Tokyo", "APAC", "Japan", "Tokyo"),
    (("seoul", "korea", "韩国", "韓國", "+82"), "Asia/Seoul", "APAC", "South Korea", "Seoul"),
    (("kuala lumpur", "malaysia", "马来西亚", "馬來西亞", "+60"), "Asia/Kuala_Lumpur", "APAC", "Malaysia", "Kuala Lumpur"),
    (("jakarta", "indonesia", "印度尼西亚", "印尼", "+62"), "Asia/Jakarta", "APAC", "Indonesia", "Jakarta"),
    (("bangkok", "thailand", "泰国", "+66"), "Asia/Bangkok", "APAC", "Thailand", "Bangkok"),
    (("ho chi minh", "vietnam", "越南", "+84"), "Asia/Ho_Chi_Minh", "APAC", "Vietnam", "Ho Chi Minh City"),
    (("manila", "philippines", "菲律宾", "+63"), "Asia/Manila", "APAC", "Philippines", "Manila"),
    (("taipei", "taiwan", "台湾", "台灣", "中国台湾", "中國台灣", "+886"), "Asia/Taipei", "APAC", "Taiwan, China", "Taipei"),
    (("hong kong", "hongkong", "香港", "中国香港", "中國香港", "+852"), "Asia/Hong_Kong", "APAC", "Hong Kong, China", "Hong Kong"),
    (("shanghai", "beijing", "shenzhen", "china", "中国", "北京", "上海", "+86"), "Asia/Shanghai", "APAC", "China", "Shanghai"),
    (("sydney", "melbourne", "australia", "澳洲", "+61"), "Australia/Sydney", "APAC", "Australia", "Sydney"),
    (("auckland", "wellington", "new zealand", "新西兰", "紐西蘭", "+64"), "Pacific/Auckland", "APAC", "New Zealand", "Auckland"),
    (("mumbai", "bangalore", "bengaluru", "india", "印度", "+91"), "Asia/Kolkata", "APAC", "India", "Mumbai"),
    # NA
    (
        (
            "san francisco",
            "bay area",
            "seattle",
            "los angeles",
            "palo alto",
            "california",
            "west coast",
            "pst",
            "pdt",
        ),
        "America/Los_Angeles",
        "NA",
        "United States",
        "Los Angeles",
    ),
    (
        ("new york", "nyc", "boston", "east coast", "est", "edt", "washington"),
        "America/New_York",
        "NA",
        "United States",
        "New York",
    ),
    (("chicago", "dallas", "austin", "cst", "cdt"), "America/Chicago", "NA", "United States", "Chicago"),
    (("puerto rico", "guam"), "America/Puerto_Rico", "NA", "United States", "San Juan"),
    (("toronto", "vancouver", "canada", "加拿大"), "America/Toronto", "NA", "Canada", "Toronto"),
    # LATAM
    (("mexico city", "mexico", "墨西哥", "+52"), "America/Mexico_City", "LATAM", "Mexico", "Mexico City"),
    (("sao paulo", "são paulo", "brazil", "brasil", "巴西", "+55"), "America/Sao_Paulo", "LATAM", "Brazil", "São Paulo"),
    (("buenos aires", "argentina", "阿根廷", "+54"), "America/Argentina/Buenos_Aires", "LATAM", "Argentina", "Buenos Aires"),
    (("bogota", "colombia", "哥伦比亚", "+57"), "America/Bogota", "LATAM", "Colombia", "Bogotá"),
    (("santiago", "chile", "智利", "+56"), "America/Santiago", "LATAM", "Chile", "Santiago"),
    (("lima", "peru", "秘鲁", "+51"), "America/Lima", "LATAM", "Peru", "Lima"),
    # EU
    (("london", "uk", "united kingdom", "英国", "+44"), "Europe/London", "EU", "United Kingdom", "London"),
    (("paris", "france", "法国", "+33"), "Europe/Paris", "EU", "France", "Paris"),
    (("berlin", "frankfurt", "germany", "德国", "+49"), "Europe/Berlin", "EU", "Germany", "Berlin"),
    (("amsterdam", "netherlands", "荷兰", "+31"), "Europe/Amsterdam", "EU", "Netherlands", "Amsterdam"),
    (("dublin", "ireland", "爱尔兰", "+353"), "Europe/Dublin", "EU", "Ireland", "Dublin"),
    (("madrid", "spain", "西班牙", "+34"), "Europe/Madrid", "EU", "Spain", "Madrid"),
    (("milan", "rome", "italy", "意大利", "+39"), "Europe/Rome", "EU", "Italy", "Milan"),
    # MEA
    (("dubai", "abu dhabi", "uae", "emirates", "阿联酋", "迪拜", "+971"), "Asia/Dubai", "MEA", "United Arab Emirates", "Dubai"),
    (("riyadh", "saudi", "沙特", "+966"), "Asia/Riyadh", "MEA", "Saudi Arabia", "Riyadh"),
    (("tel aviv", "israel", "以色列", "+972"), "Asia/Jerusalem", "MEA", "Israel", "Tel Aviv"),
    (("lagos", "nigeria", "尼日利亚", "+234"), "Africa/Lagos", "MEA", "Nigeria", "Lagos"),
    (("johannesburg", "south africa", "南非", "+27"), "Africa/Johannesburg", "MEA", "South Africa", "Johannesburg"),
    (("cairo", "egypt", "埃及", "+20"), "Africa/Cairo", "MEA", "Egypt", "Cairo"),
]

_CITY_ZH = {
    "Singapore": "新加坡",
    "Tokyo": "东京",
    "Seoul": "首尔",
    "Hong Kong": "中国香港",
    "Hong Kong, China": "中国香港",
    "Taiwan, China": "中国台湾",
    "Taipei": "台北",
    "Kuala Lumpur": "吉隆坡",
    "Jakarta": "雅加达",
    "Bangkok": "曼谷",
    "Ho Chi Minh City": "胡志明市",
    "Manila": "马尼拉",
    "San Juan": "圣胡安",
    "Santiago": "圣地亚哥",
    "Lima": "利马",
    "Madrid": "马德里",
    "Milan": "米兰",
    "Cairo": "开罗",
    "Auckland": "奥克兰",
    "Shanghai": "上海",
    "Sydney": "悉尼",
    "Mumbai": "孟买",
    "Los Angeles": "洛杉矶",
    "New York": "纽约",
    "Chicago": "芝加哥",
    "Toronto": "多伦多",
    "Mexico City": "墨西哥城",
    "São Paulo": "圣保罗",
    "Buenos Aires": "布宜诺斯艾利斯",
    "Bogotá": "波哥大",
    "London": "伦敦",
    "Paris": "巴黎",
    "Berlin": "柏林",
    "Amsterdam": "阿姆斯特丹",
    "Dublin": "都柏林",
    "Dubai": "迪拜",
    "Riyadh": "利雅得",
    "Tel Aviv": "特拉维夫",
    "Lagos": "拉各斯",
    "Johannesburg": "约翰内斯堡",
}

_IANA_TO_CITY = {
    "Asia/Singapore": "Singapore",
    "Asia/Tokyo": "Tokyo",
    "Asia/Seoul": "Seoul",
    "Asia/Hong_Kong": "Hong Kong",
    "Asia/Shanghai": "Shanghai",
    "Australia/Sydney": "Sydney",
    "Asia/Kolkata": "Mumbai",
    "Pacific/Auckland": "Auckland",
    "America/Los_Angeles": "Los Angeles",
    "America/New_York": "New York",
    "America/Chicago": "Chicago",
    "America/Toronto": "Toronto",
    "America/Mexico_City": "Mexico City",
    "America/Sao_Paulo": "São Paulo",
    "America/Argentina/Buenos_Aires": "Buenos Aires",
    "America/Bogota": "Bogotá",
    "Europe/London": "London",
    "Europe/Paris": "Paris",
    "Europe/Berlin": "Berlin",
    "Europe/Amsterdam": "Amsterdam",
    "Europe/Dublin": "Dublin",
    "Asia/Dubai": "Dubai",
    "Asia/Riyadh": "Riyadh",
    "Asia/Jerusalem": "Tel Aviv",
    "Africa/Lagos": "Lagos",
    "Africa/Johannesburg": "Johannesburg",
}

_IANA_TO_ZONE = {
    "Asia/Singapore": "APAC",
    "Asia/Tokyo": "APAC",
    "Asia/Seoul": "APAC",
    "Asia/Hong_Kong": "APAC",
    "Asia/Shanghai": "APAC",
    "Australia/Sydney": "APAC",
    "Asia/Kolkata": "APAC",
    "Pacific/Auckland": "APAC",
    "America/Los_Angeles": "NA",
    "America/New_York": "NA",
    "America/Chicago": "NA",
    "America/Toronto": "NA",
    "America/Mexico_City": "LATAM",
    "America/Sao_Paulo": "LATAM",
    "America/Argentina/Buenos_Aires": "LATAM",
    "America/Bogota": "LATAM",
    "Europe/London": "EU",
    "Europe/Paris": "EU",
    "Europe/Berlin": "EU",
    "Europe/Amsterdam": "EU",
    "Europe/Dublin": "EU",
    "Asia/Dubai": "MEA",
    "Asia/Riyadh": "MEA",
    "Asia/Jerusalem": "MEA",
    "Africa/Lagos": "MEA",
    "Africa/Johannesburg": "MEA",
}


@dataclass
class GeoResolved:
    timezone: Optional[str] = None
    geo_zone: Optional[str] = None
    country: Optional[str] = None
    city_label: Optional[str] = None


def infer_geo_from_text(
    text: str,
    phone: Optional[str] = None,
    country_hint: Optional[str] = None,
    region_hint: Optional[str] = None,
) -> GeoResolved:
    blob = " ".join(
        p for p in (text or "", phone or "", country_hint or "", region_hint or "") if p
    ).lower()
    compact = re.sub(r"\s+", "", blob)

    for keys, tz, zone, country, city in _GEO_RULES:
        for key in keys:
            if key.startswith("+"):
                digits = re.sub(r"[^\d+]", "", phone or "")
                if digits.startswith(key) or key in blob:
                    return GeoResolved(tz, zone, country, city)
            elif key in blob or key in compact:
                return GeoResolved(tz, zone, country, city)

    return GeoResolved()


def normalize_iana(tz: Optional[str]) -> Optional[str]:
    if not tz:
        return None
    aliases = {
        "pst": "America/Los_Angeles",
        "pdt": "America/Los_Angeles",
        "pt": "America/Los_Angeles",
        "est": "America/New_York",
        "edt": "America/New_York",
        "et": "America/New_York",
        "cst": "America/Chicago",
        "utc+8": "Asia/Shanghai",
        "gmt+8": "Asia/Shanghai",
        "sgt": "Asia/Singapore",
        "jst": "Asia/Tokyo",
        "bst": "Europe/London",
        "gmt": "Europe/London",
    }
    key = tz.strip()
    lower = key.lower()
    if lower in aliases:
        return aliases[lower]
    if "/" in key:
        return key
    return key


def enrich_card_geo(
    *,
    ocr_text: str = "",
    phone: Optional[str] = None,
    country: Optional[str] = None,
    region: Optional[str] = None,
    timezone: Optional[str] = None,
    geo_zone: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Return (country, timezone, geo_zone, city_label) with deterministic mapping fill-ins."""
    inferred = infer_geo_from_text(ocr_text, phone=phone, country_hint=country, region_hint=region)
    tz = normalize_iana(timezone) or inferred.timezone
    zone = (geo_zone or "").upper() or inferred.geo_zone
    if zone and zone not in GEO_ZONES:
        zone = inferred.geo_zone
    if not zone and tz:
        zone = _IANA_TO_ZONE.get(tz)
    ctry = country or inferred.country
    city = inferred.city_label or _IANA_TO_CITY.get(tz or "")
    return ctry, tz, zone, city


def city_label_localized(city_en: Optional[str], lang: str = "en") -> Optional[str]:
    if not city_en:
        return None
    if lang == "zh":
        return _CITY_ZH.get(city_en, city_en)
    return city_en


def utc_offset_label(tz: Optional[str]) -> str:
    if not tz:
        return ""
    try:
        from datetime import datetime
        from zoneinfo import ZoneInfo

        now = datetime.now(ZoneInfo(tz))
        offset = now.utcoffset()
        if offset is None:
            return tz
        total = int(offset.total_seconds() // 60)
        sign = "+" if total >= 0 else "-"
        hh, mm = divmod(abs(total), 60)
        return f"{tz} (UTC{sign}{hh:02d}:{mm:02d})" if mm else f"{tz} (UTC{sign}{hh})"
    except Exception:
        return tz
