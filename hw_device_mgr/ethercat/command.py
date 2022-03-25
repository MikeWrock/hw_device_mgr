from ..cia_301.command import (
    CiA301Command,
    CiA301SimCommand,
    CiA301CommandException,
)
from .data_types import EtherCATDataType


class EtherCATCommandException(CiA301CommandException):
    pass


class EtherCATCommand(CiA301Command):
    data_type_class = EtherCATDataType


class EtherCATSimCommand(EtherCATCommand, CiA301SimCommand):
    pass
