# Copyright (c) 2020, Eli2
# SPDX-License-Identifier: AGPL-3.0-or-later

from dataclasses import dataclass, field
from typing import List, Tuple
import re


def create_id_from_name(name):
	name = name\
		.lower()\
		.replace(' ', '-')\
		.replace('/', '-')\
		.replace('\\', '-')

	# XXX add hash from original name

	# Remove whitespace
	return re.sub(r'\s+', '', name, flags=re.UNICODE)


class MarkdownFile:
	def parse(self, content: bytes):
		if not content:
			return
		lines = content.decode('utf-8')
		for line in lines.splitlines():
			if line.startswith('# '):
				self.read_h1(line[2:])
			elif line.startswith('* '):
				self.read_li(line[2:])
			else:
				self.read_text(line)

	def read_h1(self, line: str):
		pass

	def read_li(self, line: str):
		pass

	def read_text(self, line: str):
		pass


@dataclass
class InfoFile(MarkdownFile):
	name: str = ''
	creator: str = ''
	creator_id: str = ''
	category: str = ''
	category_id: str = ''
	description: str = ''
	release_date: str = ''
	update_date: str = ''
	version: str = ''

	_lastHeader: str = ''

	def read_h1(self, line):
		self._lastHeader = line

	def read_li(self, line):
		self.read_text(line)

	def read_text(self, line):
		if self._lastHeader == 'Name':
			self.name = line
			self._lastHeader = ''
		elif self._lastHeader == 'Created by':
			self.creator = line
			self.creator_id = create_id_from_name(line)
			self._lastHeader = ''
		elif self._lastHeader == 'Category':
			self.category = line
			self.category_id = create_id_from_name(self.category)
			self._lastHeader = ''
		elif self._lastHeader == 'Description':
			self.description = line
			self._lastHeader = ''
		elif self._lastHeader == 'Release date':
			self.release_date = line
			self._lastHeader = ''
		elif self._lastHeader == 'Last update date':
			self.update_date = line
			self._lastHeader = ''			
		elif self._lastHeader == 'Version':
			self.version = line
			self._lastHeader = ''


@dataclass
class TagsFile(MarkdownFile):
	entries: List[Tuple[str, str]] = field(default_factory=list)

	def read_li(self, line: str):
		self.read_text(line)

	def read_text(self, line: str):
		tag_id = create_id_from_name(line)
		self.entries.append((tag_id, line))
