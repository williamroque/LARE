from __future__ import annotations

import csv as csv_module
import shutil
from pathlib import Path

from lare.config import LareConfig, parse_config_dict
from lare.console import console, log_step, log_success, print_audit_banner
from lare.database import open_database


def export_csv(db_path: str, output_path: str, include_unaudited: bool = False, unaudited_fallback: str = 'unaudited', score_order: str = 'highest') -> None:
    db = open_database(db_path)
    with db:
        config_dict = db.get_config()
        config = parse_config_dict(config_dict)
        labels = {lb.label: lb.title for lb in config.labels}

        labeled = db.get_all_labeled(include_unaudited=include_unaudited, unaudited_label=unaudited_fallback, config_labels=labels, score_order=score_order)
        labeled_count = len(labeled)
        total = db.get_total_count()

        if not labeled:
            log_step('No entries to export')
            print_audit_banner(0, total)
            return

        if include_unaudited:
            log_step(f'Exporting all {labeled_count} entries to CSV')
        else:
            log_step(f'Exporting {labeled_count} labeled entries to CSV')

        fieldnames = list(labeled[0].keys())
        with open(output_path, 'w', newline='') as f:
            writer = csv_module.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(labeled)

        log_success(f'CSV written to {output_path}')
        print_audit_banner(labeled_count, total)


def export_copy(db_path: str, output_path: str, include_unaudited: bool = False, unaudited_fallback: str = 'unaudited', score_order: str = 'highest') -> None:
    from rich.progress import Progress

    db = open_database(db_path)
    with db:
        config_dict = db.get_config()
        config = parse_config_dict(config_dict)
        labels = {lb.label: lb.title for lb in config.labels}

        labeled = db.get_all_labeled(include_unaudited=include_unaudited, unaudited_label=unaudited_fallback, config_labels=labels, score_order=score_order)
        labeled_count = len(labeled)
        total = db.get_total_count()

        if not labeled:
            log_step('No entries to export')
            print_audit_banner(0, total)
            return

        if include_unaudited:
            log_step(f'Copying all {labeled_count} entries')
        else:
            log_step(f'Copying {labeled_count} labeled entries')
        output_root = Path(output_path)

        with Progress(console=console) as progress:
            task = progress.add_task('Copying files...', total=labeled_count)
            copied = 0

            for entry in labeled:
                label = entry['final_label']
                for img_config in config.images:
                    col_value = entry.get(img_config.column)
                    if not col_value:
                        continue

                    if config.paths.image_directory:
                        base = Path(config.paths.image_directory)
                        basename = Path(col_value).name
                        if img_config.subdirectory:
                            source = base / img_config.subdirectory / basename
                        else:
                            source = base / basename
                    else:
                        source = Path(col_value)

                    if not source.exists():
                        continue

                    target_dir = output_root / label
                    target_dir.mkdir(parents=True, exist_ok=True)
                    target = target_dir / source.name

                    if target.exists():
                        stem = target.stem
                        suffix = target.suffix
                        counter = 1
                        while target.exists():
                            target = target_dir / f'{stem}_{counter}{suffix}'
                            counter += 1

                    shutil.copy2(str(source), str(target))
                    copied += 1

                progress.advance(task)

        log_success(f'Copied {copied} files to {output_path}')
        print_audit_banner(labeled_count, total)
