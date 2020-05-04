# Copyright (c) 2020, Eli2
# SPDX-License-Identifier: AGPL-3.0-or-later


import markdown
from .render import *


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
