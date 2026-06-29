import { reactive, ref } from 'vue'

interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export function useListPage<T = any>(
  fetchFn: (params: { page: number; page_size: number; keyword: string }) => Promise<PaginatedResponse<T>>,
) {
  const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
  const keyword = ref('')
  const items = ref<T[]>([]) as ReturnType<typeof ref<T[]>>
  const loading = ref(true)

  async function loadData() {
    loading.value = true
    try {
      const res = await fetchFn({
        page: pagination.page,
        page_size: pagination.pageSize,
        keyword: keyword.value.trim(),
      })
      items.value = res.items ?? res
      pagination.total = res.total ?? items.value.length
    } finally {
      loading.value = false
    }
  }

  function onSearch() {
    pagination.page = 1
    loadData()
  }

  function onPageChange(page: number) {
    pagination.page = page
    loadData()
  }

  function onSizeChange(size: number) {
    pagination.pageSize = size
    pagination.page = 1
    loadData()
  }

  return { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange }
}
