/**
 * 骨架屏和加载状态管理模块
 * 提供各种页面的骨架屏效果和加载状态优化
 */
export class PWASkeleton {
    constructor() {
        this.skeletonTypes = {
            book: 'book-skeleton',
            search: 'search-skeleton',
            task: 'task-skeleton',
            stats: 'stats-skeleton',
            chapter: 'chapter-skeleton'
        };
        
        this.init();
    }

    /**
     * 初始化骨架屏系统
     */
    init() {
        // 监听页面加载事件，显示骨架屏
        this.setupPageLoadSkeletons();
        
        // 监听API请求，显示加载状态
        this.setupAPILoading();
        
        // 监听页面切换，添加过渡效果
        this.setupPageTransitions();
        
        // 监听浏览器导航事件
        this.setupNavigationHandling();
    }

    /**
     * 设置页面加载骨架屏
     */
    setupPageLoadSkeletons() {
        // 页面内容加载完成后隐藏骨架屏
        window.addEventListener('load', () => {
            setTimeout(() => {
                this.hideAllSkeletons();
            }, 500);
        });
    }

    /**
     * 处理页面骨架屏显示逻辑
     */
    handlePageSkeletons() {
        const currentPath = window.location.pathname;
        
        // 先隐藏所有现有的骨架屏
        this.hideAllSkeletons();
        
        // 延迟显示骨架屏，确保Alpine.js有足够时间初始化
        setTimeout(() => {
            // 只在容器为空或内容尚未加载时显示骨架屏
            if (currentPath === '/') {
                this.showStatsSkeletonIfNeeded();
            } else if (currentPath === '/books') {
                this.showBookListSkeletonIfNeeded();
            } else if (currentPath === '/search') {
                this.showSearchSkeletonIfNeeded();
            } else if (currentPath === '/tasks') {
                this.showTaskListSkeletonIfNeeded();
            } else if (currentPath.startsWith('/book/')) {
                this.showBookDetailSkeletonIfNeeded();
            }
        }, 100); // 100ms延迟，给Alpine.js初始化时间

        // 设置超时隐藏骨架屏，确保即使内容加载失败也能隐藏
        setTimeout(() => {
            this.hideAllSkeletons();
        }, 2000);
    }

    /**
     * 设置API加载状态
     */
    setupAPILoading() {
        // 拦截fetch请求，显示加载状态
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            const url = args[0];
            
            // 只对API请求显示加载状态
            if (typeof url === 'string' && url.includes('/api/')) {
                this.showAPILoading(url);
            }
            
            try {
                const response = await originalFetch(...args);
                this.hideAPILoading(url);
                return response;
            } catch (error) {
                this.hideAPILoading(url);
                throw error;
            }
        };
    }

    /**
     * 设置页面切换过渡效果
     */
    setupPageTransitions() {
        // 监听页面导航
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a');
            if (link && link.href && link.origin === window.location.origin) {
                // 检查是否是外部链接或特殊链接
                const href = link.getAttribute('href');
                if (href && !href.startsWith('#') && !href.startsWith('javascript:')) {
                    e.preventDefault();
                    this.navigateWithTransition(link.href);
                }
            }
        });
    }

    /**
     * 设置浏览器导航处理
     */
    setupNavigationHandling() {
        // 监听浏览器前进/后退按钮
        window.addEventListener('popstate', (e) => {
            // 延迟处理，确保DOM已更新
            setTimeout(() => {
                this.handlePageSkeletons();
            }, 50);
        });

        // 监听页面可见性变化
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                // 页面变为可见时，检查并隐藏骨架屏
                setTimeout(() => {
                    this.hideAllSkeletons();
                }, 100);
            }
        });

        // 监听页面内容变化（用于SPA导航）
        const observer = new MutationObserver((mutations) => {
            let shouldHideSkeletons = false;
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList') {
                    // 检查是否有新的内容被添加
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            // 检查是否是主要内容区域的变化
                            if (node.matches && node.matches('[x-data]')) {
                                shouldHideSkeletons = true;
                            }
                            // 检查子元素
                            const contentElements = node.querySelectorAll && node.querySelectorAll('[x-data]');
                            if (contentElements && contentElements.length > 0) {
                                shouldHideSkeletons = true;
                            }
                        }
                    });
                }
            });
            
            if (shouldHideSkeletons) {
                setTimeout(() => {
                    this.hideAllSkeletons();
                }, 200);
            }
        });

        // 观察主要内容区域的变化
        const mainContent = document.querySelector('main');
        if (mainContent) {
            observer.observe(mainContent, {
                childList: true,
                subtree: true
            });
        }

        // 初始处理
        setTimeout(() => {
            this.handlePageSkeletons();
        }, 100);
    }

    /**
     * 带过渡效果的页面导航
     */
    async navigateWithTransition(url) {
        // 隐藏当前页面的骨架屏
        this.hideAllSkeletons();
        
        // 显示页面切换动画
        this.showPageTransition();
        
        // 延迟导航，让动画显示
        setTimeout(() => {
            window.location.href = url;
        }, 300);
    }

    /**
     * 显示页面切换动画
     */
    showPageTransition() {
        const transition = document.createElement('div');
        transition.id = 'page-transition';
        transition.className = 'fixed inset-0 bg-white z-50 flex items-center justify-center';
        transition.innerHTML = `
            <div class="text-center">
                <div class="inline-flex items-center justify-center w-16 h-16 bg-blue-50 rounded-full mb-4">
                    <i class="fas fa-book-reader text-blue-600 text-2xl animate-pulse"></i>
                </div>
                <div class="animate-pulse">
                    <div class="h-4 bg-gray-200 rounded w-32 mx-auto mb-2"></div>
                    <div class="h-3 bg-gray-200 rounded w-24 mx-auto"></div>
                </div>
            </div>
        `;

        document.body.appendChild(transition);
    }

    /**
     * 显示书籍列表骨架屏（仅在需要时）
     */
    showBookListSkeletonIfNeeded() {
        const container = document.querySelector('[x-data="booksList()"] .space-y-4');
        if (!container) return;

        // 检查容器是否为空或内容尚未加载
        const hasContent = container.querySelector('[x-for]') || container.children.length > 0;
        if (hasContent) return;

        const skeletonHTML = Array(3).fill(0).map(() => `
            <div class="border rounded-lg p-4 animate-pulse skeleton-placeholder">
                <div class="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4">
                    <div class="flex-1 min-w-0">
                        <div class="flex flex-wrap items-center gap-2 mb-2">
                            <div class="h-6 bg-gray-200 rounded w-32"></div>
                            <div class="h-5 bg-gray-200 rounded w-16"></div>
                        </div>
                        <div class="flex items-center space-x-4 text-sm">
                            <div class="h-4 bg-gray-200 rounded w-20"></div>
                            <div class="h-4 bg-gray-200 rounded w-16"></div>
                            <div class="h-4 bg-gray-200 rounded w-12"></div>
                        </div>
                    </div>
                    <div class="flex space-x-2">
                        <div class="h-8 bg-gray-200 rounded w-20"></div>
                        <div class="h-8 bg-gray-200 rounded w-16"></div>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = skeletonHTML;
    }

    /**
     * 显示书籍列表骨架屏（保留原方法以兼容其他调用）
     */
    showBookListSkeleton() {
        this.showBookListSkeletonIfNeeded();
    }

    /**
     * 显示搜索页面骨架屏（仅在需要时）
     */
    showSearchSkeletonIfNeeded() {
        // 搜索结果骨架屏
        const resultsContainer = document.querySelector('.grid.grid-cols-1.gap-4');
        if (!resultsContainer) return;

        // 检查容器是否为空或内容尚未加载
        const hasContent = resultsContainer.querySelector('[x-for]') || resultsContainer.children.length > 0;
        if (hasContent) return;

        const skeletonHTML = Array(3).fill(0).map(() => `
            <div class="group relative bg-white border border-gray-200 rounded-xl p-4 animate-pulse skeleton-placeholder">
                <div class="flex gap-5">
                    <div class="hidden sm:flex flex-shrink-0 w-20 h-28 bg-gray-200 rounded-lg"></div>
                    <div class="flex-1 min-w-0 py-1">
                        <div class="flex justify-between items-start gap-4 mb-2">
                            <div class="h-6 bg-gray-200 rounded w-48"></div>
                            <div class="h-5 bg-gray-200 rounded w-20"></div>
                        </div>
                        <div class="flex items-center text-sm text-gray-500 space-x-4 mb-3">
                            <div class="h-4 bg-gray-200 rounded w-16"></div>
                            <div class="h-4 bg-gray-200 rounded w-20"></div>
                        </div>
                        <div class="space-y-2 mb-4">
                            <div class="h-3 bg-gray-200 rounded w-full"></div>
                            <div class="h-3 bg-gray-200 rounded w-3/4"></div>
                        </div>
                        <div class="flex justify-end">
                            <div class="h-8 bg-gray-200 rounded w-24"></div>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        resultsContainer.innerHTML = skeletonHTML;
    }

    /**
     * 显示搜索页面骨架屏（保留原方法以兼容其他调用）
     */
    showSearchSkeleton() {
        this.showSearchSkeletonIfNeeded();
    }

    /**
     * 显示任务列表骨架屏（仅在需要时）
     */
    showTaskListSkeletonIfNeeded() {
        const container = document.querySelector('[x-data="tasksList()"] .space-y-4');
        if (!container) return;

        // 检查容器是否为空或内容尚未加载
        const hasContent = container.querySelector('[x-for]') || container.children.length > 0;
        if (hasContent) return;

        const skeletonHTML = Array(3).fill(0).map(() => `
            <div class="border rounded-lg p-4 animate-pulse skeleton-placeholder">
                <div class="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-3 mb-3">
                    <div class="flex-1 min-w-0">
                        <div class="flex flex-wrap items-center gap-2 mb-2">
                            <div class="h-5 bg-gray-200 rounded w-32"></div>
                            <div class="h-5 bg-gray-200 rounded w-20"></div>
                            <div class="h-5 bg-gray-200 rounded w-16"></div>
                        </div>
                        <div class="h-4 bg-gray-200 rounded w-40"></div>
                    </div>
                    <div class="h-8 bg-gray-200 rounded w-16"></div>
                </div>
                <div class="mb-3">
                    <div class="flex justify-between text-sm mb-1">
                        <div class="h-4 bg-gray-200 rounded w-12"></div>
                        <div class="h-4 bg-gray-200 rounded w-8"></div>
                    </div>
                    <div class="w-full bg-gray-200 rounded-full h-2">
                        <div class="bg-blue-200 h-2 rounded-full w-3/4"></div>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = skeletonHTML;
    }

    /**
     * 显示任务列表骨架屏（保留原方法以兼容其他调用）
     */
    showTaskListSkeleton() {
        this.showTaskListSkeletonIfNeeded();
    }

    /**
     * 显示统计数据骨架屏（仅在需要时）
     */
    showStatsSkeletonIfNeeded() {
        const container = document.querySelector('[x-data="stats()"] .grid.grid-cols-1');
        if (!container) return;

        // 检查容器是否为空或内容尚未加载
        const hasContent = container.children.length > 0 && !container.querySelector('.skeleton-placeholder');
        if (hasContent) return;

        const skeletonHTML = Array(3).fill(0).map(() => `
            <div class="bg-gray-50 overflow-hidden shadow rounded-lg animate-pulse skeleton-placeholder">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <div class="w-10 h-10 bg-gray-200 rounded-full"></div>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <div class="h-4 bg-gray-200 rounded w-20 mb-1"></div>
                            <div class="h-6 bg-gray-200 rounded w-12"></div>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = skeletonHTML;
    }

    /**
     * 显示统计数据骨架屏（保留原方法以兼容其他调用）
     */
    showStatsSkeleton() {
        this.showStatsSkeletonIfNeeded();
    }

    /**
     * 显示书籍详情骨架屏（仅在需要时）
     */
    showBookDetailSkeletonIfNeeded() {
        const container = document.querySelector('[x-data="bookDetail()"]');
        if (!container) return;

        // 检查容器是否为空或内容尚未加载
        const hasContent = container.children.length > 0 && !container.querySelector('.skeleton-placeholder');
        if (hasContent) return;

        container.innerHTML = `
            <div class="animate-pulse skeleton-placeholder">
                <div class="flex flex-col sm:flex-row items-center sm:items-start space-y-4 sm:space-y-0 sm:space-x-6 mb-6">
                    <div class="flex-shrink-0">
                        <div class="w-32 h-44 bg-gray-200 rounded-lg"></div>
                    </div>
                    <div class="flex-1 text-center sm:text-left w-full">
                        <div class="h-8 bg-gray-200 rounded w-64 mb-2"></div>
                        <div class="h-5 bg-gray-200 rounded w-24 mb-3"></div>
                        <div class="grid grid-cols-2 gap-2 sm:gap-4 text-sm mb-4">
                            <div class="h-4 bg-gray-200 rounded w-20"></div>
                            <div class="h-4 bg-gray-200 rounded w-20"></div>
                            <div class="h-4 bg-gray-200 rounded w-16"></div>
                            <div class="h-4 bg-gray-200 rounded w-16"></div>
                        </div>
                        <div class="flex flex-wrap gap-2">
                            <div class="h-8 bg-gray-200 rounded w-24"></div>
                            <div class="h-8 bg-gray-200 rounded w-20"></div>
                            <div class="h-8 bg-gray-200 rounded w-20"></div>
                            <div class="h-8 bg-gray-200 rounded w-20"></div>
                        </div>
                    </div>
                </div>
                
                <div class="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6">
                    <div class="flex items-center mb-3">
                        <div class="w-5 h-5 bg-gray-200 rounded-full mr-3"></div>
                        <div class="flex-1">
                            <div class="h-4 bg-gray-200 rounded w-32 mb-1"></div>
                            <div class="h-3 bg-gray-200 rounded w-24"></div>
                        </div>
                    </div>
                    <div class="w-full bg-gray-200 rounded-full h-2">
                        <div class="bg-blue-200 h-2 rounded-full w-3/4"></div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 显示书籍详情骨架屏（保留原方法以兼容其他调用）
     */
    showBookDetailSkeleton() {
        this.showBookDetailSkeletonIfNeeded();
    }

    /**
     * 显示API加载状态
     */
    showAPILoading(url) {
        // 根据API端点显示不同的加载状态
        if (url.includes('/books/search')) {
            this.showSearchLoading();
        } else if (url.includes('/books')) {
            this.showBookLoading();
        } else if (url.includes('/tasks')) {
            this.showTaskLoading();
        }
    }

    /**
     * 隐藏API加载状态
     */
    hideAPILoading(url) {
        // 这里可以添加隐藏特定加载状态的逻辑
    }

    /**
     * 显示搜索加载状态
     */
    showSearchLoading() {
        const button = document.querySelector('button[onclick*="search()"]');
        if (button) {
            const originalContent = button.innerHTML;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 搜索中...';
            button.disabled = true;
            
            // 恢复按钮状态（5秒后超时）
            setTimeout(() => {
                button.innerHTML = originalContent;
                button.disabled = false;
            }, 5000);
        }
    }

    /**
     * 显示书籍加载状态
     */
    showBookLoading() {
        // 可以添加书籍特定的加载状态
    }

    /**
     * 显示任务加载状态
     */
    showTaskLoading() {
        // 可以添加任务特定的加载状态
    }

    /**
     * 隐藏所有骨架屏
     */
    hideAllSkeletons() {
        // 移除页面切换动画
        const transition = document.getElementById('page-transition');
        if (transition) {
            transition.remove();
        }

        // 移除所有骨架屏占位符
        const skeletonPlaceholders = document.querySelectorAll('.skeleton-placeholder');
        skeletonPlaceholders.forEach(element => {
            element.remove();
        });

        // 清空可能被骨架屏替换的容器
        const containers = [
            '[x-data="booksList()"] .space-y-4',
            '.grid.grid-cols-1.gap-4',
            '[x-data="tasksList()"] .space-y-4',
            '[x-data="stats()"] .grid.grid-cols-1',
            '[x-data="bookDetail()"]'
        ];

        containers.forEach(selector => {
            const container = document.querySelector(selector);
            if (container) {
                // 检查容器是否只包含骨架屏
                const hasOnlySkeletons = Array.from(container.children).every(child =>
                    child.classList.contains('skeleton-placeholder') ||
                    (child.classList.contains('animate-pulse') && child.innerHTML && child.innerHTML.includes('bg-gray-200'))
                );
                
                if (hasOnlySkeletons) {
                    // 清空容器以便Alpine.js重新渲染
                    container.innerHTML = '';
                }
            }
        });
    }

    /**
     * 创建通用骨架屏元素
     */
    createSkeletonElement(type, className = '') {
        const skeleton = document.createElement('div');
        skeleton.className = `skeleton ${type} ${className} animate-pulse`;
        return skeleton;
    }

    /**
     * 创建文本骨架屏
     */
    createTextSkeleton(width = '100%', height = '1rem', className = '') {
        const skeleton = document.createElement('div');
        skeleton.className = `h-4 bg-gray-200 rounded ${className} animate-pulse`;
        skeleton.style.width = width;
        skeleton.style.height = height;
        return skeleton;
    }

    /**
     * 创建图片骨架屏
     */
    createImageSkeleton(width = '100%', height = '100%', className = '') {
        const skeleton = document.createElement('div');
        skeleton.className = `bg-gray-200 rounded ${className} animate-pulse flex items-center justify-center`;
        skeleton.style.width = width;
        skeleton.style.height = height;
        skeleton.innerHTML = '<i class="fas fa-image text-gray-400"></i>';
        return skeleton;
    }

    /**
     * 创建按钮骨架屏
     */
    createButtonSkeleton(width = 'auto', height = '2.5rem', className = '') {
        const skeleton = document.createElement('div');
        skeleton.className = `bg-gray-200 rounded ${className} animate-pulse`;
        skeleton.style.width = width;
        skeleton.style.height = height;
        return skeleton;
    }
}
