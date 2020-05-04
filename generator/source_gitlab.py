# Copyright (c) 2020, Eli2
# SPDX-License-Identifier: AGPL-3.0-or-later

from pathlib import PurePath

import gitlab
from gitlab import GitlabGetError

from .common import g_log
from .source import ModDataFile, RepositorySource, Repository

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


class GitlabProject(Repository):
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
