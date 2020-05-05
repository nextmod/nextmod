# Copyright (c) 2020, Eli2
# SPDX-License-Identifier: AGPL-3.0-or-later

from pathlib import Path, PurePath
from markdown import markdown

from .render import render_main_page


def render_about_page(all_mods, all_grps):
	render_args = {
		'mods': all_mods,
		'groups': all_grps
	}
	
	with open('./about.md', encoding='utf-8') as file:
		about_md = file.read()
		
	with open('./LICENSE/agpl-3.0.md', encoding='utf-8') as file:
		license_md = file.read()
	
	about_html = markdown(about_md, extensions=['nl2br', 'fenced_code'])
	license_html = markdown(license_md, extensions=['nl2br', 'fenced_code'])
	
	cpy = render_args.copy()
	cpy['about_html'] = about_html
	cpy['license_html'] = license_html
	render_main_page(PurePath('about.html'), cpy)
