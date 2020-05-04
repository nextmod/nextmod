# Copyright (c) 2020, Eli2
# SPDX-License-Identifier: AGPL-3.0-or-later

import os

from datetime import datetime
from pathlib import PurePath

from jinja2 import Environment, FileSystemLoader, select_autoescape

from generator.common import g_public_dir


jinja_env = Environment(
	loader=FileSystemLoader(['./page', './page-templates']),
	autoescape=select_autoescape(['html', 'xml']),
	lstrip_blocks=True,
	trim_blocks=True
)

jinja_env.globals['g_page_generation_time'] = datetime.now()


def human_bytes(size):
	for x in ['bytes', 'KB', 'MB', 'GB']:
		if size < 1024.0:
			return "%3.2f%s" % (size, x)
		size /= 1024.0
		
jinja_env.filters['human_bytes'] = human_bytes

from markupsafe import Markup

def html_indent(s, depth):
	newline = Markup("\n")
	s += newline
	rv = (newline + Markup("\t" * depth)).join(s.splitlines())
	return rv

jinja_env.filters['ind'] = html_indent


def render_main_page(page_name: PurePath, render_dict: dict, out_page_name: PurePath = None):
	
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
	
	def makepath(*args):
		if len(args) == 1 and isinstance(args[0], tuple):
			asf = PurePath(*args[0])
		else:
			asf = PurePath(*args)
		
		res = PurePath(current_relref) / asf
		return res
	
	jinja_env.filters['makepath'] = makepath
	
	template = jinja_env.get_template(str(page_name))
	rendered = template.render(render_dict)
	
	p = g_public_dir / out_page_name
	os.makedirs(p.parent, exist_ok=True)
	
	with open(p, 'w') as f:
		f.write(rendered)
