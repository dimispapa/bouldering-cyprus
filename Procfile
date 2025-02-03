release: python manage.py collectstatic --noinput --clear
web: gunicorn bouldering_cy.wsgi:application