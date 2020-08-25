![metricity banner](https://media.discordapp.net/attachments/563594791770914816/747917686998040657/metricity_banner.png)

Metricity is an application for the Python Discord server which collects advanced metrics on the usage of the server.

Metricity only provides the collection of metrics, a service such as Grafana should be used to generate visualisations of the data.

### Setup

You will need [Poetry](https://python-poetry.org) to setup and run Metricity. There is a Docker image available which has a working poetry installation.

There are two environment variables, `BOT_TOKEN` and `DATABASE_URI`. These should be set to the Discord developer token and postgres database URI respectively. You can also alter these configuration values by copying `config-default.toml` to `config.toml` and altering the values, this file should not be comitted to git, it is your personal configuration.

To apply database migrations run `poetry run alembic upgrade head`.

To run the application use `poetry run start`.

If you alter the models then use `poetry run alembic revision -m "<What you changed>" --autogenerate` to generate a migration. **Make sure to check the changes generated are correct**.

### Join us on Discord!

If you are a Python programmer and want to meet fellow Pythonistas, come join us at <https://discord.gg/python>! 
