# LostTime
Orienteering utilities on the web. Visit <http://LostTimeOrienteering.com> to simplify your workflow and recover some lost time.

The current goal of LostTime is not to replace event management software, but to make tasks before and after an event easier. Customization on a per-club basis is expected.

# Usage

## Entries
**Input**: any number of .csv files representing entries  
**Output**: single .csv file ready for import into SportSoftware, or a PDF check-in list ready to print for the registration table.
For the input .csv files, if the header line contains any of the following strings, its data will be included in the output: `bib`, `first`, `last`, `club` or `school`, `class`, `sex` or `gen`, `punch` or `card`, `rent`, and `nc`. Checking is loose: a column titled `First Name` will match `first`. *(Special case, the word `emergency` does not match `gen` or `nc`.)*

## Event Results
**Input**: single IOF v3 .xml `<ResultList>` file  
**Output**: an html page, results by class, sorted, and scored. Can also include a second html page with team results 
Scoring methods include: Time (no score), Ratio to winner (1000pts), World Cup (100, 95, 92, 90, ...), or Alphabetical sorting (no placement).
Team scoring methods are added as requested. Currently there is one: WIOL (Washington Interscholastic Orienteering League) teams are the top three finishers from a school in a given class, except middle school where the girls and boys races are combined in a single Middle School Team class.

## Series Results
**Input**: existing event results uploaded to Lost Time Orienteering
**Output**: html page, series results by class, calculated and sorted.
Series can be configured to count the best N scores out of M races. Individuals must run in the same class, and are matched on name+club.

# Backlog
## Entries
- make the default output an IOF xml `<EntryList>` file, for greater inter-operability
## Series
- ability to add blank events to fill out remainder of a series
- better detect input file types (for example, Sport Software ScoreO .csv)


# Technical Notes
## Architecture
This is a Flask application with a SQLite backend. There is currently no front-end framework; data is passed to the Jinja2 template engine that comes bundled with Flask.

## Development and Testing
You'll need python 3.8+ and `virtualenvwrapper` installed on a linux machine (or windows subsystem for linux). I'm using WSL2 with Ubuntu 20.04:

1. Fork the project, then clone to a folder on your machine
   ```bash
   $ git clone https://github.com/<username>/LostTime.git <Path/To/Project/Folder>
   ```

2. Set up a python virtual environment with all dependencies. (The `-a` flag adds a virtual environment to an existing project directory; that's what we want to do.)
   ```bash
   $ mkvirtualenv losttime -a <ProjectFolder> -r requirements.txt
   ```

3. add an instance folder and instanceconfig.py Mine looks like this:
   ```python
   # instance/instanceconfig.py
    from os.path import abspath, dirname, join
    _cwd = dirname(abspath(__file__))

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + join(_cwd, 'dev.db') # puts the db in the instance folder
    SQLALCHEMY_ECHO = False
    SECRET_KEY = 'generate-a-secret-key-with-os.urandom(24)-and-paste-here'

    SEND_EMAILS = False # app will call unix sendmail program.
    FLASH_EMAILS = True # app will display emails in the UI as a flashed message.
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
python -m flask db migrate -m 'message'
# review the new migration script in migrations/versions, then
python -m flask db upgrade 
```

## Deployment

It's easy! Open an ssh client and `git pull` and then restart the daemon via `TERM` in the NFS GUI. 
If there are new libraries, make sure `requirements.txt` is updated and `pip install -r requirements.txt` before restarting.
You can upgrade to a new db schema with `python -m flask db upgrade`, though that line is also in the startup script so it's not necessary.


### Initial
First Deployment on a fresh nearlyfreespeech.net server. There was a lot of debugging. Here's what worked in the end.
1. clone the repository to the protected folder:
```bash
$ cd /home/protected
$ git clone https://github.com/ercjns/LostTime.git .
```
2. create the virtual environment, install dependencies.
```bash
$ virtualenv -p /usr/local/bin/python2 venv //prevent python3 from installing
$ source venv/bin/activate
$ pip install -r requirements.txt //removed wsgiref from the list, it was causing issues
```

3. create instance file
```bash
$ mkdir instance
$ touch instanceconfig.py
$ emacs instanceconfig.py
$ // type in instance config (see above)
$ // save with C-x C-s, exit with C-x C-c
```

4. initialize the databse
```bash
$ export FLASK_APP=losttime
$ python -m flask db update
```

5. test the startup script
```bash
$ source venv/bin/activate
$ gunicorn -p app.pid losttime:app
```
Well, actually, the gunicorn command was still reading from the global gunicorn, which caused it to use python 3 and miss my packages.
So the second line in the startup script is ```usr/local/bin/gunicorn ...```

6. configure the daemon with the startup script in the NFS UI.   

