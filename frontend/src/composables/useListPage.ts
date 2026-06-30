import { reactive, ref } from 'vue'

interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

interface SortState {
  prop: string
  order: 'ascending' | 'descending' | null
}

export function useListPage<T = any>(
  fetchFn: (params: { page: number; page_size: number; keyword: string; sort_by?: string; sort_order?: 'asc' | 'desc' }) => Promise<PaginatedResponse<T>>,
) {
  const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
  const keyword = ref('')
  const items = ref<T[]>([]) as ReturnType<typeof ref<T[]>>
  const loading = ref(true)
  const sort = reactive<SortState>({ prop: '', order: null })

  async function loadData() {
    loading.value = true
    try {
      const params: any = {
        page: pagination.page,
        page_size: pagination.pageSize,
        keyword: keyword.value.trim(),
      }
      if (sort.prop && sort.order) {
        params.sort_by = sort.prop
        params.sort_order = sort.order === 'ascending' ? 'asc' : 'desc'
      }
      const res = await fetchFn(params)
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

  function onSortChange({ prop, order }: { prop: string; order: 'ascending' | 'descending' | null }) {
    sort.prop = prop || ''
    sort.order = order
    pagination.page = 1
    loadData()
  }

  return { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange, onSortChange, sort }
}
