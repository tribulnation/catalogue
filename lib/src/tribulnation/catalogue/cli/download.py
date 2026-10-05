from pathlib import Path
import typer

DEFAULT_URL = 'https://catalogue.tribulnation.com/data.zip'
MARKER = '.catalogue.json'
"""Records which archive a downloaded folder was extracted from."""

def download(
  path: Path | None = typer.Argument(None, help='Folder to extract the catalogue to; omit to only refresh the local cache'),
  url: str = typer.Option(DEFAULT_URL, '--url', help='URL to download the catalogue from'),
  refresh: bool = typer.Option(False, '--refresh', help='Download unconditionally instead of asking whether it changed'),
):
  """Downloads the catalogue, or brings an earlier download up to date.

  Like `Catalogue.load()`, it keeps the archive in ~/.cache/tribulnation and asks the
  site whether it changed (ETag / Last-Modified); the folder is only re-extracted when
  it did. A folder is only replaced if it is empty or holds an earlier download.
  """
  import io
  import json
  import os
  import shutil
  import sys
  import urllib.error
  import zipfile
  from tribulnation.catalogue.data.cache import ArchiveCache

  if path is not None and path.exists():
    is_download = path.is_dir() and ((path / MARKER).is_file() or (path / 'assets').is_dir())
    if not is_download and not (path.is_dir() and not any(path.iterdir())):
      typer.echo(f'{path} exists and is not a catalogue download; refusing to replace it', file=sys.stderr)
      raise typer.Exit(1)

  cache = ArchiveCache(url=url)
  try:
    digest = cache.load(check=True, force=refresh).digest
  except (urllib.error.URLError, OSError, ValueError, zipfile.BadZipFile) as e:
    # Only raised without a cached copy to fall back to
    typer.echo(f'Cannot download the catalogue from {url}: {e!r}', file=sys.stderr)
    raise typer.Exit(1)
  assert digest is not None

  if path is None:
    typer.echo(f'Catalogue cache at {cache.archive_path} is up to date ({digest[:12]})')
    return

  try:
    current = json.loads((path / MARKER).read_bytes()).get('sha256')
  except (OSError, ValueError, AttributeError):
    current = None
  if current == digest and not refresh:
    typer.echo(f'Catalogue at {path} is already up to date ({digest[:12]})')
    return

  data = cache.read_archive()
  assert data is not None
  # Extract next to the target and swap it in, so a failure leaves the old copy intact.
  path.parent.mkdir(parents=True, exist_ok=True)
  tmp = path.with_name(f'.{path.name}.{os.getpid()}.tmp')
  old = path.with_name(f'.{path.name}.{os.getpid()}.old')
  try:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
      zf.extractall(tmp)
    (tmp / MARKER).write_text(json.dumps({'url': url, 'sha256': digest}, indent=2))
    if path.exists():
      path.rename(old)
    tmp.rename(path)
  finally:
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.rmtree(old, ignore_errors=True)
  typer.echo(f'Catalogue {digest[:12]} extracted to {path}')
