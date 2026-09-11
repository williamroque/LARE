from __future__ import annotations

from pathlib import PurePosixPath, PureWindowsPath
import platform

import polars as pl

from lare.config import LareConfig
from lare.console import console, log_error, log_step


def _extract_stem(path_str: str) -> str:
    if platform.system() == 'Windows':
        return PureWindowsPath(path_str).stem
    return PurePosixPath(path_str).stem


def _extract_basename(path_str: str) -> str:
    if platform.system() == 'Windows':
        return PureWindowsPath(path_str).name
    return PurePosixPath(path_str).name


def load_and_process(config: LareConfig, csv_path: str) -> pl.DataFrame:
    log_step(f'Reading CSV: {csv_path}')
    df = pl.read_csv(csv_path, infer_schema_length=10000)
    rows_before = df.height

    log_step(f'Loaded {rows_before} rows, {df.width} columns')

    if config.rules.filter_method:
        log_step(f'Applying filter: {config.rules.filter_method}')
        ctx = pl.SQLContext(data=df, eager=True)
        try:
            query = f'SELECT * FROM data WHERE {config.rules.filter_method}'
            res = ctx.execute(query)
            df = res.collect() if hasattr(res, 'collect') else res
        except Exception as err:
            log_error(f'Failed to execute filter SQL expression: {err}')
        log_step(f'Rows after filter: {df.height}')

    log_step(f'Computing ranking score: {config.rules.ranking_score}')
    ctx = pl.SQLContext(data=df, eager=True)
    try:
        df = ctx.execute(
            f'SELECT *, ({config.rules.ranking_score}) AS _ranking_score FROM data'
        )
    except Exception as err:
        log_error(f'Failed to compute ranking score SQL expression: {err}')

    df = df.sort('_ranking_score', descending=True)

    id_col = config.rules.id_column
    method = config.rules.id_display_method
    log_step(f'Extracting display_id from "{id_col}" using method "{method}"')

    if method == 'raw':
        df = df.with_columns(pl.col(id_col).alias('display_id'))
    elif method == 'basename':
        df = df.with_columns(
            pl.col(id_col).map_elements(
                _extract_basename, return_dtype=pl.Utf8
            ).alias('display_id')
        )
    elif method == 'stem':
        df = df.with_columns(
            pl.col(id_col).map_elements(
                _extract_stem, return_dtype=pl.Utf8
            ).alias('display_id')
        )
        dupes = df.filter(pl.col('display_id').is_duplicated())
        if dupes.height > 0:
            from rich.table import Table
            tbl = Table(title='Duplicate Stems Detected', show_lines=True)
            tbl.add_column('display_id', style='red')
            tbl.add_column(id_col, style='white')
            for row in dupes.head(10).iter_rows(named=True):
                tbl.add_row(row['display_id'], str(row[id_col]))
            console.print(tbl)
            log_error(
                "Namespace Collision: The 'stem' method requires "
                'unique file names across all subdirectories.'
            )

    df = df.with_columns(
        pl.col(id_col).alias('entry_id')
    )

    df = df.with_row_index('queue_order')
    df = df.cast({'queue_order': pl.Int64})

    df = df.drop('_ranking_score')

    return df, rows_before
