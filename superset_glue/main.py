import typer
from superset_glue.superset import Superset

app = typer.Typer()


@app.command()
def pre_run(executable: str, run_dir: str):
    """
    Run plugin pre-confg glue code
    """
    Superset().pre_run(executable, run_dir)


@app.command()
def post_run(executable: str, run_dir: str):
    """
    Run plugin post-config tear down glue code
    """
    Superset().post_run(executable, run_dir)


if __name__ == "__main__":
    app()
