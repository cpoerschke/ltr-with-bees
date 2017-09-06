#!/usr/bin/python

import argparse
import base64
import json
import os
import urllib2


def base64BearerTokenCredentials(args):

  bearerTokenCredentials = (args.consumer_key+':'+args.consumer_secret)
  return base64.b64encode(bearerTokenCredentials)


def call_token_api(args):

  # https://dev.twitter.com/oauth/reference/post/oauth2/token
  req = urllib2.Request("https://api.twitter.com/oauth2/token", data="grant_type=client_credentials")
  req.add_header("Authorization", "Basic "+base64BearerTokenCredentials(args))
  req.add_header("Content-Type", "application/x-www-form-urlencoded;charset=UTF-8")

  res = urllib2.urlopen(req)
  response = res.read()
  print response

  response_json = json.loads(response)
  new_token = response_json["access_token"]
  old_token = os.environ.get(args.token_cache_env_variable)
  if new_token != old_token:
    if old_token:
      print "A different token was previously changed in the "+args.token_cache_env_variable+" environment variable."
      print "To update the cached token:"
    else:
      print "To cache the token in an environment variable:"
    print "export "+args.token_cache_env_variable+"=\""+new_token+"\""
  else:
    print "The token is already cached in the "+args.token_cache_env_variable+" environment variable."


def call_token_invalidate_api(args):
  cached_token = os.environ.get(args.token_cache_env_variable)
  if cached_token:
    # https://dev.twitter.com/oauth/reference/post/oauth2/invalidate/token
    req = urllib2.Request("https://api.twitter.com/oauth2/invalidate_token", data="access_token="+cached_token)
    req.add_header("Authorization", "Basic "+base64BearerTokenCredentials(args))
    req.add_header("Content-Type", "application/x-www-form-urlencoded;charset=UTF-8")

    res = urllib2.urlopen(req)
    response = res.read()
    print response

    response_json = json.loads(response)
    invalidated_token = response_json["access_token"]
    if cached_token != invalidated_token:
      print "ERROR: request.token != response.token"
      print "ERROR: "+cached_token+" != "+invalidated_token
    else:
      print "To clear the environment variable:"
      print "unset "+args.token_cache_env_variable
  else:
    print "No cached token found in the "+args.token_cache_env_variable+" environment variable."


def subparser_setup_oauth2(subparsers, token_subparser_name='token', token_invalidate_subparser_name='token-invalidate'):

  token_subparser=subparsers.add_parser(token_subparser_name)
  token_subparser.add_argument('consumer_key', type=str)
  token_subparser.add_argument('consumer_secret', type=str)
  token_subparser.set_defaults(func=call_token_api)

  token_invalidate_subparser=subparsers.add_parser(token_invalidate_subparser_name)
  token_invalidate_subparser.add_argument('consumer_key', type=str)
  token_invalidate_subparser.add_argument('consumer_secret', type=str)
  token_invalidate_subparser.set_defaults(func=call_token_invalidate_api)


def parser_setup_oauth2(parser):

  parser.add_argument('--token-cache-env-variable', type=str, default='API_TWITTER_ACCESS_TOKEN')


if __name__ == '__main__':

  parser = argparse.ArgumentParser()
  subparsers = parser.add_subparsers()

  parser_setup_oauth2(parser)
  subparser_setup_oauth2(subparsers)

  args = parser.parse_args()
  args.func(args)

