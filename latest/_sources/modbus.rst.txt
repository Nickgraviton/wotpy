Modbus
======

This section describes the mapping between the high-level actions that can be executed on a Thing and the
Modbus TCP requests sent to the device when using the Modbus Protocol Binding.

.. note:: The Modbus binding is **client-only**.

Every interaction is translated into a Modbus TCP request whose raw register or coil values are decoded into plain Python values.

Form elements
-------------

Form elements consumed by the Modbus binding are described with the ``modbus+tcp`` URI scheme and the
``modv:`` vocabulary terms. All forms contain the following fields:

=============   ===========
Field           Description
=============   ===========
``op``          Interaction verb (e.g. ``readproperty``) associated with this form element.
``href``        Contains the Modbus endpoint, the unit ID and the register/coil address.
=============   ===========

An example of a Modbus form ``href``::

    modbus+tcp://192.168.1.50:502/1/4096?quantity=2

* ``192.168.1.50:502`` is the Modbus TCP endpoint. The port defaults to ``502`` when omitted.
* ``1`` is the unit ID of the target device.
* ``4096`` is the start address of the register or coil.
* ``quantity=2`` is the optional number of registers/coils to read or write.

A form ``href`` may also be relative when the Thing Description declares a ``base``. In that case the
base path is treated as a unit ID prefix::

    "base": "modbus+tcp://192.168.1.50:502/1"
    "href": "/4096?quantity=2"

.. note:: The ``modbus+tcp`` URL scheme is used internally to select the appropriate protocol binding. Forms with any other scheme are ignored by this binding.

Vocabulary terms
----------------

Values taken from the ``href`` can be overridden with the following form fields:

=============================   ===========
Field                           Description
=============================   ===========
``modv:function``               Modbus function, either as a numeric code (e.g. ``3``) or as a name (e.g. ``readHoldingRegisters``).
``modv:entity``                 Modbus entity: ``Coil``, ``DiscreteInput``, ``InputRegister`` or ``HoldingRegister``.
``modv:unitID``                 Unit ID of the target device. Overrides the value taken from the ``href``.
``modv:address``                Start address. Overrides the value taken from the ``href``.
``modv:quantity``               Number of registers or coils involved in the operation.
``modv:type``                   XSD data type (e.g. ``xsd:float``) used to decode the raw registers.
``modv:pollingTime``            Polling interval in milliseconds used when observing properties and events. Defaults to ``2000``.
``modv:timeout``                Request timeout in milliseconds. Defaults to ``1000``.
``modv:mostSignificantByte``    Whether registers are decoded in big-endian byte order. Defaults to ``true``.
``modv:mostSignificantWord``    Whether multi-register values are decoded most significant word first. Defaults to ``true``.
=============================   ===========

Function codes
--------------

The following function names and codes are understood by the binding:

================================  =====  ====================
Name                              Code   Entity
================================  =====  ====================
``readCoil``                      1      ``Coil``
``readDiscreteInput``             2      ``DiscreteInput``
``readHoldingRegisters``          3      ``HoldingRegister``
``readInputRegisters``            4      ``InputRegister``
``writeSingleCoil``               5      ``Coil``
``writeSingleHoldingRegister``    6      ``HoldingRegister``
``writeMultipleCoils``            15     ``Coil``
``writeMultipleHoldingRegisters`` 16     ``HoldingRegister``
``readDeviceIdentification``      43     \-
================================  =====  ====================

When ``modv:function`` is not present the binding infers the function code from ``modv:entity``, the
``quantity`` and whether the operation is a read or a write. If ``modv:entity`` is missing as well,
``HoldingRegister`` is assumed.

Data types
----------

When ``modv:type`` is present the raw registers are decoded into a single scalar value. The number of
registers needed for the type is also inferred from it when ``quantity`` is not given:

=====================  ==========
Type                   Registers
=====================  ==========
``xsd:boolean``        1
``xsd:byte``           1
``xsd:unsignedByte``   1
``xsd:short``          1
``xsd:unsignedShort``  1
``xsd:int``            2
``xsd:integer``        2
``xsd:unsignedInt``    2
``xsd:float``          2
``xsd:decimal``        2
``xsd:long``           4
``xsd:unsignedLong``   4
``xsd:double``         4
=====================  ==========

If ``modv:type`` is not present, a read of a single register or coil returns the scalar value, while a
read of multiple registers or coils returns a list.

Interaction Model mapping
-------------------------

Read Property
^^^^^^^^^^^^^

The binding issues the read request matching the resolved entity:

* ``Coil`` → *Read Coils* (code ``1``)
* ``DiscreteInput`` → *Read Discrete Inputs* (code ``2``)
* ``HoldingRegister`` → *Read Holding Registers* (code ``3``)
* ``InputRegister`` → *Read Input Registers* (code ``4``)

Write Property
^^^^^^^^^^^^^^

The binding issues the write request matching the resolved entity and quantity:

* ``Coil`` → *Write Single Coil* (code ``5``) or *Write Multiple Coils* (code ``15``)
* ``HoldingRegister`` → *Write Single Register* (code ``6``) or *Write Multiple Registers* (code ``16``)

Invoke Action
^^^^^^^^^^^^^

An action invocation is mapped to the same write requests used for properties, taking the action input
as the payload. Modbus write responses carry no payload, so the invocation always resolves to ``None``.

Observe Event
^^^^^^^^^^^^^

As with property observation, events are produced by polling the read request defined in the event form
every ``modv:pollingTime`` milliseconds. Unlike property observation, every poll emits an event
regardless of whether the value changed.

Example Thing Description
-------------------------

.. code-block:: json

    {
        "id": "urn:org:fundacionctic:thing:modbus-sensor",
        "title": "Modbus Sensor",
        "base": "modbus+tcp://192.168.1.50:502/1",
        "properties": {
            "temperature": {
                "type": "number",
                "readOnly": true,
                "forms": [
                    {
                        "op": ["readproperty", "observeproperty"],
                        "href": "/4096",
                        "modv:function": "readHoldingRegisters",
                        "modv:type": "xsd:float",
                        "modv:pollingTime": 5000
                    }
                ]
            },
            "relay": {
                "type": "boolean",
                "forms": [
                    {
                        "op": ["readproperty", "writeproperty"],
                        "href": "/16",
                        "modv:entity": "Coil"
                    }
                ]
            }
        }
    }
