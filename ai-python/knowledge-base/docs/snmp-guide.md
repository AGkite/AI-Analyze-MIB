# MY-SYSTEM-MIB 使用说明

## 概述

`MY-SYSTEM-MIB` 定义了设备基础监控指标，包含 CPU、内存和设备名。

## 主要 OID

| MIB 名称    | OID 后缀 | 说明           |
|------------|----------|----------------|
| cpuUsage   | .1       | CPU 使用率 0-100 |
| memUsage   | .2       | 内存使用率 0-100 |
| deviceName | .3       | 设备主机名       |

## 代码调用

Python 客户端见 `code/snmp_client.py`，使用 `get_cpu_usage()` 读取 CPU 指标。

## 注意事项

- cpuUsage 和 memUsage 均为只读（read-only）
- 数值范围 0-100，超出范围应视为异常