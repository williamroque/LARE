from __future__ import annotations

from pathlib import Path

import questionary
from rich.table import Table

from lare.config import (
    ImageConfig,
    LabelConfig,
    LareConfig,
    PathsConfig,
    RulesConfig,
    write_config,
)
from lare.console import console, log_step, log_success


class q:
    style = questionary.Style([
        ('qmark', 'fg:#06b6d4 bold'),
        ('question', 'bold'),
        ('answer', 'fg:#06b6d4'),
        ('pointer', 'fg:#06b6d4 bold'),
        ('highlighted', 'fg:#06b6d4 bold'),
        ('selected', 'fg:#06b6d4'),
        ('separator', 'fg:#cc5454'),
        ('instruction', 'fg:#858585'),
        ('text', ''),
        ('disabled', 'fg:#858585 italic')
    ])
    
    @classmethod
    def path(cls, *args, **kwargs):
        return questionary.path(*args, style=cls.style, qmark='◆', **kwargs)
        
    @classmethod
    def text(cls, *args, **kwargs):
        return questionary.text(*args, style=cls.style, qmark='◆', **kwargs)
        
    @classmethod
    def confirm(cls, *args, **kwargs):
        return questionary.confirm(*args, style=cls.style, qmark='◆', **kwargs)
        
    @classmethod
    def select(cls, *args, **kwargs):
        return questionary.select(*args, style=cls.style, qmark='◆', pointer='❯', **kwargs)


def _read_csv_headers(csv_path: str) -> list[str]:
    with open(csv_path) as f:
        header_line = f.readline().strip()
    return [h.strip().strip('"').strip("'") for h in header_line.split(',')]


def _show_columns(headers: list[str]) -> None:
    from rich import box
    console.print()
    table = Table(title='Detected CSV Columns', box=box.SIMPLE, show_edge=False)
    table.add_column('#', style='dim')
    table.add_column('Column Name', style='cyan')
    for i, h in enumerate(headers):
        table.add_row(str(i), h)
    console.print(table)
    console.print()


def run_wizard() -> LareConfig:
    console.print('\n[bold cyan]LARE[/] Configuration Wizard\n')

    csv_path = q.path(
        'Path to your source CSV file:',
        only_directories=False,
    ).ask()

    if not csv_path or not Path(csv_path).exists():
        console.print('[red]CSV file not found[/]')
        raise SystemExit(1)

    headers = _read_csv_headers(csv_path)
    _show_columns(headers)

    project = q.text(
        'Output database filename:',
        default='project.lare',
    ).ask()

    has_image_dir = q.confirm(
        'Are image paths relative to a base directory?',
        default=False,
    ).ask()

    image_directory = None
    if has_image_dir:
        image_directory = q.path(
            'Base image directory:',
            only_directories=True,
        ).ask()

    id_column = q.select(
        'Which column contains the entry identifier?',
        choices=headers,
    ).ask()

    id_display_method = q.select(
        'How should entry IDs be displayed?',
        choices=['raw', 'basename', 'stem'],
    ).ask()

    has_filter = q.confirm(
        'Apply a SQL filter expression?',
        default=False,
    ).ask()

    filter_method = None
    if has_filter:
        console.print(
            '[dim]Example: GREATEST(sim_class_0, sim_class_1) > 0.1[/]'
        )
        filter_method = q.text(
            'SQL filter expression:',
        ).ask()

    console.print(
        '[dim]Example: GREATEST(sim_class_0, sim_class_1, sim_class_2)[/]'
    )
    ranking_score = q.text(
        'SQL expression for ranking score:',
    ).ask()

    images: list[ImageConfig] = []
    while True:
        console.print(f'\n[bold]Image #{len(images) + 1}[/]')

        img_column = q.select(
            'Column containing the image path:',
            choices=headers,
        ).ask()

        img_title = q.text('Display title for this image:').ask()

        img_format = q.select(
            'Image format:',
            choices=['fits', 'png', 'jpg', 'jpeg', 'tiff'],
        ).ask()

        stretching = None
        min_thresh = 0.5
        max_thresh = 99.5
        if img_format == 'fits':
            stretching = q.select(
                'Stretching method:',
                choices=['asinh', 'linear', 'sqrt', 'log', 'power'],
                default='asinh',
            ).ask()
            min_thresh = float(q.text(
                'Min percentile threshold:',
                default='0.5',
            ).ask())
            max_thresh = float(q.text(
                'Max percentile threshold:',
                default='99.5',
            ).ask())

        subdirectory = None
        if image_directory:
            has_subdir = q.confirm(
                'Does this image type live in a subdirectory?',
                default=False,
            ).ask()
            if has_subdir:
                subdirectory = q.text(
                    'Subdirectory name:',
                ).ask()

        images.append(ImageConfig(
            column=img_column,
            title=img_title,
            format=img_format,
            stretching=stretching,
            min_threshold=min_thresh,
            max_threshold=max_thresh,
            subdirectory=subdirectory,
        ))

        if not q.confirm('Add another image?', default=False).ask():
            break

    labels: list[LabelConfig] = []
    used_shortcuts: set[str] = set()
    while True:
        console.print(f'\n[bold]Label #{len(labels) + 1}[/]')

        label_column = q.select(
            'Column containing the prediction score:',
            choices=headers,
        ).ask()

        label_title = q.text('Display title for this label:').ask()

        while True:
            shortcut = q.text(
                'Keyboard shortcut (single letter):',
            ).ask()
            if shortcut and len(shortcut) == 1 and shortcut.isalpha():
                if shortcut.lower() in used_shortcuts:
                    console.print(
                        f'[red]Shortcut "{shortcut}" already used[/]'
                    )
                    continue
                break
            console.print('[red]Must be a single alphabetic character[/]')

        used_shortcuts.add(shortcut.lower())
        labels.append(LabelConfig(
            label=label_column,
            title=label_title,
            shortcut=shortcut.lower(),
        ))

        if not q.confirm('Add another label?', default=False).ask():
            break

    config = LareConfig(
        paths=PathsConfig(
            project=project,
            source_csv=csv_path,
            image_directory=image_directory,
        ),
        rules=RulesConfig(
            filter_method=filter_method,
            ranking_score=ranking_score,
            id_column=id_column,
            id_display_method=id_display_method,
        ),
        images=images,
        labels=labels,
    )

    from lare.config import config_to_dict
    from lare.console import print_config_table

    print_config_table(config_to_dict(config))

    if q.confirm('Write this configuration?', default=True).ask():
        output_path = 'lare_config.toml'
        write_config(config, output_path)
        log_success(f'Configuration written to {output_path}')

    return config
