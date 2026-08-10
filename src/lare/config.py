from __future__ import annotations

import sys
from typing import Literal

from pydantic import BaseModel, field_validator, model_validator

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w


class PathsConfig(BaseModel):
    project: str = 'project.lare'
    source_csv: str
    image_directory: str | None = None


class RulesConfig(BaseModel):
    filter_method: str | None = None
    ranking_score: str
    id_column: str
    id_display_method: Literal['raw', 'basename', 'stem'] = 'raw'


class ImageConfig(BaseModel):
    column: str
    title: str
    format: Literal['fits', 'png', 'jpg', 'jpeg', 'tiff']
    stretching: str | None = None
    min_threshold: float = 0.5
    max_threshold: float = 99.5
    subdirectory: str | None = None

    @field_validator('stretching')
    @classmethod
    def stretching_requires_fits(cls, v: str | None, info) -> str | None:
        if v is not None and info.data.get('format') != 'fits':
            raise ValueError('stretching is only valid for FITS format images')
        return v

    @field_validator('subdirectory')
    @classmethod
    def subdirectory_needs_image_directory(cls, v: str | None) -> str | None:
        return v


class LabelConfig(BaseModel):
    label: str
    title: str
    shortcut: str
    is_emergent: bool = False

    @field_validator('shortcut')
    @classmethod
    def validate_shortcut(cls, v: str) -> str:
        if len(v) != 1 or not v.isalpha():
            raise ValueError('shortcut must be a single alphabetic character')
        return v.lower()


class LareConfig(BaseModel):
    paths: PathsConfig
    rules: RulesConfig
    images: list[ImageConfig]
    labels: list[LabelConfig]

    @model_validator(mode='after')
    def validate_shortcuts_unique(self) -> LareConfig:
        shortcuts = [lb.shortcut for lb in self.labels]
        if len(shortcuts) != len(set(shortcuts)):
            dupes = [s for s in shortcuts if shortcuts.count(s) > 1]
            raise ValueError(
                f'duplicate keyboard shortcuts detected: {set(dupes)}'
            )
        return self

    @model_validator(mode='after')
    def validate_subdirectory_requires_image_dir(self) -> LareConfig:
        if self.paths.image_directory is None:
            for img in self.images:
                if img.subdirectory is not None:
                    raise ValueError(
                        f'image "{img.title}" has subdirectory set but '
                        f'paths.image_directory is not configured'
                    )
        return self

    @model_validator(mode='after')
    def validate_fits_extras(self) -> LareConfig:
        has_fits = any(img.format == 'fits' for img in self.images)
        if has_fits:
            try:
                import astropy  # noqa: F401
            except ImportError:
                raise ValueError(
                    'FITS image support requires extra dependencies. '
                    'Install with: pip install lare[fits]'
                )
        return self


def load_config(path: str) -> LareConfig:
    with open(path, 'rb') as f:
        raw = tomllib.load(f)
    return parse_config_dict(raw)


def parse_config_dict(raw: dict) -> LareConfig:
    return LareConfig(
        paths=PathsConfig(**raw.get('paths', {})),
        rules=RulesConfig(**raw.get('rules', {})),
        images=[ImageConfig(**img) for img in raw.get('images', [])],
        labels=[LabelConfig(**lb) for lb in raw.get('labels', [])],
    )


def config_to_dict(config: LareConfig) -> dict:
    return config.model_dump(mode='python')


def write_config(config: LareConfig, path: str) -> None:
    d = config.model_dump(mode='python', exclude_none=True)
    toml_dict = {
        'paths': d['paths'],
        'rules': d['rules'],
        'images': d['images'],
        'labels': d['labels'],
    }
    with open(path, 'wb') as f:
        tomli_w.dump(toml_dict, f)
