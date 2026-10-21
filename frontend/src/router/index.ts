// 文档对照：03_LostLink软件需求规格说明书.docx；图表编号以当前文档为准。
// 设计文档对照：04_LostLink软件设计规格说明书.docx；以下“设计文档对应”使用该文档图表编号。
// 文档对应：图2-1 用例图的页面入口；图2-3 各边界界面的导航组织。
/** LostLink 前端路由。
 *
 * 路由把首页、详情/举报、发布/登记和匹配通知组织成可通过 URL 恢复的页面流程。
 * 首页同步加载作为首屏；其他业务页懒加载，用户访问时才下载对应代码块。
 */

import { createRouter, createWebHistory, type RouteLocationNormalized } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import { readAdminSection } from './admin'
import { useAuth } from '../stores/auth'

/** 受保护页面进入前向后端确认会话；未登录时保留原目标供登录后返回。 */
// 设计文档对应：图3-3-1、图3-3-2 进入受保护页面前恢复会话，未登录时保留 redirect。
async function requireAuth(to: RouteLocationNormalized) {
  const current = await useAuth().restore()
  return current ? true : {
    name: 'login',
    query: { requested: to.name === 'my' ? 'profile' : 'protected', redirect: to.fullPath },
  }
}

/** 管理路由除登录外还要求服务端恢复出的角色为 admin。 */
// 设计文档对应：图3-2-9 管理路由在恢复会话后进一步检查 admin 角色。
async function requireAdmin(to: RouteLocationNormalized) {
  const current = await useAuth().restore()
  if (!current) return { name: 'login', query: { requested: 'admin', redirect: to.fullPath } }
  return current.role === 'admin' ? true : { name: 'home' }
}

// 设计文档对应：图3-3-1、图3-3-2、图2-1 组织首页、详情、发布、通知、举报和个人中心路由。
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
      beforeEnter: requireAuth,
    },
    {
      path: '/publish/lost',
      name: 'publish-lost',
      // 发布和登记使用两个独立 URL，但内部复用同一个 ItemEntryForm 组件。
      component: () => import('../views/PublishLostView.vue'),
      beforeEnter: requireAuth,
    },
    {
      path: '/publish/found',
      name: 'register-found',
      component: () => import('../views/RegisterFoundView.vue'),
      beforeEnter: requireAuth,
    },
    {
      path: '/notifications',
      name: 'notifications',
      component: () => import('../views/NotificationsView.vue'),
      beforeEnter: requireAuth,
    },
    {
      path: '/notifications/:id',
      name: 'match-detail',
      // :id 让某一条匹配详情可以被刷新、收藏并通过前进/后退恢复。
      component: () => import('../views/MatchDetailView.vue'),
      beforeEnter: requireAuth,
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      // query 用于说明用户为何被引导到登录页，不伪造登录状态。
      props: route => ({
        profileRequested: route.query.requested === 'profile',
        protectedRequested: route.query.requested === 'protected',
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
      component: () => import('../views/MyView.vue'),
      beforeEnter: requireAuth,
    },
    {
      path: '/admin/:section?',
      name: 'admin',
      component: () => import('../views/admin/AdminConsole.vue'),
      beforeEnter: requireAdmin,
      props: route => ({ section: readAdminSection(route.params.section) }),
    },
    {
      path: '/my-preview',
      name: 'my-preview',
      redirect: { name: 'my' },
    },
    {
      path: '/admin-preview/:section?',
      name: 'admin-preview',
      redirect: route => ({ name: 'admin', params: { section: route.params.section } }),
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
