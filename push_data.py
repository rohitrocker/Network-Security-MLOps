import os
import json
import sys



from dotenv import load_dotenv
from pymongo import collection, database
load_dotenv()

MONGO_DB_URL = os.getenv("MONGO_DB_URL")
print(MONGO_DB_URL)

import certifi
ca = certifi.where()

import numpy as np
import pandas as pd
import pymongo

from networksecurity.logging.logger import logging
from networksecurity.exceptions.exception import NetworkSecurityException

class NetworkSecurityExtract:
  def __init__(self):
    try:
      pass
    except Exception as e:
      raise NetworkSecurityException(e,sys)

  def csv_to_json_converter(self,file_path):
    try:
      data = pd.read_csv(file_path)
      data.reset_index(drop=True,inplace=True)
      records = list(json.loads(data.T.to_json()).values())

      return records

    except Exception as e:
      raise NetworkSecurityException(e,sys)

  def insert_data_to_mongodb(self,records,database,collection):
    try:
      self.collection = collection
      self.database = database
      self.records = records

      self.mongo_client = pymongo.MongoClient(MONGO_DB_URL)
      self.database = self.mongo_client[database]

      self.collection = self.database[collection]
      self.collection.insert_many(self.records)

      return (len(self.records))

    except Exception as e:
      raise NetworkSecurityException(e,sys)

if __name__=='__main__':
  FILE_PATH = "Network_Data\phisingData.csv"
  DATABASE = "rohitaay"
  Collection = "NetworkData"
  networkobj = NetworkSecurityExtract()
  records = networkobj.csv_to_json_converter(file_path=FILE_PATH)
  print(records)
  no_of_records = networkobj.insert_data_to_mongodb(records,DATABASE,Collection)
  print(no_of_records)





