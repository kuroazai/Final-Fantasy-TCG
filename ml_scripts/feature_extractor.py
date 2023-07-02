from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import LabelEncoder


def extract_features(dataset):
    # Extract input texts and corresponding labels from the dataset
    texts = dataset['text']
    labels = dataset['intent']

    # Initialize the CountVectorizer for bag-of-words representation
    vectorizer = CountVectorizer()

    # Fit the vectorizer on the input texts to learn the vocabulary
    vectorizer.fit(texts)

    # Transform the input texts into a document-term matrix
    features = vectorizer.transform(texts)

    # Encode the intent labels as integers
    label_encoder = LabelEncoder()
    encoded_labels = label_encoder.fit_transform(labels)

    return features, encoded_labels, vectorizer, label_encoder
