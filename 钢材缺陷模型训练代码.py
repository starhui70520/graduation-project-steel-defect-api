from ultralytics import YOLO

model = YOLO(r"F:\外包服务\毕设\基于机器视觉的表面缺陷检测方法\yolov8n.pt") 
model.train(data=r'F:\外包服务\毕设\基于机器视觉的表面缺陷检测方法\NEU\data.yaml', epochs = 100) 
model(r"F:\外包服务\毕设\基于机器视觉的表面缺陷检测方法\NEU\valid\images\crazing_4.jpg", show=True, save=True)
