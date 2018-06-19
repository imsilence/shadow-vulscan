# Deploy #

1. 3rd
    yum install nmap, redis, postgresql10-server
2. python环境
    python3 -m venv venv
    source venv\bin\activate
    pip install -r requirements.txt --timeout=300
3. 数据库
    create database shadow owner silence;
4. 配置(shadow/config.py)
    redis:
    postgresql:

5. chmod +x run.sh
6. ./run.sh shadow init-db #初始化数据库
7. ./run.sh auth create-user --is_super #创建用户
8. ./run.sh run --host 0.0.0.0 --port 8888 #启动web服务
9. ./run.sh schedule start-schedule #启动调度
10. ./run.sh schedule start-execute --host=localhost --port 8888 --type 2 --concurrent 5 #启动资产扫描程序
    资产发现使用nmap进行扫描, 扫描0-1024端口
11. ./run.sh schedule start-execute --host=localhost --port 8888 --type 3 --concurrent 5 #启动漏洞扫描程序
12. 创建插件&配置(见配置图片目录)
    a. ssh弱口令
        类型: script
        参数: {"usernames" : [], "passwords" : []}

        参数说明: usernames, passwords 为脚本执行中定义使用的暴力破解用户名和密码列表

    b. http_header
        类型: http/https请求
        参数: {"flags":{"key":"server","type":"header","value":"SimpleHTTP"},"port":8888}

    c. http_status
        类型: http/https请求
        参数: {"flags":{"status_code":[200],"type":"status_code"},"port":8888}

    d. http_response
        类型: http/https请求
        参数: {"flags":{"body":"bash","type":"response_body"},"port":8888}

        http/https请求参数说明:
        protocol: http/https, 默认http
        port:  请求端口，默认根据协议选择，http默认为80, https默认为443
        path: 请求路径, 默认/
        method: 请求方法, 默认GET
        cookies: 请求cookies，默认为{}
        args: url请求参数, 默认为{}
        body: body请求参数, 默认为{}
        headers: 请求headers， 默认为{}
        timeout: 请求超时时间, 默认5s
        flags: 检查方法, {"type" : "", "status_code" : [], "key" : "", "value" : "", "body" : ""}
            type: status_code, 其他值: status_code, 返回状态吗在status_code列表中则命中
            type: header, 其他值: key, value, 返回header中key的值中包含value则命中
            type: response_body, 其他值: body，返回response中包含body则命中

13. 启动测试环境server
    python3 -m http.server 8888

14. 在漏洞管理/任务管理 => 对目标进行扫描

15. 查看资产管理或漏洞管理/漏洞信息 
