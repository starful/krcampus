/* app/static/js/map.js */

let map;
let markers = [];
let infoWindow;
let markerById = {};
let mapReady = false;

async function initMap() {
    const { Map } = await google.maps.importLibrary("maps");
    const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");
    window.AdvancedMarkerElement = AdvancedMarkerElement;

    map = new Map(document.getElementById("map"), {
        zoom: 7,
        center: { lat: 36.5, lng: 127.5 },
        mapId: "2938bb3f7f034d78c237cb68",
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: false,
        zoomControlOptions: { position: google.maps.ControlPosition.TOP_RIGHT },
    });

    infoWindow = new google.maps.InfoWindow({ minWidth: 280, disableAutoPan: true });
    mapReady = true;

    bindCardInteractions();
    bindSearchEvents();

    const filtered = window.KRCampusFilters?.getCurrentFilteredData?.() || [];
    renderMarkers(filtered);
}

window.initMap = initMap;

document.addEventListener('krcampus:filter', (event) => {
    renderMarkers(event.detail?.schools || []);
});

function getAllSchools() {
    return window.KRCampusFilters?.getAllSchoolData?.() || [];
}

function bindSearchEvents() {
    const univSearchInput = document.getElementById('univ-search-input');
    const clearBtn = document.getElementById('search-clear-btn');
    if (!univSearchInput) return;

    const runSearch = () => {
        if (!mapReady || !map) return;
        const keyword = (univSearchInput.value || "").trim().toLowerCase();
        const currentFilteredData = window.KRCampusFilters?.getCurrentFilteredData?.() || [];

        if (!keyword) {
            renderMarkers(currentFilteredData);
            return;
        }

        const pool = currentFilteredData;
        const found = pool.find(s => {
            const b = s.basic_info || {};
            const candidates = [b.name_en, b.name_ja, b.name_display, s.id]
                .filter(Boolean)
                .map(v => String(v).toLowerCase());
            return candidates.some(v => v.includes(keyword));
        });

        if (found && found.location) {
            map.setCenter(found.location);
            map.setZoom(14);
            const marker = markers.find(m => {
                const title = (m.title || "").toLowerCase();
                return title === ((found.basic_info?.name_en || found.basic_info?.name_ja || "").toLowerCase());
            });
            if (marker) openInfoWindow(found, marker);
        }
    };

    univSearchInput.addEventListener('change', runSearch);
    univSearchInput.addEventListener('keydown', (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            runSearch();
        }
    });

    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            univSearchInput.value = "";
            const currentFilteredData = window.KRCampusFilters?.getCurrentFilteredData?.() || [];
            renderMarkers(currentFilteredData.length ? currentFilteredData : getAllSchools());
            univSearchInput.focus();
        });
    }
}

function bindCardInteractions() {
    document.querySelectorAll('.school-card[data-school-id]').forEach(card => {
        const schoolId = card.dataset.schoolId;
        card.addEventListener('mouseenter', () => highlightMarkerById(schoolId, true));
        card.addEventListener('mouseleave', () => highlightMarkerById(schoolId, false));
    });
}

function renderMarkers(data) {
    markers.forEach(m => { m.map = null; });
    markers = [];
    markerById = {};

    if (!data || !mapReady || !map || !window.AdvancedMarkerElement) return;

    const bounds = new google.maps.LatLngBounds();

    data.forEach(item => {
        if (!item.location || item.location.lat == null) return;

        const isUniv = (item.category === 'university');
        const markerEl = document.createElement('div');
        const thumb = item.thumbnail || '';
        if (thumb) {
            markerEl.className = 'marker-icon';
            markerEl.style.backgroundImage = `url(${thumb})`;
        } else if (isUniv) {
            markerEl.className = 'map-marker marker-univ';
            markerEl.innerHTML = '<i class="fa-solid fa-building-columns"></i>';
        } else {
            markerEl.className = 'map-marker marker-school';
            markerEl.innerHTML = '<i class="fa-solid fa-graduation-cap"></i>';
        }

        const marker = new window.AdvancedMarkerElement({
            map,
            position: item.location,
            title: item.basic_info.name_en || item.basic_info.name_ja,
            content: markerEl,
            zIndex: isUniv ? 100 : 10
        });

        marker.addListener("click", () => openInfoWindow(item, marker));
        markers.push(marker);
        if (item.id) markerById[item.id] = marker;
        bounds.extend(item.location);
    });

    if (markers.length === 0) return;

    if (markers.length === 1) {
        map.setCenter(bounds.getCenter());
        map.setZoom(14);
        return;
    }

    map.fitBounds(bounds, 80);
    const zoom = map.getZoom();
    if (zoom > 15) map.setZoom(15);
    if (zoom < 6) map.setZoom(6);
}

function getCompareLabels() {
    const cfg = window.KRCAMPUS_COMPARE || {};
    return {
        default: cfg.labelDefault || "+ Compare",
        selected: cfg.labelSelected || "✓ Comparing",
    };
}

function getCompareButtonLabel(id) {
    const labels = getCompareLabels();
    const ids = window.KRCampusCompare?.getCompareItems?.() || [];
    return ids.includes(id) ? labels.selected : labels.default;
}

function openInfoWindow(school, marker) {
    const isUniv = school.category === 'university';
    const labelColor = isUniv ? 'var(--accent)' : 'var(--primary)';
    const labelText = isUniv ? 'University' : 'Language School';
    const compareLabels = getCompareLabels();
    const compareLabel = getCompareButtonLabel(school.id);

    if (infoWindow) infoWindow.close();

    infoWindow.setContent(`
        <div class="info-window-content">
            <div class="iw-header">
                <span class="iw-badge" style="background-color: ${labelColor};">${labelText}</span>
                <h5 class="iw-title">${school.basic_info.name_en || school.basic_info.name_ja}</h5>
                <p class="iw-address">${school.basic_info.address || 'Address not available'}</p>
            </div>
            <div class="iw-actions">
                <button type="button" class="compare-toggle-btn iw-compare-btn" data-compare-id="${school.id}" data-compare-category="${isUniv ? 'university' : 'school'}" data-label-default="${compareLabels.default}" data-label-selected="${compareLabels.selected}" aria-pressed="false">${compareLabel}</button>
                <a href="${school.link}" class="iw-details-btn">View Details →</a>
            </div>
        </div>`);

    infoWindow.open({ anchor: marker, map });
    highlightCardBySchoolId(school.id);
    highlightMarkerById(school.id, true);
    setTimeout(() => highlightMarkerById(school.id, false), 1400);
    trackEvent("marker_click", school.id || "unknown");
}

function highlightCardBySchoolId(schoolId) {
    if (!schoolId) return;
    const card = document.querySelector(`.school-card[data-school-id="${schoolId}"], .university-card[data-school-id="${schoolId}"]`);
    if (!card || card.classList.contains("is-filter-hidden")) return;
    card.classList.add("is-highlighted");
    card.scrollIntoView({ behavior: "smooth", block: "center" });
    setTimeout(() => card.classList.remove("is-highlighted"), 1600);
}

function highlightMarkerById(schoolId, isActive) {
    const marker = markerById[schoolId];
    if (!marker || !marker.content) return;
    marker.content.classList.toggle("map-marker-active", !!isActive);
}

function trackEvent(action, label) {
    if (typeof window.gtag === "function") {
        window.gtag("event", action, {
            event_category: "ux_interaction",
            event_label: label || ""
        });
    }
}
