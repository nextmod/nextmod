# Copyright (c) 2020, Eli2
# SPDX-License-Identifier: AGPL-3.0-or-later

import os

from datetime import datetime
from pathlib import PurePath

from markupsafe import Markup
from jinja2 import Environment, FileSystemLoader, select_autoescape
from jinja2 import contextfilter

from generator.target import g_target


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


def html_indent(s, depth):
	newline = Markup("\n")
	s += newline
	rv = (newline + Markup("\t" * depth)).join(s.splitlines())
	return rv


@contextfilter
def makepath(ctx, *args):
	current_path = ctx.environment.globals['g_BAR']

	if len(args) == 1 and isinstance(args[0], tuple):
		target = PurePath(*args[0])
	else:
		target = PurePath(*args)

	current_depth = len(current_path.parent.parts)
	
	# os.path.commonprefix(list)
	
	i = 0
	for a, b in zip(current_path.parent.parts, target.parent.parts):
		if a != b:
			break;
		i += 1
	
	walk_up = ['.'] + ['..'] * (current_depth - i)
	rel_path = PurePath(*walk_up) / PurePath(*target.parts[i:])
	# g_log.info(f'src: {current_path} dst {target} -> rel {rel_path}')
	return rel_path

jinja_env.filters['human_bytes'] = human_bytes
jinja_env.filters['ind'] = html_indent
jinja_env.filters['makepath'] = makepath


def render_main_page(page_name: PurePath, render_dict: dict, out_page_name: PurePath = None):
	
	if not out_page_name:
		out_page_name = page_name
	
	jinja_env.globals['g_BAR'] = out_page_name
	
	template = jinja_env.get_template(str(page_name))
	rendered = template.render(render_dict)
	
	with g_target.checked_open(out_page_name, 'w') as f:
		f.write(rendered)
