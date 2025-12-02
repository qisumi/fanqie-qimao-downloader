<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  NCard,
  NForm,
  NFormItem,
  NInput,
  NButton,
  NSpace,
  NList,
  NListItem,
  NTag,
  NPopconfirm,
  NDivider,
  NAlert,
  useMessage
} from 'naive-ui'
import { PencilOutline, TrashOutline, PersonCircleOutline } from '@vicons/ionicons5'
import { useUserStore } from '@/stores/user'
import { useBookStore } from '@/stores/book'

const userStore = useUserStore()
const bookStore = useBookStore()
const router = useRouter()
const message = useMessage()

const usernameInput = ref('')
const editingUserId = ref(null)
const editingName = ref('')

const userList = computed(() => userStore.users)
const currentUser = computed(() => userStore.currentUser)
const busy = computed(() => userStore.userLoading)

onMounted(async () => {
  await userStore.initUserContext()
  usernameInput.value = userStore.currentUsername
  if (userStore.currentUserId) {
    await bookStore.fetchUserBooks(userStore.currentUserId)
  }
})

watch(
  () => userStore.currentUsername,
  (val) => {
    if (!editingUserId.value) {
      usernameInput.value = val
    }
  }
)

async function handleSwitch() {
  if (!usernameInput.value.trim()) {
    message.warning('请输入用户名')
    return
  }
  try {
    const user = await userStore.switchUser(usernameInput.value)
    await bookStore.fetchUserBooks(user.id)
    message.success(`已切换到 ${user.username}`)
  } catch (error) {
    message.error(error.message || '切换用户失败')
  }
}

function startEdit(user) {
  editingUserId.value = user.id
  editingName.value = user.username
}

async function saveEdit(user) {
  if (!editingName.value.trim()) {
    message.warning('请输入新用户名')
    return
  }
  try {
    await userStore.renameUser(user.id, editingName.value)
    message.success('用户名已更新')
    editingUserId.value = null
    editingName.value = ''
  } catch (error) {
    message.error(error.message || '更新失败')
  }
}

function cancelEdit() {
  editingUserId.value = null
  editingName.value = ''
}

async function handleDelete(user) {
  try {
    await userStore.deleteUser(user.id)
    message.success('用户已删除')
    if (userStore.currentUserId) {
      await bookStore.fetchUserBooks(userStore.currentUserId)
    } else {
      await bookStore.fetchUserBooks(null)
    }
  } catch (error) {
    message.error(error.message || '删除失败')
  }
}

function goToBooks() {
  router.push({ name: 'books' })
}
</script>

<template>
  <div class="settings-view">
    <div class="page-header">
      <div>
        <div class="eyebrow">共同密码，独立书架</div>
        <h2 class="title">设置与用户</h2>
        <p class="subtitle">
          密码依旧从 .env 读取，用户名用于区分私人书架；私人书架内容存放在服务器以便多设备同步，公共书架、任务与配额仍然共享。
        </p>
      </div>
      <div class="header-actions">
        <n-button type="primary" secondary block @click="goToBooks">
          返回书架
        </n-button>
      </div>
    </div>

    <div class="grid">
      <n-card class="card" size="large">
        <template #header>
          <div class="card-header">
            <div class="card-title">切换 / 新增用户</div>
            <n-tag type="success" v-if="currentUser">
              当前：{{ currentUser.username }}
            </n-tag>
          </div>
        </template>
        <n-alert type="info" show-icon style="margin-bottom: 16px;">
          用户名仅用于区分私人书架；私人书架数据保存在服务器，可在同一用户的不同设备间同步，不影响公共书架、下载任务和限额。
        </n-alert>
        <n-form label-placement="top" :show-require-mark="false">
          <n-form-item label="输入用户名（不存在则自动创建）">
            <n-input
              v-model:value="usernameInput"
              placeholder="例如：Alice、Bob、朋友的昵称"
              clearable
            />
          </n-form-item>
          <n-button type="primary" :loading="busy" block @click="handleSwitch">
            立即切换 / 创建
          </n-button>
        </n-form>
      </n-card>

      <n-card class="card" size="large">
        <template #header>
          <div class="card-header">
            <div class="card-title">用户列表</div>
            <n-tag v-if="userList.length" type="info">{{ userList.length }} 位</n-tag>
          </div>
        </template>

        <n-list v-if="userList.length" hoverable class="user-list">
          <n-list-item v-for="user in userList" :key="user.id">
            <div class="user-row">
              <div class="user-meta">
                <n-tag round type="success" v-if="currentUser?.id === user.id">
                  当前
                </n-tag>
                <span class="user-name">
                  <n-icon :size="16" style="margin-right: 6px;"><PersonCircleOutline /></n-icon>
                  <template v-if="editingUserId !== user.id">
                    {{ user.username }}
                  </template>
                  <n-input
                    v-else
                    v-model:value="editingName"
                    size="small"
                    style="width: 180px;"
                  />
                </span>
                <span class="user-date">创建于 {{ new Date(user.created_at).toLocaleString() }}</span>
              </div>
              <n-space size="small" wrap class="user-actions">
                <n-button
                  quaternary
                  size="small"
                  @click="editingUserId === user.id ? saveEdit(user) : startEdit(user)"
                  :loading="busy"
                >
                  <template #icon>
                    <n-icon><PencilOutline /></n-icon>
                  </template>
                  {{ editingUserId === user.id ? '保存' : '重命名' }}
                </n-button>
                <n-button v-if="editingUserId === user.id" quaternary size="small" @click="cancelEdit">
                  取消
                </n-button>
                <n-popconfirm
                  @positive-click="handleDelete(user)"
                  positive-text="删除"
                  negative-text="取消"
                  v-if="userList.length > 1"
                >
                  <template #trigger>
                    <n-button quaternary size="small" type="error" :loading="busy">
                      <template #icon>
                        <n-icon><TrashOutline /></n-icon>
                      </template>
                      删除
                    </n-button>
                  </template>
                  删除后该用户的私人书架会被清空，公共书架不受影响。
                </n-popconfirm>
              </n-space>
            </div>
          </n-list-item>
        </n-list>

        <n-alert v-else type="warning" show-icon>
          还没有用户，使用上方输入框创建一个吧。
        </n-alert>
      </n-card>
    </div>
  </div>
</template>

<style scoped>
.settings-view {
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 8px 4px 16px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 4px;
}

.header-actions {
  min-width: 200px;
  align-self: center;
}

.eyebrow {
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--primary-color);
}

.title {
  margin: 4px 0;
  font-size: 24px;
  font-weight: 700;
}

.subtitle {
  margin: 0;
  color: var(--text-color-secondary);
  max-width: 760px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
}

.card {
  box-shadow: var(--shadow-card);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-title {
  font-weight: 700;
}

.user-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.user-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  line-height: 1.4;
}

.user-name {
  font-weight: 600;
  display: inline-flex;
  align-items: center;
}

.user-date {
  color: var(--text-color-tertiary);
  font-size: 12px;
}

.user-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.user-list :deep(.n-list-item) {
  padding: 12px 10px;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    padding: 0 4px 4px;
  }

  .header-actions {
    width: 100%;
  }

  .grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .card {
    padding: 4px 0;
  }

  .user-row {
    align-items: stretch;
    flex-direction: column;
    gap: 10px;
  }

  .user-meta {
    width: 100%;
    gap: 8px;
  }

  .user-date {
    width: 100%;
    display: block;
  }

  .user-actions {
    width: 100%;
    justify-content: stretch;
    gap: 8px;
  }

  .user-actions :deep(.n-button) {
    flex: 1;
  }

  .user-list :deep(.n-list-item) {
    padding: 10px 8px;
  }

  .subtitle {
    font-size: 14px;
  }
}
</style>
