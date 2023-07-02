import pandas as pd
from ml_scripts.feature_extractor import extract_features
from databases.redis_db import RedisConn


def load_data(key: str):
    redis.get(key)


def load_dataset(data: list) -> pd.DataFrame:
    df = pd.DataFrame(data,
                      columns=['text', 'intent'])
    return df


def run_feature_extraction(data: list):
    df = load_dataset(data)
    features, encoded_labels, vectorizer, label_encoder = extract_features(df)
    return features, encoded_labels, vectorizer, label_encoder


def save_data(key: str, data: str):
    redis.set(key, data)


if __name__ == "__main__":
    redis = RedisConn()
