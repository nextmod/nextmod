# Copyright (c) 2020, Eli2
# SPDX-License-Identifier: AGPL-3.0-or-later

from pathlib import PurePath

import gitlab
from gitlab import Gitlab, GitlabGetError

from .common import g_log
from .source import ModDataFile, RepositorySource, Repository

# https://python-gitlab.readthedocs.io/en/stable/

class GitlabSource(RepositorySource):
	gl: Gitlab
	root_group_path: str
	
	def __init__(self):
		self.root_group_path = 'nextmod/mod'
		self.gl = Gitlab('https://gitlab.com')
	
	def list_mods(self):
		root_group = self.gl.groups.get(self.root_group_path)
		for game_subgroup in root_group.subgroups.list():
			game_id = game_subgroup.name
			game_group = self.gl.groups.get(game_subgroup.id)
			for mod_groupproject in game_group.projects.list():
				mod_id = mod_groupproject.name
				project = self.gl.projects.get(mod_groupproject.id, lazy=False)
				yield GitlabProject(self, project, game_id, mod_id)


class GitlabProject(Repository):
	
	game_id: str
	mod_id: str
	
	p_project = None
	
	def __init__(self, src, proj, game_id, mod_id):
		self.src = src
		self.p_project = proj
		self.game_id = game_id
		self.mod_id = mod_id
		
	
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
		except GitlabGetError as ex:
			g_log.error("gitlab failed to list files: %s", ex)
			return []
	
	def get_file(self, file_path: PurePath):
		path_str = str(file_path)
		try:
			file_data = self.p_project.files.get(file_path=path_str, ref='master').decode()
			return file_data
		except GitlabGetError as ex:
			g_log.error("gitlab failed to get file %s: %s", file_path, ex)
			return None
	
	def get_star_count(self):
		return self.p_project.attributes['star_count']
