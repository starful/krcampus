import hashlib

UNIV_THUMBNAILS = [
    "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=500", "https://images.unsplash.com/photo-1498243691581-b145c3f54a5a?w=500",
    "https://images.unsplash.com/photo-1592280771190-3e2e4d571952?w=500", "https://images.unsplash.com/photo-1562774053-701939374585?w=500",
    "https://images.unsplash.com/photo-1606092195730-5d7b9af1efc5?w=500", "https://images.unsplash.com/photo-1521587760476-6c12a4b040da?w=500",
    "https://images.unsplash.com/photo-1584697964190-7383cbee8277?w=500", "https://images.unsplash.com/photo-1511629091441-ee46146481b6?w=500",
    "https://images.unsplash.com/photo-1573894998033-c0cef4ed722b?w=500", "https://images.unsplash.com/photo-1485893086445-ed75865251e0?w=500",
    "https://images.unsplash.com/photo-1568038479111-87bf80659645?w=500", "https://images.unsplash.com/photo-1542621334-a254cf47733d?w=500",
    "https://images.unsplash.com/photo-1500088139251-37350df3c1ad?w=500",
    "https://images.unsplash.com/photo-1547699326-3d895d9acd30?w=500",
    "https://images.unsplash.com/photo-1612310480588-061aad90bb64?w=500",
    "https://images.unsplash.com/photo-1592280771190-3e2e4d571952?w=600", "https://images.unsplash.com/photo-1562774053-701939374585?w=600",
    "https://images.unsplash.com/photo-1606092195730-5d7b9af1efc5?w=600", "https://images.unsplash.com/photo-1521587760476-6c12a4b040da?w=600",
    "https://images.unsplash.com/photo-1541336318489-083c7d277b8e?w=600",
    "https://images.unsplash.com/photo-1511629091441-ee46146481b6?w=600",
    "https://images.unsplash.com/photo-1464938050520-ef2270bb8ce8?w=600", "https://images.unsplash.com/photo-1519452635265-7b1fbfd1e4e0?w=600",
    "https://images.unsplash.com/photo-1517486808906-6ca8b3f04846?w=600",
    "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=600",
    "https://images.unsplash.com/photo-1527891751199-7225231a68dd?w=600",
]

SCHOOL_THUMBNAILS = [
    "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=500", "https://images.unsplash.com/photo-1509062522246-3755977927d7?w=500",
    "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=500", "https://images.unsplash.com/photo-1580582932707-520aed937b7b?w=500",
    "https://images.unsplash.com/photo-1544531586-fde5298cdd40?w=500", "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=500",
    "https://images.unsplash.com/photo-1528164344705-47542687000d?w=500", "https://images.unsplash.com/photo-1577985051167-0d49eec21977?w=500",
    "https://images.unsplash.com/photo-1581092334978-16972703644f?w=500", "https://images.unsplash.com/photo-1608813607488-0f932c5b71ef?w=500",
    "https://images.unsplash.com/photo-1581276879432-15e50529f34b?w=500", "https://images.unsplash.com/photo-1584697964190-7383cbee8277?w=500",
    "https://images.unsplash.com/photo-1577825294026-50dc375b9119?w=500", "https://images.unsplash.com/photo-1453694595360-51e193e121fc?w=500",
    "https://images.unsplash.com/photo-1573416033034-e42e14b545d2?w=500", "https://images.unsplash.com/photo-1586877644127-e5ee9b4231c3?w=500",
    "https://images.unsplash.com/photo-1550303435-1703d8811aaa?w=500", "https://images.unsplash.com/photo-1505738313577-5357ff512f16?w=500",
    "https://images.unsplash.com/photo-1561535893-bb7a98c7ee45?w=500", "https://images.unsplash.com/photo-1523905330026-b8bd1f5f320e?w=500",
    "https://images.unsplash.com/photo-1613376023733-0a73315d9b06?w=500", "https://images.unsplash.com/photo-1493934558415-9d19f0b2b4d2?w=500",
    "https://images.unsplash.com/photo-1541336318489-083c7d277b8e?w=500", "https://images.unsplash.com/photo-1622589476300-b72799ca4ade?w=500",
    "https://images.unsplash.com/photo-1639621108959-15f9c4257508?w=500", "https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=500",
    "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=500", "https://images.unsplash.com/photo-1526916025899-1a28d20f2a5f?w=500",
    "https://images.unsplash.com/photo-1559077138-3e27e1cdb95a?w=500", "https://images.unsplash.com/photo-1598368195835-91e67f80c9d7?w=500",
]

GUIDE_THUMBNAILS = [
    "https://images.unsplash.com/photo-1491841550275-ad7854e35ca6?w=500", "https://images.unsplash.com/photo-1610312278520-bcc893a3ff1d?w=500",
    "https://images.unsplash.com/photo-1590559899731-a382839e5549?w=500", "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=500",
    "https://images.unsplash.com/photo-1561414927-6d86591d0c4f?w=500", "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=500",
    "https://images.unsplash.com/photo-1556740758-90de374c12ad?w=500", "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=500",
    "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=500", "https://images.unsplash.com/photo-1542051841857-5f90071e7989?w=500",
    "https://images.unsplash.com/photo-1580167227251-be70f01b0c51?w=500", "https://images.unsplash.com/photo-1684526688489-b08cbd8e1848?w=500",
    "https://images.unsplash.com/photo-1603491543570-f7df3c9a12c1?w=500", "https://images.unsplash.com/photo-1563089145-599997674d42?w=500",
    "https://images.unsplash.com/photo-1580477667995-2b94f01c9516?w=500", "https://images.unsplash.com/photo-1560972550-aba3456b5564?w=500",
    "https://images.unsplash.com/photo-1548630435-998a2cbbff67?w=500",
    "https://images.unsplash.com/photo-1473496169904-658ba7c44d8a?w=500", "https://images.unsplash.com/photo-1558471250-385a4b04941e?w=500",
    "https://images.unsplash.com/photo-1526127230111-0197afe94d72?w=500", "https://images.unsplash.com/photo-1557409518-691ebcd96038?w=500",
    "https://images.unsplash.com/photo-1516205651411-aef33a44f7c2?w=500", "https://images.unsplash.com/photo-1551322120-c697cf88fbdc?w=500",
    "https://images.unsplash.com/photo-1573655349936-de6bed86f839?w=500", "https://images.unsplash.com/photo-1540569014015-19a7be504e3a?w=500",
    "https://images.unsplash.com/photo-1492571350019-22de08371fd3?w=500",
    "https://images.unsplash.com/photo-1517486808906-6ca8b3f04846?w=500", "https://images.unsplash.com/photo-1522199755839-a2bacb67c546?w=500",
]

GUIDE_CATEGORY_THUMBNAILS = {
    "Budget": "https://images.unsplash.com/photo-1561414927-6d86591d0c4f?w=500",
    "Cost": "https://images.unsplash.com/photo-1561414927-6d86591d0c4f?w=500",
    "Selection": "https://images.unsplash.com/photo-1528164344705-47542687000d?w=500",
    "Visa": "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=500",
    "Housing": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=500",
    "Part-time": "https://images.unsplash.com/photo-1556740758-90de374c12ad?w=500",
    "Exam": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=500",
    "Preparation": "https://images.unsplash.com/photo-1501504905252-473c47e087f8?w=500",
    "Settlement": "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=500",
    "Insurance": "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=500",
    "Region": "https://images.unsplash.com/photo-1542051841857-5f90071e7989?w=500",
    "Life": "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=500",
}


def _guide_thumbnail_from_id(guide_id: str) -> str:
    hash_val = int(hashlib.md5(guide_id.encode("utf-8")).hexdigest(), 16)
    return GUIDE_THUMBNAILS[hash_val % len(GUIDE_THUMBNAILS)]


def resolve_guide_list_thumbnail(meta) -> str:
    return _guide_thumbnail_from_id(str(meta.get("id") or ""))


def resolve_guide_detail_thumbnail(meta) -> str:
    thumb = (meta.get("thumbnail") or "").strip()
    if thumb.startswith("http"):
        return thumb
    category = str(meta.get("category") or "")
    for key, url in GUIDE_CATEGORY_THUMBNAILS.items():
        if key.lower() in category.lower():
            return url
    return _guide_thumbnail_from_id(str(meta.get("id") or ""))


def diversify_guide_thumbnails(guides):
    used = set()
    diversified = []
    for guide in guides:
        item = dict(guide)
        thumb = item.get("thumbnail") or ""
        guide_id = item.get("link", "").split("/guide/")[-1].split("?")[0]
        if thumb in used:
            base = int(hashlib.md5(guide_id.encode("utf-8")).hexdigest(), 16)
            for offset in range(len(GUIDE_THUMBNAILS)):
                candidate = GUIDE_THUMBNAILS[(base + offset) % len(GUIDE_THUMBNAILS)]
                if candidate not in used:
                    thumb = candidate
                    break
        used.add(thumb)
        item["thumbnail"] = thumb
        diversified.append(item)
    return diversified


def resolve_guide_thumbnail(meta) -> str:
    return resolve_guide_list_thumbnail(meta)


def assign_thumbnails(items, item_category="school"):
    thumb_pool = UNIV_THUMBNAILS if item_category == "university" else SCHOOL_THUMBNAILS
    for item in items:
        if not item.get("thumbnail"):
            item_id = str(item.get("id", "default_id"))
            hash_val = int(hashlib.md5(item_id.encode("utf-8")).hexdigest(), 16)
            item["thumbnail"] = thumb_pool[hash_val % len(thumb_pool)]
    return items
