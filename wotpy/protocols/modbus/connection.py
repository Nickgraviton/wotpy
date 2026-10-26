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
Connection helpers for Modbus TCP operations.
"""

import asyncio

from pymodbus.client import AsyncModbusTcpClient

from wotpy.protocols.modbus.enums import ModbusEntity, ModbusFunction


class ModbusConnection:
    def __init__(self, host, port, timeout_ms=1000):
        self._host = host
        self._port = port
        self._timeout_secs = max(float(timeout_ms) / 1000.0, 0.1)
        self._client = AsyncModbusTcpClient(host=self._host, port=self._port, timeout=self._timeout_secs)
        self._lock = asyncio.Lock()

    @property
    def key(self):
        return "{}:{}".format(self._host, self._port)

    async def close(self):
        async with self._lock:
            try:
                self._client.close()
            except Exception:
                pass

    async def _connect(self):
        if self._client.connected:
            return

        ok = await self._client.connect()

        if not ok:
            raise ConnectionError("Could not connect to Modbus endpoint {}:{}".format(
                self._host, self._port))

    async def _call_with_unit(self, fn, *args, unit_id, **kwargs):
        try:
            return await fn(*args, slave=unit_id, **kwargs)
        except TypeError:
            try:
                return await fn(*args, unit=unit_id, **kwargs)
            except TypeError:
                return await fn(*args, device_id=unit_id, **kwargs)

    @staticmethod
    def _raise_if_error(result):
        if hasattr(result, "isError") and result.isError():
            raise RuntimeError("Modbus operation failed: {}".format(result))

    async def read(self, entity, address, quantity, unit_id):
        async with self._lock:
            await self._connect()

            if entity == ModbusEntity.INPUT_REGISTER:
                result = await self._call_with_unit(
                    self._client.read_input_registers,
                    address,
                    count=quantity,
                    unit_id=unit_id)
            elif entity == ModbusEntity.COIL:
                result = await self._call_with_unit(
                    self._client.read_coils,
                    address,
                    count=quantity,
                    unit_id=unit_id)
            elif entity == ModbusEntity.HOLDING_REGISTER:
                result = await self._call_with_unit(
                    self._client.read_holding_registers,
                    address,
                    count=quantity,
                    unit_id=unit_id)
            elif entity == ModbusEntity.DISCRETE_INPUT:
                result = await self._call_with_unit(
                    self._client.read_discrete_inputs,
                    address,
                    count=quantity,
                    unit_id=unit_id)
            else:
                raise ValueError("Unknown Modbus entity: {}".format(entity))

            self._raise_if_error(result)

            if entity in (ModbusEntity.COIL, ModbusEntity.DISCRETE_INPUT):
                return list(result.bits[:quantity])

            return list(result.registers[:quantity])

    async def write(self, function_code, address, quantity, unit_id, payload):
        async with self._lock:
            await self._connect()

            if function_code == ModbusFunction.WRITE_SINGLE_COIL:
                result = await self._call_with_unit(
                    self._client.write_coil,
                    address,
                    bool(payload),
                    unit_id=unit_id)
            elif function_code == ModbusFunction.WRITE_MULTIPLE_COILS:
                result = await self._call_with_unit(
                    self._client.write_coils,
                    address,
                    [bool(item) for item in payload],
                    unit_id=unit_id)
            elif function_code == ModbusFunction.WRITE_SINGLE_HOLDING_REGISTER:
                result = await self._call_with_unit(
                    self._client.write_register,
                    address,
                    int(payload),
                    unit_id=unit_id)
            elif function_code == ModbusFunction.WRITE_MULTIPLE_HOLDING_REGISTERS:
                result = await self._call_with_unit(
                    self._client.write_registers,
                    address,
                    [int(item) for item in payload],
                    unit_id=unit_id)
            else:
                raise ValueError("Unsupported write function code: {}".format(function_code))

            self._raise_if_error(result)

            return None
