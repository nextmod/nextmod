# Copyright (c) 2020, Eli2
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, NamedTuple, List, Tuple

from generator.source import Repository
from generator.file_parsers import InfoFile, TagsFile


logging.basicConfig(
	format='%(asctime)s %(levelname)-8s %(message)s',
	level=logging.INFO,
	datefmt='%Y-%m-%d %H:%M:%S')

# logging.basicConfig(level=logging.DEBUG)
g_log = logging.getLogger()
g_log.setLevel(logging.INFO)

g_public_dir = Path('./public')

@dataclass
class Mod:
	repository: Repository
	id: int = 0
	name: str = ''
	link: str = ''
	banner_picture: str = ''
	image_preview: str = ''
	picture_preview: str = field(default_factory=list)
	image_gallery: List = field(default_factory=list)
	authors: str = ''
	description: str = ''
	last_updated: str = ''
	star_count: int = 0
	
	info: InfoFile = field(default_factory=InfoFile)
	tags: TagsFile = field(default_factory=TagsFile)
	
	info_html: str = ''
	page_html: str = ''
	
	data_files: Tuple[str] = field(default_factory=tuple)
	data_files_size: int = 0


class GroupSpec(NamedTuple):
	id: str
	name: str
	name_singular: str
	key_getter: Callable[[Mod], List[Tuple[str, str]]]


class GroupEntry(NamedTuple):
	id: str
	name: str
	mods: Tuple[Mod]


class Group(NamedTuple):
	spec: GroupSpec
	entries: Tuple[GroupEntry]


@dataclass
class PreviewEntry:
	id: str
	next_id: str
	prev_id: str
	picture: str
	thumb: str
	thumb_pictures: List
