.PHONY: build dist

install:
	pipenv install --dev
lint:
	pipenv run pylint --rcfile=.pylintrc ccc/*.py
test:
	pipenv run pytest -m "not benchmark"
benchmark:
	pipenv run pytest -m benchmark
coverage:
	pipenv run pytest --cov-report term-missing -v --cov=ccc/

compile:
	pipenv run cython -2 ccc/cl.pyx
build:
	pipenv run python3 setup.py build_ext --inplace
sdist:
	pip3 install --upgrade setuptools
	python3 setup.py sdist
deploy:
	python3 -m twine upload dist/*

clean: clean_build clean_compile clean_cache clean_dist

clean_compile:
	rm -rf ccc/*.so
clean_build:
	rm -rf *.egg-info build/
clean_cache:
	rm -rf tests/data-dir
clean_dist:
	rm -rf dist/

docker:
	docker build -t cwb-ccc -f Dockerfile .
