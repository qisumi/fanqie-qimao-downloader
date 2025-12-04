import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/HomeView.vue'),
    meta: { title: '首页' }
  },
  {
    path: '/search',
    name: 'search',
    component: () => import('@/views/SearchView.vue'),
    meta: { title: '搜索书籍' }
  },
  {
    path: '/books',
    name: 'books',
    component: () => import('@/views/BooksView.vue'),
    meta: { title: '我的书库' }
  },
  {
    path: '/books/:id',
    name: 'book-detail',
    component: () => import('@/views/BookDetailView.vue'),
    meta: { title: '书籍详情' }
  },
  {
    path: '/tasks',
    name: 'tasks',
    component: () => import('@/views/TasksView.vue'),
    meta: { title: '下载任务' }
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('@/views/SettingsView.vue'),
    meta: { title: '设置' }
  },
  {
    path: '/reader/:bookId',
    name: 'reader',
    component: () => import('@/views/ReaderView.vue'),
    meta: { title: '在线阅读', readerLayout: true }
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { title: '登录', guest: true }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  // 更新页面标题
  document.title = to.meta.title ? `${to.meta.title} - 番茄·七猫·笔趣阁下载器` : '番茄·七猫·笔趣阁下载器'
  
  const userStore = useUserStore()
  
  // 如果需要认证且未登录
  if (!to.meta.guest && !userStore.isAuthenticated) {
    await userStore.checkAuth()
    if (!userStore.isAuthenticated && userStore.requireAuth) {
      return next({ name: 'login', query: { redirect: to.fullPath } })
    }
  }
  
  // 如果已登录且访问登录页，重定向到首页
  if (to.meta.guest && userStore.isAuthenticated) {
    return next({ name: 'home' })
  }
  
  next()
})

export default router
