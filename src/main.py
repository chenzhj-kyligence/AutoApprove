import configparser
from base import FeishuInstance
from base import JumpServerInstance


def approval_results(feishu_app_id, feishu_app_secret, approvers):
    """
    :param feishu_app_id: str, feishu app id
    :param feishu_app_secret: str, feishu app secret
    :param approvers: list, who approve the approval
    :return: dict
    """
    results = {}
    feishu_client = FeishuInstance(feishu_app_id, feishu_app_secret)
    for approver in approvers:
        resp = feishu_client.get_approval_details(approver=approver, days=2)
        if resp:
            results.update(resp)
    return results


if __name__ == '__main__':
    config_handler = configparser.ConfigParser()
    config_handler.read('./config.ini')
    feishu_app_id = config_handler.get('feishu', 'APP_ID')
    feishu_app_secret = config_handler.get('feishu', 'APP_SECRET')
    approvers = [item.strip() for item in config_handler.get('feishu', 'APPROVERS').split(',')]

    approval_info = approval_results(feishu_app_id, feishu_app_secret, approvers)

    jps_key_id = config_handler.get('jumpserver', 'JPS_KEY_ID')
    jps_secret_id = config_handler.get('jumpserver', 'JPS_SECRET_ID')
    jps = JumpServerInstance(jps_key_id, jps_secret_id)
