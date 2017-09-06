#!/usr/bin/python

import argparse
import json
import os
import urllib
import urllib2

import oauth2


def print_status(status):

  print str(status)


def subparser_setup_search(subparsers, callback_func=print_status, subparser_name='tweets'):

  q_help = '... e.g. #Lucene OR #Solr'

  tweets_subparser=subparsers.add_parser(subparser_name)
  tweets_subparser.add_argument('q', type=str, metavar='QUERY', help=q_help)
  result_type_group = tweets_subparser.add_mutually_exclusive_group()
  result_type_group.add_argument('--result-type-mixed', action='store_true')
  result_type_group.add_argument('--result-type-recent', action='store_true')
  result_type_group.add_argument('--result-type-popular', action='store_true')
  tweets_subparser.add_argument('--count', type=int, default=None)
  tweets_subparser.add_argument('--since-id', type=int, default=None)
  tweets_subparser.add_argument('--max-id', type=int, default=None)

  def call_tweets_api(args):
    cached_token = os.environ.get(args.token_cache_env_variable)
    if cached_token:

      # https://dev.twitter.com/rest/reference/get/search/tweets
      # tweet_mode=extended as per https://dev.twitter.com/overview/api/upcoming-changes-to-tweets
      url = "https://api.twitter.com/1.1/search/tweets.json?tweet_mode=extended"

      url += ("&q="+urllib.quote(args.q))

      if args.result_type_mixed:
        url += "&result_type=mixed"

      if args.result_type_recent:
        url += "&result_type=recent"

      if args.result_type_popular:
        url += "&result_type=popular"

      if args.count != None:
        url += ("&count="+str(args.count))

      if args.since_id != None:
        url += ("&since_id="+str(args.since_id))

      if args.max_id != None:
        url += ("&max_id="+str(args.max_id))

      print url
      req = urllib2.Request(url)
      req.add_header("Authorization", "Bearer "+cached_token)

      res = urllib2.urlopen(req)
      response = res.read()

      response_json = json.loads(response)
      response_json = response_json.get("statuses", [])

      for ii in range(0,len(response_json)):
        callback_func(response_json[ii])
    else:
      print "No cached token found in the "+args.token_cache_env_variable+" environment variable."

  tweets_subparser.set_defaults(func=call_tweets_api)


if __name__ == '__main__':

  parser = argparse.ArgumentParser()
  subparsers = parser.add_subparsers()

  oauth2.parser_setup_oauth2(parser)
  subparser_setup_search(subparsers)

  args = parser.parse_args()
  args.func(args)


