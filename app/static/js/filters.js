/* app/static/js/filters.js — category (school/university) + optional school features + region */

(function () {
    let allSchoolData = [];
    let currentCategory = "school";
    let currentSchoolFeature = null;
    let currentRegionFilter = "all";
    let currentFilteredData = [];

    const ACADEMIC_KEYWORDS = ["topik", "university prep", "university preparation", "academic", "degree", "진학", "大学進学"];
    const DORM_KEYWORDS = ["dormitory", "dorm", "기숙사", "寮", "student housing"];
    const MAJOR_CITIES = ["인천", "대전", "수원", "창원", "Incheon", "Daejeon", "Suwon"];

    function getFeatures(school) {
        const rawFeatures = school.features;
        return Array.isArray(rawFeatures)
            ? rawFeatures.join(" ").toLowerCase()
            : String(rawFeatures || "").toLowerCase();
    }

    function getAddress(school) {
        return school.basic_info?.address || "";
    }

    function matchesSchoolFeature(school, featureKey) {
        const features = getFeatures(school);
        const capacity = school.basic_info?.capacity;

        switch (featureKey) {
            case "dormitory":
                return DORM_KEYWORDS.some((kw) => features.includes(kw));
            case "academic":
                return ACADEMIC_KEYWORDS.some((kw) => features.includes(kw));
            case "size_medium":
                return typeof capacity === "number" && capacity > 150 && capacity <= 500;
            default:
                return true;
        }
    }

    function matchesRegion(school, regionKey) {
        if (regionKey === "all") return true;
        const address = getAddress(school);

        switch (regionKey) {
            case "seoul":
                return address.includes("서울") || address.includes("Seoul");
            case "busan":
                return address.includes("부산") || address.includes("Busan");
            case "daegu":
                return address.includes("대구") || address.includes("Daegu");
            case "gwangju":
                return address.includes("광주") || address.includes("Gwangju");
            case "major_city":
                return !address.includes("서울") && !address.includes("Seoul")
                    && !address.includes("부산") && !address.includes("Busan")
                    && !address.includes("대구") && !address.includes("Daegu")
                    && !address.includes("광주") && !address.includes("Gwangju")
                    && MAJOR_CITIES.some((city) => address.includes(city));
            default:
                return true;
        }
    }

    function computeFilteredData(category = currentCategory, schoolFeature = currentSchoolFeature, regionKey = currentRegionFilter) {
        return sortByPublishedDesc(allSchoolData.filter((school) => {
            if (category === "university") {
                return school.category === "university" && matchesRegion(school, regionKey);
            }
            if (school.category !== "school") return false;
            if (schoolFeature && !matchesSchoolFeature(school, schoolFeature)) return false;
            return matchesRegion(school, regionKey);
        }));
    }

    function sortByPublishedDesc(items) {
        return items.slice().sort((a, b) => {
            const da = String(a.published || "").slice(0, 10);
            const db = String(b.published || "").slice(0, 10);
            if (da !== db) return db.localeCompare(da);
            return String(a.id || "").localeCompare(String(b.id || ""));
        });
    }

    function countForCategory(categoryKey) {
        return computeFilteredData(categoryKey, null, currentRegionFilter).length;
    }

    function countForSchoolFeature(featureKey) {
        return computeFilteredData("school", featureKey, currentRegionFilter).length;
    }

    function countForRegion(regionKey) {
        return computeFilteredData(currentCategory, currentSchoolFeature, regionKey).length;
    }

    function updateGridEmptyState(grid, cardSelector) {
        const cards = grid.querySelectorAll(cardSelector);
        if (!cards.length) return;
        const visibleCount = [...cards].filter((c) => !c.classList.contains("is-filter-hidden")).length;
        grid.classList.toggle("is-filter-empty", visibleCount === 0);
        const sectionHeader = grid.previousElementSibling;
        if (sectionHeader && sectionHeader.classList.contains("section-header")) {
            sectionHeader.classList.toggle("is-filter-empty", visibleCount === 0);
        }
    }

    function reorderGridCards(gridSelector, cardSelector, orderedIds) {
        const grid = document.querySelector(gridSelector);
        if (!grid) return;
        const byId = {};
        grid.querySelectorAll(cardSelector).forEach((card) => {
            byId[card.dataset.schoolId] = card;
        });
        orderedIds.forEach((id) => {
            const card = byId[id];
            if (card) grid.appendChild(card);
        });
    }

    function filterVisibleCards(filteredSchools) {
        const ids = new Set(filteredSchools.map((s) => s.id));
        const showSchools = currentCategory === "school";
        const showUniversities = currentCategory === "university";

        document.querySelectorAll('[data-filter-grid="schools"] .school-card[data-school-id]').forEach((card) => {
            card.classList.toggle("is-filter-hidden", !showSchools || !ids.has(card.dataset.schoolId));
        });

        document.querySelectorAll('[data-filter-grid="universities"] .university-card[data-school-id]').forEach((card) => {
            card.classList.toggle("is-filter-hidden", !showUniversities || !ids.has(card.dataset.schoolId));
        });

        const schools = filteredSchools.filter((s) => s.category !== "university");
        const universities = filteredSchools.filter((s) => s.category === "university");
        reorderGridCards('[data-filter-grid="schools"]', ".school-card[data-school-id]", schools.map((s) => s.id));
        reorderGridCards('[data-filter-grid="universities"]', ".university-card[data-school-id]", universities.map((s) => s.id));

        document.querySelectorAll("[data-filter-grid]").forEach((grid) => {
            const cardSelector = grid.dataset.filterGrid === "universities"
                ? ".university-card[data-school-id]"
                : ".school-card[data-school-id]";
            updateGridEmptyState(grid, cardSelector);
        });

        document.querySelectorAll(".filter-row-school-features").forEach((row) => {
            row.classList.toggle("is-hidden", currentCategory !== "school");
        });

        document.querySelectorAll("[data-section-for]").forEach((section) => {
            const target = section.dataset.sectionFor;
            const visible = (target === "schools" && showSchools) || (target === "universities" && showUniversities);
            section.classList.toggle("is-filter-hidden", !visible);
        });
    }

    function updateFilterCounts() {
        document.querySelectorAll('.theme-button[data-filter-axis="category"][data-filter-key]').forEach((btn) => {
            const key = btn.dataset.filterKey;
            const el = document.getElementById(`count-category-${key}`);
            if (el) el.textContent = String(countForCategory(key));
        });
        document.querySelectorAll('.theme-button[data-filter-axis="school-feature"][data-filter-key]').forEach((btn) => {
            const key = btn.dataset.filterKey;
            const el = document.getElementById(`count-feature-${key}`);
            if (el) el.textContent = String(countForSchoolFeature(key));
        });
        document.querySelectorAll('.theme-button[data-filter-axis="region"][data-filter-key]').forEach((btn) => {
            const key = btn.dataset.filterKey;
            const el = document.getElementById(`count-region-${key}`);
            if (el) el.textContent = String(countForRegion(key));
        });
    }

    function syncActiveButtons() {
        document.querySelectorAll('.theme-button[data-filter-axis="category"]').forEach((btn) => {
            const active = btn.dataset.filterKey === currentCategory;
            btn.classList.toggle("active", active);
            btn.classList.toggle("is-active", active);
        });
        document.querySelectorAll('.theme-button[data-filter-axis="school-feature"]').forEach((btn) => {
            const active = currentCategory === "school" && btn.dataset.filterKey === currentSchoolFeature;
            btn.classList.toggle("active", active);
            btn.classList.toggle("is-active", active);
        });
        document.querySelectorAll('.theme-button[data-filter-axis="region"]').forEach((btn) => {
            const active = btn.dataset.filterKey === currentRegionFilter;
            btn.classList.toggle("active", active);
            btn.classList.toggle("is-active", active);
        });
    }

    function syncViewQueryParam() {
        if (window.location.pathname !== "/") return;
        const params = new URLSearchParams(window.location.search);
        if (params.get("view") === currentCategory) return;
        params.set("view", currentCategory);
        const next = `${window.location.pathname}?${params.toString()}${window.location.hash || ""}`;
        window.history.replaceState({}, "", next);
    }

    function applyFilters() {
        currentFilteredData = computeFilteredData();
        syncActiveButtons();
        filterVisibleCards(currentFilteredData);
        updateFilterCounts();
        syncViewQueryParam();

        document.dispatchEvent(new CustomEvent("krcampus:filter", {
            detail: {
                category: currentCategory,
                schoolFeature: currentSchoolFeature,
                region: currentRegionFilter,
                schools: currentFilteredData.slice(),
            },
        }));
    }

    function resolveInitialCategory() {
        const fromWindow = window.KRCAMPUS_INITIAL_VIEW;
        if (fromWindow === "school" || fromWindow === "university") return fromWindow;
        const params = new URLSearchParams(window.location.search);
        const fromQuery = params.get("view");
        if (fromQuery === "school" || fromQuery === "university") return fromQuery;
        return "school";
    }

    function bootstrap() {
        if (typeof SCHOOLS_DATA !== "undefined") {
            allSchoolData = sortByPublishedDesc(SCHOOLS_DATA.schools || []);
        }
        currentCategory = resolveInitialCategory();
        currentSchoolFeature = null;
        applyFilters();
    }

    document.addEventListener("click", (event) => {
        const btn = event.target.closest('.theme-button[data-filter-axis][data-filter-key]');
        if (!btn) return;
        event.preventDefault();

        const axis = btn.dataset.filterAxis;
        const key = btn.dataset.filterKey;
        if (axis === "category") {
            if (key !== "school" && key !== "university") return;
            currentCategory = key;
            currentSchoolFeature = null;
        } else if (axis === "school-feature") {
            if (currentCategory !== "school") return;
            currentSchoolFeature = currentSchoolFeature === key ? null : key;
        } else if (axis === "region") {
            currentRegionFilter = key || "all";
        }

        applyFilters();
    });

    window.KRCampusFilters = {
        applyFilters,
        getCurrentFilteredData: () => currentFilteredData.slice(),
        getAllSchoolData: () => allSchoolData.slice(),
        getCategory: () => currentCategory,
        getSchoolFeature: () => currentSchoolFeature,
        getRegionFilter: () => currentRegionFilter,
        refresh: bootstrap,
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", bootstrap);
    } else {
        bootstrap();
    }
})();
