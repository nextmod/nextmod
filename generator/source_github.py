# Copyright (c) 2020, Eli2
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import json
import requests
from sgqlc.endpoint.http import HTTPEndpoint

import base64

from pathlib import PurePath

from .common import g_log
from .source import ModDataFile, RepositorySource, Repository


# https://github.com/profusion/sgqlc

class GitHubSource(RepositorySource):

	def __init__(self):

		gh_token = os.environ.get('GH_TOKEN', None)
		if gh_token:
			headers = {'Authorization': 'bearer ' + gh_token}
		else:
			headers = None
			
		self._headers = headers
		
		self.endpoint = HTTPEndpoint('https://api.github.com/graphql', headers)

	def list_mods(self):
		query = '''
		query {
			organization(login:"nextmod") {
				repositories(first: 10) {
					nodes{
						name
					}
				}
			}
		}'''
		data = self.endpoint(query)

		for repo in data['data']['organization']['repositories']['nodes']:
			repo_name = repo['name']

			if not repo_name.startswith('mw_'):
				g_log.info(f'Unexpected repo prefix {repo_name} skipping')
				continue

			game_id, mod_id = repo_name.split('_', 1)

			yield GitHubRepository(self,  self.endpoint, 'nextmod', repo_name, game_id, mod_id)


class GitHubRepository(Repository):
	
	_repo_owner: str
	_repo_name: str

	game_id: str
	mod_id: str

	def __init__(self, src, endpoint, repo_owner, repo_name, game_id, mod_id):
		self._src = src
		self.endpoint = endpoint
		self._repo_owner = repo_owner
		self._repo_name = repo_name

		self.game_id = game_id
		self.mod_id = mod_id

	def list_dir(self, dir_path):
		dir_path = str(dir_path)
		if not dir_path.endswith('/'):
			dir_path += '/'
		
		query = '''
		query ($repo_owner: String!, $repo_name: String!, $expression: String!) {
		  repository(owner: $repo_owner, name: $repo_name) {    
			object(expression: $expression) {
			  ... on Tree {
				entries {
				  name
				  type
				}
			  }
			}
		  }
		}
		'''
		variables = {
			'repo_owner': self._repo_owner,
			'repo_name': self._repo_name,
			'expression': 'master:' + dir_path
		}
		data = self.endpoint(query, variables)

		obj = data['data']['repository']['object']
		if not obj:
			return []
		
		entries = obj['entries']
		names = [e['name'] for e in entries]
		return names

	def list_data_files(self):
		dir_path = 'data/'
		
		def gen_tree(depth: int):
			if depth == 0:
				return ''
			return 'object {...on Blob{byteSize} ... on Tree {entries{name type ' + gen_tree(depth - 1) + '}}}'

		def gen_tree_frag():
			return '... on Tree {entries{name type ' + gen_tree(8) + '}}'

		query = '''
		query ($repo_owner: String!, $repo_name: String!, $expression: String!) {
		  repository(owner: $repo_owner, name: $repo_name) {
			object(expression: $expression) {
			''' + gen_tree_frag() + '''
			}
		  }
		}
		'''
		
		variables = {
			'repo_owner': self._repo_owner,
			'repo_name': self._repo_name,
			'expression': 'master:' + dir_path
		}
		data = self.endpoint(query, variables)
		
		root_obj = data['data']['repository']['object']
		if root_obj:
			flat = []
			
			def walk(obj, prefix):
				for e in obj['entries']:
					if e['type'] == 'tree':
						walk(e['object'], prefix + '/' + e['name'])
					elif e['type'] == 'blob':
						flat.append(('data' + prefix + '/' + e['name'], e['object']['byteSize']))

			
			walk(root_obj, '')
			return flat
		else:
			return []

	def get_file(self, file_path: PurePath):
		
		query = '''
		query($owner:String!, $name:String!, $exp:String!) {
			repository(owner: $owner, name: $name) {
				object(expression: $exp) {
					... on Blob {
						oid
					}
				}	
			}
		}'''
		variables = {
			'owner': self._repo_owner,
			'name': self._repo_name,
			'exp': 'master:' + str(file_path)
		}
		data = self.endpoint(query, variables)
		
		oid = data['data']['repository']['object']['oid']
		
		# No clue how to do this with API v4, use v3 (2020.05)

		foo = ["https://api.github.com", 'repos', self._repo_owner, self._repo_name, 'git', 'blobs', oid]
		bar = '/'.join(foo)
		
		try:
			r = requests.get(bar, headers=self._src._headers)
			r.raise_for_status()
			j = r.json()
			if j['encoding'] == 'base64':
				data = base64.b64decode(j['content'])
			else:
				g_log.error("Unexpected encoding")
			return data
		except Exception as ex:
			g_log.exception(ex)
			return None
	


	def get_star_count(self):
		query = '''
		query($repo_owner:String!, $repo_name:String!) {
			repository(owner: $repo_owner, name: $repo_name) {
				stargazers(first: 10) {
					totalCount
				}
			}
		}'''
		variables = {'repo_owner': self._repo_owner, 'repo_name': self._repo_name, }
		data = self.endpoint(query, variables)
		stars = data['data']['repository']['stargazers']['totalCount']
		return stars
