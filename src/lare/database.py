from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from pathlib import Path

import polars as pl

from lare.config import LareConfig


POLARS_TO_SQLITE = {
    pl.Float64: 'REAL',
    pl.Float32: 'REAL',
    pl.Int64: 'INTEGER',
    pl.Int32: 'INTEGER',
    pl.Int16: 'INTEGER',
    pl.Int8: 'INTEGER',
    pl.UInt64: 'INTEGER',
    pl.UInt32: 'INTEGER',
    pl.UInt16: 'INTEGER',
    pl.UInt8: 'INTEGER',
    pl.Boolean: 'INTEGER',
    pl.Utf8: 'TEXT',
    pl.String: 'TEXT',
}


class LareDatabase:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self._lock = threading.Lock()
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> LareDatabase:
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute('PRAGMA journal_mode=WAL')
        self._conn.execute('PRAGMA busy_timeout=5000')
        return self

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> LareDatabase:
        return self.connect()

    def __exit__(self, *exc) -> None:
        self.close()

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError('Database not connected')
        return self._conn

    def _write(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        with self._lock:
            cursor = self._conn.execute(sql, params)
            self._conn.commit()
            return cursor

    def _write_many(self, sql: str, rows: list[tuple]) -> None:
        with self._lock:
            self._conn.executemany(sql, rows)
            self._conn.commit()

    def get_entry(self, queue_order: int) -> dict | None:
        row = self.conn.execute(
            'SELECT * FROM labeling_queue WHERE queue_order = ?',
            (queue_order,)
        ).fetchone()
        return dict(row) if row else None

    def get_next_unlabeled(self, after: int = -1) -> dict | None:
        row = self.conn.execute(
            'SELECT * FROM labeling_queue '
            'WHERE (final_label IS NULL OR TRIM(final_label) = \'\') AND queue_order > ? '
            'ORDER BY queue_order ASC LIMIT 1',
            (after,)
        ).fetchone()
        return dict(row) if row else None

    def set_label(self, entry_id: str, label: str) -> None:
        self._write(
            'UPDATE labeling_queue SET final_label = ? WHERE entry_id = ?',
            (label.strip(), entry_id),
        )

    def clear_label(self, entry_id: str) -> None:
        self._write(
            'UPDATE labeling_queue SET final_label = NULL WHERE entry_id = ?',
            (entry_id,),
        )

    def search_display_id(self, query: str) -> list[dict]:
        rows = self.conn.execute(
            'SELECT queue_order, entry_id, display_id, final_label '
            'FROM labeling_queue WHERE display_id LIKE ? ORDER BY queue_order',
            (f'%{query}%',)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_entry_by_display_id(self, display_id: str) -> list[dict]:
        rows = self.conn.execute(
            'SELECT * FROM labeling_queue WHERE display_id = ? '
            'ORDER BY queue_order',
            (display_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_audit_stats(self) -> tuple[int, int]:
        row = self.conn.execute(
            'SELECT '
            'COUNT(CASE WHEN final_label IS NOT NULL AND TRIM(final_label) != \'\' THEN 1 END) AS labeled, '
            'COUNT(*) AS total '
            'FROM labeling_queue'
        ).fetchone()
        return row['labeled'], row['total']

    def get_config(self) -> dict:
        row = self.conn.execute(
            'SELECT config_json FROM project_metadata LIMIT 1'
        ).fetchone()
        if row is None:
            raise RuntimeError('No project metadata found in database')
        return json.loads(row['config_json'])

    def get_all_labeled(self, include_unaudited: bool = False, unaudited_label: str = 'unaudited', config_labels: dict[str, str] | None = None, score_order: str = 'highest') -> list[dict]:
        if include_unaudited:
            rows = self.conn.execute(
                'SELECT * FROM labeling_queue ORDER BY queue_order'
            ).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                if not d['final_label'] or not d['final_label'].strip():
                    best_label = unaudited_label
                    if config_labels:
                        best_score = -float('inf') if score_order == 'highest' else float('inf')
                        for label_col, label_title in config_labels.items():
                            score = d.get(label_col)
                            if score is not None:
                                try:
                                    score = float(score)
                                    if score_order == 'highest' and score > best_score:
                                        best_score = score
                                        best_label = label_title
                                    elif score_order == 'lowest' and score < best_score:
                                        best_score = score
                                        best_label = label_title
                                except (ValueError, TypeError):
                                    pass
                    d['final_label'] = best_label
                result.append(d)
            return result

        rows = self.conn.execute(
            'SELECT * FROM labeling_queue '
            'WHERE final_label IS NOT NULL AND TRIM(final_label) != \'\' '
            'ORDER BY queue_order'
        ).fetchall()
        return [dict(r) for r in rows]

    def get_total_count(self) -> int:
        row = self.conn.execute(
            'SELECT COUNT(*) AS cnt FROM labeling_queue'
        ).fetchone()
        return row['cnt']


def create_database(
    path: str | Path,
    config: LareConfig,
    df: pl.DataFrame,
) -> None:
    path = str(path)
    conn = sqlite3.connect(path)
    conn.execute('PRAGMA journal_mode=WAL')

    conn.execute(
        'CREATE TABLE project_metadata ('
        '    project_id TEXT PRIMARY KEY,'
        '    created_at TEXT DEFAULT CURRENT_TIMESTAMP,'
        '    config_json TEXT NOT NULL'
        ')'
    )

    fixed_cols = [
        'queue_order INTEGER PRIMARY KEY',
        'entry_id TEXT UNIQUE NOT NULL',
        'display_id TEXT NOT NULL',
        'final_label TEXT DEFAULT NULL',
    ]

    skip_cols = {'queue_order', 'entry_id', 'display_id', 'final_label'}
    dynamic_cols = []
    for name, dtype in zip(df.columns, df.dtypes):
        if name in skip_cols:
            continue
        sqlite_type = POLARS_TO_SQLITE.get(dtype, 'TEXT')
        dynamic_cols.append(f'"{name}" {sqlite_type}')

    all_cols = fixed_cols + dynamic_cols
    col_defs = ', '.join(all_cols)

    conn.execute(f'CREATE TABLE labeling_queue ({col_defs})')
    conn.execute('CREATE INDEX idx_display_id ON labeling_queue(display_id)')
    conn.execute('CREATE INDEX idx_final_label ON labeling_queue(final_label)')

    ordered_columns = ['queue_order', 'entry_id', 'display_id']
    ordered_columns.append('final_label')
    for name in df.columns:
        if name not in skip_cols:
            ordered_columns.append(name)

    select_cols = []
    for col in ordered_columns:
        if col == 'final_label':
            select_cols.append(col)
        elif col in df.columns:
            select_cols.append(col)

    insert_df = df.select([c for c in ordered_columns if c in df.columns])

    if 'final_label' not in insert_df.columns:
        insert_df = insert_df.with_columns(
            pl.lit(None).cast(pl.Utf8).alias('final_label')
        )

    final_order = ['queue_order', 'entry_id', 'display_id', 'final_label']
    for c in insert_df.columns:
        if c not in final_order:
            final_order.append(c)
    insert_df = insert_df.select(final_order)

    placeholders = ', '.join(['?'] * len(insert_df.columns))
    insert_sql = f'INSERT INTO labeling_queue VALUES ({placeholders})'

    rows = insert_df.rows()
    conn.executemany(insert_sql, rows)

    project_id = str(uuid.uuid4())
    config_json = json.dumps(config.model_dump(mode='python'), default=str)
    conn.execute(
        'INSERT INTO project_metadata (project_id, config_json) VALUES (?, ?)',
        (project_id, config_json),
    )

    conn.commit()
    conn.close()


def open_database(path: str | Path) -> LareDatabase:
    return LareDatabase(path)
