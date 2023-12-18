#!/bin/bash
cd /var/www/sara
source webserver/bin/activate
cd webserver
gunicorn -w 4 -b 127.0.0.1:8080 app:app --timeout 600

