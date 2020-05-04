# Copyright (c) 2020, Eli2
# SPDX-License-Identifier: AGPL-3.0-or-later

import os

from datetime import datetime
from pathlib import PurePath
from jinja2 import Environment, FileSystemLoader, select_autoescape

from generator.common import *
from generator.source import *


jinja_env = Environment(
	loader=FileSystemLoader(['./page', './page-templates']),
	autoescape=select_autoescape(['html', 'xml']),
	lstrip_blocks = True,
	trim_blocks = True
)

jinja_env.globals['g_page_generation_time'] = datetime.now()


def human_bytes(size):
	for x in ['bytes', 'KB', 'MB', 'GB']:
		if size < 1024.0:
			return "%3.2f%s" % (size, x)
		size /= 1024.0


jinja_env.filters['human_bytes'] = human_bytes


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
	
	jinja_env.filters['relpath'] = foo
	render_dict['relpath'] = foo
	
	def include_css(*paths):
		lines = []
		for path in paths:
			foo = current_relref + '/' + path
			line = '<link rel="stylesheet" href="{}">'.format(foo)
			lines.append(line)
		return '\n'.join(lines)
	
	render_dict['include_css'] = include_css
	
	rendered = template.render(render_dict)
	
	p = g_public_dir / out_page_name
	os.makedirs(p.parent, exist_ok=True)
	
	with open(p, 'w') as f:
		f.write(rendered)
