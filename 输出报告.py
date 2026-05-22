import os
import requests
import time
import asyncio
import matplotlib.pyplot as plt

# 读取指定文件夹内的所有文件
def read_image_files(folder_path):
    return [os.path.join(folder_path, file) for file in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, file))]

# 并发请求
async def request_api(image_file):
    url = "http://127.0.0.1:8010/detect/"
    with open(image_file, "rb") as file:
        files = {"image_file": file}
        response = requests.post(url, files=files)
        return response.content

# 主函数
async def main():
    folder_path = "./NEU/valid/images/"
    save_folder = "./processed_images/"
    image_files = read_image_files(folder_path)

    execution_times = []  # 存储每次执行的耗时

    for _ in range(10):  # 执行10次
        start_time = time.time()

        tasks = [request_api(image_file) for image_file in image_files]
        processed_images = await asyncio.gather(*tasks)

        # 保存处理后的图像到指定文件夹
        for idx, image_content in enumerate(processed_images):
            with open(os.path.join(save_folder, os.path.basename(image_files[idx])), "wb") as f:
                f.write(image_content)

        end_time = time.time()
        execution_time = end_time - start_time
        execution_times.append(execution_time)

    # 绘制图表
    plt.plot(range(1, 11), execution_times, marker='o')
    plt.xlabel('Execution Number')
    plt.ylabel('Execution Time (s)')
    plt.title('Execution Time of API Requests')
    plt.grid(True)
    plt.savefig('execution_times.png')
    plt.show()

# 异步执行请求
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
