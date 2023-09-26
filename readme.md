# Bulk URL Indexer

This script can help you to submit URLs in bulk to the Google Indexing API. The API is free to use and you can use this tool to manage URLs, track the daily quota, and log submissions and errors.

## Prerequisites

I use pipenv to manage my virtual environments. If you don't have it, you can find info on how to install it [here](https://pipenv.pypa.io/en/latest/installation/).

If you are using a different virtual environment manager, you can use the `requirements.txt` file to install the dependencies:

```
pip install -r requirements.txt
```

**Important**: Ensure you have the Google Service Account credentials and save them as `credentials.json` in the project directory.

## Usage

If you're using pipenv, enter a shell in the virtual environment:

```
pipenv shell
```

If you are using a different virtual environment manager, activate the virtual environment however you normally would.

### 1. Adding URLs

To add URLs to the queue, run the following command:

```
python indexing.py load urls.txt
```

Make sure the text file contains one URL per line and exists in the project directory.

*Note*: This action will also clear the file after loading its URLs.

### 2. Indexing URLs

To submit URLs to the Indexing API, run the following command:

```
python indexing.py index
```

This will submit URLs to the Indexing API until the daily quota is reached. If the quota is reached, the script will stop and the remaining URLs will be saved for the next day.

## Database Overview

This script uses an SQLite database to manage:

- **URLs**: Track each URL, its indexed status, and submission details.
- **Quota**: Daily counter of submitted URLs.
- **Logs**: Detailed logs for every URL submission, ensuring you always know what's happening.

## To Do

To make this script better, I'd like to add the following features:

- Ability to use more GCP projects and multiple service accounts to increase the daily quota.
- Add option to check the index status of URLs before submitting them.
- Get sitemaps from Search Console and use them to generate a list of URLs to submit.

## Contributing

If you have any suggestions or ideas for improving this to make the internal linking suggestions more accurate, you can fork this repo and submit a pull request. I would love to hear your ideas!