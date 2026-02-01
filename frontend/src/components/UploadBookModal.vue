<script setup>
import { ref, watch } from 'vue'
import { 
  NModal, NCard, NSpace, NButton, NForm, NFormItem, 
  NInput, NUpload, NUploadDragger, NIcon, NText, NP,
  useMessage 
} from 'naive-ui'
import { CloudUploadOutline, ArchiveOutline } from '@vicons/ionicons5'
import { useBookStore } from '@/stores/book'

const props = defineProps({
  show: Boolean
})

const emit = defineEmits(['update:show', 'success'])

const message = useMessage()
const bookStore = useBookStore()

const loading = ref(false)
const formRef = ref(null)
const fileList = ref([])
const isEpub = ref(false)

const formValue = ref({
  title: '',
  author: '',
  regex: '第[0-9一二三四五六七八九十百千]+章\\s+.+'
})

const rules = {
  title: {
    required: true,
    message: '请输入书名',
    trigger: 'blur'
  },
  regex: {
    validator(rule, value) {
      if (!isEpub.value && !value) {
        return new Error('请输入正则表达式')
      }
      return true
    },
    trigger: 'blur'
  }
}

watch(() => props.show, (show) => {
  if (show) {
    // Reset form when opening
    formValue.value = {
      title: '',
      author: '',
      regex: '第[0-9一二三四五六七八九十百千]+章\\s+.+'
    }
    fileList.value = []
    isEpub.value = false
  }
})

function handleFileChange(newFileList) {
  if (newFileList.length > 0) {
    const file = newFileList[0]
    isEpub.value = file.name.toLowerCase().endsWith('.epub')
    // Auto fill title from filename
    if (file.name) {
      const name = file.name.replace(/\.(txt|epub)$/i, '')
      if (!formValue.value.title) {
        formValue.value.title = name
      }
    }
    fileList.value = [file]
  } else {
    fileList.value = []
    isEpub.value = false
  }
}

async function handleSubmit() {
  if (fileList.value.length === 0) {
    message.warning('请选择文件')
    return
  }
  
  try {
    await formRef.value?.validate()
  } catch (errors) {
    return
  }

  loading.value = true
  const file = fileList.value[0].file
  
  try {
    await bookStore.uploadBook({
      title: formValue.value.title,
      author: formValue.value.author,
      regex: formValue.value.regex,
      file: file
    })
    
    message.success('上传成功')
    emit('success')
    emit('update:show', false)
  } catch (error) {
    message.error(error.response?.data?.detail || '上传失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <n-modal
    :show="show"
    @update:show="$emit('update:show', $event)"
    preset="card"
    title="上传本地书籍"
    style="width: 600px; max-width: 90vw;"
  >
    <n-form
      ref="formRef"
      :model="formValue"
      :rules="rules"
      label-placement="left"
      label-width="80"
      require-mark-placement="right-hanging"
    >
      <n-form-item label="文件" path="file">
        <n-upload
          :multiple="false"
          directory-dnd
          :max="1"
          accept=".txt,.epub"
          :file-list="fileList"
          @update:file-list="handleFileChange"
          :default-upload="false"
        >
          <n-upload-dragger>
            <div style="margin-bottom: 12px">
              <n-icon size="48" :depth="3">
                <archive-outline />
              </n-icon>
            </div>
            <n-text style="font-size: 16px">
              点击或者拖动文件到该区域来上传
            </n-text>
            <n-p depth="3" style="margin: 8px 0 0 0">
              支持 TXT (UTF-8/GBK) 或 EPUB 格式
            </n-p>
          </n-upload-dragger>
        </n-upload>
      </n-form-item>
      
      <n-form-item label="书名" path="title">
        <n-input v-model:value="formValue.title" placeholder="请输入书名" />
      </n-form-item>
      
      <n-form-item label="作者" path="author">
        <n-input v-model:value="formValue.author" placeholder="请输入作者（可选）" />
      </n-form-item>
      
      <n-form-item v-if="!isEpub" label="章节正则" path="regex">
        <n-input v-model:value="formValue.regex" placeholder="用于匹配章节标题的正则表达式" />
        <template #feedback>
          默认规则：第[0-9一二三四五六七八九十百千]+章\s+.+
        </template>
      </n-form-item>
    </n-form>
    
    <template #footer>
      <n-space justify="end">
        <n-button @click="$emit('update:show', false)">取消</n-button>
        <n-button type="primary" :loading="loading" @click="handleSubmit">
          开始上传
        </n-button>
      </n-space>
    </template>
  </n-modal>
</template>
