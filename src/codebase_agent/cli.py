import json

import typer

from .config import get_settings
from .service import CodebaseAgent

app = typer.Typer(help="Index and question a React/TypeScript codebase.")


@app.command()
def index(path: str = ".") -> None:
    result = CodebaseAgent(get_settings()).index(path)
    typer.echo(result.model_dump_json(indent=2))


@app.command("map")
def map_repository(path: str = ".") -> None:
    result = CodebaseAgent(get_settings()).repository_map(path)
    typer.echo(json.dumps(result, indent=2))


@app.command()
def ask(question: str, limit: int = 8) -> None:
    result = CodebaseAgent(get_settings()).ask(question, limit)
    typer.echo(json.dumps(result.model_dump(), indent=2))


if __name__ == "__main__":
    app()
