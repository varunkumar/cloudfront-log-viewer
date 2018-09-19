import argparse
import logging
import gzip
import csv
import sys
import glob
import itertools

import simplejson as json
from datetime import datetime

import requests

logger = logging.getLogger(__name__)
null = None

def batchify(items, batch_size=100):
    items = iter(items)
    item_batch = list(itertools.islice(items, 0, batch_size))
    while len(item_batch) > 0:
        yield item_batch
        item_batch = list(itertools.islice(items, 0, batch_size))

def get_logs(log_filename):
    logger.info('Extracting logs from %s...', log_filename)
    with gzip.open(log_filename, 'r') as r:
        reader = csv.reader(r, dialect=csv.excel_tab)

        rows = []
        header = []
        for row in itertools.islice(reader, 1, 2):
            header = row[0]
            header = header.replace('#Fields: ', '', 1)
            header = header.split(' ')

        for row in reader:
            row_dict = {}
            for column, name in itertools.izip(row, header):
               row_dict[name] = column
            rows.append(row_dict)
        logger.info('Extracted %d log items from %s', len(rows), log_filename)
        return rows

def import_logs(logs, es_url, index, doc_type, batch_size=1000):
    total_item_count = 0
    total_item_bytes = 0
    total_ms = 0
    for batch in batchify(logs, batch_size=batch_size):
        bulk_index_url = '{es_url}/{index}/_bulk'.format(es_url=es_url, index=index)
        bulk_index_content = '\n'.join(
            itertools.chain(
                *[(
                    json.dumps({
                                    'index': {
                                        '_type' : doc_type,
                                        '_id': datetime.utcnow().isoformat()
                                    }
                                }
                    ), 
                    json.dumps(log)) for log in batch]
            )
        ) + '\n'

        item_count = len(batch)
        total_item_count = total_item_count + item_count
        item_bytes = len(json.dumps(batch))
        total_item_bytes = total_item_bytes + item_bytes
        start_time = datetime.now()

        
        headers = { "Content-Type": "application/json" }
        resp = requests.post(bulk_index_url, data=bulk_index_content, headers=headers)
        resp_json = resp.json()
        if resp.status_code != 200:
            logger.error(json.dumps(resp_json, indent=2))

        end_time = datetime.now()
        batch_ms = int((end_time - start_time).total_seconds() * 1000)
        total_ms = total_ms + batch_ms
        us_per_item = int(batch_ms * 1000 / item_count)
        logger.info('Imported {item_count} log items into {index} in {batch_ms}ms at {us_per_item}us per log item'.format(
            item_count=item_count, index=index, item_bytes=item_bytes, batch_ms=batch_ms, us_per_item=us_per_item
        ))

    logger.info('Cumulatively imported {total_item_count} log items ({total_item_mb}mb) in {total_min}min at {us_per_item}us per log item ({kb_per_sec}kB/s)'.format(
        total_item_count=total_item_count, 
        total_item_mb=int(total_item_bytes/(1024*1024)), 
        total_min=int(total_ms/(1000*60)), 
        us_per_item=int(total_ms * 1000 / total_item_count),
        kb_per_sec=0 if total_ms == 0 else int((total_item_bytes*1000)/(total_ms*1024))
    ))

def clean_index(index):
    resp = requests.delete("{es_url}/{index}".format(es_url=es_url, index=index))
    resp_json = resp.json()
    if resp.status_code != 404:
        logger.info("Deleted index '%s'", index)
    else:
        logger.error("Deleting index '%s' failed with %d status code", index, resp.status_code)
        logger.error(resp_json)
        sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Imports Cloudfront logs into ElasticSearch')

    parser.add_argument('-v', '--verbosity', help='Set logging level', default='ERROR')

    parser.add_argument('-l', '--log_file_pattern', 
        action='store', 
        required=True,
        help='Log file pattern')

    parser.add_argument('-e', '--es_url', 
        action='store', 
        default='http://localhost:9200',
        help='ElasticSearch root URL')

    parser.add_argument('-c', '--clean_index', 
        action='store_true', 
        default=False,
        help='Clean existing documents of type in the index')

    parser.add_argument('-i', '--index', 
        action='store',
        default='cloudfront',
        help='Name of the index')

    parser.add_argument('-t', '--type', 
        action='store',
        default='logs',
        help='Name of the type')


    args = parser.parse_args()

    log_handler = logging.StreamHandler()
    log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(log_handler)
    logger.setLevel(getattr(logging, args.verbosity))

    # reading logs
    logger.info(args)
    log_files = glob.glob(args.log_file_pattern)
    logger.info("Found %d matching log files for pattern '%s'", len(log_files), args.log_file_pattern)

    logs = []
    for log_file in iter(log_files):
        logger.info('---------------------------')
        logger.info(log_file)
        logs.extend(get_logs(log_file))
        logger.info('---------------------------')

    logger.info('Cumulatively extracted %d log items from %s files', len(logs), len(log_files))

    es_url = args.es_url.strip('/')
    index = args.index
    doc_type= args.type

    if args.clean_index:
        clean_index(index)

    import_logs(logs, es_url, index, doc_type)
