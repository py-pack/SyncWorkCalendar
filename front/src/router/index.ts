import { type Component } from 'vue'
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import { NAV, validScreen, type NavItem } from '@/lib/nav'
import { storage } from '@/lib/storage'
import CalendarView from '@/views/CalendarView.vue'
import JiraView from '@/views/JiraView.vue'
import JournalView from '@/views/JournalView.vue'
import ProjectsView from '@/views/ProjectsView.vue'
import JrProjects from '@/views/projects/JrProjects.vue'
import TcProjects from '@/views/projects/TcProjects.vue'
import StubView from '@/views/StubView.vue'
import TempoView from '@/views/TempoView.vue'
import TimeCampView from '@/views/TimeCampView.vue'
import UsersView from '@/views/UsersView.vue'

// `calendar` (фаза 2), «Проекти» і дані-екрани фази 3 — реальні. StubView
// лишається фолбеком для ще нереалізованих екранів. Auth-gate — на рівні App.vue.
const SCREEN_COMPONENTS: Record<string, Component> = {
  calendar: CalendarView,
  projects: ProjectsView,
  'projects-timecamp': TcProjects,
  'projects-jira': JrProjects,
  timecamp: TimeCampView,
  jira: JiraView,
  tempo: TempoView,
  journal: JournalView,
  users: UsersView,
}

const pathFor = (item: NavItem): string => item.path ?? `/${item.name}`
const componentFor = (item: NavItem): Component => SCREEN_COMPONENTS[item.name] ?? StubView
const metaFor = (item: NavItem) => ({ titleKey: item.titleKey, icon: item.icon, badge: item.badge })

// Пункт із `children` стає батьківським маршрутом (контейнер + `<router-view>`)
// з `redirect` на першу під-вʼюху і вкладеними дочірніми (абсолютні шляхи).
function routeFor(item: NavItem): RouteRecordRaw {
  if (item.children?.length) {
    return {
      path: pathFor(item),
      component: componentFor(item),
      redirect: { name: item.children[0].name },
      meta: metaFor(item),
      children: item.children.map((child) => ({
        path: pathFor(child),
        name: child.name,
        component: componentFor(child),
        meta: metaFor(child),
      })),
    }
  }
  return { path: pathFor(item), name: item.name, component: componentFor(item), meta: metaFor(item) }
}

const screenRoutes: RouteRecordRaw[] = NAV.flatMap((s) => s.items).map(routeFor)

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    // Корінь → останній відкритий екран (зі storage) або calendar.
    { path: '/', redirect: () => ({ name: validScreen(storage.get<string>('ui.route')) }) },
    ...screenRoutes,
    { path: '/:pathMatch(.*)*', redirect: { name: 'calendar' } },
  ],
})
