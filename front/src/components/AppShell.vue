<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, RouterView } from 'vue-router'

import BrandMark from '@/components/BrandMark.vue'
import TweaksPanel from '@/components/TweaksPanel.vue'
import UserChip from '@/components/UserChip.vue'
import Icon from '@/components/ui/Icon.vue'
import IconBtn from '@/components/ui/IconBtn.vue'
import Segmented from '@/components/ui/Segmented.vue'
import { useI18n } from '@/i18n'
import type { Lang } from '@/i18n/strings'
import { NAV } from '@/lib/nav'
import { useUiStore } from '@/stores/ui'

const { t, lang, setLang } = useI18n()
const ui = useUiStore()

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
            :to="{ name: item.name }"
            class="nav__item"
            active-class="is-active"
            :title="ui.navCollapsed ? t[item.titleKey] : undefined"
          >
            <Icon :name="item.icon" :size="18" />
            <span v-if="!ui.navCollapsed">{{ t[item.titleKey] }}</span>
            <span v-if="!ui.navCollapsed && item.badge" class="nav__badge">{{ item.badge }}</span>
            <span v-if="ui.navCollapsed && item.badge" class="nav__badge nav__badge--dot" />
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
