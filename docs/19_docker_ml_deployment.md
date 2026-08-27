# Docker 机器学习部署

## 为什么用 Docker

Docker 将应用及其依赖打包为容器，确保环境一致性。在 ML 部署中，Python 依赖版本冲突是常见问题，Docker 从根本上解决了这个问题。

## Dockerfile 最佳实践

1. 使用 slim 基础镜像减小体积。
2. 先 COPY requirements.txt 再 pip install，利用层缓存。
3. 用 .dockerignore 排除不必要的文件。
4. 非 root 用户运行提升安全性。
5. EXPOSE 端口声明。

## Docker Compose 多容器编排

Docker Compose 可以编排多个容器。在 AI 服务中，通常需要 API 容器 + Redis 容器。docker-compose.yml 定义服务间依赖关系、网络、卷挂载。一键 docker compose up 启动全部服务。

## 镜像优化

Python ML 镜像通常较大（>1GB）。优化方法：多阶段构建（builder 阶段编译，runtime 阶段只保留运行时）；使用 .dockerignore 排除测试数据和缓存；选择 alpine 或 slim 基础镜像。
