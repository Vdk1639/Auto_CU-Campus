import pywifi
import time
from pywifi import const
import requests
import socket
from bs4 import BeautifulSoup
from urllib.parse import unquote


# 获取本机计算机名称
hostname = socket.gethostname()
# 获取本机ip
ip = socket.gethostbyname(hostname)
#拼接登录url
url_0="http://58.240.51.118/?wlanuserip="+ip+"&basname=&ssid=school"
url_index="http://58.240.51.118/style/school/index.jsp"
url_auth="http://58.240.51.118/authServlet"
#url_2= "http://58.240.51.118/style/school/logon.jsp"

with open('config.txt') as f:
    SSID = f.readline().split('=')[1].strip()
    username = f.readline().split('=')[1].strip()
    password = f.readline().split('=')[1].strip()
    b = f.readline().split('=')[1].strip()
    DEBUG= b == str(True)

def wifi_connect_status():
    """
    判断本机是否有无线网卡,以及连接状态
    :return: 已连接或存在无线网卡返回1,否则返回0
    """
    #创建一个元线对象
    wifi = pywifi.PyWiFi()

    #取当前机器,第一个元线网卡
    iface = wifi.interfaces()[0] #有可能有多个无线网卡,所以要指定

    #判断是否连接成功
    if iface.status() in [const.IFACE_CONNECTED,const.IFACE_INACTIVE]:
        print('wifi已经连接了网络')
        return 1
    else:
        print("兄弟，我没设置自动打开Wi-Fi功能，你先打开wifi再试?")
        pass
    return 0

def scan_wifi():
    """
    扫描附近wifi
    :return: 扫描结果对象
    """
    wifi = pywifi.PyWiFi()
    iface = wifi.interfaces()[0]

    iface.scan() #扫描附近wifi
    time.sleep(1)
    basewifi = iface.scan_results()
    for i in basewifi:
        print('wifi扫描结果:{}'.format(i.ssid)) # ssid 为wifi名称
        print('wifi设备MAC地址:{}'.format(i.bssid))
    return basewifi

def connect_wifi():
    wifi = pywifi.PyWiFi()  # 创建一个wifi对象
    ifaces = wifi.interfaces()[0]  # 取第一个无线网卡
    print("本机无线网卡名称：")
    print(ifaces.name())  # 输出无线网卡名称
    ifaces.disconnect()  # 断开网卡连接
    time.sleep(3)  # 缓冲3秒


    profile = pywifi.Profile()  # 配置文件
    profile.ssid = SSID  # 目标wifi名称
    #连校园网不需要密码登录，另有登录模块
    # profile.auth = const.AUTH_ALG_OPEN  # 需要密码
    # profile.akm.append(const.AKM_TYPE_WPA2PSK)  # 加密类型
    # profile.cipher = const.CIPHER_TYPE_CCMP  # 加密单元
    # profile.key = '4000103000' #wifi密码

    ifaces.remove_all_network_profiles()  # 删除其他配置文件
    tmp_profile = ifaces.add_network_profile(profile)  # 加载配置文件

    ifaces.connect(tmp_profile)  # 连接
    time.sleep(1)  # 尝试10秒能否成功连接
    isok = True
    if ifaces.status() == const.IFACE_CONNECTED:
        print("连接校园网成功")
    else:
        print("连接校园网失败")
    #ifaces.disconnect()  # 断开连接
    time.sleep(1)
    return isok


#查看wifi状态
#这里要改一下，在返回值为0时（未连接任何WiFi）要先连接一次，返回1时才会成功
print(wifi_connect_status())
#连接wifi
print(connect_wifi())
if DEBUG:
    print(url_0)

session = requests.session()
response = session.get(url_0)
soup = BeautifulSoup(response.text, "html.parser")
paramStr=(str(soup.find_all('frame')[1]).split('"')[-2]).split('=')[-1]
paramStr=unquote(paramStr)
if DEBUG:
    print(paramStr)

response=session.get(url=url_index,params={"paramStr":paramStr})
if DEBUG:
    print(response,response.text)
data={
    "province": "wlan.js.chinaunicom.cn",
    "paramStr": paramStr,
    "gdyh": "prov",
    "shortname": "",
    "UserName": username,
    "PassWord": password
}
response=session.post(url=url_auth,data=data)
if DEBUG:
    print(response,response.text)

#status.code方法返回网页状态码
if response.status_code == 200:#网页正常访问
	print('OK')
elif response.status_code==500:
    print(response.status_code,'参数错误!!!')
else:
    print(response.status_code,'未知错误!!!')