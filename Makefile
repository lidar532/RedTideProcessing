habspec:
	nbdev_export --path nbs

test_data:
	nbdev_export --path nbs/test_data.ipynb

dev_install:
	pip install -e .
