# BCollector

- Download files from a http, https or sftp server into your local infrastructure.
- Copy or decrypt files to destination directory.
- Keep backup in the download folder for a given period of time, delete obsolete files.
- Works as daemon / in an andless loop.

## Requirements
Python 3.12 works fine. Newer versions should be no problem.

In addition to the standard libraries python-gnupg and paramiko are required:

```
python -m pip install python-gnupg paramiko
```
In case your download machine is offline, download the libraries on an online system:

```
python -m pip download python-gnupg paramiko
```
Transport the .whl files to the offline machine and execute:
```
python -m pip install --no-index --find-links .\ python-gnupg paramiko
```

## Configuration
Bcollector reads the configuration from one file. As configparser is used, INI file syntax is used. The default is
`bcollector.conf` in the directory of `bcollector.py`.

### Example:
```
[REMOTE]
# remote location (url) to sync to
#url = https://localhost/
url = http://localhost:8080/
#url = sftp://localhost/
#password for sftp
#password = dummy
# regular expression to select targetted files
match = *
#match = .*\.gpg
#match = ^[^.].*
# timout connection attempt in seconds
timeout = 30
# maximumretries on bad download attempts
retries = 10
# delay in seconds after bad download attempt
delay = 2
# for encrypted files (pgp/gpg with synmmetric password is implemented), none to disable decryption
encryption = pgp
#encryption = none
# passphrase to decrypt
passphrase = dummy

[LOCAL]
# download directory (used to sync/check for new files)
download = /home/neo/Public/test_download
# destination directory to copy files to, decrypt on the way if set
destination = /home/neo/Public/test_destination
# log file
logfile = /home/neo/Public/test_log.txt
# max. size of log file in MiB
logsize = 32
# database to track files
db = /home/neo/Public/test-sqlite.db
# set yes to delay forwarding until destination directory does not exist
wait = yes
# trigger file name to write into destination directory
trigger = /home/neo/Public/test_trigger.txt
# minutes to keep files in download directory
keep_files = 1
# minutes to keep entries in data base
keep_entries = 2

[LOOP]
# enable endless loop with yes
enable = no
# hours of the day (every = every hour)
# hours = 0, 3, 9, 12, 15, 18, 21
hours = every
# minutes of the hour when to start download attempt (every = every minute)
#minutes = 8,18,28,38,48,58
minutes = every
```

## Legal Notice

### License
Respect GPL-3: https://www.gnu.org/licenses/gpl-3.0.en.html

### Disclaimer
Use the software on your own risk.

This is not a commercial product with an army of developers and a department for quality control behind it.


