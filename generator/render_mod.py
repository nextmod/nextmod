# Copyright (c) 2020, Eli2
# SPDX-License-Identifier: AGPL-3.0-or-later

from io import BytesIO

from pathlib import PurePath
from PIL import Image
from typing import Optional, Tuple

import markdown
from generator.markdown_flavour import NextmodMarkdown

from .common import g_log, PicSrc, Picture, Mod, PreviewEntry
from .render import render_main_page
from .target import g_target


def parse_image_filename(filename: str) -> Optional[Picture]:
	dot_split = filename.rsplit('.')
	if len(dot_split) != 2:
		g_log.warn("Image files must have an extension")
		return None
	base_name = dot_split[0]
	base_ext = dot_split[1]

	dash_split = base_name.split('-', 4)
	image_type = dash_split[0]
	if image_type == 'banner':
		return Picture(
			base_name=base_name,
			base_ext=base_ext,
			type=image_type,
			number='',
			variant='',
			description=''
		)
	elif image_type == 'preview':
		if len(dash_split) < 2:
			g_log.warn("Preview images require at least a number")
			return None

		number = dash_split[1]

		if len(dash_split) == 2:
			variant = None
			description = None
		elif len(dash_split) == 3:
			if dash_split[2] in ['a', 'b']:
				variant = dash_split[2]
				description = None
			else:
				variant = None
				description = dash_split[2]
		else:
			variant = dash_split[2]
			description = dash_split[3]

		return Picture(
			base_name=base_name,
			base_ext=base_ext,
			type=image_type,
			number=number,
			variant=variant,
			description=description
		)
	else:
		g_log.warn("Unknown image type prefix found %", image_type)


def render_mod_page(config, app_args, all_mods: Tuple[Mod], all_grps, mod: Mod):
	
	mod_directory = PurePath('mw') / mod.id	
	image_directory = mod_directory / 'image'
		
	mod.link = 'mw/{}/index.html'.format(mod.id)
	
	# images
	def out_rel_url(name: str):
		return PurePath('mw') / mod.id / 'image' / name 
	
	banner_picture = None
	image_previews = []
	
	page_images_gen = mod.repository.list_dir(dir_path=PurePath('image'))
	for input_file_name in page_images_gen:

		image_info = parse_image_filename(input_file_name)
		if not image_info:
			continue

		try:
			image_data = mod.repository.get_file(file_path='image/' + input_file_name)
			image = Image.open(BytesIO(image_data))
			# image.verify()
		except Exception as ex:
			g_log.log("Failed to load image: {}".format(input_file_name))
			g_log.exception(ex)
			continue
		
		valid_ext = {}
		valid_ext['PNG'] = ['png']
		valid_ext['JPEG'] = ['jpg', 'jpeg']
		
		if not valid_ext[image.format] and not image_info.base_ext in valid_ext[image.format]:
			g_log.error('Image file extension %s does not match actual image type %s', image_info.base_ext,
			            image.format)
			continue
		
		picture = []
		if image.format in ['PNG']:
			img = image.convert('RGB')
			name = image_info.out_name('jpg') 
			with g_target.checked_open(image_directory / name, 'wb') as f:
				img.save(f, 'JPEG')
				picture.append(PicSrc(out_rel_url(name), 'image/jpeg'))
			
			name = image_info.out_name('webp')
			with g_target.checked_open(image_directory / name, 'wb') as f:
				image.save(f, 'WebP', quality=100)
				picture.append(PicSrc(out_rel_url(name), 'image/webp'))
		
		else:
			name = image_info.out_name(image_info.base_ext)
			mime = Image.MIME[image.format]
			with g_target.checked_open(image_directory / name, 'wb') as f:
				image.save(f)
				picture.append(PicSrc(out_rel_url(name), mime))
		
		if image_info.type == 'banner':
			banner_picture = picture
		elif image_info.type == 'preview':
			thumb_pictures = []
			
			thumb = image.copy()
			thumb_size = (360, 360)
			thumb.thumbnail(thumb_size, Image.ANTIALIAS)
			
			img = thumb.convert('RGB')
			name = image_info.out_name('jpg', 'thumb')
			with g_target.checked_open(image_directory / name, 'wb') as f:
				img.save(f, 'JPEG')
				thumb_pictures.append(PicSrc(out_rel_url(name), 'image/jpeg'))
			
			name = image_info.out_name('webp', 'thumb')
			with g_target.checked_open(image_directory / name, 'wb') as f:
				thumb.save(f, 'WebP')
				thumb_pictures.append(PicSrc(out_rel_url(name), 'image/webp'))

			
			e = PreviewEntry(
				id=image_info.get_id(),
				prev_id=None,
				next_id=None,
				picture=picture,
				thumb_pictures=tuple(thumb_pictures)
			)
			
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
	
	mod.banner_picture = banner_picture
	mod.image_previews = image_previews
	
	if mod.image_previews:
		mod.picture_preview = mod.image_previews[0].thumb_pictures
	
	render_mod_page_main(config, all_mods, all_grps, mod)


def render_mod_page_main(config, all_mods, all_grps, mod: Mod):
	
	mod_directory = PurePath('mw') / mod.id	
	
	info_data = mod.repository.get_file(PurePath('mod-info.md'))
	mod.info_html = markdown.markdown(info_data.decode('utf-8'), extensions=[])
	
	page_files_gen = mod.repository.list_dir(PurePath('page'))
	for file_name in page_files_gen:
		if file_name == 'index.html':
			g_log.warn('Reserved filename in page directory, skipped')
			continue
		if file_name == 'image':
			g_log.warn('Reserved filename in page directory, skipped')
			continue
		
		# TODO more filtering ?
		
		# Just copy everything
		file_data = mod.repository.get_file(file_path='page/' + file_name)
		with g_target.checked_open(mod_directory / file_name, 'wb') as f:
			f.write(file_data)
		
		if file_name == 'page.md':
			mod.page_html = markdown.markdown(file_data.decode('utf-8'), extensions=['nl2br', NextmodMarkdown()])
			out_path = mod_directory / 'index.html'
			
			render_args = {
				'config': config,
				'mods': all_mods,
				'groups': all_grps,
				'mod': mod
			}
			
			render_main_page(PurePath('mod.html'), render_args, out_path)
