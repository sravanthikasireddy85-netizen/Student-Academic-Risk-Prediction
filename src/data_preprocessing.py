"""Input validation and preprocessing helpers."""
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERIC_FEATURES = ["age", "attendance_pct", "previous_gpa", "internal_marks_pct", "assignment_completion_pct", "backlogs", "study_hours_per_day", "previous_failures", "class_participation_pct", "assignment_submission_rate", "number_of_subjects", "previous_semester_pct"]
CATEGORICAL_FEATURES = ["gender"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
REQUIRED_INPUTS = ["student_id", "student_name"] + FEATURES

def validate_student(data):
    errors=[]
    for field in ["student_id", "student_name"]:
        if not str(data.get(field, "")).strip(): errors.append(f"{field.replace('_',' ').title()} is required.")
    ranges={"age":(15,100),"attendance_pct":(0,100),"previous_gpa":(0,10),"internal_marks_pct":(0,100),"assignment_completion_pct":(0,100),"backlogs":(0,100),"study_hours_per_day":(0,24),"previous_failures":(0,100),"class_participation_pct":(0,100),"assignment_submission_rate":(0,100),"number_of_subjects":(1,50),"previous_semester_pct":(0,100)}
    for k,(lo,hi) in ranges.items():
        try:
            v=float(data.get(k))
            if not lo <= v <= hi: errors.append(f"{k.replace('_',' ').title()} must be between {lo} and {hi}.")
            if k in ("backlogs","previous_failures","number_of_subjects") and v % 1: errors.append(f"{k.replace('_',' ').title()} must be a whole number.")
        except (TypeError,ValueError): errors.append(f"{k.replace('_',' ').title()} must be a valid number.")
    if data.get("gender") not in ("Female","Male","Non-binary","Prefer not to say","Unknown",None): errors.append("Choose a valid gender option.")
    return errors

def make_preprocessor():
    numeric=Pipeline([("imputer",SimpleImputer(strategy="median")),("scaler",StandardScaler())])
    categorical=Pipeline([("imputer",SimpleImputer(strategy="most_frequent")),("onehot",OneHotEncoder(handle_unknown="ignore"))])
    return ColumnTransformer([("num",numeric,NUMERIC_FEATURES),("cat",categorical,CATEGORICAL_FEATURES)])

def clean_features(df):
    out=df.copy()
    for col in NUMERIC_FEATURES: out[col]=pd.to_numeric(out[col],errors="coerce")
    if "gender" not in out: out["gender"]="Prefer not to say"
    out["gender"]=out["gender"].fillna("Prefer not to say").astype(str)
    return out[FEATURES]
