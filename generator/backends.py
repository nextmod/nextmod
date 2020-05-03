# Copyright (c) 2020, Eli2
# SPDX-License-Identifier: AGPL-3.0-or-later

import os

import gitlab
from gitlab import GitlabGetError

from pathlib import Path
from datetime import datetime
from typing import Tuple, NamedTuple


class ModDataFile(NamedTuple):
	path: str
	size: int

class RepositorySource:
	def list_mods(self):
		pass


class Repository:
	def list_dir(self, dir_path):
		pass


class DirectorySource(RepositorySource):
	path = Path('../mw')

	def list_mods(self):
		for mod_name in os.listdir(self.path):
			path = self.path / mod_name
			p = DirectoryProject(path=path)
			p.id = mod_name
			p.name = mod_name
			p.p_path = self.path / mod_name
			yield p


class DirectoryProject(Repository):
	id = ''
	name = ''
	p_path = None

	def __init__(self, path):
		self.p_path = path

	def list_dir(self, dir_path):
		foo = self.p_path / dir_path
		for file_name in os.listdir(foo):
			yield file_name
	
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
		return -1;


class GitlabSource(RepositorySource):
	nextmods_gitlab_group_id = 7457398
	gl = gitlab.Gitlab('https://gitlab.com')

	def list_mods(self):
		group = self.gl.groups.get(self.nextmods_gitlab_group_id)
		for group_project in group.projects.list():
			project = self.gl.projects.get(group_project.id, lazy=False)
			p = GitlabProject()
			p.id = project.path
			p.name = project.name
			p.p_project = project
			yield p


class GitlabProject:
	id = ''
	name = ''
	p_project = None

	def list_dir(self, dir_path):
		path_str = str(dir_path)
		files = self.p_project.repository_tree(path=path_str, ref='master', recursive=False, as_list=False)
		for f in files:
			yield f['name']
	
	def list_data_files(self):
		data_path = "data/"
		try:
			result = []
			files = self.p_project.repository_tree(path=data_path, ref='master', recursive=True, as_list=False)
			for f in files:
				if f['type'] == 'tree':
					continue
				blob_id = f['id']
				path = f['path']
				file_info = self.p_project.repository_blob(blob_id)
				size = file_info['size']
				result.append(ModDataFile(path, size))
			return tuple(result)
		except GitlabGetError:
			return []
	
	def get_file(self, file_path):
		path_str = str(file_path)
		try:
			file_data = self.p_project.files.get(file_path=path_str, ref='master').decode()
			return file_data
		except GitlabGetError:
			return None
		
		
	def get_star_count(self):
		return self.p_project.attributes['star_count']
