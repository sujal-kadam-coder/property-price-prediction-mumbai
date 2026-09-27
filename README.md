# PROPERTY AI — Final

Complete Flask + Scikit-learn Mumbai property prediction and comparison website.

## Prediction
The user enters ONLY:
- BHK
- Property Type
- Area
- Region
- Status
- Age

Locality is NOT requested and is NOT used as an ML prediction feature.

## Automatic model selection
The system trains Linear Regression and Random Forest, evaluates both on the same 20% test split, and automatically uses the model with the lower RMSE. The user is never asked to choose a model.

## Run on Windows
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python train_model.py
python app.py
```
Open http://127.0.0.1:5000
