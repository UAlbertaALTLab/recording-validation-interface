# recording-validation-interface

Maskwacîs recordings validation interface.


Install
-------

Requires Python 3.6.

Then, create a virtualenv (if applicable), and install the requirements:

```
pip install -r requirements.txt
```

Consult `system-requirements.txt` for other system dependencies you may require.


Running
-------

```
export FLASK_APP=app.py
flask run --host HOST
```

Replace `HOST` with `127.0.0.1` (listen only locally) when running in debug mode.

Replace `HOST` with `0.0.0.0` (listen to all devices) when running in
production mode.


Testing
-------

Ensure you have a server [running] on port 5000. Then,

```
./run-tests
```

This will type-check the Python code with mypy and run the Selenium
integration tests.


License
-------

2018 © University of Alberta/Eddie Antonio Santos. All rights reserved.
