from __future__ import annotations

import importlib.resources
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from lare.config import parse_config_dict
from lare.database import open_database, LareDatabase
from lare.imaging import ImageCache


class LabelRequest(BaseModel):
    entry_id: str
    label: str


class ClearLabelRequest(BaseModel):
    entry_id: str


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except (HTTPException, StarletteHTTPException):
            return await super().get_response('index.html', scope)


def create_app(db_path: str) -> FastAPI:
    db: LareDatabase | None = None
    image_cache: ImageCache | None = None

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        nonlocal db, image_cache

        db = open_database(db_path)
        db.connect()

        config_dict = db.get_config()
        config = parse_config_dict(config_dict)
        image_cache = ImageCache(config)

        app.state.db = db
        app.state.image_cache = image_cache
        app.state.config = config
        app.state.config_dict = config_dict

        first_entry = db.get_next_unlabeled(after=-1)
        if first_entry:
            image_cache.prerender_batch(
                first_entry['queue_order'],
                db.get_entry,
            )

        yield

        if image_cache:
            image_cache.cleanup()
        if db:
            db.close()

    app = FastAPI(title='LARE', lifespan=lifespan)

    @app.get('/api/config')
    async def get_config(request: Request):
        config_dict = request.app.state.config_dict
        config = request.app.state.config

        labels_info = []
        for lb in config.labels:
            labels_info.append({
                'label': lb.label,
                'title': lb.title,
                'shortcut': lb.shortcut,
                'is_emergent': getattr(lb, 'is_emergent', False),
            })

        images_info = []
        for img in config.images:
            images_info.append({
                'column': img.column,
                'title': img.title,
                'format': img.format,
            })

        return {
            'labels': labels_info,
            'images': images_info,
            'id_display_method': config.rules.id_display_method,
            'score_min': config.rules.score_min,
            'score_max': config.rules.score_max,
        }

    @app.get('/api/stats')
    async def get_stats(request: Request):
        db: LareDatabase = request.app.state.db
        labeled, total = db.get_audit_stats()
        pct = (labeled / total * 100) if total > 0 else 0
        return {
            'labeled': labeled,
            'total': total,
            'progress_pct': round(pct, 1),
        }

    @app.get('/api/entry/{queue_order}')
    async def get_entry(queue_order: int, request: Request):
        db: LareDatabase = request.app.state.db
        cache: ImageCache = request.app.state.image_cache
        config = request.app.state.config

        entry = db.get_entry(queue_order)
        if entry is None:
            raise HTTPException(status_code=404, detail='Entry not found')

        image_results = cache.render_entry(queue_order, entry)

        scores = {}
        for lb in config.labels:
            scores[lb.label] = entry.get(lb.label)

        cache.prerender_batch(queue_order + 1, db.get_entry)

        return {
            'queue_order': entry['queue_order'],
            'entry_id': entry['entry_id'],
            'display_id': entry['display_id'],
            'final_label': entry['final_label'],
            'images': image_results,
            'scores': scores,
        }

    @app.get('/api/next')
    async def get_next(request: Request, after: int = -1):
        db: LareDatabase = request.app.state.db
        entry = db.get_next_unlabeled(after=after)
        if entry is None:
            return {'entry': None, 'complete': True}

        cache: ImageCache = request.app.state.image_cache
        config = request.app.state.config

        image_results = cache.render_entry(entry['queue_order'], entry)

        scores = {}
        for lb in config.labels:
            scores[lb.label] = entry.get(lb.label)

        cache.prerender_batch(entry['queue_order'] + 1, db.get_entry)

        return {
            'entry': {
                'queue_order': entry['queue_order'],
                'entry_id': entry['entry_id'],
                'display_id': entry['display_id'],
                'final_label': entry['final_label'],
                'images': image_results,
                'scores': scores,
            },
            'complete': False,
        }

    @app.post('/api/label')
    async def set_label(body: LabelRequest, request: Request):
        db: LareDatabase = request.app.state.db
        db.set_label(body.entry_id, body.label)
        return {'status': 'ok'}

    @app.post('/api/clear-label')
    async def clear_label(body: ClearLabelRequest, request: Request):
        db: LareDatabase = request.app.state.db
        db.clear_label(body.entry_id)
        return {'status': 'ok'}

    @app.get('/api/search')
    async def search(q: str, request: Request):
        db: LareDatabase = request.app.state.db
        if not q.strip():
            return {'results': []}
        results = db.search_display_id(q.strip())
        return {'results': results}

    cache_mount_set = False

    @app.middleware('http')
    async def dynamic_image_serving(request: Request, call_next):
        if request.url.path.startswith('/images/'):
            cache: ImageCache = request.app.state.image_cache
            filename = request.url.path.split('/images/', 1)[1]
            file_path = cache.get_path(filename)
            if file_path.exists():
                return FileResponse(str(file_path))
            return JSONResponse(
                status_code=404,
                content={'detail': 'Image not found in cache'},
            )
        return await call_next(request)

    static_dir = Path(__file__).parent / 'static'
    if static_dir.exists() and (static_dir / 'index.html').exists():
        app.mount('/', SPAStaticFiles(directory=str(static_dir), html=True), name='spa')

    return app
