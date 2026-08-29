# Docker 概览

> 来源：Docker 官方文档 https://docs.docker.com/get-started/overview/

## 什么是 Docker

Docker 是一个用于开发、交付和运行应用程序的开放平台。Docker 能将应用与其基础设施分离，从而快速交付软件。通过利用 Docker 的交付、测试和部署方法，可以显著缩短编写代码到在生产环境运行之间的延迟。

## Docker 平台

Docker 提供了在被称为"容器"的松散隔离环境中打包和运行应用的能力。隔离性和安全性允许在给定主机上同时运行多个容器。容器是轻量级的，包含运行应用所需的一切，因此不依赖宿主机上安装了什么。

容器成为分发和测试应用的基本单元。部署时，将应用作为容器或编排服务部署到生产环境——无论是本地数据中心、云提供商还是混合环境，工作方式相同。

## Docker 能做什么

1. **快速一致地交付应用**：容器适合持续集成和持续交付（CI/CD）工作流。开发者在本地用容器写代码并分享，推送到测试环境运行自动化测试，修复后重新部署。
2. **响应式部署和扩展**：容器可移植、轻量，能运行在本地笔记本、数据中心物理机/虚拟机、云提供商上，也能按业务需求近实时地动态扩展或缩减。
3. **在同一硬件上运行更多负载**：Docker 轻量快速，是虚拟机管理程序（hypervisor）的高性价比替代方案，适合高密度环境和中小规模部署。

## Docker 架构

Docker 采用客户端-服务器架构。Docker 客户端与 Docker 守护进程通信，后者负责构建、运行和分发容器。客户端和守护进程可运行在同一系统，也可连接远程守护进程。两者通过 REST API 通信（经 UNIX socket 或网络接口）。Docker Compose 是另一个客户端，用于处理由一组容器组成的应用。

### Docker 守护进程（dockerd）

`dockerd` 监听 Docker API 请求，管理镜像、容器、网络、卷等 Docker 对象。守护进程之间也能相互通信以管理 Docker 服务。

### Docker 客户端（docker）

`docker` 命令是多数用户与 Docker 交互的主要方式。执行 `docker run` 等命令时，客户端把命令发送给 `dockerd`，由它执行。`docker` 命令使用 Docker API，一个客户端可连接多个守护进程。

### Docker Desktop

Docker Desktop 是面向 Mac、Windows、Linux 的易安装应用，用于构建和分享容器化应用与微服务。它包含 Docker 守护进程、Docker 客户端、Docker Compose、Docker Content Trust、Kubernetes 和 Credential Helper。

### Docker 镜像仓库（registry）

Docker registry 存储 Docker 镜像。Docker Hub 是任何人都可使用的公共 registry，Docker 默认在 Docker Hub 上查找镜像。使用 `docker pull` 或 `docker run` 时，Docker 从配置的 registry 拉取镜像；使用 `docker push` 时推送镜像到 registry。

## Docker 对象

### 镜像（Images）

镜像是创建 Docker 容器的只读模板。镜像常基于另一个镜像并附加定制。构建自己的镜像时创建 Dockerfile，用简单语法定义创建镜像和运行它的步骤。Dockerfile 中每条指令在镜像中创建一个层，改动并重建镜像时只重建发生变化的层——这正是镜像轻量、小巧、快速的原因。

### 容器（Containers）

容器是镜像的可运行实例。可用 Docker API 或 CLI 创建、启动、停止、移动、删除容器。默认情况下，容器与其他容器及宿主机相对隔离。容器由其镜像和创建/启动时提供的配置选项定义。容器被移除后，未存储在持久化存储中的状态更改会消失。

`docker run -i -t ubuntu /bin/bash` 这条命令的运行过程：本地没有 ubuntu 镜像则从 registry 拉取；创建新容器；分配可读写文件系统作为最终层；创建网络接口连接默认网络并分配 IP；启动容器执行 `/bin/bash`；执行 `exit` 终止命令后容器停止但不会被移除。

## 底层技术

Docker 用 Go 语言编写，利用 Linux 内核的多项特性实现功能。Docker 使用名为 `namespaces` 的技术提供隔离工作区（即容器）。运行容器时，Docker 为容器创建一组 namespace，每个 namespace 提供一层隔离——容器的每个方面运行在独立的 namespace 中，访问被限制在该 namespace 内。
