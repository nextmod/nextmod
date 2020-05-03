#!/usr/bin/env python3

# Copyright (c) 2020, Eli2
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import io
import logging
import argparse

from pathlib import Path, PurePath
from dataclasses import dataclass
from collections import defaultdict
from typing import Any, NamedTuple, List, Set, Tuple, Dict, Callable

from datetime import time
from datetime import datetime

from generator.image_processor import ImageProcessor
import re
from PIL import Image
from dataclasses import field
from enum import Enum


from jinja2 import Environment, FileSystemLoader, select_autoescape
import markdown

from generator.backends import *
from generator.file_parsers import *
from generator.markdown_flavour import NextmodMarkdown

logging.basicConfig(
	format='%(asctime)s %(levelname)-8s %(message)s',
	level=logging.INFO,
	datefmt='%Y-%m-%d %H:%M:%S')

# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


jinja_env = Environment(
	loader=FileSystemLoader(['./page', './page-templates']),
	autoescape=select_autoescape(['html', 'xml']),
	lstrip_blocks = True,
	trim_blocks = True
)

def human_bytes(size):
	for x in ['bytes', 'KB', 'MB', 'GB']:
		if size < 1024.0:
			return "%3.2f%s" % (size, x)
		size /= 1024.0


jinja_env.filters['human_bytes'] = human_bytes



g_public_dir = Path('./public')

image_processor = ImageProcessor()


@dataclass
class Mod:
	repository: Repository
	id: int = 0
	name: str = ''
	link: str = ''
	image_banner: str = ''
	image_preview: str = ''
	image_gallery: List = field(default_factory=list)
	authors: str = ''
	description: str = ''
	last_updated: str = ''
	star_count: int = 0

	info: InfoFile = field(default_factory=InfoFile)
	tags: TagsFile = field(default_factory=TagsFile)

	info_html: str = ''
	page_html: str = ''
	
	data_files: Tuple[str] = field(default_factory=tuple)
	data_files_size: int = 0


class GroupSpec(NamedTuple):
	id: str
	name: str
	name_singular: str
	key_getter: Callable[[Mod], List[Tuple[str, str]]]

class GroupEntry(NamedTuple):
	id: str
	name: str
	mods: Tuple[Mod]

class Group(NamedTuple):
	spec: GroupSpec
	entries: Tuple[GroupEntry]


@dataclass
class PreviewEntry:
	id: str
	next_id: str
	prev_id: str
	img: str
	thumb: str


from datetime import datetime
page_generation_time = datetime.now()

def load_mod_repositories(repositories) -> Tuple[Mod]:
	logger.info('Loading mod data ...')

	foo = list(repositories)

	mods = []
	for mod_repository in foo:
		logger.info('Loading mod data: %s', mod_repository.id)
		
		mod = Mod(repository=mod_repository)
		mod.id = mod_repository.id
		
		date = mod_repository.get_last_update()
		date_string = date.strftime('%Y-%m-%d %H:%M')
		mod.last_updated = date_string
		
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
		GroupSpec('creator', 'Creators', 'Creator', lambda m: [(m.info.creator_id, m.info.creator)]),
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


def render_main_page(page_name: PurePath, render_dict: dict, out_page_name: PurePath = None):
	
	template = jinja_env.get_template(str(page_name))

	if not out_page_name:
		out_page_name = page_name

	depth = len(out_page_name.parts) - 1
	if depth == 0:
		current_relref = '.'
	else:
		current_relref = '/'.join(['..'] * depth)

	def mkref(base, name, suffix):
		foo = [base, name, suffix]
		res = current_relref + '/' + '/'.join(foo)
		return res
	
	render_dict['mkref'] = mkref

	def foo(*args):
		res = current_relref + '/' + '/'.join(args)
		return res

	render_dict['relpath'] = foo
	
	def include_css(*paths):
		lines = []
		for path in paths:
			foo = current_relref + '/' + path
			line = '<link rel="stylesheet" href="{}">'.format(foo)
			lines.append(line)
		return '\n'.join(lines)
	
	render_dict['include_css'] = include_css
	
	render_dict['page_generation_time'] = page_generation_time

	rendered = template.render(render_dict)

	p = g_public_dir / out_page_name
	os.makedirs(p.parent, exist_ok=True)

	with open(p, 'w') as f:
		f.write(rendered)


def render_mod_page(app_args, all_mods, all_grps, mod: Mod):

	out_mod_dir = g_public_dir / 'mw' / str(mod.id)
	out_mod_dir.mkdir(parents=True, exist_ok=True)

	out_img_dir = out_mod_dir / 'images'
	out_img_dir.mkdir(parents=True, exist_ok=True)

	mod.link = 'mw/{}/index.html'.format(mod.id)

	# images

	image_banner = None
	image_previews = []

	page_images_gen = mod.repository.list_dir(dir_path='images')
	for input_file_name in page_images_gen:
		if input_file_name.startswith('preview.md'):
			continue

		image_id = input_file_name.split('.')[0]

		try:
			image_data = mod.repository.get_file(file_path='images/' + input_file_name)
			image = Image.open(io.BytesIO(image_data))
		# image.verify()
		except Exception as ex:
			logger.log("Failed to load image: {}".format(input_file_name))
			logger.exception(ex)
			continue

		transcode_image = False
		image_formats_to_transcode_lossless = ['PNG']
		if image.format in image_formats_to_transcode_lossless:
			image_output_file_name = image_id + '.webp'
			transcode_image = True
		else:
			image_output_file_name = input_file_name

		if app_args.dev_skip_image_transcode:
			transcode_image = False

		if transcode_image:
			with open(out_img_dir / image_output_file_name, 'wb') as f:
				image.save(f, "WebP", quality=100) # lossless=True
		else:
			with open(out_img_dir / image_output_file_name, 'wb') as f:
				image.save(f)

		img_url = 'images/{}'.format(image_output_file_name)

		if input_file_name.startswith('banner'):
			image_banner = img_url
		elif input_file_name.startswith('preview'):
			thumb_file_name = image_id + '_thumb.webp'

			if app_args.dev_skip_image_transcode:
				pass
			else:
				thumb = image.copy()
				thumb_size = (360, 360)
				thumb.thumbnail(thumb_size, Image.ANTIALIAS)
				try:
					with open(out_img_dir / thumb_file_name, 'wb') as f:
						thumb.save(f, "WebP")
				except Exception as ex:
					logger.warning("Failed to write: {}", image_id, ex)

			thumb_url = 'images/{}'.format(thumb_file_name)

			e = PreviewEntry(id=image_id, prev_id=None, next_id=None, img=img_url, thumb=thumb_url)
			image_previews.append(e)

	image_previews.sort(key=lambda x: x.id)

	for i, preview in enumerate(image_previews):
		if i == 0:
			preview.prev_id = image_previews[-1].id
			preview.next_id = image_previews[i + 1].id
		elif i == len(image_previews) - 1:
			preview.prev_id = image_previews[i - 1].id
			preview.next_id = image_previews[0].id
		else:
			preview.prev_id = image_previews[i - 1].id
			preview.next_id = image_previews[i + 1].id

	mod.image_banner = image_banner
	mod.image_previews = image_previews
	mod.image_preview = 'mw/' + mod.id + '/' + mod.image_previews[0].thumb

	# page
	page_files_gen = mod.repository.list_dir(dir_path='page')
	for file_name in page_files_gen:
		if file_name.endswith('.md'):
			continue

		file_data = mod.repository.get_file(file_path='page/' + file_name)
		with open(out_mod_dir / file_name, 'wb') as f:
			f.write(file_data)

	info_data = mod.repository.get_file(file_path='mod-info.md')
	page_data = mod.repository.get_file(file_path='page/page.md')

	if info_data:
		mod.info_html = markdown.markdown(info_data.decode('utf-8'), extensions=[])

	if page_data:
		mod.page_html = markdown.markdown(page_data.decode('utf-8'), extensions=['nl2br', NextmodMarkdown()])

	out_path = PurePath('mw') / str(mod.id) / 'index.html'

	render_args = {
		'mods': all_mods,
		'groups': all_grps,
		'mod': mod
	}

	render_main_page(PurePath('mod.html'), render_args, out_path)


def render_about_page(render_args):
	
	path = Path('./about.md')
	with open(path, 'r') as file:
		about_md = file.read()
		about_html = markdown.markdown(about_md, extensions=[])

	cpy = render_args.copy()
	cpy['about_html'] = about_html
	render_main_page(PurePath('about.html'), cpy)


def render_index_pages(all_mods, all_grps):

	render_args = {
		'mods': all_mods,
		'groups': all_grps
	}
	
	render_about_page(render_args)
	
	class SortBy(NamedTuple):
		id: str
		name: str
		reverse: bool
		key_getter: Callable[[Mod], Any]
		
	class SortOrder(NamedTuple):
		id: str
		reverse: bool
	
	sort_bys = (
		SortBy('', 'Update Date', True, lambda mod: mod.info.update_date),
		SortBy('-name', 'Name', False, lambda mod: mod.info.name),
		SortBy('-release-date', 'Release Date', True, lambda mod: mod.info.release_date),
		SortBy('-file-count', 'File Count', False, lambda mod: len(mod.data_files)),
		SortBy('-file-size', 'File Size', False, lambda mod: mod.data_files_size),
	)
	
	sort_orders = (
		SortOrder('', False),
		SortOrder('-dsc', True)
	)
	
	def render_mod_index(base_name, mods):
		
		class SortLink(NamedTuple):
			name: str
			asc_url: str
			dsc_url: str
		
		sort_links = []
		for sort_by in sort_bys:
			sort_links.append(SortLink(
				name=sort_by.name,
				asc_url=base_name + sort_by.id + '.html',
				dsc_url=base_name + sort_by.id + '-dsc.html'
			))
		render_args['sort_links'] = sort_links
		
		for sort_by in sort_bys:
			render_args['sort_by'] = sort_by
			for sort_order in sort_orders:
				render_args['sort_order'] = sort_order
				file_name = PurePath(base_name + sort_by.id + sort_order.id + '.html')
				
				reverse = sort_by.reverse
				if sort_order.reverse:
					reverse = not reverse
				
				sorted_mods = list(mods)
				sorted_mods.sort(key=sort_by.key_getter, reverse=reverse)
					
				render_args['mods'] = sorted_mods
				render_args['base_name'] = base_name
				render_main_page(PurePath('index.html'), render_args, file_name)
	
	render_mod_index('index', all_mods)
	
	for group in all_grps:
		render_args['group'] = group
		render_main_page(PurePath('group.html'), render_args, PurePath(group.spec.id, 'index.html'))
		for entry in group.entries:
			render_args['group_entry'] = entry
			render_mod_index(group.spec.id + '/' + entry.id, entry.mods)


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
			'creator': mod.info.creator,
			'description': mod.info.description,
			'thumbnail': mod.image_preview
		}
		preprocess_words(mod.id, mod.info.name, 10)
		preprocess_words(mod.id, mod.info.creator, 8)
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

	logger.info('Generating index pages')
	render_index_pages(all_mods, all_grps)

	logger.info('DONE')


if __name__ == "__main__":
	main()
