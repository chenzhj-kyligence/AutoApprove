import configparser
from base import FeishuInstance
from base import JumpServerInstance
from utils.utils import ParserApprovals


def approval_results(feishu_app_id, feishu_app_secret, approvers, days):
    """
    :param feishu_app_id: str, feishu app id
    :param feishu_app_secret: str, feishu app secret
    :param approvers: list, who approve the approval, user email
    :param days: int, get approved list within days
    :return: dict
    """
    feishu_client = FeishuInstance(feishu_app_id, feishu_app_secret)
    handler = feishu_client.get_user_info(approvers)
    handler.get_approved_list(days=days)
    approved_list = handler.output
    return ParserApprovals(approved_list)


if __name__ == '__main__':
    config_handler = configparser.ConfigParser()
    config_handler.read('./config.ini')
    feishu_app_id = config_handler.get('feishu', 'APP_ID')
    feishu_app_secret = config_handler.get('feishu', 'APP_SECRET')
    approvers = [item.strip() for item in config_handler.get('feishu', 'APPROVERS').split(',')]

    approval_info = approval_results(feishu_app_id, feishu_app_secret, approvers, days=6)

    print(approval_info)

    jps_key_id = config_handler.get('jumpserver', 'JPS_KEY_ID')
    jps_secret_id = config_handler.get('jumpserver', 'JPS_SECRET_ID')
    jps = JumpServerInstance(jps_key_id, jps_secret_id)
    jps.get_user_info()
    jps.get_server_list()
    jps.get_user_rules('demo')
    out = jps.set_new_rule_name('zhongjun.chen')
    print(out)
