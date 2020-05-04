# Copyright (c) 2020, Eli2
# SPDX-License-Identifier: AGPL-3.0-or-later

import io
from pathlib import PurePath
from PIL import Image
from typing import Optional, Tuple

import markdown
from generator.markdown_flavour import NextmodMarkdown

from .common import g_public_dir, g_log, PicSrc, Picture, Mod, PreviewEntry
from .render import render_main_page





def render_mod_page(app_args, all_mods: Tuple[Mod], all_grps, mod: Mod):
	
	out_mod_dir = g_public_dir / 'mw' / mod.id
	out_mod_dir.mkdir(parents=True, exist_ok=True)
	
	out_img_dir = out_mod_dir / 'image'
	out_img_dir.mkdir(parents=True, exist_ok=True)
	
	mod.link = 'mw/{}/index.html'.format(mod.id)
	
	# images
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
			image = Image.open(io.BytesIO(image_data))
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
		

		"""
		image_id = input_file_name.split('.')[0]
		
		
		transcode_image = False
		image_formats_to_transcode_lossless = ['PNG']
		if image.format in image_formats_to_transcode_lossless:
			image_output_file_name = image_id + '.webp'
			transcode_image = True
		else:
			image_output_file_name = input_file_name
		
		if app_args.dev_skip_image_transcode:
			transcode_image = False
		"""
		
		picture = []
		if image.format in ['PNG']:
			img = image.convert('RGB')
			name = image_info.out_name('jpg') 
			with open(out_img_dir / name, 'wb') as f:
				img.save(f, 'JPEG')
				picture.append(PicSrc(out_rel_url(name), 'image/jpeg'))
			
			name = image_info.out_name('webp')
			with open(out_img_dir / name, 'wb') as f:
				image.save(f, 'WebP', quality=100)
				picture.append(PicSrc(out_rel_url(name), 'image/webp'))
		
		else:
			name = image_info.out_name(image_info.base_ext)
			mime = Image.MIME[image.format]
			with open(out_img_dir / name, 'wb') as f:
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
			with open(out_img_dir / name, 'wb') as f:
				img.save(f, 'JPEG')
				thumb_pictures.append(PicSrc(out_rel_url(name), 'image/jpeg'))
			
			name = image_info.out_name('webp', 'thumb')
			with open(out_img_dir / name, 'wb') as f:
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
	
	mod.picture_preview = mod.image_previews[0].thumb_pictures
	
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
