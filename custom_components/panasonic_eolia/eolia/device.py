class Appliance:
    def __init__(self, appliance_id=None, nickname=None, purchase_date=None,
                 shop_category_id=None, shop_area_id=None, shop_name=None,
                 inst_place_id=None, memo=None, appliance_type=None,
                 product_code=None, product_name=None, hashed_guid=None,
                 device_register_num=None, initialize_flg=None, repair_status=None,
                 point_code=None, vpa_enable=None):
        self.appliance_id = appliance_id
        self.nickname = nickname
        self.purchase_date = purchase_date
        self.shop_category_id = shop_category_id
        self.shop_area_id = shop_area_id
        self.shop_name = shop_name
        self.inst_place_id = inst_place_id
        self.memo = memo
        self.appliance_type = appliance_type
        self.product_code = product_code
        self.product_name = product_name
        self.hashed_guid = hashed_guid
        self.device_register_num = device_register_num
        self.initialize_flg = initialize_flg
        self.repair_status = repair_status
        self.point_code = point_code
        self.vpa_enable = vpa_enable

    @classmethod
    def from_dict(cls, data):
        return cls(
            appliance_id=data.get('appliance_id'),
            nickname=data.get('nickname'),
            purchase_date=data.get('purchase_date'),
            shop_category_id=data.get('shop_category_id'),
            shop_area_id=data.get('shop_area_id'),
            shop_name=data.get('shop_name'),
            inst_place_id=data.get('inst_place_id'),
            memo=data.get('memo'),
            appliance_type=data.get('appliance_type'),
            product_code=data.get('product_code'),
            product_name=data.get('product_name'),
            hashed_guid=data.get('hashed_guid'),
            device_register_num=data.get('device_register_num'),
            initialize_flg=data.get('initialize_flg'),
            repair_status=data.get('repair_status'),
            point_code=data.get('point_code'),
            vpa_enable=data.get('vpa_enable')
        )

    def to_dict(self):
        return {
            'appliance_id': self.appliance_id,
            'nickname': self.nickname,
            'purchase_date': self.purchase_date,
            'shop_category_id': self.shop_category_id,
            'shop_area_id': self.shop_area_id,
            'shop_name': self.shop_name,
            'inst_place_id': self.inst_place_id,
            'memo': self.memo,
            'appliance_type': self.appliance_type,
            'product_code': self.product_code,
            'product_name': self.product_name,
            'hashed_guid': self.hashed_guid,
            'device_register_num': self.device_register_num,
            'initialize_flg': self.initialize_flg,
            'repair_status': self.repair_status,
            'point_code': self.point_code,
            'vpa_enable': self.vpa_enable
        }
