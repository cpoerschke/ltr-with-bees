
# Learning-to-Rank with Apache Solr and Bees

This repo contains the example material of my [talk](http://sched.co/BAwI) at [Lucene/Solr Revolution](http://lucenerevolution.org) 2017.

* [Setup](#setup)
* [Using the demo script](#using-the-demo-script)
* [The python scripts in this repo](#the-python-scripts-in-this-repo)
* [Adapting the demo](#adapting-the-demo)
* [Solr Resources and Community](#solr-resources-and-community)

## Setup

This demo material for Solr's Learning-to-Rank plugin uses
* the files in this repository
* [Apache Solr](http://lucene.apache.org/solr) 6.6.0
* selected [Twitter REST APIs](https://dev.twitter.com/rest/public)
* [LIBLINEAR](https://www.csie.ntu.edu.tw/~cjlin/liblinear/) 2.11
* [RankLib](https://sourceforge.net/p/lemur/wiki/RankLib/) 2.8

### Cloning this repo

```
git clone https://github.com/cpoerschke/ltr-with-bees
cd ltr-with-bees
```

### Downloading Apache Solr

```
# Download solr-6.6.0.tgz from http://lucene.apache.org/solr/mirrors-solr-latest-redir.html
gunzip solr-6.6.0.tgz
tar xf solr-6.6.0.tar
```

### Downloading LIBLINEAR

```
# Download liblinear-2.11.tar from https://www.csie.ntu.edu.tw/~cjlin/liblinear/
tar xf liblinear-2.11.tar
cd liblinear-2.11
make
cd ..
```

### Downloading RankLib

```
# Download RankLib-2.8.jar from https://sourceforge.net/projects/lemur/files/lemur/RankLib-2.8/
```

### Register your Twitter App

Some of the scripts in this demo repo make requests to selected [Twitter REST APIs](https://dev.twitter.com/rest/public). These requests are authenticated using [Application-only authentication](https://dev.twitter.com/oauth/application-only) and therefore the application i.e. this demo needs to be registered on the Twitter Application Management page at https://apps.twitter.com.

As part of the registration the application is issued with a so-called _Consumer Key_ and _Secret_. The consumer key and secret that I registered are specific to my use of this demo repo i.e. I cannot share them with you. If you wish to fully use this demo repo yourself then you simply need to register your own clone or fork of the demo repo via the Twitter Application Management page at https://apps.twitter.com and set two shell environment variables as outlined below.

## Using the demo script

The `ltr-with-bees-demo.sh` script illustrates one way to use the materials in this repo.

```
ltr-with-bees-demo.sh
================================================================================
DEMO: Obtaining Twitter Access Token for API_TWITTER_CONSUMER_KEY/API_TWITTER_CONSUMER_SECRET environment variables
================================================================================
ERROR: Please set and export API_TWITTER_CONSUMER_KEY and API_TWITTER_CONSUMER_SECRET environment variables.
```

```
export API_TWITTER_CONSUMER_KEY="NotMyRealKey"
export API_TWITTER_CONSUMER_SECRET="NotMyRealSecret"
```

```
ltr-with-bees-demo.sh
================================================================================
DEMO: Obtaining Twitter Access Token for API_TWITTER_CONSUMER_KEY/API_TWITTER_CONSUMER_SECRET environment variables
================================================================================
{"token_type":"bearer","access_token":"NotARealAccessToken"}
To cache the token in an environment variable:
export API_TWITTER_ACCESS_TOKEN="NotARealAccessToken"
```

```
export API_TWITTER_ACCESS_TOKEN="NotARealAccessToken"
```


```
ltr-with-bees-demo.sh
================================================================================
DEMO: Using Twitter Access Token from API_TWITTER_ACCESS_TOKEN environment variable
================================================================================

...

================================================================================
DEMO: Starting solr
================================================================================

...

================================================================================
DEMO: Creating tweets using configs/tweets_config config
================================================================================

...

================================================================================
DEMO: Indexing demo tweets into Solr
================================================================================

...

================================================================================
DEMO: Gathering external file field values
================================================================================

...

================================================================================
DEMO: Uploading candidate feature ...
================================================================================

...

================================================================================
DEMO: Running sample feature extraction
================================================================================

...

================================================================================
DEMO: User ... is searching for ...
================================================================================

...

================================================================================
DEMO: Logging click for ...
================================================================================

...

================================================================================
DEMO: Training model ...
================================================================================

...

================================================================================
DEMO: Uploading model ...
================================================================================

...

================================================================================
DEMO: model=... search
================================================================================

...

```

## The python scripts in this repo

### Wrapper scripts

| Script      | What does it do? |
|-------------|------------------|
| oauth2.py   | Wraps https://dev.twitter.com/oauth/reference/post/oauth2/token and https://dev.twitter.com/oauth/reference/post/oauth2/invalidate/token API use. |
| statuses.py | Wraps https://dev.twitter.com/rest/reference/get/statuses/lookup API use. |
| users.py    | Wraps https://dev.twitter.com/rest/reference/get/users/lookup API use. |
| search.py   | Wraps https://dev.twitter.com/rest/reference/get/search/tweets API use. |
| solr.py     | Simple update/select/delete operations on the demo solr collections. |
| linear.py   | Takes inputs, calls LIBLINEAR's train in a simple way, converts output into a solr-ltr .json model file. |
| rank.py     | Takes inputs, does RankLib training in a simple way, converts output into a solr-ltr .json model file. |

You can run these scripts individually to explore what they do, e.g.
```
solr.py --help
usage: solr.py [-h]
               {select-all,select,select-facet-counts,update,delete-by-query}
               ...

positional arguments:
  {select-all,select,select-facet-counts,update,delete-by-query}

optional arguments:
  -h, --help            show this help message and exit
```

### Top-level script

`ltr-with-bees.py` is the top-level python script in this repo and its implementation uses functions from the wrapper scripts. For example `ltr-with-bees.py index-tweets-by-id` uses `statuses.py`'s `call_lookup_api` function to lookup tweets and `solr.py`'s `do_solr_update` function to add the tweets to the solr collection.

```
ltr-with-bees.py --help
usage: ltr-with-bees.py [-h]
                        [--token-cache-env-variable TOKEN_CACHE_ENV_VARIABLE]
                        {twitter-api-login,twitter-api-logout,index-tweets-by-id,index-tweets-by-query,refresh-user-data,solr-search-and-log-features,solr-log-click,train-linear-model,train-trees-model}
                        ...

positional arguments:
  {twitter-api-login,twitter-api-logout,index-tweets-by-id,index-tweets-by-query,refresh-user-data,solr-search-and-log-features,solr-log-click,train-linear-model,train-trees-model}

optional arguments:
  -h, --help            show this help message and exit
  --token-cache-env-variable TOKEN_CACHE_ENV_VARIABLE
```

## Adapting the demo

### Indexing other tweets

You can use `ltr-with-bees.py index-tweets-by-query` to index additional or alternative tweets, e.g.

```
ltr-with-bees.py index-tweets-by-query "#Lucene OR #Solr"
```

You can also define and upload further [features](features) and train new models using the existing and/or new features e.g.

```
ltr-with-bees.py train-linear-model --feature-names "myFirstFeature,mySecondFeature" --model-name myFirstModel
```

or

```
ltr-with-bees.py train-trees-model --ranklib-tree=10 --ranklib-leaf=5 --model-name mySecondModel
```

### In-browser results display

The demo config in this repo includes an example configuration for an [XSLT Response Writer](https://lucene.apache.org/solr/guide/6_6/response-writers.html#ResponseWriters-TheXSLTResponseWriter) and by adding `wt=xslt` and `tr=example.xsl` parameters to your requests you can then view results not just as JSON and text but in a web-browser with embedded tweets via the [example.xsl](configs/tweets_config/conf/xslt/example.xsl) e.g.

[http://localhost:8983/solr/tweets/select?q=\*:\*&wt=xslt&tr=example.xsl&fl=id,tweet_url:source,embedded_tweet:source](http://localhost:8983/solr/tweets/select?q=%2A:%2A&wt=xslt&tr=example.xsl&fl=id,tweet_url:source,embedded_tweet:source)

or the shorter equivalent

[http://localhost:8983/solr/tweets/select_tr?q=\*:\*](http://localhost:8983/solr/tweets/select_tr?q=%2A:%2A)

or the shorter equivalent _with_ re-ranking

[http://localhost:8983/solr/tweets/select_tr?q=\*:\*&rq={!ltr model=treesModel efi.from_desktop=1}](http://localhost:8983/solr/tweets/select_tr?q=%2A:%2A&rq=%7B!ltr%20model=treesModel%20efi.from_desktop=1%7D)

### Demo config limitations and shortcuts

* solr-6.6.0 release: The example configs shipped with Solr 6.6.0 are fully fledged and you can fully use the Solr Admin UI to explore and work with them. The downside of fully fledged is that most `solrconfig.xml` and `managed-schema` examples are 1000+ lines long.

* ltr-with-bees repo:
 * The [demo configs](configs) in this repo contain `solrconfig.xml` and `managed-schema` files which are minimally short, only a few dozen lines long. The upside of this conciseness is that you can easily see the things configured for the demo. The downside of this brevity is that certain parts of the Solr Admin UI cannot be used with the demo configs.
 * Solr is not a database. To keep things simple in this demo we persisted features and clicks in two Solr collections, for real in production you probably would store features and clicks data outside of Solr.

## Solr Resources and Community

* https://lucene.apache.org/solr/resources.html
* https://lucene.apache.org/solr/community.html

