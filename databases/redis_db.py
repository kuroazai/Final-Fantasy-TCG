import redis
import json


class RedisConn:

    def __init__(self):
        self.redis = redis.Redis(
            host='192.168.0.6',  # TODO: change this to your host
            port=6379,
            password='kaioken')  # TODO: change this to your password

    def get(self, key):
        return json.loads(self.redis.get(key))

    def set(self, key, value):
        self.redis.set(key, json.dumps(value))

    def delete(self, key):
        self.redis.delete(key)

    def check_key_exists(self, key):
        return self.redis.exists(key)


if __name__ == '__main__':
    test_conn = RedisConn()
    test_conn.set('test', {'test': 'test'})
    test_conn.delete('test')