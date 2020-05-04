# Copyright (c) 2020, Eli2
# SPDX-License-Identifier: AGPL-3.0-or-later

from pathlib import PurePath
from typing import NamedTuple, Tuple

class ModDataFile(NamedTuple):
	path: str
	size: int

class RepositorySource:
	def list_mods(self):
		pass


class Repository:
	def list_dir(self, dir_path: PurePath):
		pass
	
	def list_data_files(self) -> Tuple[ModDataFile]:
		pass
	
	def get_file(self, file_path: PurePath):
		pass
	
	def get_star_count(self) -> int:
		pass
