import abc
from importlib.resources import path as imp_path
from .logging import Logging
from .interface import Interface
from .data_types import DataType


class Device(abc.ABC):
    """Base device class for both device categories and device models."""

    category = "all"  # Device category sets up registry for models
    name = None  # Concrete device model subclasses must define

    logger = Logging.getLogger(__name__)

    data_type_class = DataType

    feedback_in_data_types = dict()
    feedback_out_data_types = dict()
    command_in_data_types = dict()
    command_out_data_types = dict()

    feedback_in_defaults = dict()
    feedback_out_defaults = dict(goal_reached=True, goal_reason="Reached")
    command_in_defaults = dict()
    command_out_defaults = dict()

    interface_names = {
        "feedback_in",
        "feedback_out",
        "command_in",
        "command_out",
    }

    def __init__(self, address=None):
        self.address = address
        self.init_interfaces()

    def init(self, index=None):
        """
        Initialize device.

        Subclasses may implement `init()` for extra initialization
        outside the constructor.  Implementations should always call
        `super().init()`.
        """
        self.index = index

    @classmethod
    def merge_dict_attrs(cls, attr):
        """
        Merge `dict` attributes across class hierarchy.

        Scan through class and parent classes for `attr`, a `dict`, and
        return merged `dict`.
        """
        res = dict()
        for c in cls.__mro__:
            c_attr = c.__dict__.get(attr, dict())
            # Overlap not allowed
            assert not (set(res.keys()) & set(c_attr.keys()))
            res.update(c_attr)
        return res

    def init_interfaces(self):
        intfs = self._interfaces = dict()
        dt_name2cls = self.data_type_class.by_shared_name
        for name in self.interface_names:
            defaults = self.merge_dict_attrs(f"{name}_defaults")
            for k, v in defaults.items():
                if isinstance(v, dict):
                    defaults[k] = v.copy()
            dt_names = self.merge_dict_attrs(f"{name}_data_types")
            data_types = {k: dt_name2cls(v) for k, v in dt_names.items()}
            intfs[name] = Interface(name, defaults, data_types)

    def interface(self, name):
        return self._interfaces[name]

    def __getattr__(self, name):
        """Provide attributes for each interface."""
        if name not in self._interfaces:
            cname = self.__class__.__name__
            raise AttributeError(f"'{cname}' object has no attribute '{name}'")
        return self._interfaces[name]

    def set_interface(self, what, **kwargs):
        self._interfaces[what].set(**kwargs)

    def update_interface(self, what, **kwargs):
        self._interfaces[what].update(**kwargs)

    def interface_changed(self, what, key, return_vals=False):
        return self._interfaces[what].changed(key, return_vals=return_vals)

    def read(self):
        """Read `feedback_in` from hardware interface."""

    def get_feedback(self):
        """Process `feedback_in` and return `feedback_out` interface."""
        fb_in = self._interfaces["feedback_in"].get()
        self._interfaces["feedback_out"].set(**fb_in)
        return self._interfaces["feedback_out"]

    def set_command(self, **kwargs):
        """Process `command_in` and return `command_out` interface."""
        self._interfaces["command_in"].set(**kwargs)
        self._interfaces["command_out"].set()  # Set defaults
        return self._interfaces["command_out"]

    def write(self):
        """Write `command_out` to hardware interface."""

    def log_status(self):
        pass

    @classmethod
    def pkg_path(cls, path):
        """Return `pathlib.Path` object for this package's directory."""
        # Find cls's module & package
        pkg = ".".join(cls.__module__.split(".")[:-1])
        with imp_path(pkg, path) as p:
            return p

    def __str__(self):
        return f"<{self.name}@{self.address}>"

    def __repr__(self):
        return self.__str__()

    ########################################
    # Device category and model registries

    # Top-level registry for device category classes
    _category_registry = dict()

    # Allow reregistering devices or not
    allow_rereg = False

    def __init_subclass__(cls, /, **kwargs):  # noqa:  E225
        # Add device type implementations to applicable registries
        cls._register_model()

    @classmethod
    def device_model_id(cls):
        """
        Return unique device model identifier.

        A unique ID that may be generated from bus scan results by which
        a detected device's model class may be looked up, e.g.
        `(manufacturer_id, model)`.
        """
        if not hasattr(cls, "model_id"):
            return None
        return cls.data_type_class.uint32(cls.model_id)

    # Record class registrations; for debugging registry
    _registry_log = list()

    # { category : { model_id : device_class } }
    _model_id_registry = dict()

    # { category : { model_name : device_class } }
    _model_name_registry = dict()

    @classmethod
    def _register_model(cls):
        # Register model in all parent categories
        if not cls.name:
            # Not a concrete device; skip
            cls._registry_log.append(("no_name", cls))
            return  # Not a model
        model_id = cls.device_model_id()
        registered = False
        for supercls in cls.category_classes():
            category = supercls.category
            # Ensure category is registered
            cls._category_registry.setdefault(category, supercls)
            # Check & register device id
            reg = cls._model_id_registry.setdefault(category, dict())
            # Be sure model is registered in at least one category, but don't
            # clobber earlier registrations
            assert model_id not in reg or registered
            if model_id not in reg:
                registered = True
                reg[model_id] = cls
            # Register device name
            reg = cls._model_name_registry.setdefault(category, dict())
            assert cls.name not in reg, f"{cls.name} in {category} registry"
            reg[cls.name] = cls
            cls._registry_log.append(
                ("cat", cls.name, model_id, category, cls, supercls)
            )

    @classmethod
    def category_classes(cls, model_cls=None):
        if model_cls is None:
            model_cls = cls
        return [c for c in model_cls.__mro__ if "category" in c.__dict__]

    @classmethod
    def category_cls(cls, category=None):
        return cls._category_registry.get(category or cls.category, None)

    @classmethod
    def get_model(cls, model_id=None):
        category = cls.category
        assert (
            category in cls._model_id_registry
        ), f"{category} not in {cls._model_id_registry}"
        model_registry = cls._model_id_registry[category]
        if model_id is None:  # Return set of all model classes
            return set(model_registry.values())
        if model_id not in model_registry:
            return None
        return model_registry[model_id]

    @classmethod
    def get_model_by_name(cls, name):
        category = cls.category
        assert category in cls._model_name_registry
        model_registry = cls._model_name_registry[category]
        assert name in model_registry, f"{name} not in {model_registry}"
        return model_registry[name]

    ########################################
    # Device identifier registry and instance factory

    # keys: device identifiers; values:  device objects
    _address_registry = dict()

    @classmethod
    def get_device(cls, address=None, **kwargs):
        registry = cls._address_registry.setdefault(cls.name, dict())
        if address in registry:
            return registry[address]
        device_obj = cls(address=address, **kwargs)
        registry[address] = device_obj
        return device_obj

    @classmethod
    def clear_devices(cls):
        """Clear out device instance registry (for tests)."""
        cls._address_registry.clear()

    @classmethod
    @abc.abstractmethod
    def scan_devices(cls):
        """
        Scan attached devices and return a list of objects.

        Typically each device on a bus is scanned for its device type
        key and its device ID.  The type key is used by `get_model(key)`
        to obtain the device class, and the device ID is used by
        `get_device_obj(address)` to obtain the device instance.
        """


class SimDevice(Device):

    sim_feedback_data_types = dict()
    sim_feedback_defaults = dict()

    interface_names = {
        "sim_feedback",
    }

    _sim_device_data = dict()

    @classmethod
    def sim_device_data_class(cls, sim_device_data):
        return cls.get_model(sim_device_data["model_id"])

    @classmethod
    def sim_device_data_address(cls, sim_device_data):
        return sim_device_data["position"]

    @classmethod
    def init_sim(cls, *, sim_device_data):
        """Massage device test data for usability."""
        cls_sim_data = cls._sim_device_data[cls.category] = dict()

        for dev in sim_device_data:
            device_cls = cls.sim_device_data_class(dev)

            # Set sparse keys
            updates = dict(
                model_id=device_cls.device_model_id(),
                name=device_cls.name,
                address=cls.sim_device_data_address(dev),
            )
            cls_sim_data[dev["model_id"]] = {**dev, **updates}

        assert cls_sim_data

    @classmethod
    def scan_devices(cls, **kwargs):
        res = list()
        cls_sim_data = cls._sim_device_data[cls.category]
        for data in cls_sim_data.values():
            dev_type = cls.get_model(data["model_id"])
            dev = dev_type.get_device(address=data["address"], **kwargs)
            res.append(dev)
        return res


    def read(self):
        """Read `feedback_in` from hardware interface."""
        super().read()
        sfb = self._interfaces["sim_feedback"].get()
        self._interfaces["feedback_in"].set(**sfb)

    def set_sim_feedback(self):
        """Simulate feedback from command and feedback."""
        sfb = self._interfaces["sim_feedback"]
        sfb.set()
        return sfb

    def write(self):
        """Write `command_out` to hardware interface."""
        super().write()
        self.set_sim_feedback()
