/**
 * PWA更新管理模块
 * 处理应用更新检测、更新通知和更新流程
 */
export class PWAUpdate {
    constructor() {
        this.currentVersion = '1.4.0'; // 当前应用版本
        this.updateAvailable = false;
        this.updateModal = null;
        this.updateBanner = null;
        this.skipVersion = null;
        
        this.init();
    }

    /**
     * 初始化更新检测
     */
    init() {
        // 监听service worker的更新事件
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.addEventListener('controllerchange', () => {
                this.onControllerChanged();
            });

            // 监听来自service worker的更新消息
            navigator.serviceWorker.addEventListener('message', (event) => {
                this.handleServiceWorkerMessage(event);
            });
        }

        // 页面加载完成后检查更新
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.checkForUpdates();
            });
        } else {
            this.checkForUpdates();
        }

        // 定期检查更新（每30分钟）
        setInterval(() => {
            this.checkForUpdates();
        }, 30 * 60 * 1000);
    }

    /**
     * 检查应用更新
     */
    async checkForUpdates() {
        try {
            if (!('serviceWorker' in navigator)) {
                return;
            }

            const registration = await navigator.serviceWorker.ready;
            
            // 检查是否有新版本的service worker
            if (registration.waiting) {
                this.updateAvailable = true;
                this.showUpdateNotification();
                return;
            }

            // 触发service worker检查更新
            if (registration.active) {
                registration.active.postMessage({
                    type: 'check-updates',
                    version: this.currentVersion
                });
            }

        } catch (error) {
            console.error('检查更新失败:', error);
        }
    }

    /**
     * 处理service worker消息
     */
    handleServiceWorkerMessage(event) {
        const { type, data } = event.data;

        switch (type) {
            case 'update-available':
                this.onUpdateAvailable(data);
                break;
            case 'update-not-available':
                console.log('应用已是最新版本');
                break;
            case 'update-downloaded':
                this.onUpdateDownloaded(data);
                break;
            default:
                break;
        }
    }

    /**
     * 有新版本可用
     */
    onUpdateAvailable(data) {
        console.log('发现新版本:', data);
        this.updateAvailable = true;
        
        // 检查用户是否跳过此版本
        const skippedVersion = localStorage.getItem('pwa_skip_version');
        if (skippedVersion === data.version) {
            console.log('用户已跳过此版本:', data.version);
            return;
        }

        this.showUpdateNotification(data);
    }

    /**
     * 更新下载完成
     */
    onUpdateDownloaded(data) {
        console.log('更新下载完成:', data);
        this.showUpdateReadyNotification(data);
    }

    /**
     * 显示更新通知
     */
    showUpdateNotification(updateInfo = {}) {
        // 如果已经显示了更新通知，则不重复显示
        if (document.getElementById('pwa-update-banner')) {
            return;
        }

        const banner = document.createElement('div');
        banner.id = 'pwa-update-banner';
        banner.className = 'fixed bottom-4 right-4 bg-gradient-to-r from-green-600 to-teal-600 text-white p-4 rounded-lg shadow-xl z-50 max-w-sm transform transition-all duration-300 translate-y-0 scale-95';
        banner.innerHTML = `
            <div class="flex items-start space-x-3">
                <div class="flex-shrink-0">
                    <i class="fas fa-download text-xl"></i>
                </div>
                <div class="flex-1">
                    <h4 class="text-sm font-medium mb-1">发现新版本</h4>
                    <p class="text-xs opacity-90 mb-3">
                        ${updateInfo.changelog ? updateInfo.changelog : '应用有新版本可用，包含性能改进和bug修复。'}
                    </p>
                    <div class="flex space-x-2">
                        <button id="pwa-update-btn" class="bg-white text-green-600 px-3 py-1 rounded text-xs font-medium hover:bg-green-50 transition-colors">
                            立即更新
                        </button>
                        <button id="pwa-update-later" class="text-white hover:text-gray-200 px-3 py-1 rounded text-xs font-medium transition-colors">
                            稍后
                        </button>
                        <button id="pwa-update-skip" class="text-white hover:text-gray-200 px-3 py-1 rounded text-xs font-medium transition-colors">
                            跳过此版本
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(banner);

        // 绑定事件
        document.getElementById('pwa-update-btn').addEventListener('click', () => {
            this.applyUpdate();
        });

        document.getElementById('pwa-update-later').addEventListener('click', () => {
            this.dismissUpdateBanner();
        });

        document.getElementById('pwa-update-skip').addEventListener('click', () => {
            this.skipVersion(updateInfo.version || 'latest');
        });

        // 动画显示
        setTimeout(() => {
            banner.classList.remove('scale-95');
            banner.classList.add('scale-100');
        }, 100);

        // 10秒后自动隐藏（除非用户正在交互）
        setTimeout(() => {
            if (document.getElementById('pwa-update-banner')) {
                this.dismissUpdateBanner();
            }
        }, 10000);
    }

    /**
     * 显示更新就绪通知
     */
    showUpdateReadyNotification(updateInfo = {}) {
        const modal = document.createElement('div');
        modal.id = 'pwa-update-modal';
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl max-w-md w-full transform transition-all duration-300 scale-95">
                <div class="p-6">
                    <div class="flex items-center mb-4">
                        <div class="flex-shrink-0">
                            <div class="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                                <i class="fas fa-check text-green-600 text-xl"></i>
                            </div>
                        </div>
                        <div class="ml-4">
                            <h3 class="text-lg font-medium text-gray-900">更新已准备就绪</h3>
                            <p class="text-sm text-gray-500">新版本已下载完成</p>
                        </div>
                    </div>
                    
                    <div class="mb-6">
                        <p class="text-sm text-gray-600 mb-3">
                            应用已下载最新版本，重启后即可应用更新。
                        </p>
                        ${updateInfo.changelog ? `
                            <div class="bg-gray-50 rounded p-3">
                                <h4 class="text-xs font-medium text-gray-700 mb-2">更新内容:</h4>
                                <ul class="text-xs text-gray-600 space-y-1">
                                    ${updateInfo.changelog.split('\n').map(item => `<li>• ${item}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                    </div>
                    
                    <div class="flex space-x-3">
                        <button id="pwa-restart-btn" class="flex-1 bg-green-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-green-700 transition-colors">
                            立即重启
                        </button>
                        <button id="pwa-restart-later" class="flex-1 bg-gray-200 text-gray-800 px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-300 transition-colors">
                            稍后重启
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // 绑定事件
        document.getElementById('pwa-restart-btn').addEventListener('click', () => {
            this.restartApplication();
        });

        document.getElementById('pwa-restart-later').addEventListener('click', () => {
            this.dismissUpdateModal();
        });

        // 动画显示
        setTimeout(() => {
            modal.querySelector('.bg-white').classList.remove('scale-95');
            modal.querySelector('.bg-white').classList.add('scale-100');
        }, 100);
    }

    /**
     * 应用更新
     */
    async applyUpdate() {
        try {
            Toast.info('正在准备更新...');
            
            // 通知service worker跳过等待
            if ('serviceWorker' in navigator) {
                const registration = await navigator.serviceWorker.ready;
                if (registration.waiting) {
                    registration.waiting.postMessage({ type: 'skip-waiting' });
                }
            }
        } catch (error) {
            console.error('应用更新失败:', error);
            Toast.error('更新失败，请刷新页面重试');
        }
    }

    /**
     * 重启应用
     */
    restartApplication() {
        // 清理更新相关的UI
        this.dismissUpdateModal();
        this.dismissUpdateBanner();
        
        // 显示重启提示
        Toast.info('应用正在重启...');
        
        // 延迟刷新，让提示显示
        setTimeout(() => {
            window.location.reload();
        }, 1000);
    }

    /**
     * 控制器变更处理（service worker激活）
     */
    onControllerChanged() {
        console.log('Service Worker控制器已变更，应用已更新');
        
        // 如果用户之前触发了更新，现在可以刷新页面
        if (this.updateAvailable) {
            this.restartApplication();
        }
    }

    /**
     * 隐藏更新横幅
     */
    dismissUpdateBanner() {
        const banner = document.getElementById('pwa-update-banner');
        if (banner) {
            banner.classList.add('scale-95');
            setTimeout(() => {
                banner.remove();
            }, 300);
        }
    }

    /**
     * 隐藏更新模态框
     */
    dismissUpdateModal() {
        const modal = document.getElementById('pwa-update-modal');
        if (modal) {
            modal.querySelector('.bg-white').classList.add('scale-95');
            setTimeout(() => {
                modal.remove();
            }, 300);
        }
    }

    /**
     * 跳过指定版本
     */
    skipVersion(version) {
        localStorage.setItem('pwa_skip_version', version);
        this.dismissUpdateBanner();
        Toast.info('已跳过此版本更新');
    }

    /**
     * 检查是否有可用更新
     */
    hasUpdate() {
        return this.updateAvailable;
    }

    /**
     * 获取更新状态
     */
    getUpdateStatus() {
        return {
            currentVersion: this.currentVersion,
            updateAvailable: this.updateAvailable,
            skippedVersion: localStorage.getItem('pwa_skip_version')
        };
    }
}
