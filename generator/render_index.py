# Copyright (c) 2020, Eli2
# SPDX-License-Identifier: AGPL-3.0-or-later

from pathlib import PurePath
from typing import Any, Callable, NamedTuple

from .common import Mod
from .render import render_main_page

def render_index_pages(config, all_mods, all_grps):
	
	render_args = {
		'config': config,
		'mods': all_mods,
		'groups': all_grps
	}
	
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
	
	def render_mod_index(base_path, base_name, mods):
		
		class SortLink(NamedTuple):
			id: str
			name: str
			asc_url: str
			dsc_url: str
		
		sort_links = []
		for sort_by in sort_bys:
			sort_links.append(SortLink(
				id=sort_by.id,
				name=sort_by.name,
				asc_url=base_path / (base_name + sort_by.id + '.html'),
				dsc_url=base_path / (base_name + sort_by.id + '-dsc.html')
			))
		render_args['sort_links'] = sort_links
		
		for sort_by in sort_bys:
			render_args['sort_by'] = sort_by
			for sort_order in sort_orders:
				render_args['sort_order'] = sort_order
				
				file_name = base_path / (base_name + sort_by.id + sort_order.id + '.html')
				
				reverse = sort_by.reverse
				if sort_order.reverse:
					reverse = not reverse
				
				sorted_mods = list(mods)
				sorted_mods.sort(key=sort_by.key_getter, reverse=reverse)
				
				render_args['mods'] = sorted_mods
				render_args['base_name'] = base_name
				render_main_page(PurePath('index.html'), render_args, file_name)
	
	render_mod_index(PurePath(), 'index', all_mods)
	
	for group in all_grps:
		render_args['group'] = group
		render_main_page(PurePath('group.html'), render_args, PurePath(group.spec.id, 'index.html'))
		for entry in group.entries:
			render_args['group_entry'] = entry
			render_mod_index(PurePath(group.spec.id, entry.id), 'index', entry.mods)
