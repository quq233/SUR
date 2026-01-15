# 🚀 SUR (Spoofed Unicast RA)

SUR 是一种利用 **Unicast Router Advertisements** 实现内网 IPv6 精准分流的工具。
通过向特定设备发送精心构造的链路层单播 RA 包，SUR 能够在不改变现有“旁路由”架构、无需额外硬件的前提下，实现极其优雅的 IPv6 接入体验。

SUR内置了WebUI，您可在数分钟内部署并上手，实现IPv6自由
<table>
  <tr>
    <td rowspan="2">
        <img src="https://raw.githubusercontent.com/quq233/static/main/scan.png" width="400" alt="SUR Dashboard"/>
    </td>
    <td>
        <img src="https://raw.githubusercontent.com/quq233/static/main/index.png" width="400" alt="SUR Dashboard"/>
    </td>
  </tr>
  <tr>
    <td>
        <img src="https://raw.githubusercontent.com/quq233/static/main/tags.png" width="400" alt="SUR Dashboard"/>
    </td>
  </tr>
</table>

### 🌟 核心特性

* **设备级精准控制**：自主决定哪些设备接入 IPv6。
* **精准分流**：
    * **直连模式**：直连设备不经过旁路由，流量直接通过主路由转发。
    * **代理模式**：上行流量经旁路由处理，下行流量由主路由直回（ASRT），最大限度降低旁路由性能占用。
* **高可用性**：即便旁路由故障，直连设备的 IPv4/IPv6 上网完全不受影响。
* **内置 Dashboard**：提供直观的 WebUI 界面，轻松管理内网设备。
* **自由分组**: 为设备和网关分组，设备可在同组网关中负载均衡

> **“旁路由才是最优雅的拓扑。”**

### 兼容性说明
理论上SUR支持**所有**遵循标准 IPv6 RA 行为的系统/设备
目前已在以下系统经过测试：
* Android （9、10、14）
* IpadOS（18.5、26.1）、MacOS（13.7）
  * ⚠️如果"配置DNS"被设置为手动，则系统会忽略SUR下发的DNS；手动添加后工作正常
  * IOS上可能会出现类似情况，但未经测试
* Windows （Windows11，Windows Server 2025）
* Ubuntu （Server 24.04.3 LTS）
* 其他支持IPv6的设备 （已测试中兴路由器私有固件）

---
### ⚠️ 安全警告
目前SUR没有鉴权或输入验证。请勿将SUR/SUR-Dashboard暴露到公网。

### 🛠️ 部署步骤

#### 0. 前提条件
* 关闭内网其他设备的 DHCPv6 / RA 服务。
* 配置 **NPTv6** 或拥有**固定 IPv6 前缀**（若前缀动态变化，需自行脚本更新 `config.py` 中的 `PREFIX` 字段）。
* 关闭交换机的RA guard

#### 1. 安装环境
```bash
# 克隆仓库
git clone https://github.com/quq233/SUR && cd SUR
```

# 安装依赖
```bash
pip install -r requirements.txt
```

# 配置  
修改`config.py`，通常只需修改`IFACE`（网卡名称）和PREFIX

# 运行  
```bash
sudo python3 app.py
```

# 访问webui  
SUR内置了[SUR-Dashboard](!https://github.com/quq233/SUR-Dashboard/)，默认监听8000端口
