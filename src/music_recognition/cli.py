#!/usr/bin/env python3
"""
Music Recognition CLI

Identify unknown music files using Shazam, write ID3 tags, rename and organize.

Examples:
    music-recognize /path/to/music
    music-recognize /path/to/music --rename
    music-recognize /path/to/music --organize --output /sorted
    music-recognize track.mp3 --dry-run
"""

import argparse
import asyncio
import json
import csv
import sys
import logging
from pathlib import Path

from .core import (
    MusicRecognizer,
    ProcessingStats,
    ProcessingResult,
    setup_logging,
    __version__,
)


# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def supports_color() -> bool:
    """Check if terminal supports colors."""
    if sys.platform == 'win32':
        try:
            import os
            return os.environ.get('TERM') is not None or 'WT_SESSION' in os.environ
        except Exception:
            return False
    return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()


USE_COLORS = supports_color()


def colored(text: str, color: str) -> str:
    """Apply color to text if supported."""
    if USE_COLORS:
        return f"{color}{text}{Colors.END}"
    return text


def print_header():
    """Print application header."""
    header = f"""
╔══════════════════════════════════════════════════════════════╗
║  🎵 Music Recognition v{__version__:<40} ║
║  Identify • Tag • Rename • Organize                          ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(colored(header, Colors.CYAN))


def print_result(result: ProcessingResult, verbose: bool = False):
    """Print single file result."""
    filename = Path(result.original_path).name
    
    if result.status == "success":
        info = result.track_info
        print(f"  {colored('✓', Colors.GREEN)} {colored(info.artist, Colors.BOLD)} - {info.title}")
        if verbose and info.album != "Unknown Album":
            print(f"    Album: {info.album}")
    elif result.status == "skipped":
        info = result.track_info
        if info:
            print(f"  {colored('○', Colors.YELLOW)} {info.artist} - {info.title} (skipped)")
        else:
            print(f"  {colored('○', Colors.YELLOW)} {filename} (skipped)")
    else:
        error = f" - {result.error}" if result.error else ""
        print(f"  {colored('✗', Colors.RED)} {filename}{error}")


def print_stats(stats: ProcessingStats):
    """Print processing statistics."""
    print()
    print(colored("═" * 50, Colors.CYAN))
    print(colored("  SUMMARY", Colors.BOLD))
    print(colored("═" * 50, Colors.CYAN))
    print(f"  Total files:    {stats.total}")
    print(f"  Processed:      {stats.processed}")
    print(f"  {colored('Recognized:', Colors.GREEN)}    {stats.recognized}")
    print(f"  {colored('Failed:', Colors.RED)}        {stats.failed}")
    print(f"  {colored('Skipped:', Colors.YELLOW)}      {stats.skipped}")
    print(f"  Success rate:   {stats.success_rate:.1f}%")
    print(f"  Duration:       {stats.duration_seconds:.1f}s")
    print(colored("═" * 50, Colors.CYAN))


def progress_callback(current: int, total: int, result: ProcessingResult):
    """Callback for progress reporting."""
    percentage = (current / total) * 100
    filename = Path(result.original_path).name[:30]
    
    # Status indicator
    if result.status == "success":
        status = colored("✓", Colors.GREEN)
    elif result.status == "skipped":
        status = colored("○", Colors.YELLOW)
    else:
        status = colored("✗", Colors.RED)
    
    print(f"\r[{current}/{total}] {percentage:5.1f}% {status} {filename:<30}", end="", flush=True)
    
    if current == total:
        print()  # New line at the end


def export_json(stats: ProcessingStats, filepath: str):
    """Export results to JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(stats.to_dict(), f, indent=2, ensure_ascii=False)
    print(f"Results exported to: {filepath}")


def export_csv(stats: ProcessingStats, filepath: str):
    """Export results to CSV file."""
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['original_path', 'final_path', 'status', 'artist', 'title', 'album', 'error']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in stats.results:
            row = {
                'original_path': result.original_path,
                'final_path': result.final_path,
                'status': result.status,
                'artist': result.track_info.artist if result.track_info else '',
                'title': result.track_info.title if result.track_info else '',
                'album': result.track_info.album if result.track_info else '',
                'error': result.error,
            }
            writer.writerow(row)
    
    print(f"Results exported to: {filepath}")


async def main_async(args: argparse.Namespace) -> int:
    """Main async function."""
    
    # Validate path
    path = Path(args.path)
    if not path.exists():
        print(f"Error: Path not found: {args.path}", file=sys.stderr)
        return 1
    
    # Determine output options
    output_dir = None
    report_file = None
    
    if args.output:
        if args.output.endswith('.json') or args.output.endswith('.csv'):
            report_file = args.output
        else:
            output_dir = args.output
    
    # Create recognizer
    recognizer = MusicRecognizer(
        max_concurrent=args.concurrent,
        delay_between_requests=args.delay,
    )
    
    # Print what we're doing
    actions = []
    if args.write_tags:
        actions.append("tag")
    if args.rename:
        actions.append("rename")
    if args.organize:
        actions.append("organize")
    
    action_str = ", ".join(actions) if actions else "recognize only"
    
    if args.dry_run:
        print(colored(f"[DRY RUN] ", Colors.YELLOW), end="")
    
    print(f"Processing: {path}")
    print(f"Actions: {action_str}")
    print()
    
    # Process
    if path.is_file():
        # Single file
        result = await recognizer.process_file(
            file_path=str(path),
            output_dir=output_dir,
            write_tags=args.write_tags,
            rename=args.rename,
            rename_template=args.template,
            organize=args.organize,
            overwrite_tags=args.overwrite,
            skip_recognized=not args.force,
            dry_run=args.dry_run,
        )
        
        print_result(result, verbose=args.verbose)
        
        if result.status == "success":
            if result.final_path != result.original_path:
                print(f"  → {result.final_path}")
            return 0
        return 1
    
    else:
        # Directory
        callback = progress_callback if not args.quiet and not args.verbose else None
        
        stats = await recognizer.process_directory(
            source_dir=str(path),
            output_dir=output_dir,
            write_tags=args.write_tags,
            rename=args.rename,
            rename_template=args.template,
            organize=args.organize,
            overwrite_tags=args.overwrite,
            skip_recognized=not args.force,
            convert_formats=args.convert,
            dry_run=args.dry_run,
            progress_callback=callback,
        )
        
        # Print detailed results if verbose
        if args.verbose:
            print("\nResults:")
            for result in stats.results:
                print_result(result, verbose=True)
        
        # Print statistics
        if not args.quiet:
            print_stats(stats)
        
        # Export report
        if report_file:
            if report_file.endswith('.json'):
                export_json(stats, report_file)
            elif report_file.endswith('.csv'):
                export_csv(stats, report_file)
        
        return 0 if stats.failed == 0 else 1


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='music-recognize',
        description='Identify unknown music files using Shazam, write ID3 tags, rename and organize.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s /music                         Recognize and tag all files
  %(prog)s /music --rename                Also rename to "Artist - Title.mp3"
  %(prog)s /music --organize -o /sorted   Organize into Artist/Album folders
  %(prog)s track.mp3 --dry-run            Preview without changes
  %(prog)s /music --output report.json    Export results to JSON
  %(prog)s /music --template "{artist}/{album}/{title}.mp3"
  
Templates:
  Available placeholders: {artist}, {title}, {album}, {year}, {genre}, {track}
        '''
    )
    
    # Positional arguments
    parser.add_argument(
        'path',
        help='File or directory to process'
    )
    
    # Output options
    parser.add_argument(
        '-o', '--output',
        metavar='PATH',
        help='Output directory or report file (.json/.csv)'
    )
    
    # Processing options
    parser.add_argument(
        '--tag', '--write-tags',
        action='store_true',
        default=True,
        dest='write_tags',
        help='Write ID3 tags (default: enabled)'
    )
    parser.add_argument(
        '--no-tag',
        action='store_false',
        dest='write_tags',
        help='Do not write ID3 tags'
    )
    parser.add_argument(
        '--rename',
        action='store_true',
        help='Rename files based on metadata'
    )
    parser.add_argument(
        '--template',
        default='{artist} - {title}.mp3',
        metavar='TPL',
        help='Filename template (default: "{artist} - {title}.mp3")'
    )
    parser.add_argument(
        '--organize',
        action='store_true',
        help='Organize files into Artist/Album folders'
    )
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing ID3 tags'
    )
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Process files even if they have valid tags'
    )
    parser.add_argument(
        '--convert',
        action='store_true',
        default=True,
        help='Convert non-MP3 files to MP3 (default: enabled)'
    )
    parser.add_argument(
        '--no-convert',
        action='store_false',
        dest='convert',
        help='Do not convert non-MP3 files'
    )
    
    # Performance options
    parser.add_argument(
        '--concurrent', '-c',
        type=int,
        default=5,
        metavar='N',
        help='Max concurrent requests (default: 5)'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=0.5,
        metavar='SEC',
        help='Delay between requests in seconds (default: 0.5)'
    )
    
    # Output options
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Preview changes without modifying files'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Minimal output'
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    if args.quiet:
        log_level = logging.WARNING
    elif args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    
    setup_logging(level=log_level)
    
    # Print header
    if not args.quiet:
        print_header()
    
    # Run
    try:
        return asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 130


if __name__ == '__main__':
    sys.exit(main())
