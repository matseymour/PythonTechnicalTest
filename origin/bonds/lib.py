import logging

import requests
from rest_framework.exceptions import APIException


logger = logging.getLogger(__name__)


class HTTP504Error(APIException):
    status_code = 504


def catchUpstreamIssues(func):
    """A decorator intended for use with the requests lib """

    def wrapper(*args, **kwargs):

        try:
            response = func(*args, **kwargs)
            if not str(response.status_code).startswith('2'):
                logger.error(
                    f'Status code {response.status_code} for upstream request ({func.__name__})'
                )
                raise APIException()
            return response
        except requests.ReadTimeout:
            logger.error(f'ReadTimeout for upstream request ({func.__name__})')
            raise HTTP504Error()
        except Exception:
            logger.exception(f'Unhandled exception for upstream request ({func.__name__})')
            raise APIException()

    return wrapper


class GleifClient:
    """
    Can be used to retrieve information from the remote GLEIF API
    """

    _BASE = 'https://leilookup.gleif.org/api/v2/'

    def __init__(self, timeout=60):
        """
        :param timeout: Read timeout for API response, in seconds
        """
        self._timeout = timeout  # Seconds to read timeout

    @catchUpstreamIssues
    def _leiLookup(self, lei):
        return requests.get(f'{self._BASE}leirecords?lei={lei}', timeout=self._timeout)

    def getLegalName(self, lei):
        # requests lib will decode bytes
        results = self._leiLookup(lei).json()
        try:
            assert len(results) == 1
            # Could do some validation here to check the legal name conforms to some
            # spec, but I'll consider it out of scope
            return results.pop()['Entity']['LegalName']['$'].replace(' ', '')

        except (AssertionError, KeyError):
            logger.error(f'Could not parse legal name from upstream response: {results}')
            raise APIException()
