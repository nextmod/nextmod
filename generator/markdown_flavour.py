# Copyright (c) 2020, Eli2
# SPDX-License-Identifier: AGPL-3.0-or-later


import xml.etree.ElementTree as etree
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor


class NextmodMarkdown(Extension):
	def extendMarkdown(self, md):
		md.treeprocessors.register(NextmodTreeprocessor(md), 'mextmod-flavor', 175)

class NextmodTreeprocessor(Treeprocessor):
	def run(self, root):
		class_to_add = None
		
		def add_class(el, clazz):
			old = child.get('class')
			if old:
				new = old + ' ' + clazz
			else:
				new = clazz
			child.set('class', new)
		
		for child in root:
			if child.tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']:
				if child.text.startswith('-->') and child.text.endswith('<--'):
					child.text = child.text[3:-3]
					add_class(child, 'center')
			
			if child.tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
				if "FAQ" in child.text:
					class_to_add = 'faq'
				else:
					class_to_add = None
			
			if class_to_add:
				add_class(child, class_to_add)
