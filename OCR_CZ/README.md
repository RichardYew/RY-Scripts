# 传智杯证书 OCR 提取工具

从证书图片批量提取：姓名 / 赛道 / 组别 / 级别（省赛|国赛）/ 奖项 / 指导老师 / 证书编号，输出 Excel。

## 文件说明

| 文件 | 作用 |
|---|---|
| `cert_ocr.py` | 公共模块：轻量模型配置 + 字段解析正则（被另外两个脚本 import） |
| `ocr_test.py` | 单张/多张测试，打印原始识别文本和解析结果 |
| `ocr_extract.py` | 批量提取，输出 `证书信息.xlsx` + `待人工审核.txt`（解析失败的） |
| `requirements.txt` | 依赖清单 |

## 安装（Windows / 拯救者 Y9000P）

```powershell
pip install -r requirements.txt
```

默认 `paddlepaddle` 是 CPU 版。用 RTX 5070 加速需换装 GPU 版：

```powershell
pip uninstall paddlepaddle
pip install paddlepaddle-gpu
```

GPU 版要求 CUDA 12.x 环境（飞桨官方命令见 <https://www.paddlepaddle.org.cn/install/quick>，按显卡和 CUDA 版本选）。
首次运行会自动下载模型（约几百 MB）到 `C:\Users\<你>\.paddlex`。

## 使用

```powershell
# 测试单张
python ocr_test.py "D:\证书\程序设计挑战赛-1768227_二等奖(10059).jpg"

# 批量（可传多个目录）
python ocr_extract.py "D:\证书\省赛_学生\程序设计挑战赛"
```

- 输出文件在**脚本所在目录**：`证书信息.xlsx`、`待人工审核.txt`
- 「级别」列按图片路径判断：路径含「省赛」→ 省赛，否则国赛
- 文件名带括号请**加引号**

## 备注

- 使用 PP-OCRv5 **mobile** 轻量模型，关闭了方向分类/文档矫正辅助模型，内存占用约为默认 medium 配置的 1/3；证书为规整正向印刷体，精度足够
- 解析失败的文件不会丢，全部列在 `待人工审核.txt`，人工看图补录即可
- 若 paddleocr 大版本升级导致 API 变化，`cert_ocr.py` 的 `ocr_lines()` 已兼容 2.x/3.x 两种返回格式，只需在这里改
