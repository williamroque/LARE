from __future__ import annotations

import os
import shutil
import tempfile
import threading
from pathlib import Path

from lare.config import ImageConfig, LareConfig
from lare.console import log_step, log_warning


def _resolve_image_path(
    column_value: str,
    image_config: ImageConfig,
    lare_config: LareConfig,
) -> Path:
    if lare_config.paths.image_directory:
        base = Path(lare_config.paths.image_directory)
        basename = Path(column_value).name
        if image_config.subdirectory:
            return base / image_config.subdirectory / basename
        return base / basename
    return Path(column_value)


def _render_fits(source: Path, dest: Path, image_config: ImageConfig) -> None:
    try:
        from astropy.io import fits
        from astropy.visualization import simple_norm
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        raise RuntimeError(
            'FITS rendering requires extra dependencies. '
            'Install with: pip install lare[fits]'
        )

    data = fits.getdata(str(source))

    if data is None:
        raise RuntimeError(f'No image data found in FITS file: {source}')

    if data.ndim > 2:
        data = data[0]

    stretch = image_config.stretching or 'linear'
    cmap = image_config.colormap or 'gray'
    norm = simple_norm(
        data,
        stretch=stretch,
        min_percent=image_config.min_threshold,
        max_percent=image_config.max_threshold,
    )
    plt.imsave(str(dest), norm(data), cmap=cmap, origin='lower')


def _render_static(source: Path, dest: Path) -> None:
    if source.resolve() != dest.resolve():
        shutil.copy2(str(source), str(dest))


class ImageCache:
    def __init__(self, config: LareConfig, prerender_ahead: int = 25):
        self.config = config
        self.cache_dir = Path(tempfile.mkdtemp(prefix='lare_cache_'))
        self.prerender_ahead = prerender_ahead
        self._lock = threading.Lock()
        self._rendered: set[str] = set()
        self._prerender_thread: threading.Thread | None = None

        log_step(f'Image cache directory: {self.cache_dir}')

    def cache_key(self, queue_order: int, image_index: int) -> str:
        return f'{queue_order}_{image_index}.png'

    def get_path(self, cache_key: str) -> Path:
        return self.cache_dir / cache_key

    def is_cached(self, cache_key: str) -> bool:
        return cache_key in self._rendered

    def render_entry(
        self,
        queue_order: int,
        entry: dict,
    ) -> list[dict]:
        results = []
        for i, img_config in enumerate(self.config.images):
            key = self.cache_key(queue_order, i)
            dest = self.get_path(key)

            if not self.is_cached(key):
                col_value = entry.get(img_config.column, '')
                if not col_value:
                    results.append({
                        'title': img_config.title,
                        'url': None,
                        'error': f'No value in column "{img_config.column}"',
                    })
                    continue

                source = _resolve_image_path(col_value, img_config, self.config)

                if not source.exists():
                    results.append({
                        'title': img_config.title,
                        'url': None,
                        'error': f'Image file not found: {source}',
                    })
                    continue

                try:
                    if img_config.format == 'fits':
                        _render_fits(source, dest, img_config)
                    else:
                        _render_static(source, dest)
                    with self._lock:
                        self._rendered.add(key)
                except Exception as e:
                    results.append({
                        'title': img_config.title,
                        'url': None,
                        'error': str(e),
                    })
                    continue

            results.append({
                'title': img_config.title,
                'url': f'/images/{key}',
                'error': None,
            })

        return results

    def prerender_batch(
        self,
        start_order: int,
        get_entry_fn,
    ) -> None:
        def _worker():
            for offset in range(self.prerender_ahead):
                order = start_order + offset
                entry = get_entry_fn(order)
                if entry is None:
                    break
                try:
                    self.render_entry(order, entry)
                except Exception:
                    pass

        if self._prerender_thread and self._prerender_thread.is_alive():
            return

        self._prerender_thread = threading.Thread(
            target=_worker, daemon=True
        )
        self._prerender_thread.start()

    def cleanup(self) -> None:
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir, ignore_errors=True)
            log_step('Image cache cleaned up')
