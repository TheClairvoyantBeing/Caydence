#!/usr/bin/env python3
"""
Caydence Industrial Long-Form Audio Production CLI.
Command-line interface to inspect catalog status and run pipelined story/audio production.

Usage:
  python run_pipeline.py --status
  python run_pipeline.py --start 6 --end 20
  python run_pipeline.py --story 7
"""

import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import argparse
from modules.pipeline import StoryCatalog, StoryType, PipelinedOrchestrator

def print_status_table(records, filter_type=None):
    title_suffix = f" [{filter_type.upper()}]" if filter_type else ""
    print("\n" + "=" * 115)
    print(f"CAYDENCE MASTER PRODUCTION STATUS (CATALOG OVERVIEW){title_suffix}")
    print("=" * 115)
    fmt = "{:<4} {:<8} {:<38} {:<8} {:<12} {:<10} {:<10} {:<12}"
    print(fmt.format("ID", "Type", "Title", "Gender", "Status", "Words", "WAV (MB)", "Voice/Cast"))
    print("-" * 115)

    completed_by_type = {StoryType.TYPE_1: 0, StoryType.TYPE_2: 0, StoryType.TYPE_3: 0}
    total_by_type = {StoryType.TYPE_1: 0, StoryType.TYPE_2: 0, StoryType.TYPE_3: 0}

    for r in records:
        st = r.get("type", StoryType.TYPE_1)
        total_by_type[st] = total_by_type.get(st, 0) + 1
        if r["status"] == "Complete":
            completed_by_type[st] = completed_by_type.get(st, 0) + 1

        voice_short = r["voice"].replace("en-US-", "").replace("Neural", "")
        title_truncated = (r["title"][:35] + "...") if len(r["title"]) > 38 else r["title"]
        print(fmt.format(
            r["sid"],
            st,
            title_truncated,
            r["gender"].capitalize(),
            r["status"],
            f"{r['words']:,}" if r['words'] else "-",
            f"{r['wav_mb']} MB" if r['wav_mb'] else "-",
            voice_short
        ))
    print("=" * 115)
    summary_parts = []
    for t in StoryType.ALL_TYPES:
        if total_by_type.get(t, 0) > 0:
            summary_parts.append(f"{t}: {completed_by_type.get(t, 0)}/{total_by_type[t]} Complete")
    print(" | ".join(summary_parts) + "\n")

def print_audit_report(audit_data, filter_type=None):
    title_suffix = f" [{filter_type.upper()}]" if filter_type else ""
    print("\n" + "=" * 90)
    print(f"CAYDENCE MASTER AUDIO AUDIT (PHYSICAL DISK INSPECTION){title_suffix}")
    print("=" * 90)

    for stype, cat in audit_data["categories"].items():
        if not cat["stories"]:
            continue
        print(f"\n>>> {stype.upper()} ({len(cat['stories'])} Master Deliverables)")
        print("-" * 90)
        fmt = "{:<40} {:<12} {:<12} {:<14} {:<10}"
        print(fmt.format("Folder / Story Name", "Duration", "Word Count", "Storage (MB)", "Format"))
        print("-" * 90)
        for s in cat["stories"]:
            dur_str = f"{s['duration_min']:.2f} min" if s['duration_sec'] > 0 else "-"
            words_str = f"{s['words']:,} w" if s['words'] > 0 else "-"
            size_str = f"{s['size_mb']:.1f} MB" if s['size_mb'] > 0 else "-"
            fmt_str = f"{s['samplerate']}Hz {s['subtype']}" if s['samplerate'] > 0 else "-"
            folder_trunc = (s['folder'][:37] + "...") if len(s['folder']) > 40 else s['folder']
            print(fmt.format(folder_trunc, dur_str, words_str, size_str, fmt_str))

        print("-" * 90)
        print(f"Subtotal: {len(cat['stories'])} Tracks | {cat['words']:,} Words | "
              f"{cat['duration_sec']/60.0:.2f} Min ({cat['duration_sec']/3600.0:.2f} Hrs) | "
              f"{cat['size_bytes']/(1024*1024*1024):.2f} GB")

    print("\n" + "=" * 90)
    print("GRAND TOTAL MASTER DELIVERABLES ACROSS CATALOG")
    print("=" * 90)
    print(f"Total Completed Stories : {audit_data['total_stories']} Stories")
    print(f"Total Master Words       : {audit_data['total_words']:,} Words")
    print(f"Total Master Audio Time  : {audit_data['total_duration_sec']/60.0:.2f} Minutes ({audit_data['total_duration_sec']/3600.0:.2f} Hours)")
    print(f"Total Storage on Disk    : {audit_data['total_size_bytes']/(1024*1024*1024):.2f} GB")
    print("=" * 90 + "\n")

def main():
    parser = argparse.ArgumentParser(
        description="Caydence Industrial Long-Form Audio Generator (Type 1, Type 2, Type 3)"
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Display status table across catalog story types"
    )
    parser.add_argument(
        "--audit", action="store_true",
        help="Run physical disk audit across all produced master tracks using soundfile"
    )
    parser.add_argument(
        "--type", type=str, default=None,
        help="Story production type: 1 (Reddit Confessions), 2 (Survival Rules), 3 (DUA Case Files)"
    )
    parser.add_argument(
        "--start", type=int, default=1,
        help="Starting Story ID (default: 1)"
    )
    parser.add_argument(
        "--end", type=int, default=None,
        help="Ending Story ID (default: full catalog size for selected type)"
    )
    parser.add_argument(
        "--story", type=int, default=None,
        help="Produce a specific single Story ID"
    )
    parser.add_argument(
        "--max-catalog", type=int, default=100,
        help="Catalog range to inspect for status (default: 100)"
    )

    args = parser.parse_args()
    orchestrator = PipelinedOrchestrator()

    normalized_type = StoryType.normalize(args.type) if args.type else None

    if args.audit:
        audit_data = orchestrator.audit_catalog(story_type=normalized_type)
        print_audit_report(audit_data, filter_type=normalized_type)
        return

    if args.status:
        records = orchestrator.get_status_report(max_sid=args.max_catalog, story_type=normalized_type)
        print_status_table(records, filter_type=normalized_type)
        return

    target_type = normalized_type or StoryType.TYPE_1
    catalog_limit = StoryCatalog.get_catalog_size(target_type)

    if args.story is not None:
        start_sid = args.story
        end_sid = args.story
    else:
        start_sid = args.start
        end_sid = min(args.end, catalog_limit) if args.end is not None else catalog_limit

    print(f"\n[CLI] Starting pipelined execution for [{target_type}] Story #{start_sid} through Story #{end_sid} (Catalog Max: {catalog_limit})...")
    orchestrator.run_pipeline(start_sid=start_sid, end_sid=end_sid, story_type=target_type)

if __name__ == "__main__":
    main()
