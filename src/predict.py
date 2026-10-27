from pathlib import Path
import json, joblib, pandas as pd
from src.data_preprocessing import clean_features, validate_student
from src.feature_engineering import risk_reasons
from src.recommendations import generate_recommendations
ROOT=Path(__file__).resolve().parents[1]; MODEL_PATH=ROOT/'models'/'best_model.pkl'; META_PATH=ROOT/'models'/'model_metadata.json'
def load_model():
    if not MODEL_PATH.exists():
        from src.train_model import train
        train()
    model=joblib.load(MODEL_PATH); meta=json.loads(META_PATH.read_text(encoding='utf-8'))
    return model,meta

def predict_student(student):
    errors=validate_student(student)
    if errors: raise ValueError(' '.join(errors))
    model,meta=load_model(); X=clean_features(pd.DataFrame([student])); pred=int(model.predict(X)[0]); probs=model.predict_proba(X)[0]
    labels=['LOW RISK','MEDIUM RISK','HIGH RISK']; probability=float(probs[pred])
    return {'risk_level':labels[pred],'risk_probability':probability,'probabilities':{labels[i]:float(probs[i]) for i in range(len(labels))},'reasons':risk_reasons(student),'recommendations':generate_recommendations(student),'model_name':meta['best_model'],'note':'Model-estimated probability from synthetic/demo training data; not a validated real-world likelihood.'}
