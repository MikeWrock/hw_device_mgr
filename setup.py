from setuptools import setup
from setuptools.command.install import install
import subprocess
import os

package_name = "hw_device_mgr"

# Packages like hw_device_mgr.{pkg}.tests.bogus_devices
pkgs_bd = [
    "cia_301",
    "cia_402",
    "errors",
    "ethercat",
    "hal",
    "lcec",
    "mgr",
    "mgr_hal",
    "mgr_ros",
    "mgr_ros_hal",
]
# Packages like hw_device_mgr.{pkg}.tests
pkgs_t = [
    "devices",
    "logging",
    *pkgs_bd,
]
# Generate lists
packages = (
    [
        "hw_device_mgr",
        "hw_device_mgr.latency",
        "hw_device_mgr.tests",
        "hw_device_mgr.tests.bogus_devices",
    ]
    + [f"hw_device_mgr.{p}" for p in pkgs_t]
    + [f"hw_device_mgr.{p}.tests" for p in pkgs_t]
    + [f"hw_device_mgr.{p}.tests.bogus_devices" for p in pkgs_bd]
    + [
        "hw_device_mgr.devices.device_xml",
        "hw_device_mgr.devices.device_err",
    ]
)


class CustomInstall(install):
    def run(self):
        """Run halcompile on `multilatency.comp`."""
        if os.environ.get("ROS_VERSION", None) != "1":
            # ROS1 builds comp from CMakeFile
            comp_src = "hw_device_mgr/latency/multilatency.comp"
            subprocess.check_call(
                ["/usr/bin/env", "halcompile", "--install", comp_src]
            )
        super().run()


setup_kwargs = dict()
if os.environ.get("ROS_VERSION", None) != "1":
    # catkin doesn't support zip_safe or entry_points
    setup_kwargs["zip_safe"] = True
    entry_points = {
        "console_scripts": [
            "hw_device_mgr = hw_device_mgr.mgr_ros_hal.__main__:main",
            "ecat_pcap_decode = hw_device_mgr.latency.ecat_pcap_decode:main",
            "halsampler_decode = hw_device_mgr.latency.halsampler_decode:main",
        ]
    }

setup(
    name=package_name,
    version="0.2.0",
    packages=packages,
    data_files=[
        (
            "share/ament_index/resource_index/packages",
            ["resource/" + package_name],
        ),
        ("share/" + package_name, ["package.xml"]),
    ],
    package_data={
        "": [  # Within any package, install:
            # ESI files
            "*.xml",
            # Error descriptions
            "device_err/*.yaml",
            # Test configs
            "tests/*.yaml",
            "bogus_devices/*.yaml",
        ],
    },
    install_requires=["setuptools"],
    maintainer="John Morris",
    maintainer_email="john@zultron.com",
    description="Machinekit HAL interface to robot hardware and I/O",
    license="BSD",
    tests_require=["pytest"],
    cmdclass={"install": CustomInstall},
    **setup_kwargs,
)
