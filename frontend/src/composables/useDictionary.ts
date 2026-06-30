/**
 * 数据字典 composable —— 前端枚举选项的统一入口。
 *
 * 用法：
 *   const { options } = useDictionary('DICT_PRIORITY')
 *   // options.value => [{ label: '高', value: '高' }, { label: '中', value: '中' }, { label: '低', value: '低' }]
 *
 *   const { labels } = useDictionary('DICT_SEVERITY')
 *   // labels.value => ['高', '中', '低']
 *
 * 设计说明：
 * - 字典在 module 级别缓存，多个组件共享同一份数据，避免重复请求。
 * - 首次调用时从后端拉取全部字典项（一次性），之后从缓存读取。
 * - 字典变更频率极低（系统配置级别），无需实时刷新；如管理员修改了字典，刷新页面即可。
 */
import { computed, ref } from 'vue'
import { getDictionaryItems } from '../api/foundation'

export interface DictOption {
  label: string
  value: string
}

// ---- module-level cache ----
let _cache: Record<string, DictOption[]> | null = null
let _loadingPromise: Promise<void> | null = null
const _version = ref(0) // 触发响应式更新

async function loadAll(): Promise<void> {
  if (_cache) return
  if (_loadingPromise) return _loadingPromise
  _loadingPromise = (async () => {
    try {
      const res = await getDictionaryItems({ page: 1, page_size: 500 })
      const items: any[] = res.items ?? res
      _cache = {}
      for (const item of items) {
        const code = item.dict_code
        if (!_cache[code]) _cache[code] = []
        _cache[code].push({ label: item.item_label || item.item_value, value: item.item_value })
      }
      _version.value++
    } finally {
      _loadingPromise = null
    }
  })()
  return _loadingPromise
}

export function useDictionary(dictCode: string) {
  const options = computed<DictOption[]>(() => {
    _version.value // 依赖版本号触发响应式
    if (!_cache) return []
    return _cache[dictCode] ?? []
  })

  const labels = computed<string[]>(() => options.value.map((o) => o.value))

  const loading = ref(!_cache)

  if (!_cache) {
    loadAll().finally(() => {
      loading.value = false
    })
  }

  /** 查找某个值对应的 label（找不到则原样返回 value） */
  function labelOf(value: string | undefined | null): string {
    if (!value) return ''
    const found = options.value.find((o) => o.value === value)
    return found ? found.label : value
  }

  return { options, labels, labelOf, loading }
}

/** 预加载字典（可选，在 App 初始化时调用可避免首次组件渲染等待） */
export function preloadDictionary(): Promise<void> {
  return loadAll()
}
