from .base_test_class import BaseCiA402TestClass
from ...cia_301.tests.test_device import TestCiA301Device as _TestCiA301Device


class TestCiA402Device(BaseCiA402TestClass, _TestCiA301Device):

    expected_mro = [
        "BogusCiA402Device",
        *_TestCiA301Device.expected_mro,
    ]

    def read_update_write_conv_test_data(self):
        if not self.is_402_device:
            return
        uint16 = self.device_class.data_type_class.uint16
        for data in (self.test_data, self.ovr_data):
            for intf, intf_data in data.items():
                # Translate control_mode, e.g. MODE_CSP -> 8
                cm = intf_data.get("control_mode", None)
                if cm is not None and intf == "command_out":
                    cm = self.obj.control_mode_int(cm)
                    intf_data["control_mode"] = cm
                cmf = intf_data.get("control_mode_fb", None)
                if cmf is not None and intf in ("feedback_in", "sim_feedback"):
                    cmf = self.obj.control_mode_int(cmf)
                    intf_data["control_mode_fb"] = cmf

                # Format status_word, control_word for readability, e.g. 0x000F
                for key in ("status_word", "control_word"):
                    if key in intf_data:
                        intf_data[key] = uint16(intf_data[key])

    def test_read_update_write(self, obj, fpath):
        if hasattr(obj, "MODE_CSP"):
            # CiA 402 device
            self.read_update_write_yaml = self.read_update_write_402_yaml
            self.is_402_device = True
        else:
            self.is_402_device = False
        super().test_read_update_write(obj, fpath)
