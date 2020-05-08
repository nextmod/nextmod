# Copyright (c) 2020, Eli2
# SPDX-License-Identifier: AGPL-3.0-or-later


import os
from pathlib import Path
from typing import Tuple

from .source import ModDataFile, RepositorySource, Repository


class DirectorySource(RepositorySource):

	def __init__(self, mod_base_path: str):
		self.path = Path(mod_base_path)
	
	def list_mods(self):
		for game_id in os.listdir(self.path):
			for mod_id in os.listdir(self.path / game_id):
				path = self.path / game_id / mod_id
				yield DirectoryProject(path, game_id, mod_id)


class DirectoryProject(Repository):
	p_path: Path
	game_id: str
	mod_id: str
	
	def __init__(self, path, game_id, mod_id):
		self.p_path = path
		self.game_id = game_id
		self.mod_id = mod_id
	
	def list_dir(self, dir_path):
		foo = self.p_path / dir_path
		try:
			for file_name in os.listdir(foo):
				yield file_name
		except FileNotFoundError:
			yield from []
	
	def list_data_files(self) -> Tuple[ModDataFile]:
		data_path = self.p_path / 'data'
		result = []
		for root, dirs, files in os.walk(data_path):
			root_path = Path(root)
			rel_dir = root_path.relative_to(data_path)
			for name in files:
				abs_path = root_path / name
				rel_path = rel_dir / name
				size = abs_path.stat().st_size
				result.append(ModDataFile(str(rel_path), size))
		return tuple(result)
	
	def get_file(self, file_path):
		foo = self.p_path / file_path
		if not foo.is_file():
			return None
		with open(foo, mode='rb') as file:
			return file.read()
	
	def get_star_count(self):
		return -1
