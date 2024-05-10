To initialize the project we first need a virtual environment. For that open up Powershell/Bash in the root folder and type:
```
python -m venv .venv
.venv/Scripts/activate
```
Now we need to download the required libraries,
```
pip install -r ./requirements.txt
```
After this we need to initialize the database and fix a version of it:
```
flask --app flask_app db init
flask --app flask_app db migrate
flask --app flask_app db upgrade
```
Now run the development server
```
flask --app flask_app run
```
