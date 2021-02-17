# 基于MCDReforged开发的QQ群聊天转发插件

## 环境

- 此插件仅适用于MCDReforged 1.x
- 机器人框架为mirai
- 机器人HTTP插件为mirai-api-http

## 插件介绍

QBot是一个能够自动转发群内消息到MC游戏中的MCDReforged插件

此插件具备转发QQ消息，向QQ群中发送消息功能

此插件的基本命令如下

- **!!qq help**: 查看帮助信息
- **!!qq send \<msg\>**: 向QQ群中发送消息
- **!!qq on**: 启动接收QQ群中的信息
- **!!qq off**: 停止接收QQ群中的信息
- **!!qq status**: 查看转发插件的运行状态

## 配置文件

一份基础的配置文件如下

```json
{
  "qq_bot_server": "",
  "auth_key": "",
  "bot_qq": 0,
  "admin_qq": 0,
  "group_id": 0
}
```

各个选项对应的参数为

- **qq_bot_server**: QQ机器人的http-api地址(域名:端口号)
- **auth_key**: QQ机器人的AUTH KEY
- **bot_qq**: 选择的QQ机器人的QQ号
- **admin_qq**: 管理员的QQ账号
- **group_id**: 绑定的QQ群号

## 使用插件

1. 安装requirements.txt所需的依赖

```shell
pip install -r requirements.txt
```

2. 启动MCDReforged

```shell
python3 MCDReforged.py
```

3. 此时会自动生成配置文件,由于配置文件并不正确, 所以插件会自己卸载掉，此时正确配置config文件夹下的qbot.json文件

4. 加载插件, 在MCDR控制台输入

```shell
!!MCDR plugin reloadall
```

5. 此时插件就已经正常运行了

## Q&A

Q1: 控制台显示"无法正常启动插件,请检查配置文件"

A1: 请检查配置文件配置是否正确，检查BOT服务器是否能够正常链接