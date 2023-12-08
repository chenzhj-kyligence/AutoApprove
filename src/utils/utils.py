class ParserApprovals(list):

    def __init__(self, approval_list):
        self.approval_list = approval_list
        self.approval_info = None
        self._init()

    def _init(self):
        for approver in self.approval_list.keys():
            for instance_id in self.approval_list[approver].keys():
                self.approval_info = self.approval_list[approver][instance_id]
                self.append({'approver': approver, 'approve_id': instance_id, 'target_location': self.get_target_location,
                             'user_type': self.get_user_type, 'date_interval': self.get_date_interval,
                             'proposers': self.get_proposer_list
                             })

    @property
    def get_target_location(self):
        return self._get_value('目标主机位置')

    @property
    def get_user_type(self):
        return self._get_value('用户类型')

    @property
    def get_date_interval(self):
        return self._get_value('DateInterval')

    @property
    def get_proposer_list(self):
        return self._get_value('申请人')

    def _get_value(self, key):
        for item in self.approval_info:
            if item['name'] == key:
                return item['value']
        return None