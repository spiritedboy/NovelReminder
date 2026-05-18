# NovelReminder

一个基于 Python 标准库实现的小说更新提醒工具，当前默认监控以下两本小说：

- 纵横：逆天邪神
- 番茄：公主太恶劣？抱紧她大腿后真香！

功能包括：

- 定期扫描最新章节
- 记录最近一次已通知状态，避免重复推送
- 检测到更新后推送钉钉群机器人消息
- 支持单次检测和常驻轮询两种模式
- 支持通过配置文件扩展多个小说 URL

## 运行要求

- Linux
- Python 3.11+

本项目只使用 Python 标准库，不依赖第三方包。

## 配置

复制环境变量模板：

```bash
cp .env.example .env
```

环境变量说明：

- `NOVEL_REMINDER_DINGTALK_WEBHOOK`：钉钉机器人 Webhook
- `NOVEL_REMINDER_DINGTALK_SECRET`：可选，若机器人启用加签则填写
- `NOVEL_REMINDER_DATABASE_PATH`：SQLite 状态库路径
- `NOVEL_REMINDER_NOVELS_PATH`：小说配置文件路径，默认 `config/novels.json`
- `NOVEL_REMINDER_INTERVAL_SECONDS`：轮询间隔，默认 `300`
- `NOVEL_REMINDER_NOTIFY_ON_FIRST_SEEN`：首次发现最新章节时是否立即通知，默认 `false`
- `NOVEL_REMINDER_LOG_LEVEL`：日志级别，默认 `INFO`

### 多小说配置

小说列表从 [config/novels.json](config/novels.json) 读取。每个配置项至少包含以下字段：

- `novel_id`：唯一 ID，用于状态去重
- `novel_name`：小说名称
- `site`：站点类型，当前支持 `zongheng` 和 `fanqie`
- `detail_url`：小说详情页 URL

示例：

```json
[
	{
		"novel_id": "zongheng_408586",
		"novel_name": "逆天邪神",
		"site": "zongheng",
		"detail_url": "https://www.zongheng.com/detail/408586"
	},
	{
		"novel_id": "fanqie_7503984033022364734",
		"novel_name": "公主太恶劣？抱紧她大腿后真香！",
		"site": "fanqie",
		"detail_url": "https://fanqienovel.com/page/7503984033022364734"
	}
]
```

如果你要新增小说，只需要在这个文件里追加一项，然后重新运行程序。

## 用法

单次检测：

```bash
python3 -m src.main run-once
```

查看当前已记录状态：

```bash
python3 -m src.main show-state
```

常驻运行：

```bash
python3 -m src.main run-loop
```

若希望先验证钉钉配置，可用下面的方式触发一次单次检测并查看日志。

## 推送内容

检测到新章节后，钉钉消息会包含：

- 小说名
- 网站来源
- 最新章节名
- 网站展示的更新时间
- 章节链接
- 检测时间

## 部署建议

前期可直接使用 `systemd` 托管 `python3 -m src.main run-loop`。

也可以直接使用仓库里的 [deploy/systemd/novel-reminder.service](deploy/systemd/novel-reminder.service) 作为模板。

如果更倾向容器运行，可使用：

```bash
docker build -t novel-reminder .
docker run -d \
	--name novel-reminder \
	--restart always \
	--env-file .env \
	-v $(pwd)/data:/app/data \
	novel-reminder
```

示例：

```ini
[Unit]
Description=Novel Reminder
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/NovelReminder
EnvironmentFile=/path/to/NovelReminder/.env
ExecStart=/usr/bin/python3 -m src.main run-loop
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## 首次上线建议

首次启动建议先执行一次 `show-state` 和一次 `run-once`，确认配置中的小说都能正常抓取后，再开启 `run-loop`。
