from ...mgr import SimROSHWDeviceMgr
from ....mgr.tests.bogus_devices.mgr import BogusHWDeviceMgr
from ....ethercat.tests.bogus_devices.device_402 import (
    BogusEtherCAT402Device,
    BogusEtherCAT402Servo,
    BogusOtherCAT402Servo,
)


class BogusROSHWDeviceMgr(SimROSHWDeviceMgr, BogusHWDeviceMgr):
    data_type_class = BogusEtherCAT402Device.data_type_class
    device_base_class = BogusEtherCAT402Device
    device_classes = (BogusEtherCAT402Servo, BogusOtherCAT402Servo)

    name = "bogus_ros_hw_device_mgr"
