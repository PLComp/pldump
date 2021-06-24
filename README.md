# pldump

A script extracting posts from the PLComp channel into a single Markdown-compatible file.

# Setup

The script is configured through a single file - `plcomp.ini`. A template config file is
provided in `plcomp.ini.tmpl`. As the script accesses the Telegram API, credentials are
required. Make use of the `requirements.txt` listing all the dependencies.

Copy the template file into `plcomp.ini`. Open the new config file and replace `api_id`
and `api_hash` with app-specific values provided by Telegram
(<https://my.telegram.org/apps>). Upon the first run data specific to a Telegram user
running will be requested.

The script dumps all the data received to `stdout`.
