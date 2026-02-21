import logging

from hypercorn.config import Config
from hypercorn.run import run

import nanapi.settings as settings
from nanapi.settings import FASTAPI_APP, HYPERCORN_CONFIG


def main():
    # disable low priority threshold for Anilist API calls
    settings.AL_LOW_PRIORITY_THRESH = 0

    config = Config()
    config.loglevel = settings.LOG_LEVEL
    config.accesslog = '-'
    config.errorlog = '-'
    config.application_path = FASTAPI_APP
    for k, v in HYPERCORN_CONFIG.items():
        setattr(config, k, v)

    run(config)


if __name__ == '__main__':
    main()
