<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'

import BrandMark from '@/components/BrandMark.vue'
import TweaksPanel from '@/components/TweaksPanel.vue'
import UserChip from '@/components/UserChip.vue'
import Icon from '@/components/ui/Icon.vue'
import IconBtn from '@/components/ui/IconBtn.vue'
import Segmented from '@/components/ui/Segmented.vue'
import { useI18n } from '@/i18n'
import type { Lang } from '@/i18n/strings'
import { NAV, type NavItem } from '@/lib/nav'
import { useJournalStore } from '@/stores/journal'
import { useUiStore } from '@/stores/ui'

const { t, lang, setLang } = useI18n()
const ui = useUiStore()
const journal = useJournalStore()
const route = useRoute()

const pathOf = (item: NavItem): string => item.path ?? `/${item.name}`

// Активність — за matched-записами маршруту: батьківський `/projects` присутній
// у matched на будь-якому `/projects/*`, тож єдиний пункт «Проекти» лишається
// підсвіченим і на вкладеній під-вʼюсі (TimeCamp/Jira).
function isActive(item: NavItem): boolean {
  return route.matched.some((r) => r.path === pathOf(item))
}

// Бейдж журналу — живий лічильник needs_verification; решта — зі статичного нав-конфігу.
function badgeFor(item: NavItem): number | undefined {
  if (item.name === 'journal') return journal.needsCount || undefined
  return item.badge
}

onMounted(() => void journal.refreshNeedsCount())

const shellClasses = computed(() => [
  'shell',
  {
    'is-collapsed': ui.navCollapsed,
    'no-workband': !ui.workBand,
    'no-weekends': !ui.weekends,
  },
  `dens-${ui.density}`,
])
</script>

<template>
  <div :class="shellClasses">
    <aside class="nav">
      <div class="nav__brand">
        <BrandMark :size="26" />
        <span v-if="!ui.navCollapsed" class="nav__brandname">Sync Work</span>
        <button class="nav__collapse" title="Toggle" @click="ui.toggleNav()">
          <Icon :name="ui.navCollapsed ? 'chevR' : 'chevL'" :size="16" />
        </button>
      </div>

      <nav class="nav__menu">
        <div v-for="grp in NAV" :key="grp.sectionKey" class="nav__group">
          <div v-if="!ui.navCollapsed" class="nav__section">{{ t[grp.sectionKey] }}</div>
          <RouterLink
            v-for="item in grp.items"
            :key="item.name"
            :to="{ path: pathOf(item) }"
            class="nav__item"
            :class="{ 'is-active': isActive(item) }"
            :title="ui.navCollapsed ? t[item.titleKey] : undefined"
          >
            <Icon :name="item.icon" :size="18" />
            <span v-if="!ui.navCollapsed">{{ t[item.titleKey] }}</span>
            <span v-if="!ui.navCollapsed && badgeFor(item)" class="nav__badge">{{ badgeFor(item) }}</span>
            <span v-if="ui.navCollapsed && badgeFor(item)" class="nav__badge nav__badge--dot" />
          </RouterLink>
        </div>
      </nav>

      <div class="nav__foot">
        <div class="nav__controls">
          <Segmented
            v-if="!ui.navCollapsed"
            size="sm"
            :model-value="lang"
            :options="[
              { value: 'uk', label: 'УКР' },
              { value: 'en', label: 'ENG' },
            ]"
            @update:model-value="(v: string) => setLang(v as Lang)"
          />
          <IconBtn
            :name="ui.theme === 'dark' ? 'sun' : 'moon'"
            variant="ghost"
            size="sm"
            title="Theme"
            @click="ui.toggleTheme()"
          />
        </div>
        <UserChip :collapsed="ui.navCollapsed" />
      </div>
    </aside>

    <main class="main">
      <RouterView />
    </main>

    <TweaksPanel />
  </div>
</template>
