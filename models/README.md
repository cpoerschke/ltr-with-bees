
The .json files (if any) in this directory can be uploaded to Solr e.g.

```
curl --silent -XPUT 'http://localhost:8983/solr/tweets/schema/model-store' --data-binary "@myModel.json" -H 'Content-type:application/json'
```

