# Copyright (c) 2020, Eli2
# SPDX-License-Identifier: AGPL-3.0-or-later

from typing import NamedTuple

class ModDataFile(NamedTuple):
	path: str
	size: int

class RepositorySource:
	def list_mods(self):
		pass


class Repository:
	def list_dir(self, dir_path):
		pass
