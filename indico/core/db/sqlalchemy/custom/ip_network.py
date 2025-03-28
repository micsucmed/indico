# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import ipaddress

from sqlalchemy import TypeDecorator
from sqlalchemy.dialects.postgresql import CIDR


class _AlwaysSortableMixin:
    def __lt__(self, other):
        if self._version != other._version:
            return self._version < other._version
        else:
            return super().__lt__(other)


class IPv4Network(_AlwaysSortableMixin, ipaddress.IPv4Network):
    pass


class IPv6Network(_AlwaysSortableMixin, ipaddress.IPv6Network):
    pass


def _ip_network(address, strict=True):
    # based on `ipaddress.ip_network` but returns always-sortable classes
    # since sqlalchemy needs to be able to sort all values of a type
    address = str(address)
    try:
        return IPv4Network(address, strict)
    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError):
        pass

    try:
        return IPv6Network(address, strict)
    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError):
        pass

    raise ValueError(f'{address!r} does not appear to be an IPv4 or IPv6 network')


class PyIPNetwork(TypeDecorator):
    """Custom type which handles values from a PEP-3144 ip network."""

    impl = CIDR
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return str(_ip_network(value)) if value is not None else None

    def process_result_value(self, value, dialect):
        return _ip_network(value) if value is not None else None

    def coerce_set_value(self, value):
        return _ip_network(value) if value is not None else None

    def alembic_render_type(self, autogen_context, toplevel_code):
        autogen_context.imports.add('from indico.core.db.sqlalchemy import PyIPNetwork')
        return f'{type(self).__name__}()'
