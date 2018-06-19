# Deploy #

1. yum install nmap, redis, postgresql10-server
2. python3 -m venv venv
3. source venv\bin\activate
4. pip install -r requirements.txt
5. config
    shadow/config.py
        redis: line 25-30
        postgresql: line 21
6. export FLASK_APP=shadow
7. flask shadow init-db
8. flask auth create-user --is_super
9. flask run --host 0.0.0.0 --port 8888
10. flask schedule start-schedule
11. flask schedule start-executor --ident ident --host host --port port --type [2|3] --concurrent 5
    ident: 进程标识(每台机器唯一)
    host: web host
    port: web port
    type: 2 资产扫描进程
    type: 3 漏洞扫描进程
    concurrent: 5 执行线程数量

12. 配置插件
    http_header:
        {"flags":{"key":"server", "value" : "SimpleHTTP","type":"header"},"port":8888}

    http_status_code:
        {"flags":{"status_code" : [200],"type":"status_code"},"port":8888}

    http_response_body:
        {"flags":{"body" : "bash","type":"response_body"},"port":8888}

    script:
        ssh_weak_password
        {"passwords":"__PASSWORDS__","usernames":["root"]}

        __PASSWORDS__: ["123456"]

13. 下发任务
# redis #

shadow:job:preprocess => list, 作业ID队列
shadow:job:content:{id} => dict, 作业内容
shadow:job:doing => list, 作业基本信息队列 {id}
shadow:job:{discover}:{id} => zset, 子作业, 用于发现类任务并发控制
shadow:job:{check}:{id} => zset, 子作业, 用于检查类任务并发控制
shadow:job:executor:{type}:{ident} => list, 执行器队列
shadow:job:result => list, 作业结果队列
shadow:job:executor:running => hash, 执行器正在执行任务记录
shadow:plugin:sys_vul:{ident} => hash, 插件配置
shadow:plugin:config:{ident} => hash, 插件参数配置

# job #

SYS_VULSCAN => 系统漏洞扫描
SYS_ASSET_DISCOVER = 系统资产发现
SYS_VUL_CHECK = 系统漏洞检测
WEB_VULSCAN = web漏洞扫描
WEB_ASSET_DISCOVER = web资产发现（爬虫）
WEB_VUL_CHECK = web漏洞检查

job_params
创建作业:
   
        {
            'ip' : '1.1.1.1,1.1.2.1/24,1.1.3.1-1.1.1.3.255',
            'concurrent' : {
                'discover' : 5,
                'check' : 5,
            },
            'plugins': ['ssh_weak_password', 'http_response']
        }

资产发现
    {
        'ip' : '1.1.1.1-1.1.1.10,1.1.3.1-1.1.1.3.255',
    }

漏洞扫描
    {
        'ip' : '1.1.1.1',
        'plugins': ['ssh_weak_password', 'http_response']
    }

# result #

资产发现
[
    {
    	'key' : ''
        'ip' : '',
        'name' : '',
        'mac' : '',
        'os' : '',
        'apps' : [
            {
                'name' : '',
                'port' : '',
                'version' : '',
		'protocol' : '',
		'product' : '',
		'state' : ''
            },
        ]
    }
]

漏洞扫描
[
    {
        "key": "112.74.164.107", 
            "ssh_weak_password": {
                "payloads": {"username": "root", "password": "123456"}
            },
            "http_header": {
                "payloads": {"header": "Server", "value": "SimpleHTTP/0.6 Python/3.6.1"
            }
        }
    }
]


流程说明:
1. 用户填写ip范围，扫描插件，并发配置等参数进行下发任务
2. flask-web接收并检查参数后将作业存储到db, 同时通过redis的preprocess队列通知后台schedule进程进行调度
3. schedule.preprocess监听队列shadow:job:preprocess, 根据任务ID查找任务详情，根据任务类型调用不同的processor对任务进行处理
4. processor.proprocess对下发任务ip进行拆分(拆分个数，并发数量*2)，并存储子任务到db, 通知更新到redis的shadow:job:{check/discover}:{id}中，并将父job更新到redis的doing队列
5. schedule.dispatch监听shadow:job:doing根据shadow:job:{check/discover}:{id}记录的任务状态将任务下发给不同的redis队列(shadow:job:executor:{type}:{ident})供execute获取任务并执行
6. execute监听shadow:job:executor:{type}:{ident}队列，并获取任务后plugin进行执行，并将结果塞回到shadow:job:result
7. schedule.result监听shadow:job:result队列，并调用processor.result对任务结果进行处理(包括存储任务结果，任务状态更新，资产存储，漏洞存储等功能)