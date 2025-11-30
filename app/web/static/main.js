class r{constructor(){this.deferredInstallPrompt=null,this.installButton=null,this.installBanner=null,this.isInstallable=!1,this.isInstalled=this.checkInstalledStatus(),this.init()}init(){window.addEventListener("beforeinstallprompt",e=>{e.preventDefault(),this.deferredInstallPrompt=e,this.isInstallable=!0,this.showInstallBanner()}),window.addEventListener("appinstalled",()=>{this.onInstallSuccess()}),document.readyState==="loading"?document.addEventListener("DOMContentLoaded",()=>{this.checkAndShowInstallPrompt()}):this.checkAndShowInstallPrompt()}checkInstalledStatus(){const e=window.matchMedia("(display-mode: standalone)").matches,t=window.navigator.standalone===!0,s=window.matchMedia("(display-mode: minimal-ui)").matches,i=e||t||s,n=localStorage.getItem("pwa_installed");return i||n==="true"?(localStorage.setItem("pwa_installed","true"),localStorage.setItem("pwa_install_date",new Date().toISOString()),!0):!1}checkAndShowInstallPrompt(){if(this.isInstalled||!this.isInstallable)return;const e=localStorage.getItem("pwa_install_dismissed");if(e){const t=new Date(e);if((new Date-t)/(1e3*60*60*24)<7)return}setTimeout(()=>{this.showInstallBanner()},3e3)}showInstallBanner(){if(this.isInstalled||!this.isInstallable)return;const e=document.createElement("div");e.id="pwa-install-banner",e.className="fixed top-0 left-0 right-0 bg-gradient-to-r from-blue-600 to-purple-600 text-white p-3 shadow-lg z-50 transform transition-transform duration-300 translate-y-0",e.innerHTML=`
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
        `,document.body.appendChild(e),document.getElementById("pwa-install-btn").addEventListener("click",()=>{this.install()}),document.getElementById("pwa-install-dismiss").addEventListener("click",()=>{this.dismissBanner()}),setTimeout(()=>{e.classList.remove("translate-y-0"),e.classList.add("translate-y-0")},100)}dismissBanner(){const e=document.getElementById("pwa-install-banner");e&&(e.classList.add("translate-y-[-100%]"),setTimeout(()=>{e.remove()},300)),localStorage.setItem("pwa_install_dismissed",new Date().toISOString())}async install(){if(!this.deferredInstallPrompt){console.warn("安装提示不可用");return}try{const e=document.getElementById("pwa-install-btn");e&&(e.innerHTML='<i class="fas fa-spinner fa-spin mr-1"></i>安装中...',e.disabled=!0),this.deferredInstallPrompt.prompt();const{outcome:t}=await this.deferredInstallPrompt.userChoice;t==="accepted"?(console.log("用户接受了PWA安装"),this.dismissBanner(),this.showInstallProgress()):(console.log("用户拒绝了PWA安装"),localStorage.setItem("pwa_install_dismissed",new Date().toISOString())),this.deferredInstallPrompt=null,this.isInstallable=!1}catch(e){console.error("PWA安装失败:",e),Toast.error("安装失败，请稍后重试");const t=document.getElementById("pwa-install-btn");t&&(t.innerHTML="安装",t.disabled=!1)}}showInstallProgress(){const e=document.createElement("div");e.id="pwa-install-progress",e.className="fixed top-0 left-0 right-0 bg-green-600 text-white p-3 shadow-lg z-50",e.innerHTML=`
            <div class="container mx-auto flex items-center justify-center">
                <i class="fas fa-check-circle mr-2"></i>
                <span>应用安装成功！正在启动...</span>
            </div>
        `,document.body.appendChild(e),setTimeout(()=>{e.remove()},3e3)}onInstallSuccess(){console.log("PWA安装成功"),this.isInstalled=!0,localStorage.setItem("pwa_installed","true"),localStorage.setItem("pwa_install_date",new Date().toISOString()),Toast.success("应用安装成功！现在可以从主屏幕快速访问了。"),window.dispatchEvent(new CustomEvent("pwa-installed",{detail:{installDate:new Date().toISOString()}}))}shouldShowInstallButton(){return this.isInstallable&&!this.isInstalled}getInstallStatus(){return{isInstalled:this.isInstalled,isInstallable:this.isInstallable,installDate:localStorage.getItem("pwa_install_date"),dismissedDate:localStorage.getItem("pwa_install_dismissed")}}}class d{constructor(){this.currentVersion="1.4.0",this.updateAvailable=!1,this.updateModal=null,this.updateBanner=null,this.skipVersion=null,this.init()}init(){"serviceWorker"in navigator&&(navigator.serviceWorker.addEventListener("controllerchange",()=>{this.onControllerChanged()}),navigator.serviceWorker.addEventListener("message",e=>{this.handleServiceWorkerMessage(e)})),document.readyState==="loading"?document.addEventListener("DOMContentLoaded",()=>{this.checkForUpdates()}):this.checkForUpdates(),setInterval(()=>{this.checkForUpdates()},1800*1e3)}async checkForUpdates(){try{if(!("serviceWorker"in navigator))return;const e=await navigator.serviceWorker.ready;if(e.waiting){this.updateAvailable=!0,this.showUpdateNotification();return}e.active&&e.active.postMessage({type:"check-updates",version:this.currentVersion})}catch(e){console.error("检查更新失败:",e)}}handleServiceWorkerMessage(e){const{type:t,data:s}=e.data;switch(t){case"update-available":this.onUpdateAvailable(s);break;case"update-not-available":console.log("应用已是最新版本");break;case"update-downloaded":this.onUpdateDownloaded(s);break}}onUpdateAvailable(e){if(console.log("发现新版本:",e),this.updateAvailable=!0,localStorage.getItem("pwa_skip_version")===e.version){console.log("用户已跳过此版本:",e.version);return}this.showUpdateNotification(e)}onUpdateDownloaded(e){console.log("更新下载完成:",e),this.showUpdateReadyNotification(e)}showUpdateNotification(e={}){if(document.getElementById("pwa-update-banner"))return;const t=document.createElement("div");t.id="pwa-update-banner",t.className="fixed bottom-4 right-4 bg-gradient-to-r from-green-600 to-teal-600 text-white p-4 rounded-lg shadow-xl z-50 max-w-sm transform transition-all duration-300 translate-y-0 scale-95",t.innerHTML=`
            <div class="flex items-start space-x-3">
                <div class="flex-shrink-0">
                    <i class="fas fa-download text-xl"></i>
                </div>
                <div class="flex-1">
                    <h4 class="text-sm font-medium mb-1">发现新版本</h4>
                    <p class="text-xs opacity-90 mb-3">
                        ${e.changelog?e.changelog:"应用有新版本可用，包含性能改进和bug修复。"}
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
        `,document.body.appendChild(t),document.getElementById("pwa-update-btn").addEventListener("click",()=>{this.applyUpdate()}),document.getElementById("pwa-update-later").addEventListener("click",()=>{this.dismissUpdateBanner()}),document.getElementById("pwa-update-skip").addEventListener("click",()=>{this.skipVersion(e.version||"latest")}),setTimeout(()=>{t.classList.remove("scale-95"),t.classList.add("scale-100")},100),setTimeout(()=>{document.getElementById("pwa-update-banner")&&this.dismissUpdateBanner()},1e4)}showUpdateReadyNotification(e={}){const t=document.createElement("div");t.id="pwa-update-modal",t.className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4",t.innerHTML=`
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
                        ${e.changelog?`
                            <div class="bg-gray-50 rounded p-3">
                                <h4 class="text-xs font-medium text-gray-700 mb-2">更新内容:</h4>
                                <ul class="text-xs text-gray-600 space-y-1">
                                    ${e.changelog.split(`
`).map(s=>`<li>• ${s}</li>`).join("")}
                                </ul>
                            </div>
                        `:""}
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
        `,document.body.appendChild(t),document.getElementById("pwa-restart-btn").addEventListener("click",()=>{this.restartApplication()}),document.getElementById("pwa-restart-later").addEventListener("click",()=>{this.dismissUpdateModal()}),setTimeout(()=>{t.querySelector(".bg-white").classList.remove("scale-95"),t.querySelector(".bg-white").classList.add("scale-100")},100)}async applyUpdate(){try{if(Toast.info("正在准备更新..."),"serviceWorker"in navigator){const e=await navigator.serviceWorker.ready;e.waiting&&e.waiting.postMessage({type:"skip-waiting"})}}catch(e){console.error("应用更新失败:",e),Toast.error("更新失败，请刷新页面重试")}}restartApplication(){this.dismissUpdateModal(),this.dismissUpdateBanner(),Toast.info("应用正在重启..."),setTimeout(()=>{window.location.reload()},1e3)}onControllerChanged(){console.log("Service Worker控制器已变更，应用已更新"),this.updateAvailable&&this.restartApplication()}dismissUpdateBanner(){const e=document.getElementById("pwa-update-banner");e&&(e.classList.add("scale-95"),setTimeout(()=>{e.remove()},300))}dismissUpdateModal(){const e=document.getElementById("pwa-update-modal");e&&(e.querySelector(".bg-white").classList.add("scale-95"),setTimeout(()=>{e.remove()},300))}skipVersion(e){localStorage.setItem("pwa_skip_version",e),this.dismissUpdateBanner(),Toast.info("已跳过此版本更新")}hasUpdate(){return this.updateAvailable}getUpdateStatus(){return{currentVersion:this.currentVersion,updateAvailable:this.updateAvailable,skippedVersion:localStorage.getItem("pwa_skip_version")}}}class c{constructor(){this.isOnline=navigator.onLine,this.offlineIndicator=null,this.offlineModal=null,this.reconnectAttempts=0,this.maxReconnectAttempts=5,this.reconnectInterval=null,this.init()}init(){window.addEventListener("online",()=>{this.onOnline()}),window.addEventListener("offline",()=>{this.onOffline()}),document.addEventListener("visibilitychange",()=>{!document.hidden&&this.isOnline!==navigator.onLine&&(this.isOnline=navigator.onLine,this.isOnline?this.onOnline():this.onOffline())}),this.updateNetworkStatus(),setInterval(()=>{this.checkNetworkStatus()},3e4)}onOnline(){console.log("网络连接已恢复"),this.isOnline=!0,this.reconnectInterval&&(clearInterval(this.reconnectInterval),this.reconnectInterval=null),this.reconnectAttempts=0,this.hideOfflineIndicator(),this.offlineModal&&this.dismissOfflineFeatures(),this.showOnlineNotification(),window.dispatchEvent(new CustomEvent("network-online",{detail:{timestamp:new Date().toISOString()}})),this.refreshPageData()}onOffline(){console.log("网络连接已断开"),this.isOnline=!1,this.showOfflineIndicator(),this.showOfflineNotification(),window.dispatchEvent(new CustomEvent("network-offline",{detail:{timestamp:new Date().toISOString()}}))}async checkNetworkStatus(){try{const e=await fetch("/health",{method:"HEAD",cache:"no-cache",timeout:5e3}),t=!this.isOnline;this.isOnline=e.ok,t&&this.isOnline?this.onOnline():!t&&!this.isOnline&&this.onOffline()}catch{this.isOnline&&(this.isOnline=!1,this.onOffline())}}updateNetworkStatus(){this.isOnline=navigator.onLine,this.isOnline?this.hideOfflineIndicator():this.showOfflineIndicator()}showOfflineIndicator(){if(this.offlineIndicator)return;const e=document.createElement("div");e.id="offline-indicator",e.className="fixed top-0 left-0 right-0 bg-orange-500 text-white p-2 text-center text-sm z-50 transform transition-transform duration-300",e.innerHTML=`
            <div class="container mx-auto flex items-center justify-center">
                <i class="fas fa-wifi-slash mr-2"></i>
                <span>网络连接已断开，部分功能可能不可用</span>
            </div>
        `,document.body.appendChild(e),this.offlineIndicator=e,document.body.style.paddingTop="32px",setTimeout(()=>{e.classList.remove("translate-y-[-100%]"),e.classList.add("translate-y-0")},100)}hideOfflineIndicator(){const e=this.offlineIndicator||document.getElementById("offline-indicator");e&&(e.classList.add("transform","translate-y-[-100%]"),setTimeout(()=>{e.remove(),document.body.style.paddingTop="",this.offlineIndicator=null},300))}showOfflineNotification(){Toast.warning("网络连接已断开，正在尝试重新连接...",5e3),setTimeout(()=>{this.showOfflineFeatures()},2e3)}showOnlineNotification(){Toast.success("网络连接已恢复！")}showOfflineFeatures(){if(localStorage.getItem("offline_features_shown")||this.offlineModal)return;const e=document.createElement("div");e.id="offline-features-modal",e.className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4",e.innerHTML=`
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
        `,document.body.appendChild(e),this.offlineModal=e;const t=document.getElementById("offline-understand-btn");t&&t.addEventListener("click",()=>{this.dismissOfflineFeatures()}),e.addEventListener("click",i=>{i.target===e&&this.dismissOfflineFeatures()});const s=i=>{i.key==="Escape"&&this.offlineModal&&(this.dismissOfflineFeatures(),document.removeEventListener("keydown",s))};document.addEventListener("keydown",s),setTimeout(()=>{const i=e.querySelector(".bg-white");i&&(i.classList.remove("scale-95"),i.classList.add("scale-100"))},100)}dismissOfflineFeatures(){const e=this.offlineModal||document.getElementById("offline-features-modal");if(e){const t=e.querySelector(".bg-white");t&&(t.classList.add("scale-95"),t.classList.remove("scale-100")),setTimeout(()=>{e&&e.parentNode&&e.remove(),this.offlineModal=null},300)}localStorage.setItem("offline_features_shown","true")}refreshPageData(){window.dispatchEvent(new CustomEvent("refresh-data",{detail:{reason:"network-restored"}}));const e=window.location.pathname;e==="/"?typeof loadStats=="function"&&loadStats():e==="/books"?typeof loadBooks=="function"&&loadBooks():e.startsWith("/book/")&&typeof loadBook=="function"&&loadBook()}startReconnectAttempts(){this.reconnectInterval||(this.reconnectAttempts=0,this.reconnectInterval=setInterval(()=>{if(this.reconnectAttempts>=this.maxReconnectAttempts){clearInterval(this.reconnectInterval),this.reconnectInterval=null;return}this.reconnectAttempts++,console.log(`尝试重新连接网络 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`),this.checkNetworkStatus()},5e3))}getNetworkStatus(){return{isOnline:this.isOnline,connectionType:this.getConnectionType(),effectiveType:this.getEffectiveType()}}getConnectionType(){return"connection"in navigator&&navigator.connection.effectiveType||"unknown"}getEffectiveType(){return"connection"in navigator&&navigator.connection.effectiveType||"unknown"}isSlowNetwork(){const e=this.getEffectiveType();return e==="slow-2g"||e==="2g"}isDataSaverMode(){return"connection"in navigator&&navigator.connection.saveData||!1}}class h{constructor(){this.skeletonTypes={book:"book-skeleton",search:"search-skeleton",task:"task-skeleton",stats:"stats-skeleton",chapter:"chapter-skeleton"},this.init()}init(){this.setupPageLoadSkeletons(),this.setupAPILoading(),this.setupPageTransitions(),this.setupNavigationHandling()}setupPageLoadSkeletons(){window.addEventListener("load",()=>{setTimeout(()=>{this.hideAllSkeletons()},500)})}handlePageSkeletons(){const e=window.location.pathname;this.hideAllSkeletons(),setTimeout(()=>{e==="/"?this.showStatsSkeletonIfNeeded():e==="/books"?this.showBookListSkeletonIfNeeded():e==="/search"?this.showSearchSkeletonIfNeeded():e==="/tasks"?this.showTaskListSkeletonIfNeeded():e.startsWith("/book/")&&this.showBookDetailSkeletonIfNeeded()},100),setTimeout(()=>{this.hideAllSkeletons()},2e3)}setupAPILoading(){const e=window.fetch;window.fetch=async(...t)=>{const s=t[0];typeof s=="string"&&s.includes("/api/")&&this.showAPILoading(s);try{const i=await e(...t);return this.hideAPILoading(s),i}catch(i){throw this.hideAPILoading(s),i}}}setupPageTransitions(){document.addEventListener("click",e=>{const t=e.target.closest("a");if(t&&t.href&&t.origin===window.location.origin){const s=t.getAttribute("href");s&&!s.startsWith("#")&&!s.startsWith("javascript:")&&(e.preventDefault(),this.navigateWithTransition(t.href))}})}setupNavigationHandling(){window.addEventListener("popstate",s=>{setTimeout(()=>{this.handlePageSkeletons()},50)}),document.addEventListener("visibilitychange",()=>{document.hidden||setTimeout(()=>{this.hideAllSkeletons()},100)});const e=new MutationObserver(s=>{let i=!1;s.forEach(n=>{n.type==="childList"&&n.addedNodes.forEach(l=>{if(l.nodeType===Node.ELEMENT_NODE){l.matches&&l.matches("[x-data]")&&(i=!0);const a=l.querySelectorAll&&l.querySelectorAll("[x-data]");a&&a.length>0&&(i=!0)}})}),i&&setTimeout(()=>{this.hideAllSkeletons()},200)}),t=document.querySelector("main");t&&e.observe(t,{childList:!0,subtree:!0}),setTimeout(()=>{this.handlePageSkeletons()},100)}async navigateWithTransition(e){this.hideAllSkeletons(),this.showPageTransition(),setTimeout(()=>{window.location.href=e},300)}showPageTransition(){const e=document.createElement("div");e.id="page-transition",e.className="fixed inset-0 bg-white z-50 flex items-center justify-center",e.innerHTML=`
            <div class="text-center">
                <div class="inline-flex items-center justify-center w-16 h-16 bg-blue-50 rounded-full mb-4">
                    <i class="fas fa-book-reader text-blue-600 text-2xl animate-pulse"></i>
                </div>
                <div class="animate-pulse">
                    <div class="h-4 bg-gray-200 rounded w-32 mx-auto mb-2"></div>
                    <div class="h-3 bg-gray-200 rounded w-24 mx-auto"></div>
                </div>
            </div>
        `,document.body.appendChild(e)}showBookListSkeletonIfNeeded(){const e=document.querySelector('[x-data="booksList()"] .space-y-4');if(!e||e.querySelector("[x-for]")||e.children.length>0)return;const s=Array(3).fill(0).map(()=>`
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
        `).join("");e.innerHTML=s}showBookListSkeleton(){this.showBookListSkeletonIfNeeded()}showSearchSkeletonIfNeeded(){const e=document.querySelector(".grid.grid-cols-1.gap-4");if(!e||e.querySelector("[x-for]")||e.children.length>0)return;const s=Array(3).fill(0).map(()=>`
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
        `).join("");e.innerHTML=s}showSearchSkeleton(){this.showSearchSkeletonIfNeeded()}showTaskListSkeletonIfNeeded(){const e=document.querySelector('[x-data="tasksList()"] .space-y-4');if(!e||e.querySelector("[x-for]")||e.children.length>0)return;const s=Array(3).fill(0).map(()=>`
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
        `).join("");e.innerHTML=s}showTaskListSkeleton(){this.showTaskListSkeletonIfNeeded()}showStatsSkeletonIfNeeded(){const e=document.querySelector('[x-data="stats()"] .grid.grid-cols-1');if(!e||e.children.length>0&&!e.querySelector(".skeleton-placeholder"))return;const s=Array(3).fill(0).map(()=>`
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
        `).join("");e.innerHTML=s}showStatsSkeleton(){this.showStatsSkeletonIfNeeded()}showBookDetailSkeletonIfNeeded(){const e=document.querySelector('[x-data="bookDetail()"]');!e||e.children.length>0&&!e.querySelector(".skeleton-placeholder")||(e.innerHTML=`
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
        `)}showBookDetailSkeleton(){this.showBookDetailSkeletonIfNeeded()}showAPILoading(e){e.includes("/books/search")?this.showSearchLoading():e.includes("/books")?this.showBookLoading():e.includes("/tasks")&&this.showTaskLoading()}hideAPILoading(e){}showSearchLoading(){const e=document.querySelector('button[onclick*="search()"]');if(e){const t=e.innerHTML;e.innerHTML='<i class="fas fa-spinner fa-spin"></i> 搜索中...',e.disabled=!0,setTimeout(()=>{e.innerHTML=t,e.disabled=!1},5e3)}}showBookLoading(){}showTaskLoading(){}hideAllSkeletons(){const e=document.getElementById("page-transition");e&&e.remove(),document.querySelectorAll(".skeleton-placeholder").forEach(i=>{i.remove()}),['[x-data="booksList()"] .space-y-4',".grid.grid-cols-1.gap-4",'[x-data="tasksList()"] .space-y-4','[x-data="stats()"] .grid.grid-cols-1','[x-data="bookDetail()"]'].forEach(i=>{const n=document.querySelector(i);n&&Array.from(n.children).every(a=>a.classList.contains("skeleton-placeholder")||a.classList.contains("animate-pulse")&&a.innerHTML&&a.innerHTML.includes("bg-gray-200"))&&(n.innerHTML="")})}createSkeletonElement(e,t=""){const s=document.createElement("div");return s.className=`skeleton ${e} ${t} animate-pulse`,s}createTextSkeleton(e="100%",t="1rem",s=""){const i=document.createElement("div");return i.className=`h-4 bg-gray-200 rounded ${s} animate-pulse`,i.style.width=e,i.style.height=t,i}createImageSkeleton(e="100%",t="100%",s=""){const i=document.createElement("div");return i.className=`bg-gray-200 rounded ${s} animate-pulse flex items-center justify-center`,i.style.width=e,i.style.height=t,i.innerHTML='<i class="fas fa-image text-gray-400"></i>',i}createButtonSkeleton(e="auto",t="2.5rem",s=""){const i=document.createElement("div");return i.className=`bg-gray-200 rounded ${s} animate-pulse`,i.style.width=e,i.style.height=t,i}}window.pwaInstall=new r;window.pwaUpdate=new d;window.pwaOffline=new c;window.pwaSkeleton=new h;
