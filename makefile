install:
	pipenv install --dev
test:
	pipenv run pytest -v
coverage:
	pipenv run pytest --cov-report term-missing -v --cov=ccc/
build:
	pip3 install --upgrade setuptools wheel
	python3 setup.py sdist bdist_wheel
clean:
	rm -rf *.egg-info build/
deploy:
	python3 -m twine upload dist/*
clear_cache:
	/bin/rm -r /tmp/ccc-anycache/
	rm tests/data-dir
