#!/bin/bash
echo ping localhost
ping -c 1 localhost
echo netstat to see who is listening
netstat -tln
echo try to run mysql
mysql --debug=d:t:O,/tmp/client.trace -h localhost -P 3306 --protocol=tcp --user=elixir --password=123 elixir < /root/initial_db.sql
echo print debug trace
cat /tmp/client.trace
