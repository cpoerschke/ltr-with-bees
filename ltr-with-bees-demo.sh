
echo_f()
{
  echo "================================================================================"
  echo "DEMO: ${1}"
  echo "================================================================================"
  sleep 2
}

if [[ -z "$API_TWITTER_ACCESS_TOKEN" ]]
then
  echo_f "Obtaining Twitter Access Token for API_TWITTER_CONSUMER_KEY/API_TWITTER_CONSUMER_SECRET environment variables"
  if [[ -n "$API_TWITTER_CONSUMER_KEY" && -n "$API_TWITTER_CONSUMER_SECRET" ]]
  then
    ./ltr-with-bees.py twitter-api-login "$API_TWITTER_CONSUMER_KEY" "$API_TWITTER_CONSUMER_SECRET"
    exit $?
  else
    echo "ERROR: Please set and export API_TWITTER_CONSUMER_KEY and API_TWITTER_CONSUMER_SECRET environment variables."
    exit 1
  fi
else
  echo_f "Using Twitter Access Token from API_TWITTER_ACCESS_TOKEN environment variable"
fi

delete_create_skip_collection=

for collection in tweets tweet_features tweet_clicks
do
  if [[ "$collection" == "$delete_create_skip_collection" ]]
  then
    continue
  fi
  echo_f "Deleting ${collection} collection (if it still exists)"
  solr-6.6.0/bin/solr delete -c ${collection}
done

echo_f "Stopping solr (if it's still running)"
solr-6.6.0/bin/solr stop

echo_f "Starting solr"
solr-6.6.0/bin/solr start

for collection in tweets tweet_features tweet_clicks
do
  if [[ "$collection" == "$delete_create_skip_collection" ]]
  then
    continue
  fi
  echo_f "Creating ${collection} collection using configs/${collection}_config config"
  solr-6.6.0/bin/solr create_core -c ${collection} -d configs/${collection}_config
done

echo_f "Indexing demo tweets into Solr"
./ltr-with-bees.py index-tweets-by-id

echo_f "Gathering external file field values"
./ltr-with-bees.py refresh-user-data

echo_f "Updating external file field values"
for field in followers_count following_count
do
  dst="solr-6.6.0/server/solr/tweets/data/"
  for file in `\ls -t external/external_${field}.* | head -1`
  do
    echo "Copying $file to $dst"
    cp $file $dst/
  done
done

echo_f "Restarting solr (simpler to demo than ExternalFileFieldReloader config and use)"
solr-6.6.0/bin/solr restart

echo_f "TODO: 'sleep 5' should not be needed here?"
sleep 5
echo "Slept for 5 seconds."

for field in followers_count following_count
do
  echo_f "Retrieving updated ${field} values"
  curl --silent "http://localhost:8983/solr/tweets/select?q=*:*&fl=handle,field(${field})"
done

for candidateFeatureFile in `\ls features/*.json`
do
  echo_f "Uploading candidate feature ($candidateFeatureFile)"
  curl --silent -XPUT 'http://localhost:8983/solr/tweets/schema/feature-store' --data-binary "@$candidateFeatureFile" -H 'Content-type:application/json'
done

echo_f "Running sample feature extraction"
curl --silent "http://localhost:8983/solr/tweets/select?q=*:*&fl=source,tweet,\[fv\]&rows=100"

search_and_click_f()
{
  user="$1" ; shift
  word="$1" ; shift
  clicked_result="$1" ; shift

  if [[ "$user" == "Bianca" ]]
  then
    efi_option="--efi-from-desktop=True"
  fi

  if [[ "$user" == "Harry" ]]
  then
    efi_option="--efi-from-mobile=True"
  fi

  export SOLR_QUERY_ID="queryId_$(date -u '+%Y%m%d_%H%M%S')"
  sleep 1 # hack: sleep to ensure demo query id uniqueness
  echo_f "User '$user' is searching for tweets with the word '$word' using '$SOLR_QUERY_ID'"
  ./ltr-with-bees.py solr-search-and-log-features tweet:$word $efi_option

  echo_f "Logging click for result $clicked_result"
  ./ltr-with-bees.py solr-log-click $SOLR_QUERY_ID $clicked_result
}

             BEE_STING_CAKE_RESULT_ID=827139009277227008
RESULT_ID_STING_IN_THE_TALE_RESULT_ID=334232443563433985

          ARCTIC_BUMBLE_BEE_RESULT_ID=784468395420946432
            MILES_PER_HONEY_RESULT_ID=777947618311860224

              BLUEBERRY_BEE_RESULT_ID=568450251612233728
             BLUEBERRY_TART_RESULT_ID=761328145995751425

search_and_click_f Bianca sting     $BEE_STING_CAKE_RESULT_ID
search_and_click_f Harry  sting     $BEE_STING_CAKE_RESULT_ID

search_and_click_f Bianca miles     $ARCTIC_BUMBLE_BEE_RESULT_ID
search_and_click_f Harry  miles     $MILES_PER_HONEY_RESULT_ID

search_and_click_f Bianca blueberry $BLUEBERRY_BEE_RESULT_ID
search_and_click_f Harry  blueberry $BLUEBERRY_TART_RESULT_ID

search_and_rerank_f()
{
  model="$1"
  for word in sting miles blueberry
  do
    for efi_from in desktop mobile
    do
      echo_f "model=$model efi.from_${efi_from}=1 tweet:${word}"
      curl --silent "http://localhost:8983/solr/tweets/select?q=tweet:${word}&fl=tweet,id,score&rq=\{!ltr+model=$model+efi.from_${efi_from}=1\}"
    done
  done

  for efi_from in desktop mobile
  do
    echo_f "model=$model efi.from_${efi_from}=1 tweet:* fq=-tweet:sting fq=-tweet:miles fq=-tweet:blueberry"
    curl --silent "http://localhost:8983/solr/tweets/select?q=tweet:*&fl=tweet,id,score&rq=\{!ltr+model=$model+efi.from_${efi_from}=1\}&fq=-tweet:sting&fq=-tweet:miles&fq=-tweet:blueberry"
  done
}

echo_f "Training model ($LINEAR_MODEL_NAME)"

LINEAR_FEATURE_NAMES="hashtagCount,honeyContent,fromMobile"

LINEAR_MODEL_NAME="linearModel$(date -u '+%Y%m%d%H%M%S')"

./ltr-with-bees.py train-linear-model --feature-names $LINEAR_FEATURE_NAMES --model-name $LINEAR_MODEL_NAME --model-file-name models/$LINEAR_MODEL_NAME.json --inputs-file-name models/$LINEAR_MODEL_NAME-inputs.txt --outputs-file-name models/$LINEAR_MODEL_NAME-outputs.txt

echo_f "Uploading model ($LINEAR_MODEL_NAME)"
curl --silent -XPUT 'http://localhost:8983/solr/tweets/schema/model-store' --data-binary "@models/$LINEAR_MODEL_NAME.json" -H 'Content-type:application/json'

search_and_rerank_f $LINEAR_MODEL_NAME

echo_f "Training model ($TREES_MODEL_NAME)"

TREES_FEATURE_NAMES="byVerifiedAccount,containsHashtag,fromDesktop,fromMobile,hashtagCount,tweetLength"

TREES_MODEL_NAME="treesModel$(date -u '+%Y%m%d%H%M%S')"

RANKLIB_OPTIONS="--ranklib-tree=1 --ranklib-leaf=4"

./ltr-with-bees.py train-trees-model $RANKLIB_OPTIONS --feature-names $TREES_FEATURE_NAMES --model-name $TREES_MODEL_NAME --model-file-name models/$TREES_MODEL_NAME.json --inputs-file-name models/$TREES_MODEL_NAME-inputs.txt --outputs-file-name models/$TREES_MODEL_NAME-outputs.txt

echo_f "Uploading model ($TREES_MODEL_NAME)"
curl --silent -XPUT 'http://localhost:8983/solr/tweets/schema/model-store' --data-binary "@models/$TREES_MODEL_NAME.json" -H 'Content-type:application/json'

search_and_rerank_f $TREES_MODEL_NAME

echo_f "optional: command for stopping solr"
echo "solr-6.6.0/bin/solr stop"

if [[ -n "$API_TWITTER_ACCESS_TOKEN" ]]
then
  echo_f "optional: command to invalidate Twitter Access Token"
  echo "./ltr-with-bees.py twitter-api-logout \"\$API_TWITTER_CONSUMER_KEY\" \"\$API_TWITTER_CONSUMER_SECRET\""
fi

