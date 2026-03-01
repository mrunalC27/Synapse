"""
SYNAPSE — Animated Splash Screen System
========================================
Drop-in Streamlit splash screen with SVG logo animation.
Runs once per session using st.session_state.

Usage:
    from synapse_splash import show_synapse_splash
    show_synapse_splash()
"""
import time
import streamlit as st
import streamlit.components.v1 as components


# ─────────────────────────────────────────────
#  SECTION 1 · SVG LOGO
# ─────────────────────────────────────────────
SYNAPSE_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 80" width="520" height="80" aria-label="SYNAPSE">
  <defs>
    <!-- Neon glow filter -->
    <filter id="neon-glow" x="-20%" y="-80%" width="140%" height="260%">
      <feGaussianBlur stdDeviation="3.5" result="blur1"/>
      <feGaussianBlur stdDeviation="8"   result="blur2"/>
      <feMerge>
        <feMergeNode in="blur2"/>
        <feMergeNode in="blur1"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    <!-- Shimmer gradient (animated via JS) -->
    <linearGradient id="shimmer" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%"   stop-color="#007474" stop-opacity="0"/>
      <stop offset="45%"  stop-color="#007474" stop-opacity="0"/>
      <stop offset="50%"  stop-color="#00ffff" stop-opacity="0.55"/>
      <stop offset="55%"  stop-color="#007474" stop-opacity="0"/>
      <stop offset="100%" stop-color="#007474" stop-opacity="0"/>
    </linearGradient>
    <!-- Clip path for shimmer -->
    <clipPath id="text-clip">
      <text
        x="50%"
        y="72"
        text-anchor="middle"
        font-family="'Syne', 'Montserrat', 'Trebuchet MS', sans-serif"
        font-size="68"
        font-weight="800"
        letter-spacing="18"
      >SYNAPSE</text>
    </clipPath>
  </defs>

  <!-- Base text — teal -->
  <text
    id="logo-text"
    x="50%"
    y="72"
    text-anchor="middle"
    font-family="'Syne', 'Montserrat', 'Trebuchet MS', sans-serif"
    font-size="68"
    font-weight="800"
    letter-spacing="18"
    fill="#007474"
    filter="url(#neon-glow)"
  >SYNAPSE</text>

  <!-- Shimmer overlay clipped to text shape -->
  <rect
    id="shimmer-rect"
    x="-100%"
    y="0"
    width="100%"
    height="100%"
    fill="url(#shimmer)"
    clip-path="url(#text-clip)"
    opacity="0"
  />
</svg>
"""


# ─────────────────────────────────────────────
#  SECTION 2 · CSS ANIMATIONS
# ─────────────────────────────────────────────
SPLASH_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=Montserrat:wght@300;400;700&display=swap');

  /* ── Reset & host ── */
  * { margin: 0; padding: 0; box-sizing: border-box; }

  html, body {
    width: 100%;
    height: 100%;
    background: #000000;
    overflow: hidden;
  }

  /* ── Splash container ── */
  #splash {
    position: fixed;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: #000000;
    z-index: 9999;
    opacity: 1;
    transition: opacity 0.75s cubic-bezier(0.4, 0, 0.2, 1);
  }

  #splash.fade-out {
    opacity: 0;
    pointer-events: none;
  }

  /* ── Logo wrapper ── */
  #logo-wrap {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 28px;
    opacity: 0;
    transform: scale(0.97);
    animation:
      logo-enter 1.0s cubic-bezier(0.16, 1, 0.3, 1) 0.25s forwards,
      logo-pulse 2.4s ease-in-out 0.8s infinite;
  }

  @keyframes logo-enter {
    to {
      opacity: 1;
      transform: scale(1.0);
    }
  }

  @keyframes logo-pulse {
    0%, 100% { filter: drop-shadow(0 0 10px rgba(0, 116, 116, 0.35)); }
    50%       { filter: drop-shadow(0 0 28px rgba(0, 116, 116, 0.75)); }
  }

  /* ── Tagline ── */
  #tagline {
    font-family: 'Syne', 'Montserrat', sans-serif;
    font-size: 11px;
    font-weight: 400;
    letter-spacing: 6px;
    color: rgba(0, 116, 116, 0.55);
    text-transform: uppercase;
    opacity: 0;
    animation: fade-in-up 0.8s ease-out 1.1s forwards;
  }

  @keyframes fade-in-up {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  /* ── Loading bar ── */
  #loader-track {
    width: 200px;
    height: 1px;
    background: rgba(0, 116, 116, 0.12);
    border-radius: 1px;
    overflow: hidden;
    opacity: 0;
    animation: fade-in 0.5s ease 1.3s forwards;
  }

  #loader-fill {
    height: 100%;
    width: 0%;
    background: linear-gradient(90deg, #007474, #00c4c4);
    border-radius: 1px;
    box-shadow: 0 0 8px rgba(0, 196, 196, 0.6);
    animation: load-progress 1.4s cubic-bezier(0.4, 0, 0.2, 1) 1.4s forwards;
  }

  @keyframes load-progress {
    0%   { width: 0%; opacity: 0.7; }
    70%  { width: 85%; opacity: 1; }
    100% { width: 100%; opacity: 1; }
  }

  @keyframes fade-in {
    to { opacity: 1; }
  }

  /* ── Ambient corner dots ── */
  .corner-dot {
    position: fixed;
    width: 3px;
    height: 3px;
    border-radius: 50%;
    background: rgba(0, 116, 116, 0.4);
    animation: dot-blink 2s ease-in-out infinite;
  }

  .corner-dot:nth-child(1) { top: 32px; left: 32px;  animation-delay: 0s; }
  .corner-dot:nth-child(2) { top: 32px; right: 32px; animation-delay: 0.4s; }
  .corner-dot:nth-child(3) { bottom: 32px; left: 32px;  animation-delay: 0.8s; }
  .corner-dot:nth-child(4) { bottom: 32px; right: 32px; animation-delay: 1.2s; }

  @keyframes dot-blink {
    0%, 100% { opacity: 0.25; }
    50%       { opacity: 0.8; }
  }

  /* ── Scan line (very subtle) ── */
  #scanline {
    position: fixed;
    inset: 0;
    background: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 3px,
      rgba(0, 116, 116, 0.015) 3px,
      rgba(0, 116, 116, 0.015) 4px
    );
    pointer-events: none;
    animation: fade-in 1s ease 0.5s both;
  }
</style>
"""


# ─────────────────────────────────────────────
#  SECTION 3 · HTML CONTAINER + JS ORCHESTRATION
# ─────────────────────────────────────────────
SPLASH_HTML_TEMPLATE = """
{css}

<!-- ── Ambient scan lines ── -->
<div id="scanline"></div>

<!-- ── Corner markers ── -->
<div class="corner-dot"></div>
<div class="corner-dot"></div>
<div class="corner-dot"></div>
<div class="corner-dot"></div>

<!-- ── Main splash ── -->
<div id="splash">
  <div id="logo-wrap">

    <!-- SVG Logo -->
    {svg}

    <!-- Tagline -->
    <div id="tagline">Intelligent Workspace</div>

    <!-- Progress bar -->
    <div id="loader-track">
      <div id="loader-fill"></div>
    </div>

  </div>
</div>

<script>
(function () {
  "use strict";

  // ── Shimmer sweep across the logo text ──────────────────
  function runShimmer() {
    var rect  = document.getElementById("shimmer-rect");
    var svg   = document.querySelector("svg");
    if (!rect || !svg) return;

    var svgW  = svg.viewBox.baseVal.width;   // 520
    var start = null;
    var dur   = 900;   // ms for one pass
    var delay = 1100;  // ms before first shimmer

    setTimeout(function () {
      rect.setAttribute("opacity", "1");

      function step(ts) {
        if (!start) start = ts;
        var prog = Math.min((ts - start) / dur, 1);
        // sweep x from -100% to +200% of viewBox
        var xVal = -svgW + prog * (svgW * 3);
        rect.setAttribute("x", xVal);
        if (prog < 1) {
          requestAnimationFrame(step);
        } else {
          rect.setAttribute("opacity", "0");
        }
      }
      requestAnimationFrame(step);
    }, delay);
  }

  // ── Fade out splash and notify Streamlit ────────────────
  function dismissSplash() {
    var splash = document.getElementById("splash");
    if (!splash) return;

    splash.classList.add("fade-out");

    // After CSS fade completes, hide completely and signal parent
    setTimeout(function () {
      splash.style.display = "none";

      // Signal Streamlit via postMessage (parent iframe)
      try {
        window.parent.postMessage({ type: "SYNAPSE_SPLASH_DONE" }, "*");
      } catch (e) {}
    }, 800);
  }

  // ── Boot sequence ────────────────────────────────────────
  document.addEventListener("DOMContentLoaded", function () {
    runShimmer();
    // Total visible duration ≈ 2500ms, then fade (750ms)
    setTimeout(dismissSplash, 2500);
  });
})();
</script>
"""


# ─────────────────────────────────────────────
#  SECTION 4 · STREAMLIT INTEGRATION
# ─────────────────────────────────────────────

def show_synapse_splash() -> None:
    """
    Render the SYNAPSE animated splash screen.

    • Injects the full HTML/CSS/JS into an st.components iframe.
    • Uses st.session_state["_synapse_splash_shown"] to ensure
      the splash only appears ONCE per browser session.
    • The component is 100% self-contained — no external CDNs required
      (Google Fonts falls back to system fonts when offline).

    Call this as the VERY FIRST statement in your app's main block,
    before any other st.* calls.

    Example
    -------
    >>> import streamlit as st
    >>> from synapse_splash import show_synapse_splash
    >>>
    >>> show_synapse_splash()
    >>>
    >>> st.title("Welcome to SYNAPSE")
    >>> # ... rest of your dashboard
    """
    # ── Guard: only show once per session ──
    if st.session_state.get("_synapse_splash_shown", False):
        return

    # Mark as shown immediately so reruns skip it
    st.session_state["_synapse_splash_shown"] = True

    # ── Build the full HTML payload ──
    html_payload = (
    SPLASH_HTML_TEMPLATE
        .replace("{css}", SPLASH_CSS)
        .replace("{svg}", SYNAPSE_SVG)
    )

    # ── Inject into Streamlit ──
    # Height covers viewport; scrolling=False prevents scroll bars.
    components.html(
        html_payload,
        height=520,
        scrolling=False,
    )


# ─────────────────────────────────────────────
#  SECTION 5 · STANDALONE DEMO (python synapse_splash.py)
# ─────────────────────────────────────────────
if __name__ == "__main__":
    # Page config must come first
    st.set_page_config(
        page_title="SYNAPSE",
        page_icon="⬡",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # ── Global dark theme overrides ──
    st.markdown(
        """
        <style>
          [data-testid="stAppViewContainer"] { background: #000000; }
          [data-testid="stHeader"]           { background: transparent; }
          [data-testid="stSidebar"]          { background: #0a0a0a; }
          body, .stMarkdown, .stText         { color: #e0e0e0; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ── Show splash (once per session) ──
    show_synapse_splash()

    # ── Main dashboard (renders underneath / after splash) ──
    st.markdown(
        """
        <h1 style="
          font-family: 'Syne', 'Montserrat', sans-serif;
          color: #007474;
          font-size: 2rem;
          letter-spacing: 4px;
          font-weight: 700;
          margin-top: 2rem;
        ">SYNAPSE</h1>
        <p style="color: rgba(255,255,255,0.35); font-size: 0.85rem; letter-spacing: 2px;">
          INTELLIGENT WORKSPACE
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.write("")
    st.write("Dashboard content loads here after the splash completes.")
