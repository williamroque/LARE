from __future__ import annotations

import webbrowser
from pathlib import Path

import click

from lare.console import console, log_error, log_step, log_success


@click.group()
@click.version_option(package_name='lare')
def main():
    '''LARE — Label And Review Engine'''
    pass


@main.command()
@click.argument('csv_file', required=False)
@click.option('--config', 'config_path', type=click.Path(exists=True), help='Path to lare_config.toml')
@click.option('--no-project', is_flag=True, help='Author config only, skip database creation')
def create(csv_file: str | None, config_path: str | None, no_project: bool):
    '''Initialize a new LARE project from a CSV dataset.'''
    import questionary
    from rich.progress import Progress

    from lare.config import LareConfig, load_config, config_to_dict
    from lare.console import print_config_table, print_creation_summary
    from lare.database import create_database
    from lare.interactive import run_wizard
    from lare.pipeline import load_and_process

    config: LareConfig | None = None

    if config_path:
        log_step(f'Loading config from {config_path}')
        config = load_config(config_path)
    elif Path('lare_config.toml').exists():
        use_existing = questionary.confirm(
            'Found existing lare_config.toml. Use this to initialize the project?',
            default=True,
        ).ask()
        if use_existing:
            config = load_config('lare_config.toml')
        else:
            config = run_wizard()
    else:
        config = run_wizard()

    if config is None:
        log_error('No configuration provided')

    print_config_table(config_to_dict(config))

    if no_project:
        log_success('Configuration authored — skipping database creation (--no-project)')
        return

    project_path = config.paths.project
    if Path(project_path).exists():
        log_error(
            f'File risk: {project_path} already exists. '
            'Overwriting is blocked.'
        )

    source_csv = csv_file or config.paths.source_csv

    if not source_csv or not Path(source_csv).exists():
        log_error(f'Source CSV not found: {source_csv}')

    with Progress(console=console) as progress:
        task = progress.add_task('Processing pipeline...', total=None)
        df, rows_before = load_and_process(config, source_csv)
        progress.update(task, completed=True)

    log_step(f'Creating database: {project_path}')

    with Progress(console=console) as progress:
        task = progress.add_task('Writing database...', total=None)
        create_database(project_path, config, df)
        progress.update(task, completed=True)

    print_creation_summary(
        rows_before=rows_before,
        rows_after=df.height,
        label_count=len(config.labels),
        project_path=project_path,
    )


@main.command()
@click.argument('project', type=click.Path(exists=True))
@click.option('--port', default=8741, type=int, help='Server port (default: 8741)')
def run(project: str, port: int):
    '''Launch the LARE review interface.'''
    import uvicorn
    from lare.server import create_app

    log_step(f'Opening project: {project}')

    app = create_app(project)

    url = f'http://127.0.0.1:{port}'
    log_step(f'Starting server at {url}')

    webbrowser.open(url)

    uvicorn.run(app, host='127.0.0.1', port=port, log_level='warning')


@main.command()
@click.argument('project', type=click.Path(exists=True))
@click.option('--strategy', type=click.Choice(['csv', 'copy']), required=True, help='Export strategy')
@click.option('--output', required=True, type=click.Path(), help='Output path')
def export(project: str, strategy: str, output: str):
    '''Export classified entries from a LARE project.'''
    from lare.export import export_copy, export_csv

    log_step(f'Exporting from {project} using strategy: {strategy}')

    if strategy == 'csv':
        export_csv(project, output)
    elif strategy == 'copy':
        export_copy(project, output)


if __name__ == '__main__':
    main()
