# Copyright (c) 2020, Eli2
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
from pathlib import Path, PurePath

from .common import g_log

class DirectoryTarget():
	g_public_dir: Path
	
	def __init__(self):
		self.g_public_dir = Path('./public').resolve(strict=True)
		if not self.g_public_dir.exists():
			raise Exception('Target directory does not exist')
	
		g_log.info(f'Writing to directory: {self.g_public_dir}')
		
	def checked_open(self, path: PurePath, mode='r'):
		if not isinstance(path,  PurePath):
			raise Exception('Wrong parameter type"')
		
		abs_path = self.g_public_dir / path
		resolved_path = abs_path.resolve()
		
		common_prefix = os.path.commonprefix([self.g_public_dir, resolved_path])
		if not os.path.samefile(self.g_public_dir, common_prefix):
			raise Exception(f'Weird file loacation: {resolved_path}')
		
		os.makedirs(resolved_path.parent, exist_ok=True)
		
		buffer_size = 1024 * 8
		if mode == 'r' or mode == 'w':
			encoding = 'utf-8'
		else:
			encoding = None
		
		return open(resolved_path, mode, buffer_size, encoding)


g_target = DirectoryTarget()
