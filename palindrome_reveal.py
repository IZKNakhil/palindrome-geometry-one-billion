"""THE PALINDROME REVEAL — V11 | 60-second YouTube Short.

Only palindromic integers n from 2 to MAX_N are plotted at
    x = n * sin(n) * cos(n)
    y = n * sin(n)**2
using radians. No coordinate axes or artificial changes to the points.

Dependencies: numpy, matplotlib, FFmpeg (for MP4 only).
Run as a Python script or paste the entire file into one Jupyter/Colab cell.
"""

import os
import time

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter
from matplotlib.colors import hsv_to_rgb


# =====================================================================
# 1. SETTINGS — change these only
# =====================================================================
MAX_N = 1000_000_000
PREVIEW_ONLY = False       # True = quick PNG; False = full 60-second MP4
PREVIEW_SECOND = 55.0    # 1.5 = hook; 10 = early; 30 = growth; 55 = finale

DURATION = 60
FPS = 30
WIDTH, HEIGHT, DPI = 1080, 1920, 120

OUTPUT = f"palindrome_reveal_{MAX_N}.mp4"
PREVIEW_OUTPUT = f"palindrome_reveal_preview_{MAX_N}_{PREVIEW_SECOND:g}s.png"
DOWNLOAD_IN_COLAB = True
SHOW_VIDEO_IN_NOTEBOOK = False  # Avoid embedding a large 1080p video

# Timeline (seconds)
HOOK_END = 3.0
RESET_END = 3.5
FAST_END = 5.5
FAST_POINTS = 20
BUILD_END = 50.0

# Visual settings
BG = "#050711"
WHITE = "#F7F9FF"
SUBTITLE_COLOR = "#EAF7FF"
COUNTER_COLOR = "#E9C4FA"
CAMERA_PADDING = 1.12
MIN_HALF_HEIGHT = 8.0
CAMERA_SMOOTHING = 0.12
LABEL_RECENT = 2        # Only during growth, never on the final pattern


def smoothstep(value):
    value = np.clip(value, 0.0, 1.0)
    return value * value * (3.0 - 2.0 * value)


def palindromes_to(limit):
    """Generate palindromes directly; do not iterate over 10 million numbers."""
    if limit < 2:
        raise ValueError("MAX_N must be >= 2")
    values = []
    for length in range(1, len(str(limit)) + 1):
        half_len = (length + 1) // 2
        start = 1 if length == 1 else 10 ** (half_len - 1)
        stop = 10 ** half_len
        for prefix in range(start, stop):
            text = str(prefix)
            value = int(text + (text[-2::-1] if length % 2 else text[::-1]))
            if value > limit:
                break
            if value >= 2:
                values.append(value)
    return np.asarray(values, dtype=np.int64)


def main():
    start_time = time.time()
    if not (0 < HOOK_END < RESET_END < FAST_END < BUILD_END < DURATION):
        raise ValueError("Invalid timeline settings")
    if not (0 <= PREVIEW_SECOND < DURATION):
        raise ValueError("PREVIEW_SECOND must be between 0 and 60")

    numbers = palindromes_to(MAX_N)
    n = numbers.astype(np.float64)
    xs = n * np.sin(n) * np.cos(n)
    ys = n * np.sin(n) ** 2
    points = np.column_stack((xs, ys))
    total = len(numbers)
    if MAX_N == 1000:
        assert total == 107, total
    if MAX_N == 10_000_000:
        assert total == 10_997, total
    print(f"MAX_N: {MAX_N:,} | Palindromes: {total:,} | Last: {numbers[-1]:,}", flush=True)

    # Color progression matches the established colorful spiral.
    hues = (np.linspace(0.54, 1.44, total) % 1.0)
    colors = hsv_to_rgb(np.column_stack((hues, np.full(total, .80), np.ones(total))))
    colors_rgba = np.column_stack((colors, np.ones(total)))

    # Smaller dots for dense 10M patterns, larger dots for small experiments.
    if total >= 5_000:
        dot_size, glow_size, glow_alpha = 5.2, 25.0, .11
    elif total >= 500:
        dot_size, glow_size, glow_alpha = 10.0, 43.0, .13
    else:
        dot_size, glow_size, glow_alpha = 18.0, 70.0, .14

    # Running bounds for the growing spiral; origin is included.
    low_x = np.minimum.accumulate(np.minimum(xs, 0.0))
    high_x = np.maximum.accumulate(np.maximum(xs, 0.0))
    low_y = np.minimum.accumulate(np.minimum(ys, 0.0))
    high_y = np.maximum.accumulate(np.maximum(ys, 0.0))

    fig = plt.figure(figsize=(WIDTH / DPI, HEIGHT / DPI), dpi=DPI, facecolor=BG)
    ax_left, ax_bottom, ax_width, ax_height = .03, .15, .94, .68
    ax = fig.add_axes([ax_left, ax_bottom, ax_width, ax_height], facecolor=BG)
    ax.set_axis_off()
    ax.set_aspect("equal", adjustable="box")
    axes_aspect = WIDTH * ax_width / (HEIGHT * ax_height)

    # Center the two differently colored words as ONE line, with a fixed gap.
    title_can = fig.text(0, .950, "CAN", color="#38D9FF", ha="left",
                         fontsize=24, fontweight="bold", alpha=0)
    title_pal = fig.text(0, .950, "PALINDROMES", color="#FFE45C", ha="left",
                         fontsize=24, fontweight="bold", alpha=0)
    title_question = fig.text(.5, .927, "CREATE A PATTERN?", color="#FF61BC",
                              ha="center", fontsize=23, fontweight="bold", alpha=0)
    subtitle = fig.text(.5, .891, "ONE FORMULA. AN UNEXPECTED SPIRAL.",
                        ha="center", color=SUBTITLE_COLOR,
                        fontsize=14, fontweight="bold", alpha=0)
    counter = fig.text(.5, .862, "", ha="center", color=COUNTER_COLOR,
                       fontsize=12, fontweight="bold")
    finale = fig.text(.5, .088, "", ha="center", color=WHITE,
                      fontsize=16, fontweight="bold", alpha=0)
    tagline = fig.text(.5, .061, "EVERY DOT IS A PALINDROME",
                       ha="center", color="#72DFFF", fontsize=11, alpha=0)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    width_can = title_can.get_window_extent(renderer).width
    width_pal = title_pal.get_window_extent(renderer).width
    gap_px = 14
    canvas_w = fig.bbox.width
    left_px = (canvas_w - width_can - gap_px - width_pal) / 2
    title_can.set_x(left_px / canvas_w)
    title_pal.set_x((left_px + width_can + gap_px) / canvas_w)

    # Only two collections are updated; no individual plot calls per point.
    glow = ax.scatter([], [], s=glow_size, color="#FFFFFF", alpha=glow_alpha,
                      edgecolors="none", zorder=2, rasterized=True)
    dots = ax.scatter([], [], s=dot_size, color="#FFFFFF", alpha=.97,
                      edgecolors="none", zorder=3, rasterized=True)
    label_artists = [
        ax.annotate("", (0, 0), xytext=(0, 8), textcoords="offset points",
                    ha="center", va="bottom", color=WHITE, fontsize=9,
                    annotation_clip=True, visible=False, zorder=5)
        for _ in range(LABEL_RECENT)
    ]

    # Full-pattern camera used for the opening hook.
    full_cx = (low_x[-1] + high_x[-1]) / 2
    full_cy = (low_y[-1] + high_y[-1]) / 2
    full_half = max(MIN_HALF_HEIGHT,
                    (high_y[-1] - low_y[-1]) * CAMERA_PADDING / 2,
                    (high_x[-1] - low_x[-1]) * CAMERA_PADDING / (2 * axes_aspect))

    # Precompute camera states once. No frame-dependent arrays can be None.
    frame_count = DURATION * FPS
    times = np.arange(frame_count, dtype=np.float64) / FPS
    visible_counts = np.empty(frame_count, dtype=np.int32)
    views = np.empty((frame_count, 3), dtype=np.float64)
    camera_x = camera_y = 0.0
    camera_half = MIN_HALF_HEIGHT
    early = min(FAST_POINTS, total)

    for frame, t in enumerate(times):
        if t < RESET_END:
            count = total
            # Very subtle zoom IN during the first three seconds.
            hook_zoom = 1.075 - .075 * smoothstep(min(t / HOOK_END, 1.0))
            views[frame] = (full_cx, full_cy, full_half * hook_zoom)
        else:
            if t < FAST_END:
                progress = (t - RESET_END) / (FAST_END - RESET_END)
                count = 1 + int(progress * (early - 1))
            elif t < BUILD_END:
                progress = (t - FAST_END) / (BUILD_END - FAST_END)
                count = early + int((progress ** 1.13) * (total - early))
            else:
                count = total
            count = max(1, min(count, total))
            j = count - 1
            lo_x, hi_x = low_x[j], high_x[j]
            lo_y, hi_y = low_y[j], high_y[j]
            target_x = (lo_x + hi_x) / 2
            target_y = (lo_y + hi_y) / 2
            target_half = max(MIN_HALF_HEIGHT,
                              (hi_y - lo_y) * CAMERA_PADDING / 2,
                              (hi_x - lo_x) * CAMERA_PADDING / (2 * axes_aspect))
            if t < RESET_END + 1.0 / FPS:
                camera_x, camera_y, camera_half = target_x, target_y, target_half
            else:
                camera_x += CAMERA_SMOOTHING * (target_x - camera_x)
                camera_y += CAMERA_SMOOTHING * (target_y - camera_y)
                camera_half += CAMERA_SMOOTHING * (target_half - camera_half)
                # Expand immediately if a new point would otherwise be clipped.
                camera_half = max(camera_half, MIN_HALF_HEIGHT,
                                  (hi_y - camera_y) * 1.04,
                                  (camera_y - lo_y) * 1.04,
                                  (hi_x - camera_x) * 1.04 / axes_aspect,
                                  (camera_x - lo_x) * 1.04 / axes_aspect)
            views[frame] = (camera_x, camera_y, camera_half)
        visible_counts[frame] = count

    previous_count = -1

    def draw_frame(frame):
        nonlocal previous_count
        t = float(times[frame])
        count = int(visible_counts[frame])
        if count != previous_count:
            dots.set_offsets(points[:count])
            glow.set_offsets(points[:count])
            dots.set_facecolors(colors_rgba[:count])
            glow.set_facecolors(colors_rgba[:count])
            previous_count = count

        cam_x, cam_y, half = views[frame]
        ax.set_xlim(cam_x - axes_aspect * half, cam_x + axes_aspect * half)
        ax.set_ylim(cam_y - half, cam_y + half)

        # Hook -> fade to black -> fast restart -> build -> final reveal.
        if t < HOOK_END:
            point_alpha = 1.0
        elif t < RESET_END:
            point_alpha = 1.0 - smoothstep((t - HOOK_END) / (RESET_END - HOOK_END))
        elif t < RESET_END + .4:
            point_alpha = smoothstep((t - RESET_END) / .4)
        else:
            point_alpha = 1.0
        dots.set_alpha(.97 * point_alpha)
        glow.set_alpha(glow_alpha * point_alpha)

        title_fade = float(smoothstep(t / 1.1))
        for artist in (title_can, title_pal, title_question, subtitle):
            artist.set_alpha(title_fade)

        if t < RESET_END:
            counter.set_text(f"UP TO {MAX_N:,}  |  {total:,} PALINDROMES")
        elif t < BUILD_END:
            counter.set_text(
                f"PALINDROMES {count:,} / {total:,}   |   NUMBER {numbers[count-1]:,}")
        else:
            counter.set_text(f"PALINDROMES {total:,} / {total:,}   |   NUMBER {numbers[-1]:,}")

        if t < HOOK_END:
            caption_alpha = float(smoothstep(t / .8))
            finale.set_text("THE PATTERN IS ALREADY THERE")
            finale.set_alpha(caption_alpha)
            tagline.set_alpha(caption_alpha)
        elif t < BUILD_END:
            finale.set_alpha(0)
            tagline.set_alpha(0)
        else:
            caption_alpha = float(smoothstep((t - BUILD_END) / 2.0))
            finale.set_text(f"{total:,} PALINDROMES. ONE PATTERN.")
            finale.set_alpha(caption_alpha)
            tagline.set_alpha(caption_alpha)

        # Keep the pattern clean: labels only on recent, well-separated points
        # during the build, and only if their text will be visible.
        for label in label_artists:
            label.set_visible(False)
        if RESET_END + .4 <= t < BUILD_END and count <= 400:
            chosen = list(range(max(0, count - LABEL_RECENT), count))
            x_left, x_right = ax.get_xlim()
            y_bottom, y_top = ax.get_ylim()
            occupied = []
            for label, index in zip(label_artists, chosen):
                screen_x = (xs[index] - x_left) / (x_right - x_left) * WIDTH * ax_width
                screen_y = (ys[index] - y_bottom) / (y_top - y_bottom) * HEIGHT * ax_height
                if not (25 < screen_x < WIDTH * ax_width - 25 and
                        30 < screen_y < HEIGHT * ax_height - 35):
                    continue
                if any((screen_x - xx)**2 + (screen_y - yy)**2 < 55**2
                       for xx, yy in occupied):
                    continue
                label.xy = (float(xs[index]), float(ys[index]))
                label.set_text(str(int(numbers[index])))
                label.set_visible(True)
                occupied.append((screen_x, screen_y))

    if PREVIEW_ONLY:
        frame = min(frame_count - 1, int(PREVIEW_SECOND * FPS))
        draw_frame(frame)
        fig.savefig(PREVIEW_OUTPUT, facecolor=BG, dpi=DPI)
        plt.close(fig)
        print(f"PNG preview: {os.path.abspath(PREVIEW_OUTPUT)}", flush=True)
        print(f"Time: {time.time() - start_time:.2f} seconds", flush=True)
        try:
            from IPython.display import display, Image
            display(Image(filename=PREVIEW_OUTPUT, width=360))
        except ImportError:
            pass
        return

    if not FFMpegWriter.isAvailable():
        plt.close(fig)
        raise RuntimeError("FFmpeg not found. Install FFmpeg and add it to PATH.")
    writer = FFMpegWriter(
        fps=FPS, codec="libx264",
        extra_args=["-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart"])
    print(f"Rendering {frame_count} frames: {OUTPUT}", flush=True)
    with writer.saving(fig, OUTPUT, dpi=DPI):
        for frame in range(frame_count):
            draw_frame(frame)
            writer.grab_frame()
            if (frame + 1) % (FPS * 5) == 0:
                print(f"  {(frame + 1) // FPS:2d}/{DURATION} seconds rendered", flush=True)
    plt.close(fig)
    print(f"MP4 saved: {os.path.abspath(OUTPUT)}", flush=True)
    print(f"Total time: {(time.time() - start_time) / 60:.1f} minutes", flush=True)

    if SHOW_VIDEO_IN_NOTEBOOK:
        try:
            from IPython.display import display, Video
            display(Video(OUTPUT, embed=True, width=360))
        except ImportError:
            pass
    if DOWNLOAD_IN_COLAB:
        try:
            from google.colab import files
            files.download(OUTPUT)
        except ImportError:
            print("Local Jupyter: MP4 saved in the current working directory.")


if __name__ == "__main__":
    main()
