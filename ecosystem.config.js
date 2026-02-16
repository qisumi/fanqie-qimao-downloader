/**
 * PM2 配置文件 - FanqieQimaoDownloader
 * 
 * 使用方法:
 *   pm2 start ecosystem.config.js
 *   pm2 stop fanqie-downloader
 *   pm2 restart fanqie-downloader
 *   pm2 logs fanqie-downloader
 *   pm2 delete fanqie-downloader
 *   pm2 monit
 */

module.exports = {
  apps: [
    {
      // 应用名称
      name: 'fanqie-downloader',
      
      // 启动命令 - 使用 uvicorn 直接启动
      script: 'uvicorn',
      
      // 参数
      args: 'app.main:app --host 0.0.0.0 --port 4568 --workers 1',
      
      // 实例数量
      instances: 1,
      
      // 执行模式 (fork 或 cluster)
      exec_mode: 'fork',
      
      // 自动重启
      autorestart: true,
      
      // 启动延迟 (毫秒)
      wait_ready: true,
      
      // 监听文件变化 (生产环境建议关闭)
      watch: false,
      
      // 忽略监听的文件
      ignore_watch: [
        'node_modules',
        'logs',
        'data',
        'frontend/dist',
        '__pycache__',
        '.git',
        '*.pyc'
      ],
      
      // 最大内存重启 (MB)
      max_memory_restart: '1G',
      
      // 环境变量
      env: {
        NODE_ENV: 'production',
        PYTHONUNBUFFERED: '1'
      },
      
      // 开发环境变量
      env_development: {
        NODE_ENV: 'development',
        DEBUG: 'true'
      },
      
      // 日志配置
      error_file: './logs/pm2-error.log',
      out_file: './logs/pm2-out.log',
      log_file: './logs/pm2-combined.log',
      
      // 日志时间格式
      time: true,
      
      // 日志日期格式
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      
      // 合并日志
      merge_logs: true,
      
      // 日志轮转
      log_type: 'json',
      
      // 进程 ID 文件
      pid_file: './logs/pm2.pid',
      
      // 最小运行时间 (毫秒) - 防止频繁重启
      min_uptime: '10s',
      
      // 最大重启次数
      max_restarts: 10,
      
      // 重启延迟 (毫秒)
      restart_delay: 4000,
      
      // 杀死超时 (毫秒)
      kill_timeout: 5000,
      
      // 监听超时 (毫秒)
      listen_timeout: 10000,
      
      // 关闭超时 (毫秒)
      shutdown_with_message: true,
      
      // 解释器
      interpreter: 'python',
      
      // 解释器参数
      interpreter_args: '-m',
      
      // 工作目录
      cwd: process.cwd(),
      
      // 源映射支持
      source_map_support: true,
      
      // 禁用遥测
      disable_trace: true
    }
  ],
  
  // 部署配置 (可选)
  deploy: {
    production: {
      user: 'node',
      host: 'your-server.com',
      ref: 'origin/main',
      repo: 'git@github.com:your-username/fanqie-qimao-downloader.git',
      path: '/var/www/fanqie-downloader',
      'post-deploy': 'pip install -r requirements.txt && pm2 reload ecosystem.config.js --env production',
      'pre-setup': 'apt-get install git python3 python3-pip -y'
    },
    staging: {
      user: 'node',
      host: 'staging-server.com',
      ref: 'origin/develop',
      repo: 'git@github.com:your-username/fanqie-qimao-downloader.git',
      path: '/var/www/fanqie-downloader-staging',
      'post-deploy': 'pip install -r requirements.txt && pm2 reload ecosystem.config.js --env staging',
      'pre-setup': 'apt-get install git python3 python3-pip -y'
    }
  }
};
