from fastapi import FastAPI, UploadFile, File, Response
from PIL import Image
from io import BytesIO
from ultralytics import YOLO

app = FastAPI()

# 全局变量用于存储模型，确保只加载一次
yolo_model = None

def load_model():
    global yolo_model
    if yolo_model is None:
        yolo_model = YOLO("钢材模型.pt")

async def detect_defects(image_file):
    # 加载模型
    load_model()

    # 读取上传的图像文件
    contents = await image_file.read()
    image = Image.open(BytesIO(contents))

    # 在模型上执行检测
    results = yolo_model(image)

    np_image = results[0].plot() 
    pil_image = Image.fromarray(np_image)

    # 将图像数据直接返回
    img_byte_array = BytesIO()
    pil_image.save(img_byte_array, format='JPEG')
    return img_byte_array.getvalue()

@app.post("/detect/")
async def detect(image_file: UploadFile = File(...)):
    result_image_data = await detect_defects(image_file)
    return Response(content=result_image_data, media_type="image/jpeg")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8010)
