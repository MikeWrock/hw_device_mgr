from .data_types import CiA301DataType
from .command import CiA301Command, CiA301SimCommand
from .sdo import CiA301SDO


class CiA301Config:
    """
    CiA 301 device configuration interface.

    This class presents a high-level configuration interface to
    CiA 301 devices.  The class can scan the bus for devices and
    their models & positions.  Class instances correspond to a single
    device, and can initialize device parameter values from a
    configuration at init, and can upload and download SDO values
    during operation.

    It uses a low-level `CiA301Command` interface to scan the bus and
    upload/download object dictionary values, and presents a
    high-level interface for manipulating devices.

    This abstract class must be subclassed and `command_class` defined
    in order to read/write dictionary objects from/to devices.
    """

    data_type_class = CiA301DataType
    command_class = CiA301Command
    sdo_class = CiA301SDO

    # Mapping of model_id to a dict of (index, subindex) to SDO object
    _model_sdos = dict()

    def __init__(self, address=None, model_id=None):
        self.address = address
        self.model_id = self.format_model_id(model_id)
        self._config = None

    @classmethod
    def format_model_id(cls, model_id):
        assert None not in model_id
        return tuple(cls.data_type_class.uint32(i) for i in model_id)

    @property
    def vendor_id(self):
        return self.model_id[0]

    @property
    def product_code(self):
        return self.model_id[1]

    @property
    def bus(self):
        return self.address[0]

    @property
    def position(self):
        return self.address[1]

    @classmethod
    def command(cls):
        if not hasattr(cls, "_command_objs"):
            cls._command_objs = dict()
        if cls.__name__ not in cls._command_objs:
            cls._command_objs[cls.__name__] = cls.command_class()
        return cls._command_objs[cls.__name__]

    def __repr__(self):
        cname = self.__class__.__name__
        return f"<{cname} addr {self.address} model {self.model_id}>"

    #
    # Object dictionary
    #

    @classmethod
    def add_device_sdos(cls, sdo_data):
        """Add device model object dictionary descriptions."""
        # print("CiA301Config:  add_device_sdos")
        # print("sdo_data.keys():", list(sdo_data.keys()))
        # print("sdo_data:", sdo_data)
        for model_id, sdos in sdo_data.items():
            sdos_new = dict()
            for ix, sd in sdos.items():
                # print("ix:", ix)
                # print("sd:", sd)
                ix = cls.sdo_ix(ix)
                if ix in sdos_new:
                    raise KeyError(f"Duplicate SDO index {ix}")
                if isinstance(sd, cls.sdo_class):
                    sdos_new[ix] = sd
                else:
                    sdos_new[ix] = cls.sdo_class(**sd)
            # print("cia_301 config model_id:", model_id)
            # print("cia_301 config sdos_new:", sdos_new)
            # assert model_id not in cls._model_sdos
            # if (model_id[1] & 0xff00) != 0x1000:  # IO
            #     assert sdos_new
            # print(f"Adding {model_id} to cls._model_sdos")
            cls._model_sdos[model_id] = sdos_new
        # print("_model_sdos.keys():", list(cls._model_sdos.keys()))
        # print("leaving CiA301Config:  add_device_sdos")

    @classmethod
    def sdo_ix(cls, ix):
        if isinstance(ix, str):
            ix = cls.sdo_class.parse_idx_str(ix)
        elif isinstance(ix, int):
            ix = (ix, 0)
        dtc = cls.data_type_class
        ix = (dtc.uint16(ix[0]), dtc.uint8(ix[1]))
        return ix

    def sdo(self, ix):
        if isinstance(ix, self.sdo_class):
            return ix
        ix = self.sdo_ix(ix)
        # print("model_id:", self.model_id)
        # print("_model_sdos[model_id]:", self._model_sdos[self.model_id])
        return self._model_sdos[self.model_id][ix]

    #
    # Param read/write
    #

    def upload(self, sdo):
        # Get SDO object
        sdo = self.sdo(sdo)
        res_raw = self.command().upload(
            address=self.address,
            index=sdo.index,
            subindex=sdo.subindex,
            datatype=sdo.data_type,
        )
        # print("sdo:", repr(sdo))
        # print("sdo.data_type:", repr(sdo.data_type))
        return sdo.data_type(res_raw)

    def download(self, sdo, val, dry_run=False):
        # Get SDO object
        sdo = self.sdo(sdo)
        # Check before setting value to avoid unnecessary NVRAM writes
        res_raw = self.command().upload(
            address=self.address,
            index=sdo.index,
            subindex=sdo.subindex,
            datatype=sdo.data_type,
        )
        if sdo.data_type(res_raw) == val:
            return  # SDO value already correct
        if dry_run:
            self.logger.info(f"Dry run:  download {val} to {sdo}")
            return
        self.command().download(
            address=self.address,
            index=sdo.index,
            subindex=sdo.subindex,
            value=val,
            datatype=sdo.data_type,
        )

    #
    # Device configuration
    #

    _device_config = list()

    @classmethod
    def set_device_config(cls, config):
        """
        Set the device configuration.

        `config` is a `list` of configurations in a `dict`.

        Each configuration matches a specific device model at any
        among a set of specific bus positions; keys for matching a
        device:

        - `vendor_id`, `product_code`:  `int` values for matching device
          model
        - `bus`:  Bus `int` value
        - `positions`:  `list` of matching `int` positions on bus

        Each configuration provides these keys:

        - `sync_manager`:  `dict` of synchronization manager `int` IDs
          to configuration data:
          - `dir`:  `str`, `out` or `in`; all SM types
          - `pdo_mapping`:  PDO mapping SM types only; `dict`:
            - `index`:  Index of PDO mapping object
            - `entries`:  Dictionary objects to be mapped;  `dict`:
              - `index`:  Index of dictionary object
              - `subindex`:  Subindex of dictionary object (default 0)
              - `name`:  Name, a handle for the data object
              - `bits`:  Instead of `name`, break out individual bits,
                 names specified by a `list`

        - `param_values`:  `dict` of `<idx>-<subidx>h`-format object
          dictionary keys to values; values may be a single scalar
          applied to all `positions`, or a `list` of scalars applied
          to corresponding entries in `positions`
        """
        assert config
        cls._device_config.clear()
        cls._device_config.extend(config)

    def munge_config(self, config_raw):
        # Flatten out param_values key
        pv = dict()
        for ix, val in config_raw.get("param_values", dict()).items():
            ix = self.sdo_class.parse_idx_str(ix)
            if isinstance(val, list):
                pos_ix = config_raw["positions"].index(self.position)
                val = val[pos_ix]
            pv[ix] = val
        dtc = self.data_type_class
        config_raw["vendor_id"] = dtc.uint32(config_raw["vendor_id"])
        config_raw["product_code"] = dtc.uint32(config_raw["product_code"])
        # Return pruned config dict
        return dict(sync_manager=config_raw["sync_manager"], param_values=pv)

    @property
    def config(self):
        if self._config is None:
            # Find matching config
            # print("self._device_config", self._device_config)
            # print("self.model_id", self.model_id)
            for conf in self._device_config:
                # print("conf:", conf)
                if "vendor_id" not in conf:
                    continue  # In tests only
                if self.model_id != (conf["vendor_id"], conf["product_code"]):
                    continue
                if self.bus != conf["bus"]:
                    continue
                if self.position not in conf["positions"]:
                    # print(
                    #     f"position {self.position} not in {conf['positions']}"
                    # )
                    continue
                break
            else:
                # print("self._device_config", self._device_config)
                # print("self.model_id", self.model_id)
                raise KeyError(f"No config for device at {self.address}")
            # Prune & cache config
            self._config = self.munge_config(conf)

        # Return cached config
        return self._config

    def write_config_param_values(self):
        for sdo, value in self.config["param_values"].items():
            self.download(sdo, value)

    #
    # Scan bus device config factory
    #

    @classmethod
    def scan_bus(cls, bus=0, **kwargs):
        """Return a `list` of configuration objects for each device."""
        res = list()
        for address, model_id in cls.command().scan_bus(bus=bus, **kwargs):
            model_id = cls.format_model_id(model_id)
            config = cls(address=address, model_id=model_id, **kwargs)
            res.append(config)
        return res


class CiA301SimConfig(CiA301Config):
    """CiA 301 device with simulated command."""

    command_class = CiA301SimCommand

    @classmethod
    def init_sim(cls, device_data=None):
        assert device_data
        # print("CiA301SimConfig init_sim")
        # print("device_data:", device_data)
        sdo_data = dict()
        # print("_model_sdos:", cls._model_sdos)
        for address, data in device_data.items():
            # print(data)
            # print("cls._model_sdos", cls._model_sdos)
            sdo_data[address] = cls._model_sdos[data["model_id"]]
        cls.command_class.init_sim(device_data=device_data, sdo_data=sdo_data)
