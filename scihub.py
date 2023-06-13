import os
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
import geopandas as gpd
from tqdm import tqdm

# SciHub用户名和密码
username = ''
password = ''

# SciHub的查询API URL
api_url = 'https://scihub.copernicus.eu/dhus/search?'

# 要搜索的日期范围 (7天一个周期,哨兵大概每两三天就有更新)
end_date = datetime.now().date()
start_date = end_date - timedelta(days=7)

# 要下载的地理坐标shp文件范围
shp_file = 'paper(3)_Polygon.shp'
gdf = gpd.read_file(shp_file)
polygon = gdf.geometry.values[0]

# ================================================== #
# 查询
# 参数配置
params = {
    'q': f" platformname:Sentinel-2 "
         f" AND footprint:\"Intersects({polygon})\""
         f" AND beginPosition:[{start_date}T00:00:00.000Z TO {end_date}T23:59:59.999Z]"
         f" AND endPosition:[{start_date}T00:00:00.000Z TO {end_date}T23:59:59.999Z]"
         f" AND cloudcoverpercentage:[0 TO 15]",
    'format': 'json',
    'rows': 100  # 返回结果的数量，根据你的需要进行调整
}

# 发送查询GET请求
search_response = requests.get(api_url, params=params, auth=HTTPBasicAuth(username, password))

# 检查响应状态码
if search_response.status_code == 200:
    # 如果状态码是200，说明查询成功
    # 返回查询结果
    response_json = search_response.json()
    if int(response_json['feed']['opensearch:totalResults']):
        data_list = response_json['feed']['entry']
        url_list = []
        for index, item in enumerate(data_list):
            # 影像日期
            Date = item['summary'][6:16]
            # 影像的下载url
            download_url = item['link'][0]['href']
            if index == 0:
                latest_date = Date
            if Date == latest_date:
                url_list.append(download_url)
            else:
                break
        # ================================================== #
        # 影像下载
        os.mkdir(latest_date)
        for index, url in enumerate(url_list):
            data_response = requests.get(url, auth=HTTPBasicAuth(username, password), stream=True)
            if data_response.status_code == 200:
                # 如果状态码是200，说明下载成功，然后你可以保存文件
                file_size = int(data_response.headers.get('Content-Length', 0))  # 获取文件大小
                progress = tqdm(data_response.iter_content(1024), f'Downloading', total=file_size, unit='B',
                                unit_scale=True,
                                unit_divisor=1024,)
                with open(f'{latest_date}/{index}.zip', 'wb') as f:
                    for data in progress.iterable:
                        progress.update(len(data))
                        f.write(data)
            else:
                print('Failed to execute download: {}'.format(search_response.content))
        print("download success.")

    else:
        print('Imagery is not available because of cloud cover.')
else:
    print('Failed to execute query: {}'.format(search_response.content))
