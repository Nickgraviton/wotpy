#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# SPDX-License-Identifier: MIT

"""
Helper functions for Modbus entities and function code mapping.
"""

import struct

from wotpy.protocols.modbus.enums import (
    ModbusDataType,
    ModbusEntity,
    ModbusFunction,
    ModbusFunctionName,
)


_FUNCTION_NAME_MAP = {
    ModbusFunctionName.READ_COIL: ModbusFunction.READ_COIL,
    ModbusFunctionName.READ_DISCRETE_INPUT: ModbusFunction.READ_DISCRETE_INPUT,
    ModbusFunctionName.READ_HOLDING_REGISTERS: ModbusFunction.READ_HOLDING_REGISTERS,
    ModbusFunctionName.READ_INPUT_REGISTERS: ModbusFunction.READ_INPUT_REGISTERS,
    ModbusFunctionName.WRITE_SINGLE_COIL: ModbusFunction.WRITE_SINGLE_COIL,
    ModbusFunctionName.WRITE_SINGLE_HOLDING_REGISTER: ModbusFunction.WRITE_SINGLE_HOLDING_REGISTER,
    ModbusFunctionName.WRITE_MULTIPLE_COILS: ModbusFunction.WRITE_MULTIPLE_COILS,
    ModbusFunctionName.WRITE_MULTIPLE_HOLDING_REGISTERS: ModbusFunction.WRITE_MULTIPLE_HOLDING_REGISTERS,
    ModbusFunctionName.READ_DEVICE_IDENTIFICATION: ModbusFunction.READ_DEVICE_IDENTIFICATION,
}


def normalize_modbus_function(value):
    """Returns the integer function code for a numeric or named value."""

    if value is None:
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, str):
        if value in _FUNCTION_NAME_MAP:
            return _FUNCTION_NAME_MAP[value]

        for enum_name in ModbusFunctionName.list():
            if enum_name.lower() == value.lower():
                return _FUNCTION_NAME_MAP[enum_name]

    raise ValueError("Unknown Modbus function: {}".format(value))


def modbus_function_to_entity(modbus_fun):
    modbus_fun = normalize_modbus_function(modbus_fun)

    if modbus_fun in (ModbusFunction.READ_COIL,
                      ModbusFunction.WRITE_SINGLE_COIL,
                      ModbusFunction.WRITE_MULTIPLE_COILS):
        return ModbusEntity.COIL

    if modbus_fun == ModbusFunction.READ_DISCRETE_INPUT:
        return ModbusEntity.DISCRETE_INPUT

    if modbus_fun == ModbusFunction.READ_INPUT_REGISTERS:
        return ModbusEntity.INPUT_REGISTER

    if modbus_fun in (ModbusFunction.READ_HOLDING_REGISTERS,
                      ModbusFunction.WRITE_SINGLE_HOLDING_REGISTER,
                      ModbusFunction.WRITE_MULTIPLE_HOLDING_REGISTERS):
        return ModbusEntity.HOLDING_REGISTER

    raise ValueError("Cannot convert {} to Modbus entity".format(modbus_fun))


_TYPE_STRUCT_FORMAT = {
    ModbusDataType.BOOLEAN: "?",
    ModbusDataType.BYTE: "b",
    ModbusDataType.UNSIGNED_BYTE: "B",
    ModbusDataType.SHORT: "h",
    ModbusDataType.UNSIGNED_SHORT: "H",
    ModbusDataType.INT: "i",
    ModbusDataType.INTEGER: "i",
    ModbusDataType.UNSIGNED_INT: "I",
    ModbusDataType.LONG: "q",
    ModbusDataType.UNSIGNED_LONG: "Q",
    ModbusDataType.FLOAT: "f",
    ModbusDataType.DECIMAL: "f",
    ModbusDataType.DOUBLE: "d",
}


def normalize_modbus_data_type(value):
    if value is None:
        return None

    value = str(value).strip()

    for data_type in ModbusDataType.list():
        if data_type.lower() == value.lower():
            return data_type

    raise ValueError("Unknown Modbus data type: {}".format(value))


def modbus_type_register_count(data_type):
    data_type = normalize_modbus_data_type(data_type)

    if data_type is None:
        return None

    fmt = _TYPE_STRUCT_FORMAT.get(data_type)

    if fmt is None:
        return None

    return max(1, (struct.calcsize(fmt) + 1) // 2)


def decode_modbus_registers(registers, data_type,
                            most_significant_byte=True, most_significant_word=True):

    data_type = normalize_modbus_data_type(data_type)
    fmt = _TYPE_STRUCT_FORMAT.get(data_type) if data_type else None

    if fmt is None or not isinstance(registers, (list, tuple)):
        return registers

    if not all(isinstance(item, int) for item in registers):
        return registers

    byte_order = "big" if most_significant_byte else "little"
    words = list(registers) if most_significant_word else list(reversed(registers))

    try:
        binary = b"".join(word.to_bytes(2, byte_order) for word in words)
        size = struct.calcsize(fmt)
        binary = binary[-size:] if most_significant_byte else binary[:size]
        return struct.unpack((">" if most_significant_byte else "<") + fmt, binary)[0]
    except (OverflowError, ValueError, struct.error):
        return registers
