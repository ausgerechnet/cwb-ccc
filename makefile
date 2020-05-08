install:
	pipenv install --dev
test:
	pipenv run pytest -v
coverage:
	pipenv run pytest --cov-report term-missing -v --cov=ccc/
build:
	pipenv run python3 setup.py sdist bdist_wheel
	pipenv run python3 -m twine upload dist/*
clean:
	rm -rf *.egg-info build/ association_measures/*.so association_measures/*.c dist/
