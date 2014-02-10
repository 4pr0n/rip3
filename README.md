About
=====

A website that downloads content from other websites.

Getting Started
===============

API keys are stored in the database file 'database.db'

`sqlite3 database.db "insert or replace into config values ('gw_root', 'TBD')"`
`sqlite3 database.db "insert or replace into config values ('gw_api', 'TBD')"`
`sqlite3 database.db "insert or replace into config values ('tumblr_key', 'tumblr API key')"`
`sqlite3 database.db "insert or replace into config values ('twitter_key', 'base64_of_consumer_key+secret')"`
`sqlite3 database.db "insert or replace into config values ('flickr_creds', 'yahoo_username:password')"`


In order to check you have everything set up properly you can run `python py/StatusManager.py` in the main directory.

To test without a web server, run `python serve.py` this serves on port 7000.

