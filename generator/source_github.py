# Copyright (c) 2020, Eli2
# SPDX-License-Identifier: AGPL-3.0-or-later

from github3 import GitHub
from github3.session import GitHubSession
from github3.exceptions import GitHubError, NotFoundError

import base64

from pathlib import PurePath

from .common import g_log
from .source import ModDataFile, RepositorySource, Repository


class GitHubSource(RepositorySource):
	
	def __init__(self):
		self.gh = GitHub()

	def list_mods(self):
		org = self.gh.organization('nextmod')
		repos = org.repositories()
		for repo in repos:
			try:
				repo.file_contents('mod-info.md')
			except NotFoundError as ex:
				g_log.info(f'mod-info file not found in repository {repo.name}, skipping')
				continue
				
			p = GitHubRepository()
			p.id = repo.name
			p.name = repo.name
			p._repo = repo
			yield p


class GitHubRepository(Repository):
	id = ''
	name = ''
	_repo = None

	def list_dir(self, dir_path):
		path_str = str(dir_path)
		try:
			files = self._repo.directory_contents(dir_path)
			for f in files:
				yield f['name']
		except GitHubError as ex:
			g_log.error("GitHub failed to list files: %s", ex)

	def list_data_files(self):
		data_path = "data/"
		try:
			result = []
			files = self._repo.directory_contents(data_path)
			for f in files:
				pass
				# TODO
				"""
				if f['type'] == 'tree':
					continue
				blob_id = f['id']
				path = f['path']
				file_info = self.p_project.repository_blob(blob_id)
				size = file_info['size']
				result.append(ModDataFile(path, size))
				"""
			return tuple(result)
		except GitHubError as ex:
			g_log.error("GitHub failed to list files: %s", ex)
			return []

	def get_file(self, file_path: PurePath):
		path_str = str(file_path)
		try:
			file_contents = self._repo.file_contents(path_str)
			file_data = base64.decodebytes(bytes(file_contents.content, 'UTF-8'))
			return file_data
		except GitHubError as ex:
			g_log.error("gitlab failed to get file %s: %s", file_path, ex)
			return None

	def get_star_count(self):
		i = 0
		for gazer in self._repo.stargazers():
			i += 1
		return i
