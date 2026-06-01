"""SNMP 客户端示例：读取 MY-SYSTEM-MIB 中的 OID。"""

# OID 前缀: 1.3.6.1.4.1.99999.1.1
ENTERPRISE_OID = "1.3.6.1.4.1.99999"
MY_SYSTEM_OID = f"{ENTERPRISE_OID}.1.1"

CPU_USAGE_OID = f"{MY_SYSTEM_OID}.1"    # cpuUsage
MEM_USAGE_OID = f"{MY_SYSTEM_OID}.2"    # memUsage
DEVICE_NAME_OID = f"{MY_SYSTEM_OID}.3"  # deviceName


def get_cpu_usage(snmp_engine, target) -> int:
    """读取 CPU 使用率，对应 MIB 中的 cpuUsage。"""
    return int(snmp_engine.get(CPU_USAGE_OID, target))


def get_mem_usage(snmp_engine, target) -> int:
    """读取内存使用率，对应 MIB 中的 memUsage。"""
    return int(snmp_engine.get(MEM_USAGE_OID, target))


def get_device_name(snmp_engine, target) -> str:
    """读取设备名称，对应 MIB 中的 deviceName。"""
    return snmp_engine.get(DEVICE_NAME_OID, target)