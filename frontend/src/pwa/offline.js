/**
 * PWA离线状态管理模块
 * 处理网络状态检测、离线提示和离线功能
 */
export class PWAOffline {
    constructor() {
        this.isOnline = navigator.onLine;
        this.offlineIndicator = null;
        this.offlineModal = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = null;
        
        this.init();
    }

    /**
     * 初始化离线状态管理
     */
    init() {
        // 监听网络状态变化
        window.addEventListener('online', () => {
            this.onOnline();
        });

        window.addEventListener('offline', () => {
            this.onOffline();
        });

        // 监听页面可见性变化，重新检测网络状态
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.isOnline !== navigator.onLine) {
                this.isOnline = navigator.onLine;
                if (this.isOnline) {
                    this.onOnline();
                } else {
                    this.onOffline();
                }
            }
        });

        // 初始状态检查
        this.updateNetworkStatus();

        // 定期检查网络状态（每30秒）
        setInterval(() => {
            this.checkNetworkStatus();
        }, 30000);
    }

    /**
     * 网络连接恢复
     */
    onOnline() {
        console.log('网络连接已恢复');
        this.isOnline = true;
        
        // 清除重连尝试
        if (this.reconnectInterval) {
            clearInterval(this.reconnectInterval);
            this.reconnectInterval = null;
        }
        this.reconnectAttempts = 0;

        // 隐藏离线指示器
        this.hideOfflineIndicator();
        
        // 隐藏离线功能说明模态框（如果正在显示）
        if (this.offlineModal) {
            this.dismissOfflineFeatures();
        }
        
        // 显示恢复连接提示
        this.showOnlineNotification();
        
        // 触发自定义事件
        window.dispatchEvent(new CustomEvent('network-online', {
            detail: {
                timestamp: new Date().toISOString()
            }
        }));

        // 刷新页面数据
        this.refreshPageData();
    }

    /**
     * 网络连接断开
     */
    onOffline() {
        console.log('网络连接已断开');
        this.isOnline = false;
        
        // 显示离线指示器
        this.showOfflineIndicator();
        
        // 显示离线提示
        this.showOfflineNotification();
        
        // 触发自定义事件
        window.dispatchEvent(new CustomEvent('network-offline', {
            detail: {
                timestamp: new Date().toISOString()
            }
        }));
    }

    /**
     * 检查网络状态
     */
    async checkNetworkStatus() {
        try {
            // 尝试请求一个小资源来检测网络状态
            const response = await fetch('/health', {
                method: 'HEAD',
                cache: 'no-cache',
                timeout: 5000
            });
            
            const wasOffline = !this.isOnline;
            this.isOnline = response.ok;
            
            if (wasOffline && this.isOnline) {
                this.onOnline();
            } else if (!wasOffline && !this.isOnline) {
                this.onOffline();
            }
            
        } catch (error) {
            if (this.isOnline) {
                this.isOnline = false;
                this.onOffline();
            }
        }
    }

    /**
     * 更新网络状态
     */
    updateNetworkStatus() {
        this.isOnline = navigator.onLine;
        if (this.isOnline) {
            this.hideOfflineIndicator();
        } else {
            this.showOfflineIndicator();
        }
    }

    /**
     * 显示离线指示器
     */
    showOfflineIndicator() {
        if (this.offlineIndicator) {
            return; // 已显示
        }

        const indicator = document.createElement('div');
        indicator.id = 'offline-indicator';
        indicator.className = 'fixed top-0 left-0 right-0 bg-orange-500 text-white p-2 text-center text-sm z-50 transform transition-transform duration-300';
        indicator.innerHTML = `
            <div class="container mx-auto flex items-center justify-center">
                <i class="fas fa-wifi-slash mr-2"></i>
                <span>网络连接已断开，部分功能可能不可用</span>
            </div>
        `;

        document.body.appendChild(indicator);
        this.offlineIndicator = indicator;

        // 调整页面布局，为指示器留出空间
        document.body.style.paddingTop = '32px';

        // 动画显示
        setTimeout(() => {
            indicator.classList.remove('translate-y-[-100%]');
            indicator.classList.add('translate-y-0');
        }, 100);
    }

    /**
     * 隐藏离线指示器
     */
    hideOfflineIndicator() {
        const indicator = this.offlineIndicator || document.getElementById('offline-indicator');
        if (indicator) {
            indicator.classList.add('transform', 'translate-y-[-100%]');
            setTimeout(() => {
                indicator.remove();
                document.body.style.paddingTop = '';
                this.offlineIndicator = null;
            }, 300);
        }
    }

    /**
     * 显示离线通知
     */
    showOfflineNotification() {
        Toast.warning('网络连接已断开，正在尝试重新连接...', 5000);
        
        // 显示离线功能说明
        setTimeout(() => {
            this.showOfflineFeatures();
        }, 2000);
    }

    /**
     * 显示在线通知
     */
    showOnlineNotification() {
        Toast.success('网络连接已恢复！');
    }

    /**
     * 显示离线功能说明
     */
    showOfflineFeatures() {
        // 如果已经显示过离线功能说明或正在显示，则不重复显示
        if (localStorage.getItem('offline_features_shown') || this.offlineModal) {
            return;
        }

        const modal = document.createElement('div');
        modal.id = 'offline-features-modal';
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl max-w-md w-full transform transition-all duration-300 scale-95">
                <div class="p-6">
                    <div class="flex items-center mb-4">
                        <div class="flex-shrink-0">
                            <div class="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
                                <i class="fas fa-wifi-slash text-orange-600 text-xl"></i>
                            </div>
                        </div>
                        <div class="ml-4">
                            <h3 class="text-lg font-medium text-gray-900">离线模式</h3>
                            <p class="text-sm text-gray-500">部分功能仍可使用</p>
                        </div>
                    </div>
                    
                    <div class="mb-6">
                        <h4 class="text-sm font-medium text-gray-700 mb-3">离线可用功能:</h4>
                        <ul class="space-y-2">
                            <li class="flex items-start">
                                <i class="fas fa-check-circle text-green-500 mt-0.5 mr-2 flex-shrink-0"></i>
                                <span class="text-sm text-gray-600">查看已下载的书籍和章节</span>
                            </li>
                            <li class="flex items-start">
                                <i class="fas fa-check-circle text-green-500 mt-0.5 mr-2 flex-shrink-0"></i>
                                <span class="text-sm text-gray-600">浏览已缓存的搜索结果</span>
                            </li>
                            <li class="flex items-start">
                                <i class="fas fa-check-circle text-green-500 mt-0.5 mr-2 flex-shrink-0"></i>
                                <span class="text-sm text-gray-600">管理本地书籍和任务</span>
                            </li>
                        </ul>
                        
                        <h4 class="text-sm font-medium text-gray-700 mb-3 mt-4">暂时不可用功能:</h4>
                        <ul class="space-y-2">
                            <li class="flex items-start">
                                <i class="fas fa-times-circle text-red-500 mt-0.5 mr-2 flex-shrink-0"></i>
                                <span class="text-sm text-gray-600">搜索新书籍</span>
                            </li>
                            <li class="flex items-start">
                                <i class="fas fa-times-circle text-red-500 mt-0.5 mr-2 flex-shrink-0"></i>
                                <span class="text-sm text-gray-600">下载章节</span>
                            </li>
                            <li class="flex items-start">
                                <i class="fas fa-times-circle text-red-500 mt-0.5 mr-2 flex-shrink-0"></i>
                                <span class="text-sm text-gray-600">检查更新</span>
                            </li>
                        </ul>
                    </div>
                    
                    <div class="flex space-x-3">
                        <button id="offline-understand-btn" class="flex-1 bg-orange-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-orange-700 transition-colors">
                            我知道了
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        this.offlineModal = modal;

        // 绑定事件
        const understandBtn = document.getElementById('offline-understand-btn');
        if (understandBtn) {
            understandBtn.addEventListener('click', () => {
                this.dismissOfflineFeatures();
            });
        }

        // 点击背景关闭模态框
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.dismissOfflineFeatures();
            }
        });

        // ESC键关闭模态框
        const handleEscape = (e) => {
            if (e.key === 'Escape' && this.offlineModal) {
                this.dismissOfflineFeatures();
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);

        // 动画显示
        setTimeout(() => {
            const modalContent = modal.querySelector('.bg-white');
            if (modalContent) {
                modalContent.classList.remove('scale-95');
                modalContent.classList.add('scale-100');
            }
        }, 100);
    }

    /**
     * 隐藏离线功能说明
     */
    dismissOfflineFeatures() {
        const modal = this.offlineModal || document.getElementById('offline-features-modal');
        if (modal) {
            const modalContent = modal.querySelector('.bg-white');
            if (modalContent) {
                modalContent.classList.add('scale-95');
                modalContent.classList.remove('scale-100');
            }
            
            setTimeout(() => {
                if (modal && modal.parentNode) {
                    modal.remove();
                }
                this.offlineModal = null;
            }, 300);
        }
        
        // 记录已显示过
        localStorage.setItem('offline_features_shown', 'true');
    }

    /**
     * 刷新页面数据
     */
    refreshPageData() {
        // 触发页面数据刷新
        window.dispatchEvent(new CustomEvent('refresh-data', {
            detail: {
                reason: 'network-restored'
            }
        }));

        // 如果在特定页面，执行相应的刷新逻辑
        const currentPath = window.location.pathname;
        
        if (currentPath === '/') {
            // 首页：刷新统计数据
            if (typeof loadStats === 'function') {
                loadStats();
            }
        } else if (currentPath === '/books') {
            // 书籍页面：刷新书籍列表
            if (typeof loadBooks === 'function') {
                loadBooks();
            }
        } else if (currentPath.startsWith('/book/')) {
            // 书籍详情页：刷新书籍信息
            if (typeof loadBook === 'function') {
                loadBook();
            }
        }
    }

    /**
     * 开始重连尝试
     */
    startReconnectAttempts() {
        if (this.reconnectInterval) {
            return;
        }

        this.reconnectAttempts = 0;
        this.reconnectInterval = setInterval(() => {
            if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                clearInterval(this.reconnectInterval);
                this.reconnectInterval = null;
                return;
            }

            this.reconnectAttempts++;
            console.log(`尝试重新连接网络 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            this.checkNetworkStatus();
        }, 5000);
    }

    /**
     * 获取网络状态
     */
    getNetworkStatus() {
        return {
            isOnline: this.isOnline,
            connectionType: this.getConnectionType(),
            effectiveType: this.getEffectiveType()
        };
    }

    /**
     * 获取连接类型
     */
    getConnectionType() {
        if ('connection' in navigator) {
            return navigator.connection.effectiveType || 'unknown';
        }
        return 'unknown';
    }

    /**
     * 获取有效连接类型
     */
    getEffectiveType() {
        if ('connection' in navigator) {
            return navigator.connection.effectiveType || 'unknown';
        }
        return 'unknown';
    }

    /**
     * 检查是否为慢速网络
     */
    isSlowNetwork() {
        const effectiveType = this.getEffectiveType();
        return effectiveType === 'slow-2g' || effectiveType === '2g';
    }

    /**
     * 检查是否为节省数据模式
     */
    isDataSaverMode() {
        if ('connection' in navigator) {
            return navigator.connection.saveData || false;
        }
        return false;
    }
}
