(function () {
    var thresholds = [25, 50, 75, 100];
    var fired = {};

    function currentDepthPercent() {
        var doc = document.documentElement;
        var scrollable = (doc.scrollHeight - doc.clientHeight) || 1;
        var scrollTop = window.scrollY || doc.scrollTop || 0;
        return Math.min(100, Math.round((scrollTop / scrollable) * 100));
    }

    function onScroll() {
        if (typeof gtag !== "function") return;
        var pct = currentDepthPercent();
        thresholds.forEach(function (t) {
            if (pct >= t && !fired[t]) {
                fired[t] = true;
                gtag("event", "scroll_depth", {
                    event_category: "engagement",
                    event_label: t + "%",
                    value: t,
                });
            }
        });
    }

    window.addEventListener("scroll", onScroll, { passive: true });
})();
