from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import MultiLabelBinarizer


def extract_features(dataset):
    texts = dataset['text'].tolist()
    labels = dataset['intent'].tolist()

    vectorizer = CountVectorizer()
    features = vectorizer.fit_transform(texts)

    label_encoder = MultiLabelBinarizer()
    encoded_labels = label_encoder.fit_transform(labels)

    return features, encoded_labels, vectorizer, label_encoder
