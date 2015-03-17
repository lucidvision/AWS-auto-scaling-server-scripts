import string
import random
import boto
import json
from PIL import Image
from bottle import route, request, run
from boto.s3.key import Key
from common import bucket, queue
from boto.sqs.message import Message

random.seed()
alphabet_numeric_set = string.lowercase + string.digits

# All the sizes our app supports
sizes = { 
        'small': { 'width': 100, 'height': 100 },
        'medium': { 'width': 300, 'height': 300 },
        'large': { 'width': 600, 'height': 600 }
}

# Generate a unique id to be used in an S3 bucket.
def generate_id():
        length = random.randint(3,63)
	id = random.choice(alphabet_numeric_set)

	for var in range(1, length-1):
		if id[-1:] == '.':
			id += random.choice(alphabet_numeric_set)

		elif id[-1:] == '-':
			id += random.choice(alphabet_numeric_set + '-')

		else:
			id += random.choice(alphabet_numeric_set + '.' + '-')

	id += random.choice(alphabet_numeric_set)
	return id

def notify_worker(id, sizes):
	data = {
		'key': id,
		'size': sizes
		}
	print data
	m = Message()
	m.set_body(json.dumps(data))
	status = queue.write(m)       

# Generate a URL for a resource in an S3 bucket
def url(name):
        return Key(bucket, name).generate_url(expires_in=-1,query_auth=False)

@route('/', method='POST')
def upload():
        
        # Get the uploaded image from the user
        upload = request.files.get('image')

        if not upload: return 'no image'

        file = upload.file
        image = None

        try:
                image = Image.open(file)
        except:
                return 'invalid image'

        file.seek(0)
        id = generate_id()

        key = bucket.new_key(id+'-original')
        key.set_metadata('Content-Type', 'image/'+image.format.lower())
        key.set_contents_from_file(file)

        notify_worker(id, sizes)

        # Return the URLs to the images.
        return  { key: url(id+'-'+key) for key in ['original'] + sizes.keys() }

run(host='0.0.0.0', port=80)
