#!/usr/bin/python

import argparse
from datetime import datetime
import json
import subprocess
import os


def queryId2results_mock(args):

  return {
    "queryId1" : {
      "resultId1" : {
        "score" : 1.23,
        "features" : [ "hasXYZ:0", "byABC:1", "zContent:0.5" ],
        "click_times" : [ "YYYY-MM-DD HH:MM:SS" ]
      },
      "resultId2" : {
        "score" : 1.0,
        "features" : [ "hasXYZ:1", "byABC:0", "zContent:0" ],
        "click_times" : [] # no clicks
      }
    },
    "queryId2" : {
      # no results
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

  if not args.feature_names:
    featuresOfInterest = []
  else:
    featuresOfInterest = args.feature_names.split(",")

  rows = []
  for queryId in queryId2results:
     for resultId in queryId2results[queryId]:
       row = {}
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
      line = "+1" if row["was_clicked"] else "-1"
      line += " "
      line += (" ".join(row["features"]))
      line += "\n"
      file.write(line)

  cmd   =   [args.liblinear_train]
  cmd.append(args.inputs_file_name)
  cmd.append(args.outputs_file_name)

  if args.verbose:
    print
    print "calling '"+" ".join(cmd)+"'"

  subprocess.call(cmd)

  featureIndex2featureWeight = {}

  seen_w = False
  with open(args.outputs_file_name, 'r') as file:
    lines = file.read().split('\n')
    for line in lines:
      if line=='w':
        seen_w = True
      elif seen_w and line!='':
        featureIndex = len(featureIndex2featureWeight) + 1
        featureIndex2featureWeight[featureIndex] = float(line.replace(' ',''))

  return featureIndex2featureWeight


def saveModel(args, featureIndex2featureWeight, featureIndex2featureName):

  linearModel = {
    "class" : "org.apache.solr.ltr.model.LinearModel",
    "name" : args.model_name,
    "features" : [],
    "params" : { "weights" : {} }
  }

  for featureIndex in featureIndex2featureWeight:
    featureName   = featureIndex2featureName[featureIndex]
    featureWeight = featureIndex2featureWeight[featureIndex]

    if featureWeight == 0.0:
      continue

    linearModel["features"].append({ "name" : featureName })
    linearModel["params"]["weights"][featureName] = featureWeight

  with open(args.model_file_name, 'w') as file:
     # todo: influence ordering of elements
    json.dump(linearModel, file, indent=2, separators=(',', ' : '))

  print "Saved %s model to %s file." % (args.model_name, args.model_file_name)

  return linearModel


def subparser_setup_train(subparsers, subparser_name, queryId2results_func, verbose=False, modelInputRows_func=modelInputRows, modelOutputParams_func=modelOutputParams, saveModel_func=saveModel):

  YYYYMMDD_HHMMSS = datetime.now().strftime("%Y%m%d-%H%M%S")

  train_subparser=subparsers.add_parser(subparser_name)
  train_subparser.add_argument('--inputs-file-name', default='linear-inputs-'+YYYYMMDD_HHMMSS+'.txt', type=str)
  train_subparser.add_argument('--outputs-file-name', default='linear-outputs-'+YYYYMMDD_HHMMSS+'.txt', type=str)
  train_subparser.add_argument('--feature-names', default=None, type=str)
  train_subparser.add_argument('--model-name', default='linear-model-'+YYYYMMDD_HHMMSS, type=str)
  train_subparser.add_argument('--model-file-name', default='linear-model-'+YYYYMMDD_HHMMSS+'.json', type=str)
  train_subparser.add_argument('--liblinear-train', default='liblinear-2.11/train', type=str)
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

    featureIndex2featureWeight = modelOutputParams_func(args, rows)
    if args.verbose:
      print
      print featureIndex2featureWeight

    savedModel = saveModel_func(args, featureIndex2featureWeight, featureIndex2featureName)
    if args.verbose:
      print
      print savedModel

  train_subparser.set_defaults(func=call_train_api)


if __name__ == '__main__':

  parser = argparse.ArgumentParser()
  subparsers = parser.add_subparsers()

  subparser_setup_train(subparsers, subparser_name='train-mock-model', verbose=False, queryId2results_func=queryId2results_mock)

  subparser_setup_train(subparsers, subparser_name='train-and-show-mock-model', verbose=True, queryId2results_func=queryId2results_mock)

  args = parser.parse_args()
  args.func(args)


