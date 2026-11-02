(function () {
    "use strict";

    // Drives the home page's fixed spotlight mark animation: each
    // .frame-layer gets a mask-image set directly every frame from a
    // single shared clock, instead of a CSS @keyframes animation --
    // needed because the mask has two independently-moving stops (an
    // inner "erase" edge and an outer "reveal" edge), which can't be
    // expressed as a CSS animation without @property (inconsistent
    // browser support) or mask-composite (different compositing
    // keyword syntax in Safari).
    //
    // --- the reveal/conceal math (one shared clock drives every layer) ---
    //
    // Each layer gets two circles, both growing from the center at the
    // SAME constant rate: an outer (reveal) edge and an inner (erase)
    // edge that starts STAGGER_MS after the outer edge. The layer is
    // visible in the ring between inner and outer.
    //
    //   phase 1 [0, T1):      outer 0% -> 50%,   inner = 0%        (solid growing disk)
    //   phase 2 [T1, 2*T1):   outer 50% -> 100%, inner 0% -> 50%   (constant-width ring, translating outward)
    //   phase 3 [2*T1, 3*T1): outer = 100% (clamped), inner 50% -> 100%  (ring closing from inside)
    //
    // Starting layer k+1 exactly STAGGER_MS after layer k makes layer
    // (k+1)'s outer edge trace layer k's inner edge exactly (same
    // formula, same rate, time-shifted), so at every instant the active
    // layers partition the whole disk with no gap and no overlap -- no
    // two frames are ever painted in the same spot at once. Each frame
    // only ever blends against bare paper, never against another
    // frame's colors, which is what keeps mix-blend-mode: multiply from
    // compounding. No z-index is needed anywhere: non-overlapping
    // regions never have a paint-order conflict to resolve.
    var STAGGER_MS = 2750; // T1
    var CYCLE_MS = 10 * STAGGER_MS;
    var ACTIVE_MS = 3 * STAGGER_MS;

    // The frame JPEGs have real whitespace margin around the mandala --
    // measured directly (bounding box of non-white pixels in each
    // frame-N.jpg) at 55.2% of the canvas's half-width, consistent
    // across every frame. `closest-side` sizing (see the mask-image
    // default in site.css) makes a bare 100% land at the box's own
    // edge, well past the mandala's true edge, so every computed
    // percentage is scaled by this factor to put "100% grown" at the
    // mandala's actual edge instead. Re-measure (bounding box of
    // non-white pixels) if the source frame images are ever replaced.
    var CONTENT_RADIUS_PCT = 55.2;

    function computeRadii(localT) {
        var T1 = STAGGER_MS;
        if (localT < 0 || localT >= ACTIVE_MS) return null;
        if (localT < T1) {
            return { inner: 0, outer: 50 * (localT / T1) };
        }
        if (localT < 2 * T1) {
            var p1 = (localT - T1) / T1;
            return { inner: 50 * p1, outer: 50 + 50 * p1 };
        }
        var p2 = (localT - 2 * T1) / T1;
        return { inner: 50 + 50 * p2, outer: 100 };
    }

    function maskString(inner, outer) {
        var scaledInner = (inner * CONTENT_RADIUS_PCT) / 100;
        var scaledOuter = (outer * CONTENT_RADIUS_PCT) / 100;
        return (
            "radial-gradient(circle closest-side, transparent " + scaledInner + "%, " +
            "black " + scaledInner + "%, black " + scaledOuter + "%, " +
            "transparent " + scaledOuter + "%)"
        );
    }

    function applyMask(el, inner, outer) {
        var mask = maskString(inner, outer);
        el.style.maskImage = mask;
        el.style.webkitMaskImage = mask;
    }

    function startSpotlight() {
        var layers = Array.prototype.slice.call(document.querySelectorAll(".frame-layer"));
        if (!layers.length) return;

        if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
            // Static: show the mid-cycle frame fully revealed, leave
            // the rest closed (their CSS default).
            var midFrame = layers[Math.floor(layers.length / 2)];
            applyMask(midFrame, 0, 100);
            return;
        }

        var start = performance.now();

        function tick() {
            var elapsed = performance.now() - start;

            layers.forEach(function (el, k) {
                var rawLocal = (elapsed - k * STAGGER_MS) % CYCLE_MS;
                var localT = (rawLocal + CYCLE_MS) % CYCLE_MS;
                var radii = computeRadii(localT);
                if (radii) {
                    applyMask(el, radii.inner, radii.outer);
                }
            });

            requestAnimationFrame(tick);
        }

        requestAnimationFrame(tick);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", startSpotlight);
    } else {
        startSpotlight();
    }
})();
