package com.rsps.witness

/**
 * RSPS Witness — Pause Detector
 *
 * A simple state machine that distinguishes meaningful attentional pauses
 * from noise (rapid scrolling, phone-down events, accidental stops).
 *
 * State transitions:
 *   IDLE → SCROLLING (on scroll event)
 *   SCROLLING → PAUSED (on scroll stop, timer starts)
 *   PAUSED → IDLE + emit PauseEvent (if pause duration in [MIN, MAX])
 *   PAUSED → IDLE (if phone put down — duration > MAX)
 *   SCROLLING → SCROLLING (on continued scroll — timer resets)
 *
 * The insight from Phase 0: it's not what you scroll past that matters.
 * It's what makes you stop. The pause is the signal.
 *
 * Duration distribution analysis (Phase 0 empirical findings):
 *   - 0–1500ms: Mechanical pause between scrolls — noise
 *   - 1500–8000ms: Genuine attention — primary signal window
 *   - 8000–20000ms: Deep engagement (video, article) — high IDS weight
 *   - >45000ms: Phone down / interruption — excluded
 *
 * The IDS scorer weights these duration bands differently. A 12-second
 * pause on a TikTok about relational intelligence contributes more to
 * the "relational-intelligence" cluster score than a 2-second pause.
 */
class PauseDetector {

    companion object {
        private const val PAUSE_MIN_MS = 1500L
        private const val PAUSE_MAX_MS = 45_000L
        private const val SCROLL_DEBOUNCE_MS = 800L  // Consider scrolling stopped after this
    }

    private enum class State { IDLE, SCROLLING, PAUSED }
    private var state: State = State.IDLE
    private var scrollStartMs: Long = 0L
    private var lastScrollEventMs: Long = 0L
    private var pauseStartMs: Long = 0L
    private var pendingPause: Long? = null

    fun onScrollEvent(packageName: String, timestampMs: Long) {
        lastScrollEventMs = timestampMs

        when (state) {
            State.IDLE -> {
                state = State.SCROLLING
                scrollStartMs = timestampMs
            }
            State.SCROLLING -> {
                // Continue scrolling — update last scroll time
            }
            State.PAUSED -> {
                // User was paused but scrolled again — emit the pause if valid
                evaluatePause(timestampMs)
                state = State.SCROLLING
                scrollStartMs = timestampMs
            }
        }
    }

    fun onContentChangeEvent(packageName: String, timestampMs: Long) {
        // If we haven't seen a scroll event in SCROLL_DEBOUNCE_MS,
        // the user has likely stopped scrolling — transition to PAUSED
        if (state == State.SCROLLING &&
            timestampMs - lastScrollEventMs > SCROLL_DEBOUNCE_MS) {
            state = State.PAUSED
            pauseStartMs = lastScrollEventMs
        }
    }

    /**
     * Called after content change events to check if a pause has completed.
     * Returns the pause duration in ms if a valid pause was detected, else null.
     * The caller is responsible for reading this after each event batch.
     */
    fun getPendingPauseEvent(): Long? {
        val pending = pendingPause
        pendingPause = null
        return pending
    }

    private fun evaluatePause(currentTimeMs: Long) {
        if (state != State.PAUSED) return
        val duration = currentTimeMs - pauseStartMs
        if (duration in PAUSE_MIN_MS..PAUSE_MAX_MS) {
            pendingPause = duration
        }
        state = State.IDLE
    }

    /** Called periodically (e.g., from a Handler) to flush stale pauses */
    fun tick(currentTimeMs: Long) {
        if (state == State.SCROLLING &&
            currentTimeMs - lastScrollEventMs > SCROLL_DEBOUNCE_MS) {
            state = State.PAUSED
            pauseStartMs = lastScrollEventMs
        }
        if (state == State.PAUSED &&
            currentTimeMs - pauseStartMs > PAUSE_MAX_MS) {
            // Phone probably put down — discard
            state = State.IDLE
        }
    }
}
