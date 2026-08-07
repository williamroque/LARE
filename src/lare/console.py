from __future__ import annotations

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def log_step(msg: str) -> None:
    console.print(f'[bold cyan]▸[/] {msg}')


def log_success(msg: str) -> None:
    console.print(f'[bold green]✓[/] {msg}')


def log_warning(msg: str) -> None:
    console.print(f'[bold yellow]⚠[/] {msg}')


def log_error(msg: str) -> None:
    console.print(f'[bold red]✗[/] {msg}')
    raise click.Abort()


def print_config_table(config_dict: dict) -> None:
    table = Table(title='Project Configuration', show_lines=True)
    table.add_column('Parameter', style='cyan')
    table.add_column('Value', style='white')

    def _flatten(d: dict, prefix: str = '') -> None:
        for key, val in d.items():
            full_key = f'{prefix}.{key}' if prefix else key
            if isinstance(val, dict):
                _flatten(val, full_key)
            elif isinstance(val, list):
                for i, item in enumerate(val):
                    if isinstance(item, dict):
                        _flatten(item, f'{full_key}[{i}]')
                    else:
                        table.add_row(f'{full_key}[{i}]', str(item))
            else:
                table.add_row(full_key, str(val))

    _flatten(config_dict)
    console.print(table)


def print_audit_banner(labeled: int, total: int) -> None:
    if labeled < total:
        console.print(Panel(
            f'Exported {labeled} entries.\n'
            f'[bold yellow]Alert:[/] You have only audited '
            f'{labeled}/{total} filtered entries in this project database!',
            title='⚠ Audit Warning',
            border_style='yellow',
        ))
    else:
        console.print(Panel(
            f'Exported {labeled}/{total} entries — full audit complete.',
            title='✓ Audit Complete',
            border_style='green',
        ))


def print_creation_summary(
    rows_before: int,
    rows_after: int,
    label_count: int,
    project_path: str,
) -> None:
    table = Table(title='Project Created', show_lines=True)
    table.add_column('Metric', style='cyan')
    table.add_column('Value', style='white')
    table.add_row('Source rows', str(rows_before))
    table.add_row('Queued rows (after filter)', str(rows_after))
    table.add_row('Labels registered', str(label_count))
    table.add_row('Database path', project_path)
    console.print(table)
