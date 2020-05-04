# Copyright (c) 2020, Eli2
# SPDX-License-Identifier: AGPL-3.0-or-later

import io
from pathlib import PurePath
from PIL import Image

import markdown
from generator.markdown_flavour import NextmodMarkdown

from .common import g_public_dir, g_log, Mod, PreviewEntry
from .render import render_main_page

def render_mod_page(app_args, all_mods, all_grps, mod: Mod):
	out_mod_dir = g_public_dir / 'mw' / str(mod.id)
	out_mod_dir.mkdir(parents=True, exist_ok=True)
	
	out_img_dir = out_mod_dir / 'images'
	out_img_dir.mkdir(parents=True, exist_ok=True)
	
	mod.link = 'mw/{}/index.html'.format(mod.id)
	
	# images
	
	banner_picture = None
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
			g_log.log("Failed to load image: {}".format(input_file_name))
			g_log.exception(ex)
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
		
		picture = []
		if transcode_image:
			img = image.convert('RGB')
			name = image_id + '.jpg'
			with open(out_img_dir / name, 'wb') as f:
				img.save(f, 'JPEG')
				picture.append(('mw/' + mod.id + '/images/' + name, 'image/webp'))
			
			name = image_id + '.webp'
			with open(out_img_dir / name, 'wb') as f:
				image.save(f, 'WebP', quality=100)
				picture.append(('mw/' + mod.id + '/images/' + name, 'image/webp'))
		
		else:
			name = input_file_name
			with open(out_img_dir / image_output_file_name, 'wb') as f:
				image.save(f)
				picture.append(('mw/' + mod.id + '/images/' + name, 'image/webp'))
		
		if input_file_name.startswith('banner'):
			banner_picture = picture
		elif input_file_name.startswith('preview'):
			thumb_file_name = image_id + '_thumb.webp'
			
			thumb_pictures = []
			
			if app_args.dev_skip_image_transcode:
				pass
			else:
				thumb = image.copy()
				thumb_size = (360, 360)
				thumb.thumbnail(thumb_size, Image.ANTIALIAS)
				try:
					img = thumb.convert('RGB')
					name = image_id + '_thumb.jpg'
					with open(out_img_dir / name, 'wb') as f:
						img.save(f, 'JPEG')
						thumb_pictures.append(('mw/' + mod.id + '/images/' + name, 'image/jpeg'))
					
					name = image_id + '_thumb.webp'
					with open(out_img_dir / name, 'wb') as f:
						thumb.save(f, 'WebP')
						thumb_pictures.append(('mw/' + mod.id + '/images/' + name, 'image/webp'))
				
				except Exception as ex:
					g_log.warning("Failed to write: {}", image_id, ex)
			
			thumb_url = 'images/{}'.format(thumb_file_name)
			
			e = PreviewEntry(
				id=image_id,
				prev_id=None,
				next_id=None,
				picture=picture,
				thumb=thumb_url,
				thumb_pictures=thumb_pictures
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
