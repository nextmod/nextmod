#!/usr/bin/env python3

# Copyright (c) 2020, Eli2
# SPDX-License-Identifier: AGPL-3.0-or-later


import argparse
from collections import defaultdict

from generator.common import *
from generator.file_parsers import ConfigFile, InfoFileParser
from generator.image_processor import ImageProcessor

from generator.render_about import render_about_page
from generator.render_mod import render_mod_page
from generator.render_index import render_index_pages

from generator.source_directory import DirectorySource
from generator.source_github import GitHubSource
from generator.source_gitlab import GitlabSource

from generator.target import g_target


image_processor = ImageProcessor()

def load_mod_repositories(repositories) -> Tuple[Mod]:
	g_log.info('Loading mod data ...')

	foo = list(repositories)

	mods = []
	for mod_repository in foo:
		g_log.info('Loading mod data: %s', mod_repository.id)
		
		mod = Mod(repository=mod_repository)
		mod.id = mod_repository.id
				
		mod.star_count = mod_repository.get_star_count()
		mod.data_files = mod_repository.list_data_files()
		mod.data_files_size = sum(size for name, size in mod.data_files)
		
		info_parser = InfoFileParser()
		info_parser.parse(mod_repository.get_file('mod-info.md'))
		mod.info = info_parser

		mods.append(mod)
	return tuple(mods)


def build_groups(all_mods: Tuple[Mod]) -> Tuple[Group]:

	group_specs = (
		GroupSpec('category', 'Categories', 'Category', lambda m: [m.info.category]),
		GroupSpec('tag', 'Tags', 'Tag', lambda m: m.info.tags),
		GroupSpec('creator', 'Creators', 'Creator', lambda m: m.info.creators),
	)

	groups = []
	for group_spec in group_specs:
		group_keys = dict()
		group_mods = defaultdict(list)

		for mod in all_mods:
			foo = group_spec.key_getter(mod)
			for bar in foo:
				key, name = bar
				group_keys[key] = name
				group_mods[key].append(mod)

		grp_entries = []
		for key, name in group_keys.items():
			grp_entries.append(GroupEntry(
				id=key,
				name=name,
				mods=tuple(group_mods.get(key))
			))

		groups.append(Group(spec=group_spec, entries=grp_entries))

	return tuple(groups)


def generate_search_data(all_mods: Tuple[Mod]):

	mods = {}
	all_words = []

	def preprocess_words(mod_id: str, string: str, prio: int):
		words = string.lower().split(' ')
		for word in words:
			all_words.append([word, prio, mod_id])

	for mod in all_mods:
		mods[mod.id] = {
			'name': mod.info.name,
			'creators': mod.info.creators,
			'description': mod.info.description,
			'thumbnail': mod.image_preview
		}
		preprocess_words(mod.id, mod.info.name, 10)
		for creator in mod.info.creators:
			preprocess_words(mod.id, creator.name, 8)
		preprocess_words(mod.id, mod.info.description, 3)

	data = {'mods': mods, 'words': all_words}

	import json
	with g_target.checked_open(PurePath('search-data.json'), 'w') as f:
		json.dump(data, f, ensure_ascii=False, indent=1)


def generate_index_json(all_mods: Tuple[Mod]):
	
	json_mods = []
	json_mods.append("nextmod-v1")
	for mod in all_mods:
		json_mods.append({
			'id': mod.id
		})
	
	import json
	with g_target.checked_open(PurePath('index.json'), 'w') as f:
		json.dump(json_mods, f, ensure_ascii=False)
	

def main():
	parser = argparse.ArgumentParser(description='Static site generator for browsing mod repositories')
	parser.add_argument('-s', '--source', choices=['local', 'gitlab', 'github', 'remotes'])
	parser.add_argument('--dev-skip-image-transcode', action='store_true')

	app_args = parser.parse_args()
	
	cfg_file = ConfigFile()
	with open('./nextmod-config.md', 'rb') as file:
		cfg_file.parse(file.read())
	
	config = cfg_file.get_result()
	

	if app_args.source == 'local':
		source = DirectorySource()
	elif app_args.source == 'gitlab':
		source = GitlabSource()
	elif app_args.source == 'github':
		source = GitHubSource()
	elif app_args.source == 'remotes':
		source = GitHubSource()
	else:
		raise Exception('Unexpected source argument')

	all_mods = load_mod_repositories(source.list_mods())
	all_grps = build_groups(all_mods)

	for mod in all_mods:
		g_log.info('Generating mod page for: {}'.format(mod.repository.id))
		try:
			render_mod_page(config, app_args, all_mods, all_grps, mod)
		except Exception as ex:
			g_log.exception(ex)

	g_log.info('Generating search data')
	generate_search_data(all_mods)
	
	g_log.info("Rendering Common pages")
	render_about_page(config, all_mods, all_grps)
	
	g_log.info('Generating index pages')
	render_index_pages(config, all_mods, all_grps)

	generate_index_json(all_mods)

	g_log.info('DONE')


if __name__ == "__main__":
	main()
