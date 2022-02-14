from ...mgr import SimHALHWDeviceMgr
from ....lcec.device import LCECSimDevice
from ....cia_402.device import CiA402SimDevice
from ....devices.tests.devices import (
    ElmoGold420,
    ElmoGold520,
    InovanceIS620N,
    InovanceSV660,
)


class HALHWMgrTestDevices(LCECSimDevice, CiA402SimDevice):
    category = "hal_hw_mgr_test_devices"


class HALHWMgrTestElmoGold420(HALHWMgrTestDevices, ElmoGold420):
    name = "elmo_gold_0x30924_0x10420_hal_hw_mgr_test"
    test_category = "elmo_gold_420_test"


class HALHWMgrTestElmoGold520(HALHWMgrTestDevices, ElmoGold520):
    name = "elmo_gold_0x30925_0x10420_hal_hw_mgr_test"
    test_category = "elmo_gold_520_test"


class HALHWMgrTestInovanceIS620N(HALHWMgrTestDevices, InovanceIS620N):
    name = "IS620N_ECAT_hal_hw_mgr_test"
    test_category = "inovance_sv660n_test"


class HALHWMgrTestInovanceSV660N(HALHWMgrTestDevices, InovanceSV660):
    name = "SV660_ECAT_hal_hw_mgr_test"
    test_category = "inovance_is620n_test"


class HALHWDeviceMgrForTest(SimHALHWDeviceMgr):
    data_type_class = HALHWMgrTestDevices.data_type_class
    device_base_class = HALHWMgrTestDevices
    device_classes = (
        HALHWMgrTestElmoGold420,
        HALHWMgrTestElmoGold520,
        HALHWMgrTestInovanceIS620N,
        HALHWMgrTestInovanceSV660N,
    )

    name = "hal_hw_device_mgr_for_test"
