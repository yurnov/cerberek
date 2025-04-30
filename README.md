# Сerberek

The name of this Telegram antispam bot is inspired by the name of name of Cerberus from the Greek mythology. Can be also named Cerbuś.

This repository contains a Telegram bot configured to monitor a specific group chat. The bot reads all messages, checks for keywords, deletes messages containing those keywords, and bans the user who sent them.

Messages from the admin of the chat are unfiltered.

## Features

- Reads messages from a specific group chat
- Deletes messages containing keywords from a list
- Bans users who send messages with keywords
- Unfiltered messages from chat admins
- Configurable via environment variables
- Deployed using Docker

## Prerequisites

- Docker
- Telegram bot token
- Group chat ID

## Setup

1. Clone the repository:

```sh
git clone https://github.com/yurnov/cerberek.git
cd cerberek
```

2. Create a `.env` file with the following content:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GROUP_CHAT_ID=your_group_chat_id
```

3. Create a `keywords.yaml` with keywords:
```
keywords:
  - spam
  - scam
  - phishing
  - malware
  - virus
  - hack
  - fraud
  - fake
  - illegal
  - offensive
```

3. Build the Docker image:

```sh
docker build -t yurnov/cerberek .
```

4. Run the Docker container:

```sh
docker run --env-file .env -v ./keywords.yaml:/app/keywords.yaml yurnov/cerberek.git
```

## Local Development

1. Install dependencies:

```sh
pip pip wheel --no-deps .
pip install --no-cache-dir *

```

2. Run the bot:

```sh
python -m cerberek.main"
```

## TODO:

- Add configirable quarantine (i.e. set read-only for configurable period);
- Improve bot configuration;
- Move keyword list from the YAML file to some more proper location
- Improve CI part

## Contributing

Feel free to open issues or submit pull requests if you have any improvements or bug fixes.

## License

This project is licensed under the MIT License.

