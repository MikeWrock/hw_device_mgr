# Real devices under LCEC
from ..hal.device import HALPinDevice
from ..lcec.device import LCECDevice, LCECSimDevice
from ..cia_402.device import CiA402Device, CiA402SimDevice
from ..devices.elmo_gold import ElmoGold420, ElmoGold520
from ..devices.inovance_is620n import InovanceIS620N
from ..devices.inovance_sv660 import InovanceSV660
from ..devices.bogus import BogusServo


class ManagedDevices(LCECDevice, CiA402Device, HALPinDevice):
    category = "managed_lcec_devices"


class ElmoGold420LCEC(ElmoGold420, ManagedDevices):
    product_code = 0x20030924
    name = "elmo_gold_420_lcec"


class ElmoGold520LCEC(ElmoGold520, ManagedDevices):
    product_code = 0x20030925
    name = "elmo_gold_520_lcec"


class InovanceIS620NLCEC(InovanceIS620N, ManagedDevices):
    product_code = 0x200C0108
    name = "inovance_is620n_lcec"


class InovanceSV660LCEC(InovanceSV660, ManagedDevices):
    product_code = 0x200C010D
    name = "inovance_sv660n_lcec"


class SimManagedLCECDevices(LCECSimDevice, CiA402SimDevice, HALPinDevice):
    category = "sim_lcec_managed_devices"


class BogusServoSimLCEC(BogusServo, SimManagedLCECDevices):
    product_code = 0xB09050F2
    name = "bogus_servo_drive_sim_lcec"


class ElmoGold420SimLCEC(ElmoGold420, SimManagedLCECDevices):
    product_code = 0x30030924
    name = "elmo_gold_420_sim_lcec"


class ElmoGold520SimLCEC(ElmoGold520, SimManagedLCECDevices):
    product_code = 0x30030925
    name = "elmo_gold_520_sim_lcec"


class InovanceIS620NSimLCEC(InovanceIS620N, SimManagedLCECDevices):
    product_code = 0x300C0108
    name = "inovance_is620n_sim_lcec"


class InovanceSV660SimLCEC(InovanceSV660, SimManagedLCECDevices):
    product_code = 0x300C010D
    name = "inovance_sv660n_sim_lcec"
