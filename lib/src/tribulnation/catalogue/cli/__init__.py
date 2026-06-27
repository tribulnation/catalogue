import typer

from .download import download

app = typer.Typer()
app.command()(download)

@app.callback()
def main():
  ...