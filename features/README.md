
The .json files in this directory can be uploaded to Solr e.g.

```
curl --silent -XPUT 'http://localhost:8983/solr/tweets/schema/feature-store' --data-binary "@originalScore.json" -H 'Content-type:application/json'
```

