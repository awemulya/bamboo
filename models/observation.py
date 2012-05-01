import json

from bson import json_util

from config.db import Database
from lib.constants import DATAFRAME_ID, SOURCE
from lib.utils import df_to_mongo
from models.abstract_model import AbstractModel


class Observation(AbstractModel):

    __collectionname__ = 'observation'

    @classmethod
    def delete(cls, id):
        cls.collection.remove({DATAFRAME_ID: id})

    @classmethod
    def find(cls, query=None, as_df=False):
        """
        Try to parse query if exists, then get all rows for ID matching query,
        or if no query all.  Decode rows from mongo and return.
        """
        if query:
            try:
                query = json.loads(query, object_hook=json_util.object_hook)
            except ValueError, e:
                return e.message
        else:
            query = {}
        query[DATAFRAME_ID] = df[DATAFRAME_ID]
        cursor = cls.collection.find(query)
        if as_df:
            return mongo_to_df(cursor)
        return cursor

    @classmethod
    def save(cls, dframe, dataset, **kwargs):
        df = df_to_mongo(dframe)
        # add metadata to file
        dataframe_id = dataset[DATAFRAME_ID]
        url = kwargs.get('url')
        #raise Exception(dframe.next())
        for row in dframe:
            row[DATAFRAME_ID] = dataframe_id
            row[SOURCE] = url
            # insert data into collection
            cls.collection.insert(row)
