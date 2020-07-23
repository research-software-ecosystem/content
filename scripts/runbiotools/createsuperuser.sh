#!/bin/bash
echo "from django.contrib.auth.models import User; User.objects.create_superuser('uploadbot', 'uploadbot@example.com', 'botbotbot')" | python3 manage.py shell
