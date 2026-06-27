from pathlib import Path
import typer

def download(
  path: Path = typer.Argument(..., help='Path to download the catalogue to'),
  url: str = typer.Option('https://catalogue.tribulnation.com/data.zip', '--url', help='URL to download the catalogue from'),
):
  """Downloads and unzips the catalogue to the given path."""
  import zipfile
  import urllib.request
  import io
  import shutil
  import sys

  if path.exists():
    typer.echo(f'Path {path} already exists', file=sys.stderr)
    raise typer.Exit(1)

  with urllib.request.urlopen(url) as response:
    data = response.read()
  with zipfile.ZipFile(io.BytesIO(data)) as zf:
    zf.extractall(path)
  typer.echo(f'Catalogue downloaded and unzipped to {path}', file=sys.stdout)