#!/usr/bin/env python3

# Copyright (c) 2020, Eli2
# SPDX-License-Identifier: AGPL-3.0-or-later


import argparse
from collections import defaultdict

from generator.image_processor import ImageProcessor
from generator.render_mod import *
from generator.render_index import *
from generator.source_directory import DirectorySource
from generator.source_gitlab import GitlabSource


image_processor = ImageProcessor()

def load_mod_repositories(repositories) -> Tuple[Mod]:
	logger.info('Loading mod data ...')

	foo = list(repositories)

	mods = []
	for mod_repository in foo:
		logger.info('Loading mod data: %s', mod_repository.id)
		
		mod = Mod(repository=mod_repository)
		mod.id = mod_repository.id
				
		mod.star_count = mod_repository.get_star_count()
		mod.data_files = mod_repository.list_data_files()
		mod.data_files_size = sum(size for name, size in mod.data_files)
		
		mod.info.parse(mod_repository.get_file('mod-info.md'))
		mod.tags.parse(mod_repository.get_file('tags.md'))

		mods.append(mod)
	return tuple(mods)


def build_groups(all_mods: Tuple[Mod]) -> Tuple[Group]:

	group_specs = (
		GroupSpec('category', 'Categories', 'Category', lambda m: [(m.info.category_id, m.info.category)]),
		GroupSpec('tag', 'Tags', 'Tag', lambda m: m.tags.entries),
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


def render_about_page(all_mods, all_grps):
	
	render_args = {
		'mods': all_mods,
		'groups': all_grps
	}
	
	path = Path('./about.md')
	with open(path, 'r') as file:
		about_md = file.read()
		about_html = markdown.markdown(about_md, extensions=[])

	cpy = render_args.copy()
	cpy['about_html'] = about_html
	render_main_page(PurePath('about.html'), cpy)



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

	data_file = g_public_dir / 'search-data.json'

	import json
	with open(data_file, 'w', encoding='utf-8') as f:
		json.dump(data, f, ensure_ascii=False, indent=1)


def main():
	parser = argparse.ArgumentParser(description='Static site generator for browsing mod repositories')
	parser.add_argument('-s', '--source', choices=['local', 'gitlab'])
	parser.add_argument('--dev-skip-image-transcode', action='store_true')

	app_args = parser.parse_args()

	if app_args.source == 'local':
		source = DirectorySource()
	else:
		source = GitlabSource()

	all_mods = load_mod_repositories(source.list_mods())
	all_grps = build_groups(all_mods)

	for mod in all_mods:
		logger.info('Generating mod page for: {}'.format(mod.repository.id))
		try:
			render_mod_page(app_args, all_mods, all_grps, mod)
		except Exception as ex:
			logger.exception(ex)

	logger.info('Generating search data')
	generate_search_data(all_mods)
	
	logger.info("Rendering Common pages")
	render_about_page(all_mods, all_grps)
	
	logger.info('Generating index pages')	
	render_index_pages(all_mods, all_grps)

	logger.info('DONE')


if __name__ == "__main__":
	main()
