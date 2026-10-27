"""Human-readable, rule-based context for predictions; not causal explanations."""
from src.feature_engineering import risk_reasons

def global_importance(model):
    try:
        estimator=model.named_steps['model']; prep=model.named_steps['preprocessor']
        names=prep.get_feature_names_out(); values=getattr(estimator,'feature_importances_',None)
        if values is None and hasattr(estimator,'coef_'): values=abs(estimator.coef_).mean(axis=0)
        if values is None: return []
        return sorted([{'feature':str(n).replace('num__','').replace('cat__',''),'importance':float(v)} for n,v in zip(names,values)],key=lambda x:x['importance'],reverse=True)[:12]
    except Exception: return []
