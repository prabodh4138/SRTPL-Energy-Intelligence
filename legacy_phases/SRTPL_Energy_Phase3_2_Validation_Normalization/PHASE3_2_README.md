# SRTPL Energy Phase 3.2 — Validation & Normalization Engine

## Scope

Five current JUNO sources:

- Solar
- DG
- EB
- Transformer
- UPS

## Core rule

A source record is never silently discarded.

Validation produces:
- INFO
- WARNING
- ERROR
- CRITICAL

The normalized record receives:
- VALID
- EXCEPTION

## Cumulative meter protection

A decreasing cumulative value is classified as `DECREASE`.

It is NOT converted into negative consumption.

Example:

Previous = 10,000
Current = 10,050
=> 50 kWh

Previous = 10,050
Current = 200
=> meter reset/replacement candidate
=> interval consumption remains NULL
=> exception generated

## NULL rule

Blank JUNO cells remain NULL.

NULL does not mean zero.

This is particularly important for UPS reports because different UPS models/report configurations can have different populated fields.

## Threshold architecture

ThresholdProvider is intentionally an adapter.

Production values should come from:

energy_master.threshold

and not from hard-coded Python constants.

## Important engineering limitation

Transformer efficiency/loss is NOT calculated here.

That calculation should only be enabled after:
- transformer rated capacity is known
- measurement boundaries are known
- CT/PT ratios are confirmed
- primary/secondary measurement points are confirmed
- meter source is confirmed

Likewise, EB MD billing interpretation remains pending TPWODL bill information.
