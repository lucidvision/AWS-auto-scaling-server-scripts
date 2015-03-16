import json
import time
import StringIO
from PIL import Image
from common import bucket, queue

# Create a thumbnail from an image.
def thumbnail(image, maxWidth, maxHeight):

	# Perform some sanity checks
	if not isinstance(maxWidth, int): raise Exception('Width must be an int')
	if not isinstance(maxHeight, int): raise Exception('Height must be an int')
	if maxWidth <= 0: raise Exception('Width must not be <= 0')
	if maxHeight <= 0: raise Exception('Height must not be <= 0');
	
	# Do some wizardry to maintain the aspect ratio of the image
	width, height = image.size
	targetWidth, targetHeight = width, height
	if targetWidth > maxWidth:
		targetWidth = maxWidth
		targetHeight = (targetWidth * height) / width
	if targetHeight > maxHeight:
		targetHeight = maxHeight
		targetWidth = (targetHeight * width) / height

	return image.resize((targetWidth, targetHeight), resample=Image.ANTIALIAS)

# Read an image from S3.
def read(name):
	key = bucket.get_key(name)
	if not key: raise Exception('no such key '+name)
	return Image.open(StringIO.StringIO(key.get_contents_as_string()))

# Save an image to S3.
def write(name, image, format):
	key = bucket.new_key(name)
	buf = StringIO.StringIO()
	image.save(buf, format=format, quality=8)
	key.set_metadata('Content-Type', 'image/'+format.lower())
	key.set_contents_from_string(buf.getvalue())
	buf.close()

try:
	
	# Loop forever.
	while 1:
		rs = queue.get_messages()

		for m in rs:
			data = json.loads(m.get_body())
			xkey = data['key']

			wssize = data['size']['small']['width']
			hssize = data['size']['small']['height']
			wmsize = data['size']['medium']['width']
			hmsize = data['size']['medium']['height']
			wlsize = data['size']['large']['width']
			hlsize = data['size']['large']['height']

			image = read(xkey+'-original')

			sImage = thumbnail(image,wssize,hssize)
			mImage = thumbnail(image,wmsize,hmsize)
			lImage = thumbnail(image,wlsize,hlsize)

			write(xkey+'-small', sImage, 'png')
			write(xkey+'-medium', mImage, 'png')
			write(xkey+'-large', lImage, 'png')

			queue.delete_message(m)
			print 'done'
		
except KeyboardInterrupt:
	pass