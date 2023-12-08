import requests
import json
import datetime
import time
from httpsig.requests_auth import HTTPSignatureAuth
from httpclient import BasicHttpClient


# All approved approvals in a day
approval_dict = {}


class FeishuInstance:
    """
    1. 通过审批人的用户信息，得到该审批人审批列表。
    2. 通过审批列表里的信息，获取服务器信息，申请人信息
    3. 返回 审批人的邮箱对应的审批信息，如{'zhongjun.chen@kyligence.io': {'审批实例1': {审批信息}, '审批实例2': {审批信息}}, ...}
    """
    _base_url = 'https://open.feishu.cn/open-apis'
    _userinfo = {}
    # 审批人id
    _userids = []
    _userid_2_email = {}

    def __init__(self, app_id, app_secret):
        self.output = {}
        self.app_id = app_id
        self.app_secret = app_secret
        self.sess = requests.Session()
        self.headers = {
          'Content-Type': 'application/json'
        }
        self.private_headers = self.headers.copy()
        self.private_headers['Authorization'] = f"Bearer {self.tenant_access_token}"

    def _request(self, method, url, **kwargs):
        inner_kwargs = kwargs
        to_json = inner_kwargs.get('to_json', True)
        if 'to_json' in inner_kwargs.keys():
            inner_kwargs.pop('to_json')
        resp = self.sess.request(method, self._base_url + url, **inner_kwargs)
        if to_json:
            return resp.json()['data']
        else:
            return resp

    def _get_approval_list(self, user_id, start_time, end_time):
        """
        :param user_id: who approves the approvals
        :param start_time: start time
        :param end_time: end time
        :return: list, each approval is a dict, all approvals approved by approver in current time duration
        """

        url = "/approval/v4/tasks/search?page_size=100&user_id_type=user_id"

        payload = json.dumps({
            "locale": "zh-CN",
            "order": 2,
            "task_start_time_from": start_time,
            "task_start_time_to": end_time,
            "task_status": "APPROVED",
            "task_status_list": [
                "APPROVED"
            ],
            "user_id": user_id
        })

        response = self._request("POST", url, headers=self.private_headers, data=payload)
        try:
            return response['task_list']
        except KeyError:
            return []

    def get_approval_instance_ids(self, user_id, days=1):
        """
        :param user_id: str, who approved these approvals
        :param days: int, approval within days
        :return: list, approvals list
        """
        approval_instance_ids = []
        end_time = int(time.time() * 1000)
        start_time = end_time - 24 * 3600 * days * 1000

        resp = self._get_approval_list(user_id, start_time, end_time)
        try:
            for item in resp:
                if item['approval']['name'] == '堡垒机权限申请':
                    approval_instance_ids.append(item['instance']['code'])
        except KeyError:
            print("No approvals found.")
        return approval_instance_ids

    def get_approval_details(self, user_id, days=2):
        """

        :param user_id: str, who request this approval
        :param days: int, approved approvals in days
        :return: dict, {user_mail1: [approve_form1, approve_form2...], user_mail2: [1,2,3] }
        """
        try:
            instance_ids = self.get_approval_instance_ids(user_id, days=days)
            for instance_id in instance_ids:
                url = f"/approval/v4/instances/{instance_id}"
                resp = self._request("GET", url, headers=self.private_headers)
                proposer_user_ids = self._get_initiator(user_id, instance_id)
                proposer_email_list = self.get_user_email_list_by_user_id(proposer_user_ids)
                user_mail = self._userid_2_email[user_id]
                if user_mail not in self.output:
                    self.output[user_mail] = {}
                self.output[user_mail][instance_id] = json.loads(resp['form'])
                self.output[user_mail][instance_id].append({"name": "申请人", "value": proposer_email_list})
        except Exception as e:
            print('exceptions: ', e)

    def _get_initiator(self, approver_id, instance_id):
        """

        :param approver_id: 审批人id
        :param instance_id: 当前审批的单子序列号
        :return:
        """
        url = f"/approval/v4/tasks/query?page_size=100&topic=2&user_id={approver_id}&user_id_type=user_id"
        resp = self._request('GET', url, headers=self.private_headers)
        try:
            for item in resp['tasks']:
                if item['process_code'] == instance_id:
                    return item['initiators']
        except Exception:
            return []

    def _get_user_info_by_email(self, emails):
        """
        :param emails: list, user email list
        :return:
        """
        url = '/contact/v3/users/batch_get_id?user_id_type=open_id'
        payload = json.dumps({
          "emails": emails
        })
        resp = self._request('POST', url, data=payload, headers=self.private_headers)

        return resp['user_list']

    def _get_user_info_by_user_id(self, user_id):
        url = f"/contact/v3/users/{user_id}?department_id_type=open_department_id&user_id_type=user_id"
        resp = self._request("GET", url, headers=self.private_headers)
        return resp['user']

    def get_user_email_by_user_id(self, user_id):
        resp = self._get_user_info_by_user_id(user_id)
        return resp['email']

    def get_user_email_list_by_user_id(self, user_ids):
        result = []
        for user_id in user_ids:
            result.append(self.get_user_email_by_user_id(user_id))
        return result

    def get_user_ou_ids(self, emails):
        """

        :param emails: list, user email list
        :return: list
        """
        ids = []
        user_infos = self._get_user_info_by_email(emails)
        for user_info in user_infos:
            if 'user_id' in user_info:
                ids.append(user_info['user_id'])
        return ids

    def get_user_info(self, emails):
        """

        :param emails: user email list
        :return:
        """
        ou_ids = self.get_user_ou_ids(emails)
        for ou_id in ou_ids:
            url = f"/contact/v3/users/{ou_id}?department_id_type=open_department_id&user_id_type=open_id"
            resp = self._request("GET", url, headers=self.private_headers)
            if resp['user']['email'] not in self._userinfo:
                self._userinfo[resp['user']['email']] = {}
            self._userinfo[resp['user']['email']]['user_id'] = resp['user']['user_id']
            self._userinfo[resp['user']['email']]['open_id'] = resp['user']['open_id']
            self._userinfo[resp['user']['email']]['mobile'] = resp['user']['mobile']
            self._userids.append(resp['user']['user_id'])
            self._userid_2_email[resp['user']['user_id']] = resp['user']['email']
        return self

    def get_approved_list(self, days=3):
        for user_id in self._userids:
            self.get_approval_details(user_id=user_id, days=days)
        return self

    @property
    def tenant_access_token(self):
        url = "/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        response = self._request("POST", url, to_json=False, headers=self.headers, params=payload)
        return json.loads(response.text)['tenant_access_token']


class JumpServerInstance(BasicHttpClient):

    _region = {
        "azure": {"超级用户": "root", "普通用户": "azureuser"},
        "aws": {"超级用户": "root", "普通用户": 'ec2-user'}
    }

    _base_url = "https://jumpserver-ofs.kyligence.com/api/v1"
    user_info = []
    server_info = []

    def __init__(self, key_id, secret_id):
        super().__init__()
        self.key_id = key_id
        self.secret_id = secret_id
        self.headers = {
            'Accept': 'application/json',
            'X-JMS-ORG': '00000000-0000-0000-0000-000000000002',
            'Date': datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        }
        self.signature_auth(self.get_auth)
        self.get_server_list()
        self.get_user_info()

    def _request(self, method, url, **kwargs):  # pylint: disable=arguments-differ, method-hidden
        return json.loads(super()._request(method, self._base_url + url, to_json=False, **kwargs))

    @property
    def get_auth(self):
        signature_headers = ['(request-target)', 'accept', 'date']
        auth = HTTPSignatureAuth(key_id=self.key_id, secret=self.secret_id, algorithm='hmac-sha256', headers=signature_headers)
        return auth

    def get_user_info(self):
        url = '/users/users/'
        results = self._request('GET', url=url, headers=self.headers)
        for item in results:
            self.user_info.append({'id': item['id'], 'name': item['name'], 'username': item['username'], 'email': item['email']})

    def get_server_list(self):
        url = '/assets/nodes/'
        self.server_info = self._request('GET', url=url, headers=self.headers)

    def get_user_rules(self, user_name):
        url = f"/perms/asset-permissions/?asset=&node=&search={user_name}"
        resp = self._request('GET', url=url, headers=self.headers)
        return resp

    def delete_user_rules(self, rule_list):
        """

        :param rule_list:
        :return:
        """
        if len(rule_list) != 0:
            url = '/perms/asset-permissions/{rule_id}'
            for item in rule_list:
                if not item['is_active']:
                    rule_id = item['id']
                    resp = self._request('DELETE', url=url.format(rule_id), headers=self.headers)
                    print(f"Delete rule: {item['name']}, id: {item['id']}")

    def set_new_rule_name(self, user_name):
        exist_rules = self.get_user_rules(user_name)
        # delete in-active rules
        self.delete_user_rules(exist_rules)

        exist_rules_active = self.get_user_rules(user_name)
        if len(exist_rules_active) == 0:
            print(f"Current user {user_name} has no active rule.")
            return f"{user_name}-ssh-rule"

        rule_names = [item['name'] for item in exist_rules_active]
        temp = max(rule_names).split('-')
        if len(temp) == 3:
            return f"{user_name}-ssh-rule-1"
        else:
            number = int(temp[-1]) + 1
            return f"{user_name}-ssh-rule-{number}"

    def create_new_rule(self, proposer_detail):
        """

        :param proposer_detail:
        :return:
        """
        url = "/perms/asset-permissions/"

        proposer = proposer_detail['proposers'][0]
        rule_name = self.set_new_rule_name(proposer.split('@')[0])
        server_id = self.get_server_id(proposer_detail['target_location'])
        user_id = self.get_user_id(proposer)
        user_type = proposer_detail['user_type']
        start_time = proposer_detail['date_interval']['start']
        end_time = proposer_detail['date_interval']['end']

        params = {
          "assets": [
            server_id
          ],
          "nodes": [],
          "accounts": [
            "@SPEC",
            "ec2-user"
          ],
          "actions": [
            "connect",
            "upload",
            "download",
            "copy",
            "paste",
            "delete"
          ],
          "is_active": True,
          "date_start": start_time.split('+')[0],
          "date_expired": end_time.split('+')[0],
          "name": rule_name,
          "users": [
            {
              "pk": user_id
            }
          ]
        }

        self._request('POST', data=params, headers=self.headers)

    def _set_user_(self, location, user_type):
        pass

    def get_server_id(self, server_name):
        for server in self.server_info:
            if server_name in server['name']:
                return server['id']

    def get_user_id(self, user_email):
        for user in self.user_info:
            if user['email'] == user_email:
                return user['id']

    def get_user_servers_list(self, user):
        url = f'/perms/users/{user}/assets/'
        return self._request('GET', url, headers=self.headers)

    def get_assets_list(self):
        # url = '/perms/asset-permissions/'
        url = '/assets/assets'
        resp = self._request('GET', url, headers=self.headers)
        return resp

    def get_user_authentication(self, server_name):
        pass


