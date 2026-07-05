def compare_city(item: dict) -> str:
    address = (item.get("basic_info") or {}).get("address") or ""
    if not address:
        return "—"
    return address.split(",")[0].strip()


def compare_fee_value(item: dict) -> int | None:
    tuition = item.get("tuition") or {}
    value = tuition.get("yearly_tuition")
    return value if isinstance(value, (int, float)) else None


def compare_fee_label(item: dict, lang: str) -> str | None:
    value = compare_fee_value(item)
    if value is None:
        return None
    suffix = " <small>(yearly)</small>" if item.get("category") == "university" else " <small>(yearly tuition)</small>"
    return f"₩{int(value):,}{suffix}"


def prepare_compare_items(items: list[dict], lang: str) -> list[dict]:
    prepared = []
    for item in items:
        row = dict(item)
        row["compare_city"] = compare_city(item)
        row["compare_fee_value"] = compare_fee_value(item)
        row["compare_fee_label"] = compare_fee_label(item, lang)
        fee_value = compare_fee_value(item)
        row["compare_fee_plain"] = f"₩{int(fee_value):,}" if fee_value is not None else None
        prepared.append(row)
    return prepared


def build_compare_export(selected: list[dict], lang: str, site_name: str) -> dict:
    items = []
    for item in selected:
        bi = item.get("basic_info", {}) or {}
        name = bi.get("name_display") or bi.get("name_en") or bi.get("name_ko") or bi.get("name_ja") or item.get("id", "")
        fee = item.get("compare_fee_plain") or item.get("compare_fee_label", "")
        if fee and "<" in str(fee):
            fee = str(fee).split("<")[0].strip()
        features = item.get("features") or []
        items.append({
            "name": name,
            "city": item.get("compare_city", "—"),
            "fee": fee or "—",
            "features": features[:3],
        })
    return {"siteName": site_name, "lang": lang, "items": items}
