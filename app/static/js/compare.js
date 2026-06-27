/* app/static/js/compare.js — school compare (max 3, localStorage, same category only) */

(function () {
    const MAX = 3;
    const STORAGE_KEY = "kr_compare_ids_v1";
    const cfg = window.KRCAMPUS_COMPARE || {};

    function getLang() {
        return cfg.lang || "en";
    }

    function inferCategory(id) {
        if (id && id.startsWith("univ_")) return "university";
        return "school";
    }

    function normalizeCompareItems(raw) {
        if (!Array.isArray(raw)) return [];
        return raw.map((entry) => {
            if (entry && typeof entry === "object" && entry.id) {
                return {
                    id: String(entry.id),
                    category: entry.category === "university" ? "university" : "school",
                };
            }
            const id = String(entry || "");
            if (!id) return null;
            return { id, category: inferCategory(id) };
        }).filter(Boolean);
    }

    function getCompareItems() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            if (!raw) return [];
            return normalizeCompareItems(JSON.parse(raw));
        } catch (_) {
            return [];
        }
    }

    function getCompareIds() {
        return getCompareItems().map((item) => item.id);
    }

    function setCompareItems(items) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(items.slice(0, MAX)));
    }

    function compareUrl(ids) {
        const lang = getLang();
        const base = `/compare?lang=${encodeURIComponent(lang)}`;
        if (!ids || !ids.length) return base;
        return `${base}&ids=${encodeURIComponent(ids.join(","))}`;
    }

    function showToast(message) {
        let el = document.getElementById("compare-toast");
        if (!el) {
            el = document.createElement("div");
            el.id = "compare-toast";
            el.className = "compare-toast";
            document.body.appendChild(el);
        }
        el.textContent = message;
        el.classList.add("is-visible");
        clearTimeout(el._hideTimer);
        el._hideTimer = setTimeout(() => el.classList.remove("is-visible"), 2200);
    }

    function trackEvent(action, label) {
        if (typeof window.gtag === "function") {
            window.gtag("event", action, {
                event_category: "ux_interaction",
                event_label: label || "",
            });
        }
    }

    async function copyText(text) {
        try {
            if (navigator.clipboard && navigator.clipboard.writeText) {
                await navigator.clipboard.writeText(text);
                return true;
            }
        } catch (_) { /* fallback below */ }
        const ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.left = "-9999px";
        document.body.appendChild(ta);
        ta.select();
        try {
            return document.execCommand("copy");
        } catch (_) {
            return false;
        } finally {
            document.body.removeChild(ta);
        }
    }

    function buildCompareTextFromExport(data) {
        if (!data || !data.items || !data.items.length) return "";
        const site = data.siteName || "Campus";
        const lines = [`${site} — School comparison`, ""];
        data.items.forEach((item, i) => {
            lines.push(`${i + 1}. ${item.name}`);
            lines.push(`   City: ${item.city}`);
            lines.push(`   Fees: ${item.fee}`);
            if (item.features && item.features.length) {
                lines.push(`   Features: ${item.features.join(", ")}`);
            }
            lines.push("");
        });
        lines.push(window.location.href);
        return lines.join("\n").trim();
    }

    function syncCompareUI() {
        const items = getCompareItems();
        const ids = items.map((item) => item.id);
        const count = ids.length;
        const canCompare = count >= 2;

        document.querySelectorAll("[data-compare-count]").forEach((el) => {
            el.textContent = String(count);
        });

        const bar = document.getElementById("compare-bar");
        if (bar) bar.classList.toggle("is-visible", count > 0);
        document.body.classList.toggle("compare-bar-active", count > 0);

        document.querySelectorAll("[data-compare-open]").forEach((el) => {
            const url = compareUrl(ids);
            if (el.tagName === "A") {
                if (canCompare) {
                    el.href = url;
                    el.classList.remove("is-disabled");
                    el.removeAttribute("aria-disabled");
                } else {
                    el.href = "#";
                    el.classList.add("is-disabled");
                    el.setAttribute("aria-disabled", "true");
                }
            } else if (el.tagName === "BUTTON") {
                el.disabled = !canCompare;
            }
        });

        document.querySelectorAll(".compare-toggle-btn[data-compare-id]").forEach((btn) => {
            const selected = ids.includes(btn.dataset.compareId);
            btn.classList.toggle("is-selected", selected);
            const defaultLabel = btn.dataset.labelDefault || "+ Compare";
            const selectedLabel = btn.dataset.labelSelected || "✓ Comparing";
            btn.textContent = selected ? selectedLabel : defaultLabel;
            btn.setAttribute("aria-pressed", selected ? "true" : "false");
        });

        document.querySelectorAll(".school-card[data-school-id], .university-card[data-school-id]").forEach((card) => {
            card.classList.toggle("in-compare", ids.includes(card.dataset.schoolId));
        });
    }

    function toggleCompareItem(id, category) {
        if (!id) return;
        const nextCategory = category || inferCategory(id);
        const items = getCompareItems();
        const exists = items.some((item) => item.id === id);
        let next;

        if (exists) {
            next = items.filter((item) => item.id !== id);
            showToast(cfg.toastRemoved || "Removed from compare");
        } else if (items.length >= MAX) {
            showToast(cfg.toastMax || "Max 3 schools — remove one first");
            return;
        } else if (items.length > 0 && items[0].category !== nextCategory) {
            showToast(cfg.toastMixed || "Compare language institutes and universities separately");
            return;
        } else {
            next = [...items, { id, category: nextCategory }];
            showToast(cfg.toastAdded || "Added to compare ✓");
        }

        setCompareItems(next);
        syncCompareUI();
        trackEvent("compare_toggle", id);
    }

    function clearCompare() {
        setCompareItems([]);
        syncCompareUI();
        showToast(cfg.toastCleared || "Compare list cleared");
        trackEvent("compare_clear", "clear");
    }

    function bootstrapFromQuery() {
        const params = new URLSearchParams(window.location.search);

        if (window.location.pathname === "/compare") {
            const idsParam = params.get("ids");
            if (idsParam) {
                const ids = idsParam.split(",")
                    .map((value) => value.trim())
                    .filter(Boolean)
                    .slice(0, MAX);
                const normalized = normalizeCompareItems(ids);
                const firstCategory = normalized[0]?.category;
                setCompareItems(normalized.filter((item) => item.category === firstCategory));
            }
        }

        const addId = params.get("add_compare");
        if (!addId) return;

        const category = inferCategory(addId);
        const items = getCompareItems();
        if (!items.some((item) => item.id === addId)) {
            if (items.length > 0 && items[0].category !== category) {
                setCompareItems([{ id: addId, category }]);
            } else {
                const next = items.length >= MAX
                    ? [...items.slice(1), { id: addId, category }]
                    : [...items, { id: addId, category }];
                setCompareItems(next);
            }
            trackEvent("compare_add_from_detail", addId);
        }

        params.delete("add_compare");
        const nextQuery = params.toString();
        const nextUrl = `${window.location.pathname}${nextQuery ? `?${nextQuery}` : ""}${window.location.hash || ""}`;
        window.history.replaceState({}, "", nextUrl);
    }

    document.addEventListener("click", (event) => {
        const toggleBtn = event.target.closest(".compare-toggle-btn[data-compare-id]");
        if (toggleBtn) {
            event.preventDefault();
            event.stopPropagation();
            toggleCompareItem(toggleBtn.dataset.compareId, toggleBtn.dataset.compareCategory);
            return;
        }

        const clearBtn = event.target.closest("[data-compare-clear]");
        if (clearBtn) {
            event.preventDefault();
            clearCompare();
            return;
        }

        const removeBtn = event.target.closest("[data-compare-remove]");
        if (removeBtn) {
            event.preventDefault();
            const id = removeBtn.dataset.compareRemove;
            const next = getCompareItems().filter((item) => item.id !== id);
            setCompareItems(next);
            window.location.href = compareUrl(next.map((item) => item.id));
            return;
        }

        const openLink = event.target.closest("[data-compare-open].is-disabled");
        if (openLink) {
            event.preventDefault();
            return;
        }

        const copyUrlBtn = event.target.closest("[data-compare-copy-url]");
        if (copyUrlBtn) {
            event.preventDefault();
            copyText(window.location.href).then((ok) => {
                if (ok) {
                    showToast(cfg.toastCopied || "Copied!");
                    trackEvent("compare_copy_url", "");
                }
            });
            return;
        }

        const copyTextBtn = event.target.closest("[data-compare-copy-text]");
        if (copyTextBtn) {
            event.preventDefault();
            const text = buildCompareTextFromExport(window.COMPARE_PAGE_DATA);
            copyText(text).then((ok) => {
                if (ok) {
                    showToast(cfg.toastCopied || "Copied!");
                    trackEvent("compare_copy_text", "");
                }
            });
        }
    });

    window.KRCampusCompare = {
        getCompareItems: getCompareIds,
        getCompareEntries: getCompareItems,
        toggleCompareItem,
        clearCompare,
        syncCompareUI,
        compareUrl,
    };

    bootstrapFromQuery();
    syncCompareUI();
})();
