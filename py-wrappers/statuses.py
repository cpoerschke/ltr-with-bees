#!/usr/bin/python

import argparse
import json
import os
import urllib2

import oauth2


def print_status(status):

  print str(status)


def subparser_setup_statuses(subparsers, callback_func=print_status, subparser_name='lookup', default_ids_func=None):

  id_help = 'a Tweet ID e.g. 823576076769054720' # https://twitter.com/TechAtBloomberg/status/823576076769054720

  lookup_subparser=subparsers.add_parser(subparser_name)

  if default_ids_func == None:
    lookup_subparser.add_argument('id', type=int, nargs='+', metavar='ID', help=id_help)
  else:
    lookup_subparser.add_argument('id', type=int, nargs='*', metavar='ID', help=id_help)

  def call_lookup_api(args):
    cached_token = os.environ.get(args.token_cache_env_variable)
    if cached_token:
      if len(args.id) > 0:
        ids = args.id
      else:
        ids = default_ids_func(args)

      ids = ",".join([str(x) for x in ids])

      # https://dev.twitter.com/rest/reference/get/statuses/lookup
      # tweet_mode=extended as per https://dev.twitter.com/overview/api/upcoming-changes-to-tweets
      req = urllib2.Request("https://api.twitter.com/1.1/statuses/lookup.json?tweet_mode=extended&id="+ids)
      req.add_header("Authorization", "Bearer "+cached_token)

      res = urllib2.urlopen(req)
      response = res.read()

      response_json = json.loads(response)

      for ii in range(0,len(response_json)):
        callback_func(response_json[ii])
    else:
      print "No cached token found in the "+args.token_cache_env_variable+" environment variable."

  lookup_subparser.set_defaults(func=call_lookup_api)


if __name__ == '__main__':

  parser = argparse.ArgumentParser()
  subparsers = parser.add_subparsers()

  oauth2.parser_setup_oauth2(parser)
  subparser_setup_statuses(subparsers)

  args = parser.parse_args()
  args.func(args)


