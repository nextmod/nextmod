# Copyright (c) 2020, Eli2
# SPDX-License-Identifier: AGPL-3.0-or-later

from dataclasses import dataclass, field
from typing import Any, List, Tuple, NamedTuple
import re

from generator.common import ConfigData, InfoFile, Creator, Category, Tag

def create_id_from_name(name):
	name = name\
		.lower()\
		.replace(' ', '-')\
		.replace('/', 'and')\
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
			if not line:
				continue
			
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
	
	def get_result(self) -> Any:
		pass



@dataclass
class ConfigFile(MarkdownFile):
	_lastHeader: str = ''
	
	instance_name: str = ''

	def read_h1(self, line):
		self._lastHeader = line

	def read_li(self, line):
		self.read_text(line)

	def read_text(self, line):
		if self._lastHeader == 'Instance Name':
			self.instance_name = line
			self._lastHeader = ''
			
	def get_result(self) -> Any:
		return ConfigData(self.instance_name)


@dataclass
class InfoFileParser(InfoFile, MarkdownFile):

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
			creator_name = line
			creator_id = create_id_from_name(line)
			self.creators.append(Creator(creator_id, creator_name))
		elif self._lastHeader == 'Category':
			category_name = line
			category_id = create_id_from_name(category_name)
			self.category = Category(category_id, category_name)
			self._lastHeader = ''
		elif self._lastHeader == 'Description':
			self.description = line
			self._lastHeader = ''
		elif self._lastHeader == 'Tags':
			tag_name = line
			tag_id = create_id_from_name(tag_name)
			self.tags.append(Tag(tag_id, tag_name))
		elif self._lastHeader == 'Release date':
			self.release_date = line
			self._lastHeader = ''
		elif self._lastHeader == 'Last update date':
			self.update_date = line
			self._lastHeader = ''			
		elif self._lastHeader == 'Version':
			self.version = line
			self._lastHeader = ''
