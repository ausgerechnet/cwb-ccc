.PHONY: build dist

install:
	python3 -m venv venv && \
	. venv/bin/activate && \
	pip3 install -U pip setuptools wheel twine && \
	pip3 install -r requirements.txt && \
	pip3 install -r requirements-dev.txt

lint:
	. venv/bin/activate && \
	pylint --rcfile=.pylintrc ccc/*.py
test:
	. venv/bin/activate && \
	pytest -m "not benchmark"
benchmark:
	. venv/bin/activate && \
	pytest -m benchmark
coverage:
	. venv/bin/activate && \
	pytest --cov-report term-missing -v --cov=ccc/

compile:
	. venv/bin/activate && \
	cython -2 ccc/cl.pyx
build:
	. venv/bin/activate && \
	python3 setup.py build_ext --inplace
sdist:
	. venv/bin/activate && \
	python3 setup.py sdist
deploy:
	. venv/bin/activate && \
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
