import logging
from metrics import vault


def status():
    try:
        vault.create_client()
    except Exception as e:
        logging.error(f'Error while creating Vault client: {str(e)}')
        return 'NOK', 500
    else:
        return 'OK', 200
