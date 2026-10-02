/** LostLink 前端路由。
 *
 * 路由把首页、详情/举报、发布/登记和匹配通知组织成可通过 URL 恢复的页面流程。
 * 首页同步加载作为首屏；其他业务页懒加载，用户访问时才下载对应代码块。
 */

import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import { readAdminSection } from './admin'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/items/:id',
      name: 'item-detail',
      // 详情和举报页按需加载，避免增加首页首屏体积。
      component: () => import('../views/ItemDetailView.vue'),
    },
    {
      path: '/items/:id/report',
      name: 'report-submit',
      component: () => import('../views/ReportSubmitView.vue'),
    },
    {
      path: '/publish/lost',
      name: 'publish-lost',
      // 发布和登记使用两个独立 URL，但内部复用同一个 ItemEntryForm 组件。
      component: () => import('../views/PublishLostView.vue'),
    },
    {
      path: '/publish/found',
      name: 'register-found',
      component: () => import('../views/RegisterFoundView.vue'),
    },
    {
      path: '/notifications',
      name: 'notifications',
      component: () => import('../views/NotificationsView.vue'),
    },
    {
      path: '/notifications/:id',
      name: 'match-detail',
      // :id 让某一条匹配详情可以被刷新、收藏并通过前进/后退恢复。
      component: () => import('../views/MatchDetailView.vue'),
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      // query 用于说明用户为何被引导到登录页，不伪造登录状态。
      props: route => ({
        profileRequested: route.query.requested === 'profile',
        adminRequested: route.query.requested === 'admin',
      }),
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue'),
    },
    {
      path: '/my',
      name: 'my',
      // 当前没有认证接口，真实个人页入口必须先进入登录说明页。
      redirect: { name: 'login', query: { requested: 'profile' } },
    },
    {
      path: '/admin/:section?',
      name: 'admin',
      // 管理端同样不根据前端演示数据授予权限。
      redirect: { name: 'login', query: { requested: 'admin' } },
    },
    {
      path: '/my-preview',
      name: 'my-preview',
      component: () => import('../views/MyView.vue'),
      // 开发预览不会进入生产构建中的业务入口。
      beforeEnter: () => import.meta.env.DEV ? true : { name: 'login' },
    },
    {
      path: '/admin-preview/:section?',
      name: 'admin-preview',
      component: () => import('../views/admin/AdminConsole.vue'),
      beforeEnter: () => import.meta.env.DEV ? true : { name: 'login' },
      props: route => ({ section: readAdminSection(route.params.section) }),
    },
    {
      path: '/:pathMatch(.*)*',
      // 未知路径统一返回首页，避免用户停留在空白页面。
      redirect: { name: 'home' },
    },
  ],
  scrollBehavior() {
    // 页面切换后回到顶部，避免详情页从首页原来的滚动位置开始。
    return { top: 0 }
  },
})

export default router
