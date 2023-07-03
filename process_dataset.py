import pandas as pd
from ml_scripts.feature_extractor import extract_features
from databases.redis_db import RedisConn
from nlp_scripts import intent_classification


def load_data(key: str) -> pd.DataFrame:
    return pd.DataFrame(list(redis.get(key)))


def process_intents(data: pd.DataFrame) -> list:
    intents = []
    i = 0
    for index, row in data.iterrows():
        intents += intent_classification.process_card_description(row['text'])
        i += 1
        if i ==5:
            print(intents)
            break
    return intents


def load_dataset(data: list) -> pd.DataFrame:
    df = pd.DataFrame(data,
                      columns=['text', 'intent'])
    return df


def run_feature_extraction(data: list):
    df = load_dataset(data)
    print(df.head())
    features, encoded_labels, vectorizer, label_encoder = extract_features(df)
    return features, encoded_labels, vectorizer, label_encoder


if __name__ == "__main__":
    redis = RedisConn()
    data = load_data("ff-tcg-cards")
    intents = process_intents(data)
    redis.set("ff-tcg-intents", intents)
    features, encoded_labels, vectorizer, label_encoder = run_feature_extraction(intents)
