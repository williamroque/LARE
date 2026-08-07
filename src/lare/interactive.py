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


def _read_csv_headers(csv_path: str) -> list[str]:
    with open(csv_path) as f:
        header_line = f.readline().strip()
    return [h.strip().strip('"').strip("'") for h in header_line.split(',')]


def _show_columns(headers: list[str]) -> None:
    table = Table(title='Detected CSV Columns')
    table.add_column('#', style='dim')
    table.add_column('Column Name', style='cyan')
    for i, h in enumerate(headers):
        table.add_row(str(i), h)
    console.print(table)


def run_wizard() -> LareConfig:
    console.print('\n[bold]LARE Configuration Wizard[/]\n')

    csv_path = questionary.path(
        'Path to your source CSV file:',
        only_directories=False,
    ).ask()

    if not csv_path or not Path(csv_path).exists():
        console.print('[red]CSV file not found[/]')
        raise SystemExit(1)

    headers = _read_csv_headers(csv_path)
    _show_columns(headers)

    project = questionary.text(
        'Output database filename:',
        default='project.lare',
    ).ask()

    has_image_dir = questionary.confirm(
        'Are image paths relative to a base directory?',
        default=False,
    ).ask()

    image_directory = None
    if has_image_dir:
        image_directory = questionary.path(
            'Base image directory:',
            only_directories=True,
        ).ask()

    id_column = questionary.select(
        'Which column contains the entry identifier?',
        choices=headers,
    ).ask()

    id_display_method = questionary.select(
        'How should entry IDs be displayed?',
        choices=['raw', 'basename', 'stem'],
    ).ask()

    has_filter = questionary.confirm(
        'Apply a SQL filter expression?',
        default=False,
    ).ask()

    filter_method = None
    if has_filter:
        console.print(
            '[dim]Example: GREATEST(sim_class_0, sim_class_1) > 0.1[/]'
        )
        filter_method = questionary.text(
            'SQL filter expression:',
        ).ask()

    console.print(
        '[dim]Example: GREATEST(sim_class_0, sim_class_1, sim_class_2)[/]'
    )
    ranking_score = questionary.text(
        'SQL expression for ranking score:',
    ).ask()

    images: list[ImageConfig] = []
    while True:
        console.print(f'\n[bold]Image #{len(images) + 1}[/]')

        img_column = questionary.select(
            'Column containing the image path:',
            choices=headers,
        ).ask()

        img_title = questionary.text('Display title for this image:').ask()

        img_format = questionary.select(
            'Image format:',
            choices=['fits', 'png', 'jpg', 'jpeg', 'tiff'],
        ).ask()

        stretching = None
        min_thresh = 0.5
        max_thresh = 99.5
        if img_format == 'fits':
            stretching = questionary.select(
                'Stretching method:',
                choices=['asinh', 'linear', 'sqrt', 'log', 'power'],
                default='asinh',
            ).ask()
            min_thresh = float(questionary.text(
                'Min percentile threshold:',
                default='0.5',
            ).ask())
            max_thresh = float(questionary.text(
                'Max percentile threshold:',
                default='99.5',
            ).ask())

        subdirectory = None
        if image_directory:
            has_subdir = questionary.confirm(
                'Does this image type live in a subdirectory?',
                default=False,
            ).ask()
            if has_subdir:
                subdirectory = questionary.text(
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

        if not questionary.confirm('Add another image?', default=False).ask():
            break

    labels: list[LabelConfig] = []
    used_shortcuts: set[str] = set()
    while True:
        console.print(f'\n[bold]Label #{len(labels) + 1}[/]')

        label_column = questionary.select(
            'Column containing the prediction score:',
            choices=headers,
        ).ask()

        label_title = questionary.text('Display title for this label:').ask()

        while True:
            shortcut = questionary.text(
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

        if not questionary.confirm('Add another label?', default=False).ask():
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

    if questionary.confirm('Write this configuration?', default=True).ask():
        output_path = 'lare_config.toml'
        write_config(config, output_path)
        log_success(f'Configuration written to {output_path}')

    return config
