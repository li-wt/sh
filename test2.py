import json

import requests

url = "https://www.youtube.com/youtubei/v1/browse?prettyPrint=false"
proxy = {
    'http': "http://127.0.0.1:7890",
    'https': "https://127.0.0.1:7890"
}
headers = {
    'authority': 'www.youtube.com',
    'accept': '*/*',
    'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'content-type': 'application/json',
    'origin': 'https://www.youtube.com',
    'referer': 'https://www.youtube.com',
    "userAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36,gzip(gfe)",
}
payload = json.dumps({
    "context": {
        "client": {
            "hl": "zh-CN",
            "clientName": "WEB",
            "clientVersion": "2.20240724.00.00",
        },
    },
    "continuation": "4qmFsgKrCBIYVUNFMlVIWEdPbHFvdFJKZ0VXbF90aU13Go4IOGdhRUJocUJCbnItQlFyNUJRclFCVUZXT1VkUU1qQm9iSE5rZGxaelNVUnNaMnhqTWxsa1ZIRXdRblJPYXpOTU5HdFNWRFpyY1RCRWEybDZZWFJoYldKR1IwcFViRk50VUU0d056SmtiMFkyV1dZd01HSkpORjl3WDFWNmNVOWhhbVZLUW5sdVYybDVlRmM0TWw4MVgycEdlVEppZVMxTGNtaG1UMVkzUWtOak5VSkxNMlJrT1RSRmRXUjRSRFY0V0RGUVZ6TnRNVFV6ZG5WdmNrUlNTMVJNTFc5dWRURlhOVmxXUjNZNVYxUnZXazVNU2tWUFoxcGtaVzl4TTJGMlNWbEdVMkZaYkVkTVpqUXRXVWxVYkV4bk5HTnFWMloxVnpNd1JuRjFZVlZ2U0dWb05sVTVOak5JUW10QlMwcDFXak52VVZkQ1YwUkRSR05IVjNkSU5uRTJPR3RaYm5oWmMzVjFlVkYyYkd0M1JIRldRVU5xZG1OSlF5MU5NM0Z4VFdOSWNWZFFYMWxaWDBKM2JWOHdkMFZVZDAxcFpUaDVjVlJpTnpad1UwRnlNVzQzY2pWVWFYTmpaMnQ1Y21GU04wdEdaMEkxVmxNeVFrcFpPR0ZQYkRZd1NrdFRlR1ZvZFZWaU9VTkRSalJNUlROQmNYSktZVFpqZFhCd1VWcGhWV3hIZVVkbU5WaHFkSGg1ZFVWaFVFZHhWbVZLYm1RNVJrVlNXblZuTTNKcVVFVmFNV0YzTm1ORU5sVm9WR3RCVjFNMk5FUTRhME4yT1ZWRFUycDJUVFZmYW10RGQxa3dSamxvZVdGeWRtZFFZbmN0TnpoalptSm1aV3d3YlVOQmRHZHVUWEptUkY5M1JGazJRMVJ5WTJWVmFVZ3lhbEZxY1Zwc1IybFJNbTR4YjFSNVZYTXdTMWRzV1hvM2R6Qlhia054TXpSR00xWnVPVGhwVFc5emFISnNka1psZUVwTmVISktSblZTU1V4a1dtdFJjWEJuV2paTVVIaHVSM0Z0T0d4RlJUQmhkMnB6TFVsNmJFOW5NbXMyWTBkdVFtaFJRamN5Y2xOdlJVZGpURVZqWVMxQk1XWTNjbVpIVFhOYVNGbG9VMVpMZUc1Wk0yRjVRbGRqWWxabGJrRk1PVkpuUzBKS01EaG5OM2RUV1haNk9XMUdhbXRRVUZZelducFFiak5PZURjeldYbGtjVk10WDFWclpWY3lOV3RmVmxONWJGbDNVRVozTFVwdU1FTXliblJtZUMxclZIcFNWVTU0WlZodFJqRlNOVGt6WDNWWlFURnJlQklrTmpaaU1qWTFOakV0TURBd01DMHlZMk14TFRsa1ltRXRaalJtTldVNE1EazNNRE13R0FFJTNE"
})

response = requests.request("POST", url, headers=headers, proxies=proxy, data=payload)

print(response.text)
