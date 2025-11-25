# BCollector

- Download files from a http, https or sftp server into your local infrastructure.
- Copy or decrypt files to destination directory.
- Keep backup in the download folder for a given period of time, delete obsolete files.
- Works as daemon / in an andless loop.

## Requirements
Python 3.12 works fine. Newer versions should be no problem.

In addition to the CPython standard libraries python-gnupg and paramiko are required:

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
# url to sync with: http://host[:port]/..., https://host[:port]/... or sftp://user@host[:port]/...
#url = http://localhost:8080/
url = sftp://user@localhost/
#password for sftp
password = dummy
# regular expression to select targetted files
match = .*\.gpg
#match = ^[^.].*
# timout connection attempt in seconds
timeout = 30
# maximumretries on bad download attempts
retries = 10
# delay in seconds after bad download attempt
delay = 2
# for encrypted files (pgp/gpg with synmmetric password is implemented), none to disable decryption
encryption = pgp
# passphrase to decrypt
passphrase = dummy

[LOCAL]
# download directory (used to sync/check for new files)
download = /home/neo/Public/download
# destination directory to copy files to, decrypt on the way if set
destination = /home/neo/Public/destination
# log file
logfile = /home/neo/Public/log.txt
# max. size of log file in MiB
logsize = 16

[LOOP]
# hours of the day (every = every hour)
hours = every
# minutes of the hour when to start download attempt (every = every minute)
#minutes = 8,18,28,38,48,58
minutes = every
# seconds that main loop is paused inbetween download attempts
delay = 10
# hour of the day to clean download directory
clean = 23
# months to keep files in download directory, 0 not to purge download directory
keep = 3
```

## Legal Notice

### License
Respect GPL-3: https://www.gnu.org/licenses/gpl-3.0.en.html

### Disclaimer
Use the software on your own risk.

This is not a commercial product with an army of developers and a department for quality control behind it.


