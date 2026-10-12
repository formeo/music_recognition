# Changelog

## Unreleased

### Added
- Tags are written and read for FLAC, M4A, OGG and Opus, not only MP3. Already tagged files in these formats
  are skipped on the next run instead of being sent to Shazam again.

### Fixed
- `--concurrent` / `max_concurrent` had no effect: files were processed one by one. Files now run concurrently,
  with at most `--concurrent` Shazam requests in flight (default 5). Lower it if Shazam starts rejecting requests.

## 1.2.2

### Changed (behavior)
- `--convert` is now **off by default**. Conversion keeps the source file; pass `--delete-source` to remove it.
  Previously every non-MP3 file was transcoded to MP3 and the original (including lossless FLAC/WAV) was deleted.
- `MusicRecognizer.process_directory(convert_formats=...)` now defaults to `False`; new `delete_source` argument.
- Missing album is left empty instead of `"Unknown Album"` (no such tag, no such folder with `--organize`).

### Fixed
- Recognized files were renamed to `name (1).mp3` on every run, even without `--rename`.
- `--rename` replaced the real extension with `.mp3` (a FLAC file became `Artist - Title.mp3`).
- Genre tag contained "Open in Apple Music" instead of the actual genre.
- Cache hits crashed with `TypeError`, which broke the `--dry-run` → real run workflow.
- Tag writing for non-MP3 files now logs a clear "not supported" warning instead of an error.
- Package failed to import on Python 3.13+ (`audioop` removed); `audioop-lts` is now a dependency there.
- Single source of truth for the version (`pyproject.toml`).

### Removed
- `api.py`: imported a module that no longer exists.
