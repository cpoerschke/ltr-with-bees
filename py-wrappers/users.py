#!/usr/bin/python

import argparse
import json
import os
import urllib2

import oauth2


def print_user(user):

  print str(user)


def subparser_setup_users(subparsers, callback_func=print_user, subparser_name='lookup', default_screen_names_func=None):

  lookup_subparser=subparsers.add_parser(subparser_name)
  if default_screen_names_func == None:
    lookup_subparser.add_argument('screen_name', type=str, nargs='+')
  else:
    lookup_subparser.add_argument('screen_name', type=str, nargs='*')

  def call_lookup_api(args):
    cached_token = os.environ.get(args.token_cache_env_variable)
    if cached_token:
      if len(args.screen_name) > 0:
        screen_names = args.screen_name
      else:
        screen_names = default_screen_names_func(args)

      screen_name = ",".join(screen_names)

      # https://dev.twitter.com/rest/reference/get/users/lookup
      req = urllib2.Request("https://api.twitter.com/1.1/users/lookup.json?screen_name="+screen_name)
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
  subparser_setup_users(subparsers)

  args = parser.parse_args()
  args.func(args)


