# LostTime
Orienteering utilities on the web. Visit <http://LostTimeOrienteering.com> to simplify your workflow and recover some lost time.

The current goal of LostTime is not to replace event management software, but to make tasks before and after an event easier. Customization on a per-club basis is expected.

# Usage

## Entries
**Input**: any number of .csv files representing entries  
**Output**: single .csv file ready for import into SportSoftware  
For the input .csv files, if the header line contains any of the following strings, its data will be included in the output: `bib`, `first`, `last`, `club` or `school`, `class`, `sex` or `gen`, `punch` or `card`, `rent`, and `nc`. Checking is loose: a column titled `First Name` will match `first`. *(Special case, the word `emergency` does not match `gen` or `nc`.)*

## Event Results
**Input**: single IOF v3 .xml `<ResultList>` file  
**Output**: single .html page, results by class, sorted, and scored  
Scoring methods include: Time (no score), Ratio to winner (1000pts), World Cup (100, 95, 92, 90, ...), or Alphabetical sorting (no placement).

# Backlog
## Entries
- make the default output an IOF xml `<EntryList>` file, for greater inter-operability

## Event Results
- Calculate and output an additional html page with team results, starting with COC WIOL scoring algorithm.

## Series Results
- Allow multiple events to be combined into a series for scoring purposes
- Configure different series scoring parameters
- Calculate and output html page of series results


# Technical Notes
## Architecture
This is a Flask application with a SQLite backend. There is currently no front-end framework; data is passed to the Jinja2 template engine that comes bundled with Flask.
## Development and Testing
You'll need python 2.x and `virtualenvwrapper` installed on a linux machine (or windows subsystem for linux):

1. Fork the project, then clone to a folder on your machine
   ```bash
   $ git clone https://github.com/<username>/LostTime.git <Path/To/Project/Folder>
   ```

2. Set up a python virtual environment with all dependencies. (The `-a` flag adds a virtual environment to an existing project directory; that's what we want to do.)
   ```bash
   $ mkvirtualenv losttime -a <ProjectFolder> -r requirements.txt
   ```

   It's likely that the `lxml` package will fail to install as it has some lower level C dependencies. Check out the lxml [http://lxml.de/installation.html](installation instructions) for help. I needed the following on my Ubuntu 14.04 in Windows Subsystem for Linux:
   ```bash
   (losttime)$ sudo apt-get install libxml2-dev libxslt-dev python-dev zlib1g-dev
   (losttime)$ pip install lxml #success!
   ```

3. add your instance config. It might look like this:
   ```python
   # instance/instanceconfig.py

   DEBUG = True
   SQLALCHEMY_DATABASE_URI = 'sqlite:///development.db' #relative path
   SQLALCHEMY_ECHO = True
   SECRET_KEY = 'generate-a-secret-key-with-os.urandom(24)-and-paste-here'
   ```

4. run the development server
   ```bash
   python rundevserver.py
   ```

   OR
   ```bash
   export FLASK_APP=losttime
   export FLASK_DEBUG=1
   python -m flask run
   ```

   There are some bugs with how the `flask` command works in virtual environments, but running it from `python -m` works. 

## Database Management
Using the Flask-Migrations package which leverages the Alembic package for managing database schema changes. Changes in models.py are detected and automatically create a migration script. After making changes, run the following: 
```bash
python -m flask db migrate 
# review the new migration script in migrations/versions, then
python -m flask db upgrade 
```

## Deployment
