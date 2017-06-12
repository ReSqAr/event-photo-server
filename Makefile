clean:
	rm -f tmp.db db.sqlite3
	rm -rf wphotos/migrations

setup: clean
	python3 manage.py migrate --run-syncdb
	python3 manage.py migrate --run-syncdb
	echo "from django.contrib.auth.models import User; User.objects.create_superuser('yasin', '', 'abc123abc')" | python3 manage.py shell
	echo "from django.contrib.auth.models import User; User.objects.create_superuser('yvonne', '', 'abc123abc')" | python3 manage.py shell

run:
	python3 manage.py runserver

release:
	python3 manage.py migrate --run-syncdb
	python3 manage.py migrate --run-syncdb
	python3 manage.py collectstatic
