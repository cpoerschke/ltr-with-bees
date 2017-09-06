#!/usr/bin/python

import argparse
import json
import os
import urllib
import urllib2


solr_port=int(os.environ.get("SOLR_PORT", "8983"))

solr_select_url_pattern='http://localhost:'+str(solr_port)+'/solr/%s/select'
solr_update_url_pattern='http://localhost:'+str(solr_port)+'/solr/%s/update?commit=true'


def print_row(row):

  print str(row)


def do_solr_select_all(collection_name, callback_func=print_row):

  url = solr_select_url_pattern % collection_name
  url += ('?q=*:*')
  url += ('&rows=1000000') # note: technically 1000000 is not 'all' of course

  response = urllib.urlopen(url).read()
  response_json = json.loads(response)
  docs = response_json["response"]["docs"]
  for dd in range(0,len(docs)):
    callback_func(docs[dd])


def subparser_setup_solr_select_all(subparsers, subparser_name='select-all', collection_name=None, callback_func=print_row):

  select_subparser=subparsers.add_parser(subparser_name)
  if collection_name == None:
      select_subparser.add_argument('collection_name', type=str, metavar='COLLECTION')

  def call_select_all_api(args):

    if collection_name != None:
        c = collection_name
    else:
        c = args.collection_name

    do_solr_select_all(c, callback_func)

  select_subparser.set_defaults(func=call_select_all_api)


def subparser_setup_solr_select(subparsers, subparser_name='select', collection_name=None, fl_func=None, callback_func=print_row):

  select_subparser=subparsers.add_parser(subparser_name)
  # required args
  if collection_name == None:
      select_subparser.add_argument('collection_name', type=str, metavar='COLLECTION')
  select_subparser.add_argument('q', type=str, metavar='QUERY')
  # defaulted args
  select_subparser.add_argument('--rows', default=None, type=int, metavar='ROW')
  select_subparser.add_argument('--sort', default=None, type=str, metavar='SORT')
  # defaulted efi args
  select_subparser.add_argument('--efi-from-desktop', default=None, type=bool)
  select_subparser.add_argument('--efi-from-mobile', default=None, type=bool)

  def call_select_api(args):

    if collection_name != None:
        url = solr_select_url_pattern % collection_name
    else:
        url = solr_select_url_pattern % args.collection_name
    url += ('?q='+urllib.quote(args.q))
    if fl_func != None:
      url += ('&fl='+urllib.quote(','.join(fl_func(args))))
    if args.rows != None:
      url += ('&rows='+str(args.rows))
    if args.sort != None:
      url += ('&sort='+urllib.quote(args.sort))

    response = urllib.urlopen(url).read()
    response_json = json.loads(response)
    docs = response_json["response"]["docs"]
    for dd in range(0,len(docs)):
      callback_func(docs[dd])

  select_subparser.set_defaults(func=call_select_api)


def do_solr_select_facet_counts(collection_name, facet_field):

  url = solr_select_url_pattern % collection_name
  url += ("?q=*:*&facet=on&facet.field="+facet_field)

  response = urllib.urlopen(url).read()
  response_json = json.loads(response)

  raw_facet_counts = response_json.get("facet_counts", {}).get("facet_fields", {}).get(facet_field,[])

  facet_counts = {}
  for ii in range(0,len(raw_facet_counts)):
    if ii%2 == 1:
      facet_counts[raw_facet_counts[ii-1]] = raw_facet_counts[ii]

  return facet_counts


def subparser_setup_solr_select_facet_counts(subparsers, subparser_name='select-facet-counts', collection_name=None, facet_field=None):

  select_subparser=subparsers.add_parser(subparser_name)
  if collection_name == None:
      select_subparser.add_argument('collection_name', type=str, metavar='COLLECTION')
  if facet_field == None:
      select_subparser.add_argument('facet_field', type=str, metavar='FACET-FIELD')

  def call_select_facet_counts_api(args):

    if collection_name != None:
        c = collection_name
    else:
        c = args.collection_name

    if facet_field != None:
        f = facet_field
    else:
        f = args.facet_field

    print do_solr_select_facet_counts(c, f)

  select_subparser.set_defaults(func=call_select_facet_counts_api)


def do_solr_update(collection_name, document):

  url = solr_update_url_pattern % collection_name
  doc = { "add" : { "doc" : document } }

  req = urllib2.Request(url, data=json.dumps(doc))
  req.add_header('Content-Type', 'application/json')

  res = urllib2.urlopen(req)
  return res.read()


def subparser_setup_solr_update(subparsers, subparser_name='update', collection_name=None, document=None):

  select_subparser=subparsers.add_parser(subparser_name)
  if collection_name == None:
      select_subparser.add_argument('collection_name', type=str, metavar='COLLECTION')
  if document == None:
      select_subparser.add_argument('document', type=str, metavar='DOCUMENT')

  def call_update_api(args):

    if collection_name != None:
        c = collection_name
    else:
        c = args.collection_name

    if document != None:
        d = document
    else:
        d = json.loads(args.document)

    print do_solr_update(c, d)

  select_subparser.set_defaults(func=call_update_api)


def subparser_setup_solr_delete_by_query(subparsers, subparser_name='delete-by-query', collection_name=None, query=None):

  select_subparser=subparsers.add_parser(subparser_name)
  if collection_name == None:
      select_subparser.add_argument('collection_name', type=str, metavar='COLLECTION')
  if query == None:
      select_subparser.add_argument('q', type=str, metavar='QUERY')

  def call_delete_api(args):

    if collection_name != None:
        url = solr_update_url_pattern % collection_name
    else:
        url = solr_update_url_pattern % args.collection_name

    if query != None:
        doc = { "delete" : { "query" : query } }
    else:
        doc = { "delete" : { "query" : args.q } }

    req = urllib2.Request(url, data=json.dumps(doc))
    req.add_header('Content-Type', 'application/json')

    res = urllib2.urlopen(req)
    print res.read()

  select_subparser.set_defaults(func=call_delete_api)


if __name__ == '__main__':

  parser = argparse.ArgumentParser()
  subparsers = parser.add_subparsers()

  subparser_setup_solr_select_all(subparsers)
  subparser_setup_solr_select(subparsers)
  subparser_setup_solr_select_facet_counts(subparsers)
  subparser_setup_solr_update(subparsers)
  subparser_setup_solr_delete_by_query(subparsers)

  args = parser.parse_args()
  args.func(args)


