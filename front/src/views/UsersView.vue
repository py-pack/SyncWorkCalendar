<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import DataTable from '@/components/data/DataTable.vue'
import PageHeader from '@/components/data/PageHeader.vue'
import type { Column } from '@/components/data/types'
import Avatar from '@/components/ui/Avatar.vue'
import Btn from '@/components/ui/Btn.vue'
import Field from '@/components/ui/Field.vue'
import Icon from '@/components/ui/Icon.vue'
import IconBtn from '@/components/ui/IconBtn.vue'
import Menu from '@/components/ui/Menu.vue'
import Segmented from '@/components/ui/Segmented.vue'
import Sheet from '@/components/ui/Sheet.vue'
import Toggle from '@/components/ui/Toggle.vue'
import type { MenuItem, SegmentedOption } from '@/components/ui/types'
import { ApiError, type UserItem } from '@/api/types'
import { useI18n } from '@/i18n'
import { hueFor } from '@/lib/format'
import { useUsersStore } from '@/stores/users'

const { t } = useI18n()
const store = useUsersStore()

const menuId = ref<number | null>(null)
const adding = ref(false)
const editing = ref<UserItem | null>(null)
const submitting = ref(false)
const formError = ref('')

const draft = reactive({ username: '', email: '', worker_key: '', role: 'member' })

const formOpen = computed(() => adding.value || editing.value !== null)
const formTitle = computed(() => (editing.value ? t.value.user_edit : t.value.users_add))

const cols = computed<Column[]>(() => [
  { key: 'name', label: t.value.user_full_name },
  { key: 'worker_key', label: t.value.user_worker_key, width: 150 },
  { key: 'last_seen', label: t.value.col_last_seen, width: 130 },
  { key: 'active', label: '', align: 'right', width: 90 },
  { key: 'act', label: '', align: 'right', width: 44 },
])

const roleOptions = computed<SegmentedOption[]>(() => [
  { value: 'admin', label: t.value.user_role_admin },
  { value: 'member', label: t.value.user_role_member },
  { value: 'viewer', label: t.value.user_role_viewer },
])

function initials(name: string): string {
  const parts = name.split(/[\s._-]+/).filter(Boolean)
  const chars = parts.slice(0, 2).map((p) => p[0]).join('')
  return (chars || name.slice(0, 2)).toUpperCase()
}

function rowMenu(u: UserItem): MenuItem[] {
  return [
    { label: t.value.user_edit, icon: 'edit', onClick: () => openEdit(u) },
    {
      label: u.is_active ? t.value.user_disabled : t.value.user_active,
      icon: u.is_active ? 'lock' : 'check',
      onClick: () => void store.toggleActive(u),
    },
    { divider: true },
    { label: t.value.blk_delete, icon: 'trash', danger: true, onClick: () => void store.remove(u) },
  ]
}

function openAdd(): void {
  formError.value = ''
  editing.value = null
  Object.assign(draft, { username: '', email: '', worker_key: '', role: 'member' })
  adding.value = true
}

function openEdit(u: UserItem): void {
  formError.value = ''
  menuId.value = null
  editing.value = u
  adding.value = false
  Object.assign(draft, {
    username: u.username,
    email: u.email ?? '',
    worker_key: u.worker_key ?? '',
    role: 'member',
  })
}

function closeForm(): void {
  adding.value = false
  editing.value = null
}

async function submit(): Promise<void> {
  if (submitting.value || !draft.username.trim()) return
  submitting.value = true
  formError.value = ''
  try {
    if (editing.value) {
      await store.update(editing.value.id, {
        username: draft.username.trim(),
        worker_key: draft.worker_key.trim() || null,
      })
    } else {
      await store.create({
        username: draft.username.trim(),
        email: draft.email.trim(),
        worker_key: draft.worker_key.trim() || null,
      })
    }
    closeForm()
  } catch (e) {
    formError.value = e instanceof ApiError ? e.detail : String(e)
  } finally {
    submitting.value = false
  }
}

onMounted(() => void store.load())
</script>

<template>
  <div class="page">
    <PageHeader :title="t.users_title" :desc="t.users_desc">
      <template #actions>
        <Btn size="sm" variant="primary" icon="plus" @click="openAdd">{{ t.users_add }}</Btn>
      </template>
    </PageHeader>

    <p v-if="store.error" class="data-error"><Icon name="alert" :size="15" />{{ store.error }}</p>

    <div class="page__body">
      <DataTable :columns="cols" :rows="store.users" :get-id="(r) => r.id" :empty="t.empty">
        <template #cell-name="{ row }">
          <div class="dt-name">
            <Avatar :initials="initials(row.username)" :hue="hueFor(row.username)" :size="30" />
            <div class="user-name">
              <span>{{ row.username }}</span>
              <span class="muted">{{ row.email ?? '—' }}</span>
            </div>
          </div>
        </template>
        <template #cell-worker_key="{ row }">
          <span v-if="row.worker_key" class="mono key-pill">{{ row.worker_key }}</span>
          <span v-else class="faint">—</span>
        </template>
        <template #cell-last_seen>
          <span class="muted">—</span>
        </template>
        <template #cell-active="{ row }">
          <Toggle size="sm" :checked="row.is_active" @update:checked="store.toggleActive(row)" />
        </template>
        <template #cell-act="{ row }">
          <span style="position: relative">
            <IconBtn
              name="dots"
              size="sm"
              @click="menuId = menuId === row.id ? null : row.id"
            />
            <Menu
              v-if="menuId === row.id"
              :items="rowMenu(row)"
              @close="menuId = null"
            />
          </span>
        </template>
      </DataTable>
    </div>

    <Sheet :open="formOpen" :title="formTitle" :width="400" @close="closeForm">
      <div class="userform">
        <Field :label="t.user_full_name">
          <input v-model="draft.username" class="sw-input" placeholder="i.petrenko" />
        </Field>
        <Field :label="t.col_email">
          <input
            v-model="draft.email"
            class="sw-input"
            type="email"
            placeholder="name@leadsdoit.io"
            :disabled="editing !== null"
          />
        </Field>
        <Field :label="t.user_worker_key" hint="Jira key">
          <input v-model="draft.worker_key" class="sw-input mono" placeholder="i.petrenko" />
        </Field>
        <Field :label="t.col_role">
          <Segmented v-model="draft.role" :options="roleOptions" />
        </Field>

        <div class="userform__note">
          <Icon name="lock" :size="13" />
          <span>{{ t.users_desc }}</span>
        </div>

        <p v-if="formError" class="data-error">{{ formError }}</p>

        <div class="userform__foot">
          <Btn variant="default" :disabled="submitting" @click="closeForm">{{ t.blk_cancel }}</Btn>
          <Btn
            variant="primary"
            :icon="editing ? 'check' : 'plus'"
            :disabled="submitting || !draft.username.trim()"
            @click="submit"
          >
            {{ editing ? t.blk_save : t.users_invite }}
          </Btn>
        </div>
      </div>
    </Sheet>
  </div>
</template>
