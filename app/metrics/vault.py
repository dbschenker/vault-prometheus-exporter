import hvac
from hvac import Client
from hvac.api.auth_methods import Kubernetes
from prometheus_client import Gauge
from datetime import datetime
import os
from pathlib import Path
import logging
from cryptography import x509
from cryptography.hazmat.backends import default_backend


VAULT_ADDR = os.environ.get('VAULT_ADDR')
VAULT_ROLE = os.environ.get('VAULT_ROLE')
VAULT_MOUNT_POINT = os.environ.get('VAULT_MOUNT_POINT')
VAULT_SA_TOKEN = '/var/run/secrets/kubernetes.io/serviceaccount/token'
VAULT_USER_TOKEN = f'{str(Path.home())}/.vault-token'


certificate_expiry = Gauge('vault_issuer_validity_seconds',
                           'Issuer expires in seconds',
                           ['engine', 'issuer', 'url'])


def create_client():
    """
    Creates a Vault client using either a VAULT_TOKEN environment
    variable, user VAULT_USER_TOKEN or Kubernetes service account token.

    :return: A Vault client instance.
    """
    if os.environ.get('VAULT_TOKEN') is not None:
        client = Client(url=VAULT_ADDR, token=os.environ.get('VAULT_TOKEN'))
    elif os.path.isfile(VAULT_USER_TOKEN):
        with open(VAULT_USER_TOKEN, 'r') as f:
            client = Client(url=VAULT_ADDR, token=f.read())
    elif os.path.isfile(VAULT_SA_TOKEN):
        with open(VAULT_SA_TOKEN, 'r') as f:
            client = Client(url=VAULT_ADDR)
            Kubernetes(client.adapter).login(role=VAULT_ROLE, jwt=f.read(),
                                             mount_point=VAULT_MOUNT_POINT)
    else:
        raise Exception('VaultClientConfigError')

    client.is_authenticated()

    return client


def get_certificate_validity(crt):
    """
    Calculates the remaining validity of a certificate in seconds.

    This function takes a certificate in PEM format, calculates its validity
    period, and then compares it with the current time to determine the
    remaining validity.

    :param crt: The certificate in PEM format.
    :return: The remaining validity of the certificate in seconds. This value
             can be positive (if the certificate is still valid) or negative
             (if the certificate has already expired).
    """
    certificate = x509.load_pem_x509_certificate(crt.encode(),
                                                 default_backend())
    validity = certificate.not_valid_after_utc.timestamp()
    current_timestamp = datetime.now().timestamp()
    remaining_validity = validity - current_timestamp
    return remaining_validity


def update_metrics():
    """
    Updates Prometheus metrics with the validity of PKI issuers.

    This function lists all PKI secrets engines, retrieves the issuers
    for each, calculates their remaining validity, and updates the Prometheus
    gauge accordingly.
    """
    try:
        client = create_client()
    except Exception as e:
        logging.error(f'Error while creating Vault client: {str(e)}')
        return

    response = client.sys.list_mounted_secrets_engines()

    if 'data' in response:
        secrets_engines_list = []
        for engine in response['data'].keys():
            if response['data'][engine]['type'] == 'pki':
                secrets_engines_list.append(engine)
        logging.info(f'List of Engines: {secrets_engines_list}')
    else:
        logging.warn('No data found in the response.')
        return

    for engine in secrets_engines_list:
        try:
            issuers = client.secrets.pki.list_issuers(mount_point=engine)
        except hvac.exceptions.InvalidPath:
            logging.warn(f'Invalid path for issuers in {engine}.')
            continue

        issuers = issuers['data'].get('keys', []) if 'data' in issuers else []
        for issuer in issuers:
            details = client.secrets.pki.read_issuer(issuer,
                                                     mount_point=engine)

            if 'data' in details and 'certificate' in details['data']:
                certificate = details['data']['certificate']
                validity = get_certificate_validity(certificate)

                certificate_expiry.labels(engine=engine,
                                          issuer=issuer,
                                          url=VAULT_ADDR).set(validity)
