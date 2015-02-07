deps: pager node_modules iced
	# yui css compress needs java
	which java > /dev/null

pager: venv venv/lib/python2.7/sitecustomize.py
	venv/bin/python setup.py develop

venv/lib/python2.7/sitecustomize.py:
	echo "import sys; sys.setdefaultencoding('utf-8')" >\
	venv/lib/python2.7/sitecustomize.py
	
venv:
	virtualenv venv

node_modules:
	npm install

clean_webassets:
	rm -rf pager/static/built pager/static/.webassets-cache

iced:
	echo 'await setTimeout defer(), 0' | node_modules/.bin/iced -sp -I window > pager/static/vendor/iced-coffee-script-runtime.js

upgrade:
	PAGER_CONFIG=Production venv/bin/alembic upgrade head

build: pull deps upgrade
	PAGER_CONFIG=Production ./app.py assets build

start: build
	PYTHONIOENCODING=UTF-8 PAGER_CONFIG=Production venv/bin/gunicorn \
	--worker-class socketio.sgunicorn.GeventSocketIOWorker \
	-p gunicorn.pid --log-file gunicorn.log -D pager:app --proxy-protocol

reload: build celery_restart
	kill -HUP `cat gunicorn.pid`

stop:
	kill `cat gunicorn.pid`

pull:
	git pull

celery_start:
	venv/bin/celery multi start mail -c 1 -E -l WARNING -A pager.tasks

celery_stop:
	venv/bin/celery multi stop mail -c 1 -E -l WARNING -A pager.tasks

celery_restart:
	venv/bin/celery multi restart mail -c 1 -E -l WARNING -A pager.tasks

pager.zip: crx/manifest.json crx/icon_128.png
	(cd crx && zip ../pager.zip manifest.json icon_128.png)

.PHONY: pager node_modules iced upgrade build pull celery_start celery_stop celery_restart
