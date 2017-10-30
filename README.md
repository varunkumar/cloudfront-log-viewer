# CloudFront log viewer

Import [CloudFront logs](http://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/AccessLogs.html#LogFileFormat) into a local [Elasticsearch](https://www.elastic.co/products/elasticsearch) instance and visualize them using [Kibana](https://www.elastic.co/products/kibana)

## Start a local Elasticsearch instance

#### Set environment variables for Elasticsearch
```bash
export ES_ROOT=~/elasticsearch
export ES_PORT=9201
export ES_VERSION=6.0.0-rc1
```

#### Download Elasticsearch and untar into $ES_ROOT - this needs to be done once
```bash
\rm -rf $ES_ROOT
mkdir -p $ES_ROOT
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-$ES_VERSION.tar.gz -O $ES_ROOT/elasticsearch.tar.gz
tar xzf $ES_ROOT/elasticsearch.tar.gz -C $ES_ROOT
mv $ES_ROOT/elasticsearch-$ES_VERSION $ES_ROOT/elasticsearch
```

#### Start instance
```bash
$ES_ROOT/elasticsearch/bin/elasticsearch -E http.port=$ES_PORT
```

#### Test connection via curl
```bash
curl http://$HOST:$ES_PORT
```

## Import cloudfront logs into local Elasticsearch
```bash
python import_logs.py --log_file_pattern 'logs/*' --es_url 'http://$HOST:$ES_PORT' --index cloudfront --type prod --clean_index --verbosity INFO
```

## Start a local Kibana instance

#### Set environment variables for Kibana
```bash
export ESKB_PORT=9211
export ESKB_UNAME=darwin # darwin | linux
export ESKB_VERSION=$ES_VERSION
```

#### Download Kibana and untar into $ES_ROOT.tar.gz - this needs to be done once
```bash
wget https://artifacts.elastic.co/downloads/kibana/kibana-$ESKB_VERSION-$ESKB_UNAME-x86_64.tar.gz -O $ES_ROOT/kibana.tar.gz
tar xzf $ES_ROOT/kibana.tar.gz -C $ES_ROOT
mv $ES_ROOT/kibana-$ESKB_VERSION-$ESKB_UNAME-x86_64 $ES_ROOT/kibana
```

#### Start instance
```bash
$ES_ROOT/kibana/bin/kibana --host=$HOST --port=$ESKB_PORT --elasticsearch=http://$HOST:$ES_PORT
```

## License
The source code is available [here](https://github.com/varunkumar/google-input-tools) under [MIT licence](http://varunkumar.mit-license.org/). Feel free to use any part of the code. Please send any bugs, feedback, complaints, patches to me at varunkumar[dot]n[at]gmail[dot]com.

-- [Varun](http://www.varunkumar.me)