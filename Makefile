.PHONY: test ship

run:
	python air_quality_index/__init__.py

test:
	flake8 ./
	coverage run test.py
	coverage report -m


ship:
	rm -rf build/
	rm -rf dist/
	python setup.py sdist bdist_wheel
	twine upload dist/* --skip-existing
