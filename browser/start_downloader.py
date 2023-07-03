import downloader
from databases.redis_db import RedisConn


def main():
    redis_conn = RedisConn()
    downloader.DLEngine(redis_conn).download_cards()


if __name__ == "__main__":
    main()




