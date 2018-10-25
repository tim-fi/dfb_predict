# DFB match predictions

## assignment
We were tasked with creating a "_simple_" application to make predictions
for the next/any given DFB match.
The assignment was broken up into 3 parts for us:

1. data acquisition
    * gather the data required for this task
2. data processing
    * actually make the predictions using 2 different algorithms
3. data visualisation
    * present the data/results in a UI (_no cheezy excel export sadly..._)


## option assessment
As a first step we have to assess our options for each part of the project,
for this purpose I have collected multiple options for each major part.
All the library choices are related to our language of choice for this project: [python3](https://www.python.org/).

### meta-project stuff
1. env managment
    * [virtualenv](https://virtualenv.pypa.io/en/stable/)
    * [pipenv](https://github.com/pypa/pipenv)
2. IDE/editor
    * [pycharm](https://www.jetbrains.com/pycharm/)
    * [vscode](https://code.visualstudio.com/)
    * [mu](https://codewith.mu/)
    * [sublime text](https://www.sublimetext.com/3)
3. test automation
    * [tox](https://tox.readthedocs.io/en/latest/)
    * [pytest](https://docs.pytest.org/en/latest/)
    * some system in gitlab?
4. linters (*not necessarily mutually exclusive*)
    * [flake8](https://gitlab.com/pycqa/flake8) ([docs](http://flake8.pycqa.org/en/latest/))
    * [pylint](https://www.pylint.org/)
    * [pydocstyle](https://github.com/PyCQA/pydocstyle/tree/2.1.1)
    * [mypy](http://www.mypy-lang.org/)

### acquisition
1. published dataset
    * [university of Bayreuth](https://dbup2date.uni-bayreuth.de/bundesliga.html)
2. scrape the net
    * [fussballdaten.de](https://www.fussballdaten.de/)
    * [rand.de](https://www.ran.de/)
    * [bulibox.de](http://www.bulibox.de/index.html)
    * [liga-statistik.de](https://www.liga-statistik.de/)
    * [statista.com](https://de.statista.com/themen/63/bundesliga/)
3. open api:
    * [openligadb.de](https://www.openligadb.de/) ([docs](https://github.com/OpenLigaDB/OpenLigaDB-Samples))

### storage
1. db
    * [sqlalchemy](https://www.sqlalchemy.org/)
2. file based
    * [csv](https://en.wikipedia.org/wiki/Comma-separated_values)
    * [json](https://json.org/)
    * [xml](https://en.wikipedia.org/wiki/XML)
    * [pickle](https://docs.python.org/3.7/library/pickle.html) (+ [dill](https://github.com/uqfoundation/dill))

### processing
1. neural networks
    * not to sure what types would be applicable for this problem
2. stochastics
    * [Monte Carlo algorithm](https://en.wikipedia.org/wiki/Monte_Carlo_algorithm)
    * [Atlantic City algorithm](https://en.wikipedia.org/wiki/Atlantic_City_algorithm)
    * [Las Vegas algorithm](https://en.wikipedia.org/wiki/Las_Vegas_algorithm)
    * [Poisson regression model](https://dashee87.github.io/football/python/predicting-football-results-with-statistical-modelling/)
    * [Dixon-Coles model](https://dashee87.github.io/football/python/predicting-football-results-with-statistical-modelling-dixon-coles-and-time-weighting/)
	* [True Skill]()

### visualisation
1. native ui
    * [tkinter](https://docs.python.org/3/library/tkinter.html) (+ [ttk](https://docs.python.org/3/library/tkinter.ttk.html))
    * [appJar](http://appjar.info/)
    * [pyglet](https://bitbucket.org/pyglet/pyglet/wiki/Home)
    * [qt](http://pythonqt.sourceforge.net/)
2. browser based
    * [django](https://www.djangoproject.com/)
    * [flask](http://flask.pocoo.org/)
    * [reahl](https://www.reahl.org/)

### final choices
1. __meta-project stuff__:
    * __env management__: [pipenv](https://github.com/pypa/pipenv)
    * __IDE/editor__: ...
    * __test automation__: [pytest](https://docs.pytest.org/en/latest/)
    * __linters__
        * [flake8](https://gitlab.com/pycqa/flake8) ([docs](http://flake8.pycqa.org/en/latest/))
        * [pydocstyle](https://github.com/PyCQA/pydocstyle/tree/2.1.1)
        * [mypy](http://www.mypy-lang.org/)
2. __acqusition__: open api _via_ [openligadb.de](https://www.openligadb.de/) ([docs](https://github.com/OpenLigaDB/OpenLigaDB-Samples))
3. __storage__: database _via_ [sqlalchemy](https://www.sqlalchemy.org/)
4. __processing__:
    * __algorithm 1__: [Poisson regression model](https://github.com/dashee87/blogScripts/blob/master/Jupyter/2018-09-13-predicting-football-results-with-statistical-modelling-dixon-coles-and-time-weighting.ipynb)
    * __algorithm 2__: ...
5. __visualisation__: native ui _via_ [tkinter](https://docs.python.org/3/library/tkinter.html) (+ [ttk](https://docs.python.org/3/library/tkinter.ttk.html))

## proposed planing
As a start, in my opinion, it would very nice to split this whole
project up into 4 epics:

1. aquisition
2. storage
3. processing
4. visualisation

Additionally it might be a good idea to start out simple and just create
tickets as needed. But later on, when we get a grip on the project, we
should have meeting to write all of the tickets needed.

For each step we would extend a cli, to make testing and commandline use
possible before we have a UI ready.