#!/usr/bin/python

import argparse
from datetime import datetime
import json
import subprocess
import os
from xml.etree import ElementTree


def queryId2results_mock(args):

  return {
    "queryId1" : {
      "resultId1" : {
        "score" : 1.25,
        "features" : [ "xyzContent:0.75", "byABC:0", "hasZ:0" ],
        "click_times" : [ "YYYY-MM-DD HH:MM:SS" ]
      },
      "resultId2" : {
        "score" : 1.0,
        "features" : [ "xyzContent:0.5", "byABC:0", "hasZ:0" ],
        "click_times" : [] # no clicks
      }
    },
    "queryId2" : {
      "resultId3" : {
        "score" : 1.5,
        "features" : [ "xyzContent:0.5", "byABC:1", "hasZ:0" ],
        "click_times" : [ "YYYY-MM-DD HH:MM:SS" ]
      },
      "resultId4" : {
        "score" : 1.0,
        "features" : [ "xyzContent:1.5", "byABC:1", "hasZ:0" ],
        "click_times" : [] # no clicks
      }
    }
  }


def featureMappings(queryId2results):

  featureName2featureIndex = {}
  for queryId in queryId2results:
     for resultId in queryId2results[queryId]:
       for feature in queryId2results[queryId][resultId]["features"]:
         (featureName, featureValue) = feature.split(':')
         if featureName not in featureName2featureIndex:
            featureName2featureIndex[featureName] = len(featureName2featureIndex)+1

  featureIndex2featureName = { featureName2featureIndex[x] : x for x in featureName2featureIndex }

  return (featureName2featureIndex, featureIndex2featureName)


def modelInputRows(args, queryId2results, featureName2featureIndex):

  queryId2qid = {}
  for queryId in queryId2results:
     if queryId not in queryId2qid:
       queryId2qid[queryId] = len(queryId2qid)+1

  if not args.feature_names:
    featuresOfInterest = []
  else:
    featuresOfInterest = args.feature_names.split(",")

  rows = []
  for queryId in queryId2results:
     for resultId in queryId2results[queryId]:
       row = { "qid" : str(queryId2qid[queryId]) }
       for key in queryId2results[queryId][resultId]:
         val = queryId2results[queryId][resultId][key]

         if key == "features":
           val_original = val
           val = []
           for feature in val_original:
             (featureName, featureValue) = feature.split(':')
             if len(featuresOfInterest) > 0 and featureName not in featuresOfInterest:
               continue
             featureIndex = featureName2featureIndex[featureName]
             val.append(':'.join([str(featureIndex), featureValue]))
         elif key == "click_times":
           key = "was_clicked"
           val = True if len(val) > 0 else False
         else:
           continue

         row[key] = val

       rows.append(row)

  return rows


def modelOutputParams(args, modelInputRows):

  with open(args.inputs_file_name, 'w') as file:
    for row in modelInputRows:
      line = "2" if row["was_clicked"] else "1"
      line += " "
      line += (":".join(["qid", row["qid"]]))
      line += " "
      line += (" ".join(row["features"]))
      line += "\n"
      file.write(line)

  cmd   =    ['java', '-jar', args.ranklib_jar]
  cmd.extend(['-train', args.inputs_file_name])
  cmd.extend(['-save', args.outputs_file_name])
  cmd.extend(['-ranker', str(args.ranklib_ranker)])
  if args.ranklib_tree != None:
    cmd.extend(['-tree', str(args.ranklib_tree)])
  if args.ranklib_leaf != None:
    cmd.extend(['-leaf', str(args.ranklib_leaf)])

  if args.verbose:
    print
    print "calling '"+" ".join(cmd)+"'"

  subprocess.call(cmd)

  ensemble_xml_string = None

  with open(args.outputs_file_name, 'r') as file:
    lines = file.read().split('\n')
    for line in lines:
      if line=='<ensemble>':
        ensemble_xml_string = (line+'\n')
      elif ensemble_xml_string != None:
        ensemble_xml_string += (line+'\n')

  return ensemble_xml_string


def saveModel(args, ensemble_xml_string, featureIndex2featureName):

  def transform_branches(root, featureIndex2featureName):

    # turn feature index into feature name
    for feature in root.findall("feature"):
      feature.text = featureIndex2featureName[int(feature.text)]

    for threshold in root.findall("threshold"):
        threshold.text = str(float(threshold.text))

    for branch in root.findall("split"):
      # turn <split> element with pos='???' attribute into <???> element
      branch.tag = branch.get("pos")

      # turn <output> element into <value> element
      for output in branch.findall("output"):
        output.tag = "value"
        output.text = str(float(output.text))

      # recurse
      transform_branches(branch, featureIndex2featureName)


  def parse_and_adjust_xml(xml_string):

    ensemble = ElementTree.fromstring(xml_string)

    for tree in ensemble.findall("tree"):

      # turn 'weight' attribute into 'weight' sub-element
      weight = ElementTree.SubElement(tree, 'weight')
      weight.text = str(tree.get("weight"))

      # rename tree root from <split> to <root>
      for root in tree.findall("split"):
        root.tag = "root"

        transform_branches(root, featureIndex2featureName)

    return ensemble


  def json_from_xml(input):

    if input.text != None and input.text.replace("\n","").replace("\t","") != "":

      return input.text

    else:

      return { elem.tag : json_from_xml(input.find(elem.tag)) for elem in list(input) }


  def trees_from_ensemble(xml_string):

    ensemble_xml = parse_and_adjust_xml(xml_string)

    return [ json_from_xml(tree) for tree in ensemble_xml.findall("tree") ]


  def features_set_from_trees(trees):

    features_set = set()

    def collect_features_from_tree(sub_tree):

      if sub_tree.has_key("feature"):
        features_set.add(sub_tree.get("feature"))

      if sub_tree.has_key("left"):
        collect_features_from_tree(sub_tree.get("left"))

      if sub_tree.has_key("right"):
        collect_features_from_tree(sub_tree.get("right"))

    for tree in trees:
      collect_features_from_tree(tree.get("root"))

    return [ { "name" : name } for name in features_set ]


  trees = trees_from_ensemble(ensemble_xml_string)
  features = list(features_set_from_trees(trees))

  treesModel = {
    "class" : "org.apache.solr.ltr.model.MultipleAdditiveTreesModel",
    "name" : args.model_name,
    "features" : features,
    "params" : { "trees" : trees }
  }

  with open(args.model_file_name, 'w') as file:
     # todo: influence ordering of elements
    json.dump(treesModel, file, indent=2, separators=(',', ' : '))

  print "Saved %s model to %s file." % (args.model_name, args.model_file_name)

  return treesModel


def subparser_setup_train(subparsers, subparser_name, queryId2results_func, verbose=False, modelInputRows_func=modelInputRows, modelOutputParams_func=modelOutputParams, saveModel_func=saveModel):

  YYYYMMDD_HHMMSS = datetime.now().strftime("%Y%m%d-%H%M%S")

  train_subparser=subparsers.add_parser(subparser_name)
  train_subparser.add_argument('--inputs-file-name', default='trees-inputs-'+YYYYMMDD_HHMMSS+'.txt', type=str)
  train_subparser.add_argument('--outputs-file-name', default='trees-outputs-'+YYYYMMDD_HHMMSS+'.txt', type=str)
  train_subparser.add_argument('--feature-names', default=None, type=str)
  train_subparser.add_argument('--model-name', default='trees-model-'+YYYYMMDD_HHMMSS, type=str)
  train_subparser.add_argument('--model-file-name', default='trees-model-'+YYYYMMDD_HHMMSS+'.json', type=str)
  train_subparser.add_argument('--ranklib-jar', default='RankLib-2.8.jar', type=str)
  train_subparser.add_argument('--ranklib-ranker', default=0, type=int)
  train_subparser.add_argument('--ranklib-tree', default=None, type=int)
  train_subparser.add_argument('--ranklib-leaf', default=None, type=int)
  train_subparser.add_argument('--verbose', default=verbose, action='store_true')

  def call_train_api(args):

    queryId2results = queryId2results_func(args)
    if args.verbose:
      print
      print queryId2results

    (featureName2featureIndex, featureIndex2featureName) = featureMappings(queryId2results)
    if args.verbose:
      print
      print featureName2featureIndex
      print featureIndex2featureName

    rows = modelInputRows_func(args, queryId2results, featureName2featureIndex)
    if args.verbose:
      print
      print rows

    ensemble_xml_string = modelOutputParams_func(args, rows)
    if args.verbose:
      print
      print ensemble_xml_string

    savedModel = saveModel_func(args, ensemble_xml_string, featureIndex2featureName)
    if args.verbose:
      print
      print json.dumps(savedModel, indent=2, separators=(',', ' : '))

  train_subparser.set_defaults(func=call_train_api)


if __name__ == '__main__':

  parser = argparse.ArgumentParser()
  subparsers = parser.add_subparsers()

  subparser_setup_train(subparsers, subparser_name='train-mock-model', verbose=False, queryId2results_func=queryId2results_mock)

  subparser_setup_train(subparsers, subparser_name='train-and-show-mock-model', verbose=True, queryId2results_func=queryId2results_mock)

  args = parser.parse_args()
  args.func(args)


