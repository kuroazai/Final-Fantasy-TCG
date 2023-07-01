import unittest
from redis_db import RedisConn


class TestRedisDB(unittest.TestCase):
    def setUp(self):
        self.redis = RedisConn()

    def test_set(self):
        self.redis.set("test", {"test": "test"})
        self.assertEqual(self.redis.get("test"), {"test": "test"})

    def test_set_delete(self):
        self.redis.set("test", {"test": "test"})
        self.redis.delete("test")
        self.assertEqual(0, self.redis.check_key_exists("test"))


if __name__ == "__main__":
    unittest.main()