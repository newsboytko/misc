from optparse import OptionParser
import flickrapi
import fnmatch
import os
import sys
import hashlib
from csv import DictReader, DictWriter
from datetime import datetime

API_KEY = 'f5b40cdc2dfac381aefcfd48687ddaba'
API_SECRET = '30bce1a79b59ea4a'
PYFLICKR_TAG = 'PyFlickr'

def parse_command_line():

    parser = OptionParser(
        usage = '%prog [options]'
    )

    parser.add_option(
        '-o', '--output', dest='output_path', default='dump.csv',
        help='path to output CSV file',
    )

    return parser.parse_args()

if __name__ == "__main__":

    (options, args) = parse_command_line()

    print 'Authenticating ...'
    flickr = flickrapi.FlickrAPI(API_KEY, API_SECRET)
    flickr.authenticate_console(perms='read')

    print 'Getting previously uploaded photos ...'
    append = os.path.isfile(options.output_path)

    dumped = set()
    if append:
        with open(options.output_path, 'rb') as csvfile:
            reader = DictReader(csvfile)
            dumped.update([ int(row['id']) for row in reader ])

    with open(options.output_path, 'ab') as csvfile:
        writer = DictWriter(csvfile, extrasaction='ignore', fieldnames=(
            'id',
            'title',
            'media',
            'original_format',
            'date_taken',
            'date_updated',
            'date_posted',
            'url',
        ))

        if not append:
            writer.writeheader()

        count = 0
        start = None

        for photo in flickr.walk(
            user_id='me',
            tag_mode='all',
            tags=PYFLICKR_TAG,
            per_page=500,
        ):
            if int(photo.get('id')) in dumped:
                continue

            if not start:
                start = datetime.now()

            info = flickr.photos_getInfo(photo_id=photo.get('id'))
            photo_info = info.find('photo')
            data = {
                'id': photo.get('id'),
                'title': photo.get('title'),
                'media': photo_info.get('media'),
                'original_format': photo_info.get('originalformat'),
                'date_taken': photo_info.find('dates').get('taken'),
                'date_updated': photo_info.find('dates').get('lastupdate'),
                'date_posted': photo_info.find('dates').get('posted'),
                'url': photo_info.find('urls').find('url').text,
            }
            writer.writerow(data)
            count += 1

            if count % 100 == 0:
                elapsed = (datetime.now() - start).total_seconds()
                print 'dumped %d photos (%.2f/s)' % (
                    count,
                    float(count) / elapsed,
                )

    print 'Done!'
