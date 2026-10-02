/** LostLink 前端路由。
 *
 * 路由把首页、详情/举报、发布/登记和匹配通知组织成可通过 URL 恢复的页面流程。
 * 首页同步加载作为首屏；其他业务页懒加载，用户访问时才下载对应代码块。
 */

import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

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
