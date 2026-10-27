import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import streamlit as st, pandas as pd, numpy as np, json
import matplotlib.pyplot as plt
from src.database import init_db, save_student, get_students, delete_student, save_prediction, get_predictions, save_metrics, get_metrics
from src.data_preprocessing import FEATURES, validate_student
from src.predict import predict_student, load_model
from src.train_model import train
from src.explainability import global_importance

st.set_page_config(page_title='Student Academic Risk | Early Warning',page_icon='🎓',layout='wide')
st.markdown("""<style>.block-container{padding-top:1.5rem}.hero{padding:1.4rem 1.6rem;border-radius:16px;background:linear-gradient(120deg,#10243b,#245b76);color:white;margin-bottom:1rem}.hero h1{color:white;margin:0}.hero p{color:#dceaf3;margin:.4rem 0 0}.metric-card{border:1px solid #dce3ea;border-radius:12px;padding:1rem;background:#fff}</style>""",unsafe_allow_html=True)
init_db()
if not (ROOT/'models'/'best_model.pkl').exists():
    with st.spinner('Preparing demo dataset and training initial models...'):
        meta=train(); save_metrics(meta['metrics'])
try: model,meta=load_model(); save_metrics(meta['metrics'])
except Exception as e: st.error(f'Model loading failed: {e}'); st.stop()
page=st.sidebar.radio('Navigation',['Dashboard','Student Prediction','Student Records','Early Warning System','Model Performance','Data Upload','About Project'])
st.sidebar.caption('Local demo • SQLite • No paid API')
st.sidebar.info('Privacy: use anonymized student data. Predictions support early intervention, not punishment.')
def show_result(result,student,save=False):
    st.subheader('Student Academic Risk')
    c1,c2,c3=st.columns(3); c1.metric('Risk level',result['risk_level']); c2.metric('Model-estimated risk probability',f"{result['risk_probability']*100:.1f}%"); c3.metric('Model',result['model_name'])
    st.caption(result['note'])
    left,right=st.columns(2)
    with left:
        st.markdown('**Main contributing risk flags**')
        for x in result['reasons']: st.write('• '+x)
        st.markdown('**Class probability estimates**')
        st.bar_chart(pd.DataFrame({'Estimated probability':result['probabilities']}))
    with right:
        st.markdown('**Recommended supportive actions**')
        for x in result['recommendations']: st.write('☑ '+x)
    if save and st.button('Save Prediction',type='primary'):
        save_student(student); save_prediction(student['student_id'],result); st.success('Student record and prediction history saved locally.')

def student_form(prefix='student'):
    with st.form(prefix+'_form'):
        st.markdown('**Student details**')
        a,b,c=st.columns(3)
        sid=a.text_input('Student ID',value='ST001',key=prefix+'id'); name=b.text_input('Student Name',value='Demo Student',key=prefix+'name'); age=c.number_input('Age',15,100,20,key=prefix+'age')
        gender=a.selectbox('Gender (optional)',['Prefer not to say','Female','Male','Non-binary'],key=prefix+'gender')
        attendance=b.number_input('Attendance (%)',0.0,100.0,72.0,key=prefix+'att'); gpa=c.number_input('Previous GPA / CGPA (0–10)',0.0,10.0,6.2,key=prefix+'gpa')
        internal=a.number_input('Internal marks (%)',0.0,100.0,52.0,key=prefix+'internal'); assignment=b.number_input('Assignment completion (%)',0.0,100.0,65.0,key=prefix+'assignment'); backlogs=c.number_input('Backlogs',0,100,1,key=prefix+'backlogs')
        study=a.number_input('Study hours per day',0.0,24.0,2.0,key=prefix+'study'); failures=b.number_input('Previous semester failures',0,100,0,key=prefix+'failures'); participation=c.number_input('Class participation (%)',0.0,100.0,55.0,key=prefix+'participation')
        submission=a.number_input('Assignment submission rate (%)',0.0,100.0,70.0,key=prefix+'submission'); subjects=b.number_input('Number of subjects',1,50,6,key=prefix+'subjects'); pct=c.number_input('Previous semester percentage',0.0,100.0,65.0,key=prefix+'pct')
        submitted=st.form_submit_button('PREDICT ACADEMIC RISK',type='primary',use_container_width=True)
    student={'student_id':sid.strip(),'student_name':name.strip(),'age':age,'gender':gender,'attendance_pct':attendance,'previous_gpa':gpa,'internal_marks_pct':internal,'assignment_completion_pct':assignment,'backlogs':backlogs,'study_hours_per_day':study,'previous_failures':failures,'class_participation_pct':participation,'assignment_submission_rate':submission,'number_of_subjects':subjects,'previous_semester_pct':pct}
    return submitted,student

if page=='Dashboard':
    st.markdown('<div class="hero"><h1>Student Academic Risk Prediction</h1><p>Early warning signals that help teachers provide timely, supportive intervention.</p></div>',unsafe_allow_html=True)
    students=get_students(); predictions=get_predictions(); df=pd.DataFrame(students); p=pd.DataFrame(predictions)
    if not df.empty and not p.empty:
        latest=p.sort_values('created_at').groupby('student_id').tail(1); counts=latest['risk_level'].value_counts()
    else: counts=pd.Series(dtype=int)
    cols=st.columns(5); cols[0].metric('Students tracked',len(df)); cols[1].metric('High risk',int(counts.get('HIGH RISK',0))); cols[2].metric('Medium risk',int(counts.get('MEDIUM RISK',0))); cols[3].metric('Low risk',int(counts.get('LOW RISK',0))); cols[4].metric('Need attention',int(counts.get('HIGH RISK',0)+counts.get('MEDIUM RISK',0)))
    if not df.empty:
        c1,c2=st.columns(2)
        with c1:
            st.markdown('#### Student attendance'); st.bar_chart(df.set_index('student_id')['attendance_pct'])
        with c2:
            st.markdown('#### Previous GPA'); st.bar_chart(df.set_index('student_id')['previous_gpa'])
    else: st.info('No saved student records yet. Go to Student Prediction to assess and save a demo student, or upload a CSV.')
    st.markdown('#### Latest prediction history')
    if predictions: st.dataframe(pd.DataFrame(predictions).drop(columns=['probabilities_json','reasons_json','recommendations_json'],errors='ignore'),use_container_width=True)
    st.caption('Demo training uses synthetic data. Model scores and risk probabilities are not real-world validated.')
elif page=='Student Prediction':
    st.title('Student Prediction'); st.write('Enter student information to generate a model-estimated academic risk assessment.')
    submitted,student=student_form('predict')
    if submitted:
        errors=validate_student(student)
        if errors:
            for e in errors: st.error(e)
        else:
            try: result=predict_student(student); show_result(result,student,save=True)
            except Exception as e: st.error(f'Prediction failed: {e}')
elif page=='Student Records':
    st.title('Student Records'); students=get_students(); df=pd.DataFrame(students)
    if df.empty: st.info('No saved records yet. Save a prediction first.')
    else:
        query=st.text_input('Search by student ID or name'); view=df[df.astype(str).apply(lambda r:r.str.contains(query,case=False,na=False).any(),axis=1)] if query else df
        st.dataframe(view.drop(columns=['updated_at'],errors='ignore'),use_container_width=True)
        ids=view['student_id'].tolist(); selected=st.selectbox('Select student for history / delete',ids) if ids else None
        if selected:
            with st.expander('Prediction history'): st.dataframe(pd.DataFrame(get_predictions(selected)),use_container_width=True)
            if st.button('Delete selected student and their history',type='secondary'):
                delete_student(selected); st.success('Record deleted. Refresh the page to update the table.')
elif page=='Early Warning System':
    st.title('Early Warning System'); records=get_predictions(); df=pd.DataFrame(records)
    if df.empty: st.info('No prediction history available yet. Save predictions to populate this view.')
    else:
        risk=st.multiselect('Risk level',['HIGH RISK','MEDIUM RISK','LOW RISK'],default=['HIGH RISK','MEDIUM RISK']); df=df[df['risk_level'].isin(risk)]
        att=st.checkbox('Only attendance below 75%')
        if att:
            sm=pd.DataFrame(get_students()); df=df.merge(sm[['student_id','attendance_pct','backlogs','internal_marks_pct']],on='student_id',how='left'); df=df[df['attendance_pct']<75]
        st.dataframe(df.drop(columns=['probabilities_json','reasons_json','recommendations_json'],errors='ignore'),use_container_width=True)
        st.download_button('Download warning list CSV',df.to_csv(index=False).encode('utf-8'),file_name='early_warning_students.csv',mime='text/csv')
elif page=='Model Performance':
    st.title('Model Performance'); st.warning('All metrics below are evaluated on a held-out split of synthetic/demo data. They are not evidence of real-world performance.')
    metrics=meta['metrics']; st.dataframe(pd.DataFrame(metrics).sort_values('f1',ascending=False),use_container_width=True)
    mdf=pd.DataFrame(metrics).set_index('model')[['accuracy','precision','recall','f1']]; st.bar_chart(mdf)
    selected=st.selectbox('Inspect confusion matrix / report',[m['model'] for m in metrics],index=[m['model'] for m in metrics].index(meta['best_model']))
    cm=np.array(meta['confusion_matrices'][selected]); fig,ax=plt.subplots(); im=ax.imshow(cm); ax.set_xticks([0,1,2],['Low','Medium','High']); ax.set_yticks([0,1,2],['Low','Medium','High']); ax.set_xlabel('Predicted'); ax.set_ylabel('Actual');
    for i in range(3):
        for j in range(3): ax.text(j,i,str(cm[i,j]),ha='center',va='center')
    st.pyplot(fig); st.text(meta['classification_reports'][selected])
    imp=global_importance(model)
    if imp: st.markdown('#### Global model feature importance (where supported)'); st.bar_chart(pd.DataFrame(imp).set_index('feature'))
    if st.button('Retrain models on a newly generated synthetic dataset'):
        with st.spinner('Training models...'): new=train(); save_metrics(new['metrics'])
        st.success('Models retrained. Refresh the app to load the updated model.')
elif page=='Data Upload':
    st.title('Data Upload'); st.write('Upload a CSV with the student feature columns. Predictions are generated locally; uploaded data is not automatically saved to the database.')
    st.caption('Required columns: '+', '.join(FEATURES)); uploaded=st.file_uploader('Upload student CSV',type=['csv'])
    if uploaded:
        try:
            df=pd.read_csv(uploaded); st.write('Preview'); st.dataframe(df.head(10),use_container_width=True)
            required=set(FEATURES+['student_id','student_name']); missing=sorted(required-set(df.columns))
            if missing: st.error('Missing required columns: '+', '.join(missing))
            elif st.button('Validate and predict all rows',type='primary'):
                results=[]; errors=[]
                for i,row in df.iterrows():
                    student=row.to_dict(); issue=validate_student(student)
                    if issue: errors.append({'row':int(i)+2,'errors':' '.join(issue)}); continue
                    try:
                        result=predict_student(student); results.append({**{k:student.get(k) for k in ['student_id','student_name']},'risk_level':result['risk_level'],'risk_probability_pct':round(result['risk_probability']*100,2),'main_reasons':'; '.join(result['reasons']),'recommendations':'; '.join(result['recommendations'])})
                    except Exception as e: errors.append({'row':int(i)+2,'errors':str(e)})
                if results:
                    out=pd.DataFrame(results); st.success(f'Predictions generated for {len(out)} row(s).'); st.dataframe(out,use_container_width=True); st.download_button('Download prediction results CSV',out.to_csv(index=False).encode('utf-8'),file_name='student_risk_predictions.csv',mime='text/csv')
                if errors: st.error(f'{len(errors)} row(s) failed validation.'); st.dataframe(pd.DataFrame(errors),use_container_width=True)
        except Exception as e: st.error(f'Could not read CSV: {e}')
elif page=='About Project':
    st.title('About Project'); st.markdown("""### Student Academic Risk Prediction & Early Warning System
**Problem:** Teachers may need help identifying students who could benefit from additional academic support.

**Technology:** Python, Streamlit, SQLite, pandas, scikit-learn, optional XGBoost, joblib and Matplotlib.

**ML workflow:** Synthetic dataset → validation/cleaning → preprocessing → stratified train/test split → model comparison → selection by weighted F1 (recall/precision tie-breaks) → probability estimate and supportive recommendations.

**Privacy:** Use anonymized or consented data. Gender is included only as an optional demonstration input and should be excluded from consequential decision workflows unless there is a justified, audited reason. Do not use sensitive attributes to punish or deny opportunities.

**Limitations:** The bundled dataset is synthetic and the model has not been validated on real student populations. Synthetic labels are generated from illustrative rules and noise, so reported metrics measure performance on that artificial task only. Probability values are not calibrated guarantees. Rules listed as contributing flags are contextual indicators, not causal explanations. A teacher must review context and speak with the student before acting.

**Disclaimer:** This system is an academic decision-support tool. Predictions are estimates and should not be used as the sole basis for academic decisions.""")
