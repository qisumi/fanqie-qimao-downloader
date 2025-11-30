/**
 * PWA安装管理模块
 * 处理PWA安装提示、安装状态管理和安装引导
 */
export class PWAInstall {
    constructor() {
        this.deferredInstallPrompt = null;
        this.installButton = null;
        this.installBanner = null;
        this.isInstallable = false;
        this.isInstalled = this.checkInstalledStatus();
        
        this.init();
    }

    /**
     * 初始化PWA安装功能
     */
    init() {
        // 监听安装事件
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.deferredInstallPrompt = e;
            this.isInstallable = true;
            this.showInstallBanner();
        });

        // 监听安装完成事件
        window.addEventListener('appinstalled', () => {
            this.onInstallSuccess();
        });

        // 页面加载完成后检查是否需要显示安装提示
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.checkAndShowInstallPrompt();
            });
        } else {
            this.checkAndShowInstallPrompt();
        }
    }

    /**
     * 检查应用是否已安装
     */
    checkInstalledStatus() {
        // 检查是否在独立模式下运行（PWA安装后的特征）
        const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
        const isInWebAppiOS = (window.navigator.standalone === true);
        const isInWebAppChrome = (window.matchMedia('(display-mode: minimal-ui)').matches);
        
        const installed = isStandalone || isInWebAppiOS || isInWebAppChrome;
        
        // 从localStorage读取安装状态
        const storedStatus = localStorage.getItem('pwa_installed');
        if (installed || storedStatus === 'true') {
            localStorage.setItem('pwa_installed', 'true');
            localStorage.setItem('pwa_install_date', new Date().toISOString());
            return true;
        }
        
        return false;
    }

    /**
     * 检查并显示安装提示
     */
    checkAndShowInstallPrompt() {
        // 如果已安装或不可安装，则不显示
        if (this.isInstalled || !this.isInstallable) {
            return;
        }

        // 检查用户是否已经拒绝过安装
        const dismissedTime = localStorage.getItem('pwa_install_dismissed');
        if (dismissedTime) {
            const dismissedDate = new Date(dismissedTime);
            const now = new Date();
            const daysSinceDismissed = (now - dismissedDate) / (1000 * 60 * 60 * 24);
            
            // 如果用户在7天内拒绝过，则不显示
            if (daysSinceDismissed < 7) {
                return;
            }
        }

        // 延迟显示安装提示，让用户先熟悉应用
        setTimeout(() => {
            this.showInstallBanner();
        }, 3000);
    }

    /**
     * 显示安装横幅
     */
    showInstallBanner() {
        if (this.isInstalled || !this.isInstallable) return;

        // 创建安装横幅
        const banner = document.createElement('div');
        banner.id = 'pwa-install-banner';
        banner.className = 'fixed top-0 left-0 right-0 bg-gradient-to-r from-blue-600 to-purple-600 text-white p-3 shadow-lg z-50 transform transition-transform duration-300 translate-y-0';
        banner.innerHTML = `
            <div class="container mx-auto flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <div class="flex-shrink-0">
                        <i class="fas fa-download text-xl"></i>
                    </div>
                    <div>
                        <p class="text-sm font-medium">安装番茄七猫下载器</p>
                        <p class="text-xs opacity-90">离线使用，更快体验</p>
                    </div>
                </div>
                <div class="flex items-center space-x-2">
                    <button id="pwa-install-btn" class="bg-white text-blue-600 px-4 py-1.5 rounded-full text-sm font-medium hover:bg-blue-50 transition-colors">
                        安装
                    </button>
                    <button id="pwa-install-dismiss" class="text-white hover:text-gray-200 p-1.5 transition-colors">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(banner);

        // 绑定事件
        document.getElementById('pwa-install-btn').addEventListener('click', () => {
            this.install();
        });

        document.getElementById('pwa-install-dismiss').addEventListener('click', () => {
            this.dismissBanner();
        });

        // 动画显示
        setTimeout(() => {
            banner.classList.remove('translate-y-0');
            banner.classList.add('translate-y-0');
        }, 100);
    }

    /**
     * 隐藏安装横幅
     */
    dismissBanner() {
        const banner = document.getElementById('pwa-install-banner');
        if (banner) {
            banner.classList.add('translate-y-[-100%]');
            setTimeout(() => {
                banner.remove();
            }, 300);
        }

        // 记录用户拒绝的时间
        localStorage.setItem('pwa_install_dismissed', new Date().toISOString());
    }

    /**
     * 触发PWA安装
     */
    async install() {
        if (!this.deferredInstallPrompt) {
            console.warn('安装提示不可用');
            return;
        }

        try {
            // 显示安装按钮的加载状态
            const installBtn = document.getElementById('pwa-install-btn');
            if (installBtn) {
                installBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>安装中...';
                installBtn.disabled = true;
            }

            // 显示安装对话框
            this.deferredInstallPrompt.prompt();
            
            // 等待用户响应
            const { outcome } = await this.deferredInstallPrompt.userChoice;
            
            if (outcome === 'accepted') {
                console.log('用户接受了PWA安装');
                // 隐藏横幅
                this.dismissBanner();
                // 显示安装中提示
                this.showInstallProgress();
            } else {
                console.log('用户拒绝了PWA安装');
                // 记录拒绝状态
                localStorage.setItem('pwa_install_dismissed', new Date().toISOString());
            }

            // 清除安装提示
            this.deferredInstallPrompt = null;
            this.isInstallable = false;

        } catch (error) {
            console.error('PWA安装失败:', error);
            Toast.error('安装失败，请稍后重试');
            
            // 恢复按钮状态
            const installBtn = document.getElementById('pwa-install-btn');
            if (installBtn) {
                installBtn.innerHTML = '安装';
                installBtn.disabled = false;
            }
        }
    }

    /**
     * 显示安装进度提示
     */
    showInstallProgress() {
        const progress = document.createElement('div');
        progress.id = 'pwa-install-progress';
        progress.className = 'fixed top-0 left-0 right-0 bg-green-600 text-white p-3 shadow-lg z-50';
        progress.innerHTML = `
            <div class="container mx-auto flex items-center justify-center">
                <i class="fas fa-check-circle mr-2"></i>
                <span>应用安装成功！正在启动...</span>
            </div>
        `;

        document.body.appendChild(progress);

        // 3秒后自动消失
        setTimeout(() => {
            progress.remove();
        }, 3000);
    }

    /**
     * 安装成功处理
     */
    onInstallSuccess() {
        console.log('PWA安装成功');
        
        // 更新安装状态
        this.isInstalled = true;
        localStorage.setItem('pwa_installed', 'true');
        localStorage.setItem('pwa_install_date', new Date().toISOString());
        
        // 显示成功提示
        Toast.success('应用安装成功！现在可以从主屏幕快速访问了。');
        
        // 触发自定义事件
        window.dispatchEvent(new CustomEvent('pwa-installed', {
            detail: {
                installDate: new Date().toISOString()
            }
        }));
    }

    /**
     * 检查是否应该显示安装按钮
     */
    shouldShowInstallButton() {
        return this.isInstallable && !this.isInstalled;
    }

    /**
     * 获取安装状态信息
     */
    getInstallStatus() {
        return {
            isInstalled: this.isInstalled,
            isInstallable: this.isInstallable,
            installDate: localStorage.getItem('pwa_install_date'),
            dismissedDate: localStorage.getItem('pwa_install_dismissed')
        };
    }
}
