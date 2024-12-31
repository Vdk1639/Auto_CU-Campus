import pywifi
import sys
import time
from pywifi import const
import requests
import socket
from bs4 import BeautifulSoup
from urllib.parse import unquote
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def wifi_connect_status():
    """
    判断本机是否有无线网卡,以及连接状态
    :return: 已连接或存在无线网卡返回True,否则返回False
    """
    wifi = pywifi.PyWiFi()
    interfaces = wifi.interfaces() #获取无线网卡接口
    
    if not interfaces:
        print("没有找到无线网卡")
        return False

    iface = interfaces[0] #取第一个无线网卡

    if iface.status() in [const.IFACE_CONNECTED, const.IFACE_INACTIVE]: #判断是否连接成功
        print('WiFi已经连接了网络')
        return True
    else:
        print("WiFi未启用，请启用Wi-Fi后重试！")
        return False

def scan_wifi():
    """
    扫描附近wifi
    :return: 扫描结果对象
    """
    wifi = pywifi.PyWiFi()
    interfaces = wifi.interfaces()
    
    if not interfaces:
        print("没有找到无线网卡")
        return []

    iface = interfaces[0]
    iface.scan()
    time.sleep(1)
    basewifi = iface.scan_results()
    for i in basewifi:
        print('wifi扫描结果:{}'.format(i.ssid))
        print('wifi设备MAC地址:{}'.format(i.bssid))
    return basewifi

def connect_wifi():
    wifi = pywifi.PyWiFi()
    interfaces = wifi.interfaces()
    
    if not interfaces:
        print("没有找到无线网卡")
        return False

    iface = interfaces[0] #取第一个无线网卡
    print("本机无线网卡名称：")
    print(iface.name())
    iface.disconnect()
    time.sleep(1)

    profile = pywifi.Profile()
    profile.ssid = SSID

    # 不删除所有网络配置，只添加新的配置
    tmp_profile = iface.add_network_profile(profile)

    iface.connect(tmp_profile)
    
    retry_count = 0 #尝试连接次数
    max_retries = 5 
    # 尝试连接5次，每次间隔1秒
    while iface.status() != const.IFACE_CONNECTED and retry_count < max_retries:
        print(f"尝试连接 {SSID} 中...")
        time.sleep(1)
        retry_count += 1

    if iface.status() == const.IFACE_CONNECTED:
        print(f"连接 {SSID} 成功")
        return True
    else:
        print(f"连接 {SSID} 失败")
        return False

def tryconnect(max_retries=3):
    """
    尝试连接wifi
    :return: 连接成功返回True,否则返回False
    """
    retry_count = 0 #尝试连接次数
    flag = False #连接成功标志
    while not flag and retry_count < max_retries:
        retry_count += 1
        flag = connect_wifi() #连接wifi
    if flag:
        print(f"{SSID}已连接，正在登录……")
    else:
        print(f"{SSID}连接失败，请检查网络")
        return False
    return True

def read_config(file_path='config.txt'):
    """
    读取配置文件
    :param file_path: 配置文件路径
    :return: SSID, USERNAME, PASSWORD, AUTH_SERVER_IP, DEBUG
    """
    try:
        with open(file_path) as f:
            config = {}
            for line in f:
                key, value = line.strip().split('=')
                config[key.strip()] = value.strip()
            ssid = config.get('SSID')
            username = config.get('username')
            password = config.get('password')
            auth_server_ip = config.get('auth_server_ip')
            DEBUG = config.get('DEBUG', 'false').lower() == 'true'
        return ssid, username, password, auth_server_ip, DEBUG
    except FileNotFoundError:
        print("配置文件 config.txt 未找到")
        sys.exit(1)
    except Exception as e:
        print(f"读取配置文件时发生错误: { e }")
        sys.exit(1)

def login_to_wifi():
    """
    登录到WiFi
    """
    hostname = socket.gethostname() # 获取本机计算机名称
    local_ip = socket.gethostbyname(hostname) # 获取本机ip
    url_0 = f"http://{AUTH_SERVER_IP}/?wlanuserip={local_ip}&basname=&ssid=school"
    url_index = f"http://{AUTH_SERVER_IP}/style/school/index.jsp"
    url_auth = f"http://{AUTH_SERVER_IP}/authServlet"
    if DEBUG:
        print(url_0)

    try:
        session = requests.session()
        retry = Retry(
            total=5,  # 总共重试次数
            backoff_factor= 1 ,  # 重试间隔时间的增长因子
            status_forcelist=[502, 503, 504]  # 需要重试的状态码
        ) 
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        response = session.get(url_0)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        frames = soup.find_all('frame')
        if len(frames) > 1:
            paramStr = (str(frames[1]).split('"')[-2]).split('=')[-1]
        else:
            print("未找到足够的frame元素")
            sys.exit(1)
        print(paramStr) # 未解码的参数
        paramStr = unquote(paramStr)
        print(paramStr) # 解码后的参数  
        
        if DEBUG:
            print(paramStr)

        response = session.get(url=url_index, params={"paramStr": paramStr}) # 携带参数paramStr访问url_index
        response.raise_for_status() # 如果请求失败，抛出异常
        if DEBUG:
            print(response, response.text)
        
        # 构造POST请求参数
        data = {
            "province": "wlan.js.chinaunicom.cn", #这里因为我的校园网在江苏 js，所以我写死在代码里，如果使用者不在江苏，需要修改这个参数，详情需要自己分析登录请求
            "paramStr": paramStr,
            "gdyh": "prov", #这里这个参数不清楚是什么，看不懂，但还是写死在代码里
            "shortname": "",
            "UserName": USERNAME,
            "PassWord": PASSWORD
        }
        response = session.post(url=url_auth, data=data)
        response.raise_for_status() # 如果请求失败，抛出异常
        if DEBUG:
            print(response, response.text) #

        if response.status_code == 200:
            print('OK')
        elif response.status_code == 500:
            print(response.status_code, '参数错误!!!')
        else:
            print(response.status_code, '未知错误!!!')
    except requests.RequestException as e:
        print(f"网络请求发生错误: { e }")
        sys.exit(1)

def main():
    global SSID, USERNAME, PASSWORD, AUTH_SERVER_IP, DEBUG
    SSID, USERNAME, PASSWORD, AUTH_SERVER_IP, DEBUG = read_config()

    # 检查WiFi连接状态，1表示已连接，0表示未连接
    status = wifi_connect_status()
    if not status:
        sys.exit(1)

    # 尝试连接校园网
    if not tryconnect():
        sys.exit(1)

    # 登录到校园网
    login_to_wifi()

if __name__ == "__main__":
    main()