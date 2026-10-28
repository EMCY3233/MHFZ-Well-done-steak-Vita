"""Explicit SDK location for the Windows ARM harnesses."""
import os
from pathlib import Path


def sdk_bin():
    default = Path(__file__).resolve().parents[2] / 'analysis-tools/vitasdk-win-20260825/bin'
    sdk = Path(os.environ.get('WDSV_VITASDK_BIN', default)).resolve()
    for name in ('arm-vita-eabi-gcc.exe', 'arm-vita-eabi-nm.exe'):
        if not (sdk / name).is_file():
            raise RuntimeError('Set WDSV_VITASDK_BIN to the VitaSDK bin directory')
    return sdk
