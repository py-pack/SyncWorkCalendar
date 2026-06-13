import { type Component } from 'vue'
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import { SCREENS, validScreen } from '@/lib/nav'
import { storage } from '@/lib/storage'
import CalendarView from '@/views/CalendarView.vue'
import JiraView from '@/views/JiraView.vue'
import JournalView from '@/views/JournalView.vue'
import StubView from '@/views/StubView.vue'
import TempoView from '@/views/TempoView.vue'
import TimeCampView from '@/views/TimeCampView.vue'
import UsersView from '@/views/UsersView.vue'

// `calendar` (фаза 2) і дані-екрани фази 3 — реальні. StubView лишається
// фолбеком для ще нереалізованих екранів. Auth-gate — на рівні App.vue.
const SCREEN_COMPONENTS: Record<string, Component> = {
  calendar: CalendarView,
  timecamp: TimeCampView,
  jira: JiraView,
  tempo: TempoView,
  journal: JournalView,
  users: UsersView,
}

const screenRoutes: RouteRecordRaw[] = SCREENS.map((s) => ({
  path: `/${s.name}`,
  name: s.name,
  component: SCREEN_COMPONENTS[s.name] ?? StubView,
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
