import logging
import curlify
import requests


class BasicHttpClient:

    _headers = {}

    _auth = ''

    def token(self, token):
        self._headers['Authorization'] = f'Basic {token}'

    def auth(self, username, password):
        self._auth = (username, password)

    def signature_auth(self, signature_auth_key):
        self._auth = signature_auth_key

    def headers(self, headers):
        self._headers = headers

    def _request(self, method, url, params=None, data=None, json=None,
                 files=None, headers=None, stream=False, to_json=True,
                 timeout=120, origin_data=False):

        with requests.Session() as session:
            session.auth = self._auth
            return self._request_with_session(session, method, url,
                                              params=params,
                                              data=data,
                                              json=json,
                                              files=files,
                                              headers=headers,
                                              stream=stream,
                                              to_json=to_json,
                                              timeout=timeout,
                                              origin_data=origin_data)

    def _request_with_session(self, session, method, url, params=None, data=None,
                              json=None, files=None, headers=None, stream=False, to_json=True,
                              timeout=120, origin_data=False):
        if headers is None:
            headers = self._headers

        try:
            resp = session.request(method, url,
                                   params=params,
                                   data=data,
                                   json=json,
                                   timeout=timeout,
                                   files=files,
                                   headers=headers,
                                   stream=stream
                                   )
        except Exception as error:
            request = requests.Request(method, url, headers, data=data, json=json)
            logging.error(str(error))
            logging.error(curlify.to_curl(session.prepare_request(request)))
            raise error

        try:
            if stream:
                return resp.raw

            if not resp.content:
                return None

            if to_json:
                data = resp.json()
                resp.raise_for_status()
                if origin_data:
                    return data
                return data.get('data', data)

            return resp.text
        except requests.HTTPError as http_error:
            err_msg = f"{str(http_error)} [return code: {data.get('code', '')}]-[{data.get('msg', '')}]\n" \
                      f"{data.get('stacktrace', '')}"
            logging.error(err_msg)
            raise requests.HTTPError(err_msg, request=http_error.request, response=http_error.response, )
        except Exception as error:
            logging.error(str(error))
            raise error

