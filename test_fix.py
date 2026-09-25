"""Test fixed pipeline with diverse, non-default topics"""
import requests
import json

topics = [
    ("成都火锅", "成都火锅, 麻辣红油锅底, 涮毛肚黄喉, 四川火锅店"),
    ("上海外滩夜景", "上海外滩, 陆家嘴夜景, 东方明珠灯光, 黄浦江游船"),
    ("日本樱花", "日本樱花, 京都清水寺樱花, 富士山樱花海, 目黑川夜樱"),
    ("特斯拉Cybertruck", "特斯拉Cybertruck, 不锈钢车身, 赛博皮卡, 城市街头"),
]

url = "http://127.0.0.1:8002/generate"

for name, prompt in topics:
    print(f"\n{'='*70}")
    print(f"主题: {name}")
    print(f"输入: {prompt}")
    print(f"{'='*70}")

    body = {"prompt": prompt, "style": "真实摄影"}
    try:
        resp = requests.post(url, json=body, timeout=600)
        data = resp.json()
        print(f"成功: {data['success']} | 图片数: {len(data['image_urls'])} | 来源: {data['source']}")
        for i, u in enumerate(data['image_urls'][:5]):
            # Show filename/domain to assess relevance
            import re
            filename = re.search(r'/([^/]+\.[a-z]{3,4})(?:\?|$)', u)
            domain = re.search(r'https?://([^/]+)/', u)
            fname = filename.group(1) if filename else u[-60:]
            dom = domain.group(1) if domain else "?"
            print(f"  [{i+1}] {dom} / {fname[:80]}")
    except Exception as e:
        print(f"  错误: {e}")
