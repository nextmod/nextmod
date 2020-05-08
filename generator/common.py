# Copyright (c) 2020, Eli2
# SPDX-License-Identifier: AGPL-3.0-or-later

import logging

from dataclasses import dataclass, field
from pathlib import Path, PurePath
from typing import Callable, NamedTuple, List, Tuple, Optional

from generator.source import Repository


logging.basicConfig(
	format='%(asctime)s %(levelname)-8s %(message)s',
	level=logging.INFO,
	datefmt='%Y-%m-%d %H:%M:%S')

# logging.basicConfig(level=logging.DEBUG)
g_log = logging.getLogger()
g_log.setLevel(logging.INFO)

class ConfigData(NamedTuple):
	instance_name: str = ''


class Picture(NamedTuple):
	base_name: str
	base_ext: str
	type: str
	number: str
	variant: Optional[str]
	description: Optional[str]
	
	def get_id(self):
		if self.variant:
			return f'{self.type}-{self.number}-{self.variant}'
		else:
			return f'{self.type}-{self.number}'
	
	def out_name(self, ext: str, suffix: str = None) -> str:
		if suffix:
			return f'{self.get_id()}_{suffix}.{ext}'
		else:
			return f'{self.get_id()}.{ext}'


class Category(NamedTuple):
	id: str
	name: str

class Tag(NamedTuple):
	id: str
	name: str

class Creator(NamedTuple):
	id: str
	name: str


class InfoFile(NamedTuple):
	name: str
	creators: Tuple[Creator]
	category: Category
	description: str
	tags: Tuple[Tag]
	release_date: str
	update_date: str
	version: str

@dataclass
class Mod:
	repository: Repository
	id: str = ''
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
	
	info: InfoFile = None
		
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

class GroupEntryRef(NamedTuple):
	spec: GroupSpec
	entry: GroupEntry

class Group(NamedTuple):
	spec: GroupSpec
	entries: Tuple[GroupEntry]
	
	def get_refs(self):
		for e in self.entries:
			yield GroupEntryRef(self.spec, e)


class PicSrc(NamedTuple):
	path: PurePath
	mime: str

@dataclass
class PreviewEntry:
	id: str
	next_id: str
	prev_id: str
	picture: str
	thumb_pictures: Tuple[PicSrc]
