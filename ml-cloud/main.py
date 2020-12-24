from json import load as json_load
from google.cloud import storage, vision

with open('config.json') as json_data_file:
	cfg = json_load(json_data_file)

storage_client = storage.Client()
vision_client = vision.ImageAnnotatorClient()

def check_images(data, context):
	uri = "gs://" + data['bucket'] + "/" + data['name']
	image = vision.Image()
	image.source.image_uri = uri

	response = vision_client.safe_search_detection(image=image)
	safe = response.safe_search_annotation
	likelihood_name = ('UNKOWN', 'VERY_UNLIKELY', 'UNLIKELY', 'POSSIBLE', 'LIKELY', 'VERY_LIKELY')

	flagged = False
	for outcome in ['POSSIBLE', 'LIKELY', 'VERY_LIKELY']:
		for result in [
			likelihood_name[safe.adult],
			likelihood_name[safe.violence],
			likelihood_name[safe.racy]
		]:

			if result == outcome:
				flagged = True
				break

	print("{}: {}".format(data['name'], safe))

	bucket = storage_client.get_bucket(data['bucket'])
	blob = bucket.get_blob(data['name'])

	if flagged:
		new_bucket = storage_client.get_bucket(cfg['FLAGGED_BUCKET'])
	else:
		new_bucket = storage_client.get_bucket(cfg['APPROVED_BUCKET'])

	newblob = new_bucket.blob(data['name'])
	newblob.rewrite(blob)
	blob.delete()