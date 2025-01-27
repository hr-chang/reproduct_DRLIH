# 依赖库列表以及其版本要求

```
matplotlib==3.10.0
numpy==1.23.0
Pillow==11.1.0
torch==2.5.0+cu121
torchvision==0.20.0+cu121
```

# 数据准备

使用了预处理后的cifar10作为输入。

下载链接: https://pan.baidu.com/s/19LAa6f5OtXvDK-jOlV5_UA?pwd=8aia

也可直接联系本人 QQ: 178220929 （常昊冉）

数据内容需分别放入 train 和 test 文件夹

# 训练命令（含测试）

格式：python train.py **gpu_id** bit_length batch_size dataset

例：

```
python train.py 0 32 16 cifar
```
