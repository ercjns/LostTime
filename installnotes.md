# Notes

### Werkzeug error
```
  File "/root/.pyenvs/ltrebuild/lib/python3.8/site-packages/flask_uploads.py", line 26, in <module>
    from werkzeug import secure_filename, FileStorage
ImportError: cannot import name 'secure_filename' from 'werkzeug' (/root/.pyenvs/ltrebuild/lib/python3.8/site-packages/werkzeug/__init__.py)
```
used second answer here, downgrade package: https://stackoverflow.com/questions/61628503/flask-uploads-importerror-cannot-import-name-secure-filename

so Werkzeug is frozen at 0.16.0 and must not be updated to 1.x

### WeasyPrint / Libcairo error
```
  File "/root/.pyenvs/ltrebuild/lib/python3.8/site-packages/weasyprint/__init__.py", line 469, in <module>
    from .css import preprocess_stylesheet  # noqa isort:skip
  File "/root/.pyenvs/ltrebuild/lib/python3.8/site-packages/weasyprint/css/__init__.py", line 27, in <module>
    from . import computed_values, counters, media_queries
  File "/root/.pyenvs/ltrebuild/lib/python3.8/site-packages/weasyprint/css/computed_values.py", line 15, in <module>
    from .. import text
  File "/root/.pyenvs/ltrebuild/lib/python3.8/site-packages/weasyprint/text.py", line 11, in <module>
    import cairocffi as cairo
  File "/root/.pyenvs/ltrebuild/lib/python3.8/site-packages/cairocffi/__init__.py", line 48, in <module>
    cairo = dlopen(
  File "/root/.pyenvs/ltrebuild/lib/python3.8/site-packages/cairocffi/__init__.py", line 45, in dlopen
    raise OSError(error_message)  # pragma: no cover
OSError: no library called "cairo" was found
no library called "libcairo-2" was found
cannot load library 'libcairo.so.2': libcairo.so.2: cannot open shared object file: No such file or directory
cannot load library 'libcairo.2.dylib': libcairo.2.dylib: cannot open shared object file: No such file or directory
cannot load library 'libcairo-2.dll': libcairo-2.dll: cannot open shared object file: No such file or directory
```

following instructions on weasyprint install at https://weasyprint.readthedocs.io/en/stable/install.html#linux

apt install libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info

after installing the above os packages, it worked.




