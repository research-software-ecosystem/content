#!/bin/sh
# wait until MySQL is really available
maxcounter=60
 
counter=1
while ! mysql --protocol TCP -u"elixir" -p"123" -e "show databases;" > /dev/null 2>&1; do
    sleep 1
    echo "Waiting for MySQL..."
    counter=`expr $counter + 1`
    if [ $counter -gt $maxcounter ]; then
        >&2 echo "We have been waiting for MySQL too long already; failing."
        exit 1
    fi;
done
echo "MySQL is ready"
