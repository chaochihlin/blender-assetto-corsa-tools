# Lightweight profiler for moppius KN5 export pipeline.
#
# Usage from a wrapper script:
#     import os
#     os.environ["MOPPIUS_PROFILE"] = "1"
#     from blender_assetto_corsa_tools.exporter import profiler
#     profiler.start()
#     # ... run TextureWriter / MaterialWriter / NodeWriter ...
#     profiler.report()
#
# When MOPPIUS_PROFILE is unset/false, all section() calls are zero-overhead
# no-ops so this module is safe to leave instrumented in upstream code.

import os
import time
from contextlib import contextmanager
from collections import defaultdict


def _is_enabled():
    return os.environ.get("MOPPIUS_PROFILE", "").lower() in ("1", "true", "yes", "on")


_stats = defaultdict(lambda: {"count": 0, "total": 0.0})
_start_wall = None


def start():
    """Reset stats and mark wall-clock start. Safe to call when disabled."""
    global _start_wall
    _stats.clear()
    _start_wall = time.perf_counter()


@contextmanager
def section(name):
    """Time a code block. Zero overhead when MOPPIUS_PROFILE is not set."""
    if not _is_enabled():
        yield
        return
    t0 = time.perf_counter()
    try:
        yield
    finally:
        dt = time.perf_counter() - t0
        s = _stats[name]
        s["count"] += 1
        s["total"] += dt


def add(name, seconds):
    """Manually add a timing entry (for code paths where 'with' is awkward)."""
    if not _is_enabled():
        return
    s = _stats[name]
    s["count"] += 1
    s["total"] += seconds


def _format_report(total_wall):
    lines = []
    lines.append("=" * 78)
    lines.append(f"MOPPIUS EXPORT PROFILE  (wall {total_wall:.2f}s)")
    lines.append("=" * 78)
    lines.append(f"{'section':<48s} {'count':>8s} {'total':>10s} {'avg':>10s}")
    lines.append("-" * 78)
    rows = sorted(_stats.items(), key=lambda kv: kv[1]["total"], reverse=True)
    for name, s in rows:
        avg_ms = (s["total"] / s["count"] * 1000.0) if s["count"] else 0.0
        lines.append(f"{name:<48s} {s['count']:>8d} {s['total']:>9.3f}s {avg_ms:>8.2f}ms")
    lines.append("=" * 78)
    measured = sum(s["total"] for s in _stats.values())
    unaccounted = total_wall - measured
    lines.append(f"measured: {measured:.2f}s   unaccounted: {unaccounted:.2f}s")
    lines.append("=" * 78)
    return "\n".join(lines)


def report(out_path=None):
    """Print profile report and (optionally) also write to a file.

    out_path defaults to env MOPPIUS_PROFILE_OUT, else None (no file).
    No-op when disabled or never started.
    """
    if not _is_enabled():
        return
    if _start_wall is None:
        print("[moppius profiler] report() called before start()")
        return
    total_wall = time.perf_counter() - _start_wall
    text = _format_report(total_wall)
    print()
    print(text)
    if out_path is None:
        out_path = os.environ.get("MOPPIUS_PROFILE_OUT")
    if out_path:
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(text + "\n")
            print(f"[moppius profiler] wrote {out_path}")
        except Exception as e:
            print(f"[moppius profiler] failed to write {out_path}: {e}")
