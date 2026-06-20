/* app/static/js/filters.js — map-independent category filters */

(function () {
    let allSchoolData = [];
    let currentFilterKey = 'all';
    let currentFilteredData = [];

    const ACADEMIC_KEYWORDS = ["topik", "university prep", "university preparation", "academic", "degree", "진학", "大学進学"];
    const BIZ_KEYWORDS = ["business", "job", "취업", "ビジネス"];
    const CULTURE_KEYWORDS = ["conversation", "culture", "short-term", "회화", "短期", "문화"];
    const DORM_KEYWORDS = ['dormitory', 'dorm', '기숙사', '寮', 'student housing'];
    const MAJOR_CITIES = ['대구', '인천', '광주', '대전', '수원', 'Daegu', 'Incheon', 'Gwangju', 'Daejeon'];

    function filterSchoolsByKey(key) {
        if (key === 'university') return allSchoolData.filter(s => s.category === 'university');
        if (key === 'all') return allSchoolData.filter(s => s.category !== 'university');

        return allSchoolData.filter(school => {
            if (school.category === 'university') return false;

            const rawFeatures = school.features;
            const features = Array.isArray(rawFeatures)
                ? rawFeatures.join(" ").toLowerCase()
                : String(rawFeatures || "").toLowerCase();
            const address = school.basic_info?.address || '';
            const capacity = school.basic_info?.capacity;

            switch (key) {
                case 'academic': return ACADEMIC_KEYWORDS.some(kw => features.includes(kw));
                case 'business': return BIZ_KEYWORDS.some(kw => features.includes(kw));
                case 'culture': return CULTURE_KEYWORDS.some(kw => features.includes(kw));
                case 'seoul': return address.includes('서울') || address.includes('Seoul');
                case 'busan': return address.includes('부산') || address.includes('Busan');
                case 'major_city':
                    return !address.includes('서울') && !address.includes('Seoul')
                        && !address.includes('부산') && !address.includes('Busan')
                        && MAJOR_CITIES.some(city => address.includes(city));
                case 'size_small': return typeof capacity === 'number' && capacity <= 150;
                case 'size_medium': return typeof capacity === 'number' && capacity > 150 && capacity <= 500;
                case 'dormitory': return DORM_KEYWORDS.some(kw => features.includes(kw));
                default: return true;
            }
        });
    }

    function updateGridEmptyState(grid, cardSelector) {
        const cards = grid.querySelectorAll(cardSelector);
        if (!cards.length) return;
        const visibleCount = [...cards].filter(c => !c.classList.contains('is-filter-hidden')).length;
        grid.classList.toggle('is-filter-empty', visibleCount === 0);
        const sectionHeader = grid.previousElementSibling;
        if (sectionHeader && sectionHeader.classList.contains('section-header')) {
            sectionHeader.classList.toggle('is-filter-empty', visibleCount === 0);
        }
    }

    function filterVisibleCards(filteredSchools) {
        const ids = new Set(filteredSchools.map(s => s.id));
        const isUniversityFilter = currentFilterKey === 'university';

        document.querySelectorAll('[data-filter-grid="schools"] .school-card[data-school-id]').forEach(card => {
            card.classList.toggle('is-filter-hidden', isUniversityFilter || !ids.has(card.dataset.schoolId));
        });

        document.querySelectorAll('[data-filter-grid="universities"] .university-card[data-school-id]').forEach(card => {
            card.classList.toggle('is-filter-hidden', !isUniversityFilter && currentFilterKey !== 'all');
        });

        document.querySelectorAll('[data-filter-grid]').forEach(grid => {
            const cardSelector = grid.dataset.filterGrid === 'universities'
                ? '.university-card[data-school-id]'
                : '.school-card[data-school-id]';
            updateGridEmptyState(grid, cardSelector);
        });
    }

    function updateFilterCounts() {
        document.querySelectorAll('.theme-button[data-filter-key]').forEach(btn => {
            const key = btn.dataset.filterKey;
            const el = document.getElementById(`count-${key}`);
            if (el) el.textContent = String(filterSchoolsByKey(key).length);
        });
    }

    function applyFilterKey(filterKey) {
        currentFilterKey = filterKey || 'all';
        currentFilteredData = filterSchoolsByKey(currentFilterKey);

        document.querySelectorAll('.theme-button[data-filter-key]').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filterKey === currentFilterKey);
        });
        document.querySelectorAll('.quick-filter-chip[data-filter-key]').forEach(chip => {
            chip.classList.toggle('is-active', chip.dataset.filterKey === currentFilterKey);
        });

        filterVisibleCards(currentFilteredData);

        document.dispatchEvent(new CustomEvent('krcampus:filter', {
            detail: { key: currentFilterKey, schools: currentFilteredData.slice() }
        }));
    }

    function bootstrap() {
        if (typeof SCHOOLS_DATA !== 'undefined') {
            allSchoolData = SCHOOLS_DATA.schools || [];
        }
        updateFilterCounts();
        applyFilterKey(currentFilterKey);
    }

    document.addEventListener('click', (event) => {
        const btn = event.target.closest('.theme-button[data-filter-key], .quick-filter-chip[data-filter-key]');
        if (!btn) return;
        event.preventDefault();
        applyFilterKey(btn.dataset.filterKey || 'all');
    });

    window.KRCampusFilters = {
        applyFilterKey,
        filterSchoolsByKey,
        getCurrentFilteredData: () => currentFilteredData.slice(),
        getAllSchoolData: () => allSchoolData.slice(),
        refresh: bootstrap,
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bootstrap);
    } else {
        bootstrap();
    }
})();
