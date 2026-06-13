import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import { SCREENS, validScreen } from '@/lib/nav'
import { storage } from '@/lib/storage'
import StubView from '@/views/StubView.vue'

// Усі екрани фази 1 — заглушки (StubView); реальні екрани прийдуть із
// add-calendar-timesheet / add-data-screens. Auth-gate — на рівні App.vue.
const screenRoutes: RouteRecordRaw[] = SCREENS.map((s) => ({
  path: `/${s.name}`,
  name: s.name,
  component: StubView,
  meta: { titleKey: s.titleKey, icon: s.icon, badge: s.badge },
}))

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    // Корінь → останній відкритий екран (зі storage) або calendar.
    { path: '/', redirect: () => ({ name: validScreen(storage.get<string>('ui.route')) }) },
    ...screenRoutes,
    { path: '/:pathMatch(.*)*', redirect: { name: 'calendar' } },
  ],
})
