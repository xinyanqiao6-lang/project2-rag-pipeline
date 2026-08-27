# Hugging Face Spaces 部署

## HF Spaces 简介

Hugging Face Spaces 是一个免费托管 ML 应用演示的平台。支持 Gradio 和 Streamlit 框架。适合部署 RAG 系统的在线 Demo，让面试官和招聘方直接体验。

## Gradio 部署

Gradio 是一个 Python 库，可以快速构建 ML 应用的 Web 界面。几行代码就能创建一个交互式界面。在 HF Spaces 上部署 Gradio 应用，只需在仓库根目录放一个 app.py 和 requirements.txt。

## 部署步骤

1. 在 Hugging Face 创建 Space，选择 Gradio SDK。
2. 将项目代码推送到 Space 仓库。
3. 确保 requirements.txt 包含所有依赖。
4. 等待自动构建部署，获得公开 URL。

## 免费 CPU 部署的限制

HF Spaces 免费版使用 CPU，不适合运行大模型推理。解决方案：Demo 调用云 API（如硅基流动）而非本地推理。这样可以充分利用免费 CPU 资源，只在需要时调用 API。

## 部署的意义

在线 Demo 是简历的重要加分项。简历中附一个可访问的 URL，让招聘方直接体验你的产品，比文字描述更有说服力。HF Spaces 是零成本部署 Demo 的最佳选择。
