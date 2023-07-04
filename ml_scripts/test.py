from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Conv1D, GlobalMaxPooling1D
from tensorflow.keras.callbacks import EarlyStopping

def prepare_data(dataset):
    texts = dataset['text']
    intents = dataset['intent']

    # Initialize the vectorizer
    vectorizer = CountVectorizer()
    features = vectorizer.fit_transform(texts)

    # Initialize the MultiLabelBinarizer for encoding the intents
    label_encoder = MultiLabelBinarizer()
    encoded_labels = label_encoder.fit_transform(intents)

    return features, encoded_labels, vectorizer, label_encoder

# Example usage
dataset = {
    'text': ['Sample text 1', 'Sample text 2', 'Sample text 3'],
    'intent': [['intent1', 'intent2'], ['intent2'], ['intent1', 'intent3']]
}

features, labels, vectorizer, label_encoder = prepare_data(dataset)

print("Features shape:", features.shape)
print("Labels shape:", labels.shape)


# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)

# Define the CNN model
model = Sequential()
model.add(Conv1D(128, 5, activation='relu', input_shape=(X_train.shape[1], 1)))
model.add(GlobalMaxPooling1D())
model.add(Dense(128, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(y_train.shape[1], activation='sigmoid'))

# Compile the model
model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

# Define early stopping to prevent overfitting
early_stopping = EarlyStopping(monitor='val_loss', patience=3)

# Train the model
history = model.fit(X_train.toarray(), y_train, validation_data=(X_test.toarray(), y_test),
                    epochs=10, batch_size=16, callbacks=[early_stopping])

# Evaluate the model
loss, accuracy = model.evaluate(X_test.toarray(), y_test)
print("Test Loss:", loss)
print("Test Accuracy:", accuracy)