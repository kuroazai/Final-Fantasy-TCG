from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import LabelEncoder

def extract_features(dataset):
    texts = dataset['text'].tolist()
    labels = dataset['intent'].tolist()

    vectorizer = CountVectorizer()
    features = vectorizer.fit_transform(texts)

    label_encoder = LabelEncoder()
    encoded_labels = label_encoder.fit_transform([label for labels in labels for label in labels])

    return features, encoded_labels, vectorizer, label_encoder
