import os
import joblib
from janome.tokenizer import Tokenizer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'ml_models', 'sentiment_model.pkl')
VECTORIZER_PATH = os.path.join(BASE_DIR, 'ml_models', 'vectorizer.pkl')

t = Tokenizer()


def tokenize_ja(text):
    """日本語の文章を単語に分割する(TfidfVectorizerから参照される関数)"""
    return list(t.tokenize(text, wakati=True))


_model = joblib.load(MODEL_PATH)
_vectorizer = joblib.load(VECTORIZER_PATH)

# pickle化された古いtokenizer関数を、この環境で動くものに差し替える
_vectorizer.tokenizer = tokenize_ja


def predict_sentiment(text):
    if not text:
        return None

    X = _vectorizer.transform([text])
    prediction = _model.predict(X)[0]

    return 'positive' if prediction == 0 else 'negative'
