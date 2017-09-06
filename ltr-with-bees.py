#!/usr/bin/python

import argparse
from datetime import datetime
import json
import os
import sys

sys.path.append("./py-wrappers")

import oauth2
import search
import statuses
import users

import linear
import trees

import solr

tweets_collection_name=os.environ.get("SOLR_TWEETS_COLLECTION_NAME", 'tweets')
tweet_features_collection_name=os.environ.get("SOLR_TWEET_FEATURES_COLLECTION_NAME", 'tweet_features')
tweet_clicks_collection_name=os.environ.get("SOLR_TWEET_CLICKS_COLLECTION_NAME", 'tweet_clicks')

solr_external_field_file_prefix='external/external_'
solr_external_field_file_suffix=datetime.now().strftime(".%Y%m%d_%H%M%S")

solr_field_name_handle="handle"


def process_status(status):

  def source_url(p_status):
    return "https://twitter.com/"+p_status["user"]["screen_name"]+"/status/" + p_status["id_str"]

  doc = {
    "id" : status["id_str"],
     "created_at" : datetime.strptime(status["created_at"], "%a %b %d %H:%M:%S +0000 %Y").strftime("%Y-%m-%dT%H:%M:%SZ"),
     "source" : source_url(status),
     solr_field_name_handle : status["user"]["screen_name"],
     "handle_name" : status["user"]["name"],
     "tweet" : status["full_text"],
     "mention" : " ".join([x["screen_name"] for x in status.get("entities",{}).get("user_mentions",[])]),
     "hashtag" : " ".join([x["text"]        for x in status.get("entities",{}).get("hashtags",[])]),
     "verified_account" : status["user"]["verified"]
  }

  if status["is_quote_status"]:
    doc["retweet_source"] = source_url(status["quoted_status"])

  print "Indexed tweet: "+doc["source"]
  print solr.do_solr_update(tweets_collection_name, doc)


def process_user(user):

  solr_external_field_map = {
    "followers_count" : "followers_count",
    "following_count" : "friends_count"
  }

  for field in solr_external_field_map.keys():
    if solr_external_field_map[field] in user:
      with open(solr_external_field_file_prefix+str(field)+solr_external_field_file_suffix, 'a') as file:
        handle = user["screen_name"]
        val = user[solr_external_field_map[field]]
        row = "=".join([ handle, str(val) ])
        # to file
        file.write(row+"\n")
        file.close()
        # to standard output
        print("%s(%s)=%s" % (field, handle, str(val)))


def fl_for_print_and_log_solr_search_row(args):

  fv = ["fv"]

  if args.efi_from_desktop != None:
    fv.append("efi.from_desktop="+str(1 if args.efi_from_desktop else 0))

  if args.efi_from_mobile != None:
    fv.append("efi.from_mobile="+str(1 if args.efi_from_mobile else 0))

  solr_query_id=os.environ.get("SOLR_QUERY_ID", 'queryId'+datetime.now().strftime("%Y%m%d%H%M%S"))
  return [ "query_id:[value v='"+solr_query_id+"']", "result_id:id", "features:["+(" ".join(fv))+"]", "score", "tweet"  ]


def print_and_log_solr_search_row(row):

  print("%s %s\n%s\n" % (row["query_id"], row["result_id"], row["tweet"].encode(encoding="ascii",errors="ignore")))

  doc = {
    "query_id" : row["query_id"],
    "result_id" : row["result_id"],
    "features" : row["features"],
    "result_score" : row["score"]
  }

  solr.do_solr_update(tweet_features_collection_name, doc)


def default_ids_func(args):
  return [
    334232443563433985, # sting-in-the-tale
    568450251612233728, # blueberry-bee
    738007183330140160, # bee-hunters
    761328145995751425, # blueberry-tart
    766666294804504577, # bees-knees-cocktail
    771771675981520896, # 300-honeys
    777947618311860224, # miles-per-honey
    784468395420946432, # arctic-bumblebee
    809365630319259652, # sun-god-ra
    827139009277227008, # bee-sting-cake
    829783795809280002, # robot-bees
    845671602440286208, # 21-days
  ]


def default_screen_names_func(args):

  return solr.do_solr_select_facet_counts(tweets_collection_name, solr_field_name_handle).keys()


def subparser_setup_solr_log_click(subparsers, subparser_name):

  select_subparser=subparsers.add_parser(subparser_name)
  select_subparser.add_argument('query_id', type=str, metavar='QUERY-ID')
  select_subparser.add_argument('result_id', type=str, metavar='RESULT-ID')

  def call_update_api(args):

    doc = {
      "query_id" : args.query_id,
      "result_id" : args.result_id
    }

    print solr.do_solr_update(tweet_clicks_collection_name, doc)

  select_subparser.set_defaults(func=call_update_api)


def queryId2results(args):

  queryId2results = {}

  def append_tweet_feature_row(row):
      queryId = row["query_id"]
      if queryId not in queryId2results:
        queryId2results[queryId] = {}
      resultId = row["result_id"]
      queryId2results[queryId][resultId] = {
        "score" : row["result_score"],
        "features" : row["features"].split(' '),
        "click_times" : []
      }
  solr.do_solr_select_all(tweet_features_collection_name, callback_func=append_tweet_feature_row)

  def append_tweet_click_row(row):
      queryId = row["query_id"]
      resultId = row["result_id"]
      timeOfClick = row["time_of_click"]
      if queryId in queryId2results and resultId in queryId2results[queryId]:
        queryId2results[queryId][resultId]["click_times"].append(timeOfClick)
  solr.do_solr_select_all(tweet_clicks_collection_name, callback_func=append_tweet_click_row)

  return queryId2results


if __name__ == '__main__':

  parser = argparse.ArgumentParser()
  subparsers = parser.add_subparsers()

  oauth2.parser_setup_oauth2(parser)

  oauth2.subparser_setup_oauth2(subparsers, token_subparser_name='twitter-api-login', token_invalidate_subparser_name='twitter-api-logout')

  statuses.subparser_setup_statuses(subparsers, callback_func=process_status, subparser_name='index-tweets-by-id', default_ids_func=default_ids_func)
  search.subparser_setup_search(subparsers, callback_func=process_status, subparser_name='index-tweets-by-query')

  users.subparser_setup_users(subparsers, callback_func=process_user, subparser_name='refresh-user-data', default_screen_names_func=default_screen_names_func)

  solr.subparser_setup_solr_select(subparsers, subparser_name='solr-search-and-log-features', collection_name=tweets_collection_name,
    fl_func=fl_for_print_and_log_solr_search_row, callback_func=print_and_log_solr_search_row)

  subparser_setup_solr_log_click(subparsers, subparser_name='solr-log-click')

  linear.subparser_setup_train(subparsers, subparser_name='train-linear-model', queryId2results_func=queryId2results)

  trees.subparser_setup_train(subparsers, subparser_name='train-trees-model', queryId2results_func=queryId2results)

  args = parser.parse_args()
  args.func(args)


