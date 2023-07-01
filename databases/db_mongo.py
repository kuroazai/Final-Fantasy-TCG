from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError


class MongoDB:
    def __init__(self, uri: str, database: str):
        self.client = MongoClient(uri)
        self.db = self.client[database]

    def get_collection(self, collection_name: str) -> Collection:
        return self.db[collection_name]

    def find_one(self, collection_name: str, query: dict) -> dict:
        return self.get_collection(collection_name).find_one(query)

    def find(self, collection_name: str, query: dict, sort: list = None) -> list:
        cursor = self.get_collection(collection_name).find(query)
        if sort:
            cursor.sort(sort)
        return list(cursor)

    def insert_one(self, collection_name: str, data: dict) -> bool:
        try:
            self.get_collection(collection_name).insert_one(data)
            return True
        except DuplicateKeyError:
            return False

    def update_one(self, collection_name: str, filter: dict, update: dict) -> bool:
        result = self.get_collection(collection_name).update_one(filter, {"$set": update})
        return result.modified_count > 0

    def create_unique_index(self, collection_name: str, field_name: str) -> None:
        self.get_collection(collection_name).create_index(field_name, unique=True)

    def upsert_one(self, collection_name: str, filter: dict, update: dict) -> bool:
        if self.update_one(collection_name, filter, update):
            return True
        return self.insert_one(collection_name, {**filter, **update})

    def close(self):
        self.client.close()
