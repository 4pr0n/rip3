#!/usr/bin/python

from os       import path, getcwd, sep as ossep, mkdir
from PIL      import Image # Python Image Library
from commands import getstatusoutput

class ImageUtils(object):
	
	MAXIMUM_THUMBNAIL_SIZE = 1024 * 1024 * 5
	MAXIMUM_THUMBNAIL_DIM  = 4000
	'''
		Create thumbnail from existing image file.
		Raises exception if unable to save thumbnail
	'''
	@staticmethod
	def create_thumbnail(image, saveas):
		if image.lower().endswith('.mp4') or \
		   image.lower().endswith('.flv') or \
			 image.lower().endswith('.wmv'):
			return ImageUtils.create_video_thumbnail(image, saveas)
		if path.getsize(image) > ImageUtils.MAXIMUM_THUMBNAIL_SIZE:
			raise Exception('Image too large: %db %db' % 
					(path.getsize(image), ImageUtils.MAXIMUM_THUMBNAIL_SIZE))
		try:
			im = Image.open(image)
		except Exception, e:
			raise Exception('failed to create thumbnail: %s' % str(e))
		(width, height) = im.size
		if width  > ImageUtils.MAXIMUM_THUMBNAIL_DIM or \
		   height > ImageUtils.MAXIMUM_THUMBNAIL_DIM:
			raise Exception(
					'Image too large: %dx%d > %dpx' % 
					(width, height, ImageUtils.MAXIMUM_THUMBNAIL_DIM))

		if im.mode != 'RGB': im = im.convert('RGB')
		im.thumbnail( (200,200), Image.ANTIALIAS)
		im.save(saveas, 'JPEG')
		return (saveas, im.size[0], im.size[1])

	''' 
		Create thumbnail for video file using ffmpeg.
		Raises exception if unable to save video thumbnail
	'''
	@staticmethod
	def create_video_thumbnail(video, saveas):
		if saveas.lower().endswith('.mp4') or \
			 saveas.lower().endswith('.flv') or \
			 saveas.lower().endswith('.wmv'):
			saveas = '%s.png' % saveas[:saveas.rfind('.')]
		overlay = path.join(ImageUtils.get_root(), 'ui', 'images', 'play_overlay.png')
		ffmpeg = '/usr/bin/ffmpeg'
		if not path.exists(ffmpeg):
			ffmpeg = '/opt/local/bin/ffmpeg'
			if not path.exists(ffmpeg):
				raise Exception('ffmpeg not found; unable to create video thumbnail')
		cmd = ffmpeg
		cmd += ' -i "'
		cmd += video
		cmd += '" -vf \'movie='
		cmd += overlay
		cmd += ' [watermark]; '
		cmd += '[in]scale=200:200 [scale]; '
		cmd += '[scale][watermark] overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2 [out]\' '
		cmd += saveas
		output = ''
		try:
			(status, output) = getstatusoutput(cmd)
		except:
			raise Exception('failed to generate thumbnail using ffmpeg: %s' % output)
		return (saveas, 200, 200)

	'''
		Get width/height of image or video
	'''
	@staticmethod
	def get_dimensions(image):
		if image.lower().endswith('.mp4') or \
		   image.lower().endswith('.flv'):
			ffmpeg = '/usr/bin/ffmpeg'
			if not path.exists(ffmpeg):
				ffmpeg = '/opt/local/bin/ffmpeg'
				if not path.exists(ffmpeg):
					raise Exception('ffmpeg not found; unable to get video dimensions')
			(status, output) = getstatusoutput('%s -i "%s"' % (ffmpeg, image))
			for line in output.split('\n'):
				if 'Stream' in line and 'Video:' in line:
					line = line[line.find('Video:')+6:]
					fields = line.split(', ')
					dims = fields[2]
					if not 'x' in dims: raise Exception('invalid video dimensions')
					(width, height) = dims.split('x')
					if ' ' in height: height = height[:height.find(' ')]
					try:
						width  = int(width)
						height = int(height)
					except:
						raise Exception('invalid video dimensions: %sx%s' % (width, height))
					return (width, height)
			raise Exception('unable to get video dimensions')
		else:
			im = Image.open(image)
			return im.size

	@staticmethod
	def get_root():
		if getcwd().replace(ossep, '').endswith('py'):
			return '..'
		return '.'

	@staticmethod
	def create_subdirectories(directory):
		current = ''
		for subdir in directory.split(ossep):
			if subdir == '': continue
			current = path.join(current, subdir)
			if not path.exists(current):
				print 'creating %s' % current
				mkdir(current)

if __name__ == '__main__':
	#ImageUtils.create_thumbnail('test.jpg', 'test_thumb.jpg')
	#ImageUtils.create_thumbnail('../test.mp4', '../test_thumb.jpg')
	pass
