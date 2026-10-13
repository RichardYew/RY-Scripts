import os
import sys
import win32com.client

# 控制台统一使用 UTF-8，避免中文/符号输出报错
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ====================== 配置区域 ======================
# 请修改为你要处理的PPT文件名（支持 .ppt / .pptx 格式）
# 脚本必须和该PPT文件放在同一个目录下
PPT_FILENAME = "26年课表.pptx"
# ======================================================


def main():
    # 获取脚本所在的目录（确保与PPT同目录）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 拼接得到PPT的完整路径
    ppt_full_path = os.path.join(script_dir, PPT_FILENAME)

    # 1. 判断文件是否存在，不存在则报错退出
    if not os.path.isfile(ppt_full_path):
        print(f"[错误] 当前目录下未找到文件：{PPT_FILENAME}")
        print(f"[提示] 请将脚本与PPT放在同一文件夹，并检查文件名是否正确。")
        sys.exit(1)

    # 获取不带扩展名的文件名，用于导出图片命名
    base_name = os.path.splitext(PPT_FILENAME)[0]

    ppt_app = None
    presentation = None

    try:
        # 2. 启动 PowerPoint（后台运行，不弹出窗口）
        print("正在启动 PowerPoint 组件...")
        ppt_app = win32com.client.Dispatch("PowerPoint.Application")
        try:
            ppt_app.Visible = False  # 部分 PowerPoint 版本不允许设置，忽略即可
        except Exception:
            pass

        # 3. 以只读方式打开PPT，避免修改原文件
        print(f"正在打开文件：{PPT_FILENAME}")
        presentation = ppt_app.Presentations.Open(ppt_full_path, ReadOnly=True)

        slide_total = presentation.Slides.Count
        print(f"检测到共 {slide_total} 页幻灯片，开始逐页导出 PNG...\n")

        # 4. 逐页导出，序号从 1 开始，命名格式：原文件名_序号.png
        for slide_num in range(1, slide_total + 1):
            slide = presentation.Slides(slide_num)
            output_name = f"{base_name}_{slide_num}.png"
            output_path = os.path.join(script_dir, output_name)

            # 导出为PNG格式
            slide.Export(output_path, "PNG")
            print(f"已导出 [{slide_num}/{slide_total}]：{output_name}")

        print("\n✅ 全部导出完成！图片已保存在脚本所在目录。")

    except Exception as e:
        print(f"\n❌ 导出出错：{str(e)}")
        sys.exit(1)

    finally:
        # 5. 确保资源释放，关闭PPT进程（即使报错也会执行）
        if presentation is not None:
            try:
                presentation.Close()
            except Exception:
                pass
        if ppt_app is not None:
            try:
                ppt_app.Quit()
            except Exception:
                pass
        # 释放COM对象，避免残留PowerPoint进程
        del presentation
        del ppt_app


if __name__ == "__main__":
    main()
