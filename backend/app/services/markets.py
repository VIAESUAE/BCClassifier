from __future__ import annotations

from typing import Any, Dict, List, Optional

GEO_ZONES = ("APAC", "NA", "LATAM", "EU", "MEA")

def _with_other(places: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return places + [{"id": "Other", "label_zh": "其他", "label_en": "Other"}]


# Directory cascading filters — no LLM required.
# NA uses market slices instead of plain "United States".
GEO_FILTER_TREE: List[Dict[str, Any]] = [
    {
        "id": "APAC",
        "label_zh": "亚太 (APAC)",
        "label_en": "Asia-Pacific (APAC)",
        "places": _with_other(
            [
                {"id": "Singapore", "label_zh": "新加坡", "label_en": "Singapore"},
                {"id": "Japan", "label_zh": "日本", "label_en": "Japan"},
                {"id": "South Korea", "label_zh": "韩国", "label_en": "South Korea"},
                {"id": "Malaysia", "label_zh": "马来西亚", "label_en": "Malaysia"},
                {"id": "India", "label_zh": "印度", "label_en": "India"},
                {"id": "Indonesia", "label_zh": "印度尼西亚", "label_en": "Indonesia"},
                {"id": "China", "label_zh": "中国大陆", "label_en": "China"},
                {"id": "Hong Kong", "label_zh": "中国香港", "label_en": "Hong Kong, China"},
                {"id": "Taiwan", "label_zh": "中国台湾", "label_en": "Taiwan, China"},
                {"id": "Thailand", "label_zh": "泰国", "label_en": "Thailand"},
                {"id": "Vietnam", "label_zh": "越南", "label_en": "Vietnam"},
                {"id": "Philippines", "label_zh": "菲律宾", "label_en": "Philippines"},
                {"id": "Australia", "label_zh": "澳大利亚", "label_en": "Australia"},
            ]
        ),
    },
    {
        "id": "NA",
        "label_zh": "北美 (NA)",
        "label_en": "North America (NA)",
        "places": _with_other(
            [
                {"id": "US West Coast", "label_zh": "美国西海岸", "label_en": "US West Coast"},
                {"id": "US East Coast", "label_zh": "美国东海岸", "label_en": "US East Coast"},
                {"id": "US Central", "label_zh": "美国中部", "label_en": "US Central"},
                {"id": "US Territories", "label_zh": "美国海外领土", "label_en": "US Territories"},
                {"id": "Canada", "label_zh": "加拿大", "label_en": "Canada"},
            ]
        ),
    },
    {
        "id": "LATAM",
        "label_zh": "拉美 (LATAM)",
        "label_en": "Latin America (LATAM)",
        "places": _with_other(
            [
                {"id": "Mexico", "label_zh": "墨西哥", "label_en": "Mexico"},
                {"id": "Brazil", "label_zh": "巴西", "label_en": "Brazil"},
                {"id": "Argentina", "label_zh": "阿根廷", "label_en": "Argentina"},
                {"id": "Colombia", "label_zh": "哥伦比亚", "label_en": "Colombia"},
                {"id": "Chile", "label_zh": "智利", "label_en": "Chile"},
                {"id": "Peru", "label_zh": "秘鲁", "label_en": "Peru"},
            ]
        ),
    },
    {
        "id": "EU",
        "label_zh": "欧洲 (EU)",
        "label_en": "Europe (EU)",
        "places": _with_other(
            [
                {"id": "United Kingdom", "label_zh": "英国", "label_en": "United Kingdom"},
                {"id": "France", "label_zh": "法国", "label_en": "France"},
                {"id": "Germany", "label_zh": "德国", "label_en": "Germany"},
                {"id": "Netherlands", "label_zh": "荷兰", "label_en": "Netherlands"},
                {"id": "Ireland", "label_zh": "爱尔兰", "label_en": "Ireland"},
                {"id": "Spain", "label_zh": "西班牙", "label_en": "Spain"},
                {"id": "Italy", "label_zh": "意大利", "label_en": "Italy"},
            ]
        ),
    },
    {
        "id": "MEA",
        "label_zh": "中东与非洲 (MEA)",
        "label_en": "Middle East & Africa (MEA)",
        "places": _with_other(
            [
                {"id": "United Arab Emirates", "label_zh": "阿联酋", "label_en": "United Arab Emirates"},
                {"id": "Saudi Arabia", "label_zh": "沙特阿拉伯", "label_en": "Saudi Arabia"},
                {"id": "Israel", "label_zh": "以色列", "label_en": "Israel"},
                {"id": "Nigeria", "label_zh": "尼日利亚", "label_en": "Nigeria"},
                {"id": "South Africa", "label_zh": "南非", "label_en": "South Africa"},
                {"id": "Egypt", "label_zh": "埃及", "label_en": "Egypt"},
            ]
        ),
    },
]

# Aliases so messy region/city labels still match a place filter.
_PLACE_ALIASES: Dict[str, tuple[str, ...]] = {
    "US West Coast": (
        "us west coast",
        "west coast",
        "bay area",
        "san francisco",
        "seattle",
        "los angeles",
        "palo alto",
        "silicon valley",
        "california",
        "america/los_angeles",
    ),
    "US East Coast": (
        "us east coast",
        "east coast",
        "new york",
        "nyc",
        "boston",
        "washington",
        "america/new_york",
    ),
    "US Central": ("us central", "central", "chicago", "dallas", "austin", "america/chicago"),
    "US Territories": ("puerto rico", "guam", "us territories", "america/puerto_rico"),
    "Canada": ("canada", "toronto", "vancouver", "montreal", "america/toronto"),
    "Singapore": ("singapore", "asia/singapore"),
    "Japan": ("japan", "tokyo", "asia/tokyo"),
    "South Korea": ("south korea", "korea", "seoul", "asia/seoul"),
    "Malaysia": ("malaysia", "kuala lumpur", "asia/kuala_lumpur"),
    "India": ("india", "mumbai", "bangalore", "bengaluru", "asia/kolkata"),
    "Indonesia": ("indonesia", "jakarta", "asia/jakarta"),
    "China": ("china", "shanghai", "beijing", "shenzhen", "asia/shanghai"),
    "Hong Kong": ("hong kong", "hongkong", "asia/hong_kong", "hong kong, china", "china hong kong"),
    "Taiwan": ("taiwan", "taipei", "asia/taipei", "taiwan, china", "china taiwan"),
    "Thailand": ("thailand", "bangkok", "asia/bangkok"),
    "Vietnam": ("vietnam", "ho chi minh", "hanoi", "asia/ho_chi_minh"),
    "Philippines": ("philippines", "manila", "asia/manila"),
    "Australia": ("australia", "sydney", "melbourne", "australia/sydney"),
    "Mexico": ("mexico", "mexico city", "america/mexico_city"),
    "Brazil": ("brazil", "brasil", "sao paulo", "são paulo", "america/sao_paulo"),
    "Argentina": ("argentina", "buenos aires"),
    "Colombia": ("colombia", "bogota", "bogotá"),
    "Chile": ("chile", "santiago"),
    "Peru": ("peru", "lima"),
    "United Kingdom": ("united kingdom", "uk", "london", "europe/london"),
    "France": ("france", "paris", "europe/paris"),
    "Germany": ("germany", "berlin", "frankfurt", "europe/berlin"),
    "Netherlands": ("netherlands", "amsterdam", "europe/amsterdam"),
    "Ireland": ("ireland", "dublin", "europe/dublin"),
    "Spain": ("spain", "madrid"),
    "Italy": ("italy", "milan", "rome"),
    "United Arab Emirates": ("united arab emirates", "uae", "dubai", "abu dhabi", "asia/dubai"),
    "Saudi Arabia": ("saudi", "riyadh", "asia/riyadh"),
    "Israel": ("israel", "tel aviv", "asia/jerusalem"),
    "Nigeria": ("nigeria", "lagos", "africa/lagos"),
    "South Africa": ("south africa", "johannesburg", "africa/johannesburg"),
    "Egypt": ("egypt", "cairo", "africa/cairo"),
}


def filter_tree_for_lang(lang: str = "zh") -> List[Dict[str, Any]]:
    use_zh = (lang or "zh").startswith("zh")
    out = []
    for zone in GEO_FILTER_TREE:
        out.append(
            {
                "id": zone["id"],
                "label": zone["label_zh"] if use_zh else zone["label_en"],
                "places": [
                    {
                        "id": p["id"],
                        "label": p["label_zh"] if use_zh else p["label_en"],
                    }
                    for p in zone["places"]
                ],
            }
        )
    return out


def card_matches_place(country: Optional[str], region: Optional[str], timezone: Optional[str], place_id: str) -> bool:
    if not place_id:
        return True
    if place_id == "Other":
        return False  # handled by card_matches_other
    blob = " ".join(x for x in (country or "", region or "", timezone or "") if x).lower()
    if place_id.lower() in blob:
        return True
    for alias in _PLACE_ALIASES.get(place_id, ()):
        if alias in blob:
            return True
    return False


def known_place_ids(geo_zone: str) -> List[str]:
    for zone in GEO_FILTER_TREE:
        if zone["id"] == geo_zone.upper():
            return [p["id"] for p in zone["places"] if p["id"] != "Other"]
    return []


def card_matches_other(
    country: Optional[str],
    region: Optional[str],
    timezone: Optional[str],
    geo_zone: Optional[str],
) -> bool:
    """True when the card sits in the zone but matches no named place."""
    if not geo_zone:
        return True
    for place_id in known_place_ids(geo_zone):
        if card_matches_place(country, region, timezone, place_id):
            return False
    return True


def normalize_na_region(region: Optional[str], timezone: Optional[str], country: Optional[str]) -> Optional[str]:
    """Map free-text NA locations onto the Directory place ids."""
    if country and "canada" in country.lower():
        return "Canada"
    blob = " ".join(x for x in (region or "", timezone or "", country or "") if x).lower()
    for place_id in ("US West Coast", "US East Coast", "US Central", "US Territories", "Canada"):
        if card_matches_place(country, region, timezone, place_id):
            return place_id
    if "united states" in blob or "usa" in blob or "america/los_angeles" in blob:
        return "US West Coast"
    return region
