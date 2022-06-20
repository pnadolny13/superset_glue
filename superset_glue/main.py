import typer
import json
import os
import subprocess

app = typer.Typer()


def inject_env(env, run_dir):
    env["SUPERSET_HOME"] = str(run_dir)
    env["SUPERSET_CONFIG_PATH"] = str(os.path.join(run_dir, 'superset_config.py'))
    env["FLASK_APP"] = "superset"
    return env

def pre_config(env, config):
    config_script_lines = [
            "import sys",
            "module = sys.modules[__name__]",
            f"config = {str(config)}",
            "for key, value in config.items():",
            "    if key.isupper():",
            "        setattr(module, key, value)",
        ]

    # TODO: this doesnt work yet
    custom_config_filename = ''
    if custom_config_filename:
        project_root = ""
        custom_config_path = os.path.join(project_root, custom_config_filename)

        if custom_config_path.exists():
            config_script_lines.extend(
                [
                    "import imp",
                    f'custom_config = imp.load_source("superset_config", "{str(custom_config_path)}")',
                    "for key in dir(custom_config):",
                    "    if key.isupper():",
                    "        setattr(module, key, getattr(custom_config, key))",
                ]
            )

            typer.echo(f"Merged in config from {custom_config_path}")
        else:
            raise Exception(
                f"Could not find config file {custom_config_path}"
            )

    config_path = env["SUPERSET_CONFIG_PATH"]
    with open(config_path, "w") as config_file:
        config_file.write("\n".join(config_script_lines))
    typer.echo(f"Created configuration at {config_path}")

def update_db(executable, env):
    typer.echo(f"Upgrade Superset db")
    subprocess.run(
        [
            executable,
            'db',
            'upgrade'
        ],
        env=env,
        check=True
    )

def init_superset(executable, env):
    typer.echo(f"Init Superset")
    subprocess.run(
        [
            executable,
            'init'
        ],
        env=env,
        check=True
    )


def run_plugin(executable, env, command):
    typer.echo(f"Running Superset")
    subprocess.run(
        [
            executable,
            command
        ],
        env=env,
        check=True
    )

def cleanup(env):
    typer.echo(f"Cleaning up Superset")
    os.remove(env["SUPERSET_CONFIG_PATH"])

@app.command()
def wrapper(command: str, executable: str, run_dir: str, config: str, env: str):
    """
    Run plugin glue code
    """
    typer.echo(f"Running Meltano Command: {command}")
    typer.echo(f"Executable in Use: {executable}")
    typer.echo(f"Env in Use: {env} {json.loads(env).get('abc')}")
    enriched_env = inject_env(json.loads(env), run_dir)
    pre_config(enriched_env, config)
    init_superset(executable, enriched_env)
    update_db(executable, enriched_env)
    run_plugin(executable, enriched_env, command)
    cleanup(enriched_env)


@app.command()
def pre_run(executable: str, run_dir: str, config: str, env: str):
    """
    Run plugin pre-confg glue code
    """
    typer.echo(f"Executable in Use: {executable}")
    typer.echo(f"Env in Use: {env} {json.loads(env).get('abc')}")
    enriched_env = inject_env(json.loads(env), run_dir)
    pre_config(enriched_env, config)
    update_db(executable, enriched_env)
    init_superset(executable, enriched_env)

@app.command()
def post_run(executable: str, run_dir: str, config: str, env: str):
    """
    Run plugin post-config tear down glue code
    """
    typer.echo(f"Executable in Use: {executable}")
    typer.echo(f"Env in Use: {env} {json.loads(env).get('abc')}")
    enriched_env = inject_env(json.loads(env), run_dir)
    cleanup(enriched_env)

if __name__ == "__main__":
    app()
