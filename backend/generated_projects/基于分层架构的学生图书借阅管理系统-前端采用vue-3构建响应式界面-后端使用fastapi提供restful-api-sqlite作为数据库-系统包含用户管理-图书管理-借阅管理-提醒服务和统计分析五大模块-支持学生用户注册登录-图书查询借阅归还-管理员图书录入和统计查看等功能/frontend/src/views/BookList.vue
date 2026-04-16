<template>
  <div class="book-list-container">
    <div class="header">
      <h1>图书列表</h1>
      <div class="search-bar">
        <el-input
          v-model="searchQuery"
          placeholder="搜索书名、作者或ISBN"
          clearable
          @input="handleSearch"
          style="width: 300px; margin-right: 10px;"
        />
        <el-button type="primary" @click="fetchBooks">搜索</el-button>
        <el-button @click="resetSearch">重置</el-button>
      </div>
    </div>

    <div class="book-table">
      <el-table :data="books" style="width: 100%" v-loading="loading">
        <el-table-column prop="isbn" label="ISBN" width="180" />
        <el-table-column prop="title" label="书名" />
        <el-table-column prop="author" label="作者" width="150" />
        <el-table-column prop="publisher" label="出版社" width="150" />
        <el-table-column prop="publication_year" label="出版年份" width="120" />
        <el-table-column prop="available_copies" label="可借数量" width="100">
          <template #default="scope">
            <span :class="{ 'text-danger': scope.row.available_copies === 0 }">
              {{ scope.row.available_copies }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              :disabled="scope.row.available_copies === 0"
              @click="handleBorrow(scope.row)"
            >
              借阅
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="totalBooks"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const books = ref([])
const searchQuery = ref('')
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const totalBooks = ref(0)

const fetchBooks = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      size: pageSize.value,
      query: searchQuery.value
    }
    const response = await axios.get('/api/books', { params })
    books.value = response.data.items || []
    totalBooks.value = response.data.total || 0
  } catch (error) {
    console.error('获取图书列表失败:', error)
    ElMessage.error('获取图书列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  fetchBooks()
}

const resetSearch = () => {
  searchQuery.value = ''
  currentPage.value = 1
  fetchBooks()
}

const handleSizeChange = (newSize) => {
  pageSize.value = newSize
  currentPage.value = 1
  fetchBooks()
}

const handleCurrentChange = (newPage) => {
  currentPage.value = newPage
  fetchBooks()
}

const handleBorrow = async (book) => {
  if (!authStore.isAuthenticated) {
    ElMessage.warning('请先登录')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确认借阅《${book.title}》？`, 
      '借阅确认', 
      { type: 'warning' }
    )
    
    const response = await axios.post('/api/borrow', {
      book_id: book.id,
      user_id: authStore.user.id
    })
    
    if (response.data.success) {
      ElMessage.success('借阅成功')
      fetchBooks() // 刷新列表
    } else {
      ElMessage.error(response.data.message || '借阅失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('借阅失败:', error)
      ElMessage.error('借阅失败')
    }
  }
}

onMounted(() => {
  fetchBooks()
})
</script>

<style scoped>
.book-list-container {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.search-bar {
  display: flex;
  align-items: center;
}

.book-table {
  margin-bottom: 20px;
}

.pagination {
  display: flex;
  justify-content: center;
}

.text-danger {
  color: #f56c6c;
}
</style>
