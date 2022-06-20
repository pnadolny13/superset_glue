from superset_glue.sdk.base import Base
import typer
import json
import os
import subprocess

class Superset(Base):

    def pre_run(self, executable, run_dir):
        typer.echo(f"Executable in Use: {executable}")
        env = self._get_env(run_dir)
        self._pre_config(env, self._get_config_from_env(env))
        self._upgrade_db(executable, env)
        self._init_superset(executable, env)

    def post_run(self, executable, run_dir):
        typer.echo(f"Executable in Use: {executable}")
        env = self._get_env(run_dir)
        self._cleanup(env)

    def _get_config_from_env(self, env):
        config = {}
        for env_key, env_value in env.items():
            if env_key.startswith('SUPERSET_GLUE_'):
                config[(env_key.split('SUPERSET_GLUE_')[1]).lower()] = env_value
        return config

    def _get_env(self, run_dir):
        env = dict(os.environ)
        env["SUPERSET_HOME"] = str(run_dir)
        env["SUPERSET_CONFIG_PATH"] = str(os.path.join(run_dir, 'superset_config.py'))
        env["FLASK_APP"] = "superset"
        return env

    def _cleanup(self, env):
        typer.echo(f"Cleaning up Superset")
        os.remove(env["SUPERSET_CONFIG_PATH"])

    def _pre_config(self, env, config):
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

    def _upgrade_db(self, executable, env):
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

    def _init_superset(self, executable, env):
        typer.echo(f"Init Superset")
        subprocess.run(
            [
                executable,
                'init'
            ],
            env=env,
            check=True
        )