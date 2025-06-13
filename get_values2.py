import requests
import json
import re
import os
from urllib.parse import urlparse

def find_all_component_nos(data):
    results = []
    if isinstance(data, dict):
        if "component_no" in data:
            results.append(data["component_no"])
        for value in data.values():
            results.extend(find_all_component_nos(value))
    elif isinstance(data, list):
        for item in data:
            results.extend(find_all_component_nos(item))
    return results

def get_required_values():
    # 第一步：获取页面配置
    config_url = "https://gw2c-hw-open.longfor.com/supera/member/api/bff/pages/v1_14_0/publicApi/v1/pageConfig"
    config_payload = {"pageCode": "C2mine"}
    config_headers = {
        'User-Agent': "com.longfor.supera/1.10.2 iOS/17.0.2",
        'Content-Type': "application/json",
        'X-LF-Api-Version': "v1_14_0",
        'X-LF-Bucode': "C20400"
    }

    config_response = requests.post(config_url, data=json.dumps(config_payload), headers=config_headers)
    config_data = config_response.json()

    # 提取会员页抽奖的URL
    lottery_url = None
    for component in config_data.get("data", {}).get("components", []):
        for child in component.get("children", []):
            if child.get("content") == "每日抽奖":
                lottery_url = child.get("jumpUrl")
                break
        if lottery_url:
            break

    if not lottery_url:
        raise Exception("未找到会员页抽奖的URL")

    # 第二步：从URL中提取参数
    pattern = r"https?://[^/]+/([^/]+)/([^/]+)"
    match = re.search(pattern, lottery_url)
    if match:
        activity_no = match.group(1)
        page_no = match.group(2)
    else:
        parsed = urlparse(lottery_url)
        path_parts = parsed.path.split('/')
        non_empty_parts = [part for part in path_parts if part]
        if len(non_empty_parts) >= 2:
            activity_no = non_empty_parts[0]
            page_no = non_empty_parts[1]
        else:
            raise Exception("无法从URL中提取参数")

    # 第三步：请求页面信息
    info_url = "https://gw2c-hw-open.longfor.com/llt-gateway-prod/api/v1/page/info"
    params = {"activityNo": activity_no, "pageNo": page_no}
    info_headers = {
        'User-Agent': "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 &MAIAWebKit_iOS_com.longfor.supera_1.10.2_202501191934_Default_3.2.4.2",
        'x-gaia-api-key': "2f9e3889-91d9-4684-8ff5-24d881438eaf"
    }

    info_response = requests.get(info_url, params=params, headers=info_headers)
    info_data = info_response.json()
    
    # 查找component_no
    all_component_nos = find_all_component_nos(info_data)
    regex_matches = re.findall(r'\\"component_no\\":\\"([^\\"]*)\\"', info_response.text)
    
    if len(all_component_nos) >= 3:
        component_no = all_component_nos[1]
    elif len(regex_matches) >= 3:
        component_no = regex_matches[1]
    else:
        raise Exception("无法找到第三个component_no字段")
    
    return activity_no, component_no

if __name__ == "__main__":
    try:
        activity_no, component_no = get_required_values()
        
        # 输出到环境变量（GitHub Actions使用）
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"ACTIVITY_NO={activity_no}\n")
                f.write(f"COMPONENT_NO={component_no}\n")
        else:
            print(f"ACTIVITY_NO={activity_no}")
            print(f"COMPONENT_NO={component_no}")
            
    except Exception as e:
        print(f"::error::{str(e)}")
        exit(1)
