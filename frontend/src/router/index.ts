import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import LandingPage from '../views/LandingPage.vue'
import AppLayout from '../layouts/AppLayout.vue'
import Dashboard from '../views/Dashboard.vue'
import StockPrediction from '../views/StockPrediction.vue'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'Landing',
    component: LandingPage
  },
  {
    path: '/app',
    name: 'AppLayout',
    component: AppLayout,
    redirect: '/app/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: Dashboard
      },
      {
        path: 'stock/:ticker',
        name: 'StockPrediction',
        component: StockPrediction,
        props: true
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
