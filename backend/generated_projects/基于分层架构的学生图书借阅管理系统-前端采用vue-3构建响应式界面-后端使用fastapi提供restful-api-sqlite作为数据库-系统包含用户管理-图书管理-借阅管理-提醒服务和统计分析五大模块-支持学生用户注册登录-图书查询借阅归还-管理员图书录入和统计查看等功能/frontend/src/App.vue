<template>
  <div id="app">
    <!-- 导航栏 -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
      <div class="container-fluid">
        <router-link class="navbar-brand" to="/">
          <i class="bi bi-book me-2"></i>学生图书借阅系统
        </router-link>
        
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
          <span class="navbar-toggler-icon"></span>
        </button>
        
        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav me-auto">
            <li class="nav-item">
              <router-link class="nav-link" to="/books">
                <i class="bi bi-book-half me-1"></i>图书查询
              </router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/borrow-records">
                <i class="bi bi-clock-history me-1"></i>我的借阅
              </router-link>
            </li>
            <li v-if="isAdmin" class="nav-item">
              <router-link class="nav-link" to="/admin/books">
                <i class="bi bi-plus-circle me-1"></i>图书管理
              </router-link>
            </li>
            <li v-if="isAdmin" class="nav-item">
              <router-link class="nav-link" to="/admin/statistics">
                <i class="bi bi-bar-chart me-1"></i>统计分析
              </router-link>
            </li>
          </ul>
          
          <div class="navbar-nav">
            <template v-if="isAuthenticated">
              <span class="nav-link text-light">
                <i class="bi bi-person-circle me-1"></i>{{ userInfo?.name || '用户' }}
              </span>
              <button class="btn btn-outline-light btn-sm ms-2" @click="handleLogout">
                <i class="bi bi-box-arrow-right me-1"></i>退出
              </button>
            </template>
            <template v-else>
              <router-link class="nav-link" to="/login">
                <i class="bi bi-box-arrow-in-right me-1"></i>登录
              </router-link>
              <router-link class="nav-link" to="/register">
                <i class="bi bi-person-plus me-1"></i>注册
              </router-link>
            </template>
          </div>
        </div>
      </div>
    </nav>
    
    <!-- 主要内容区域 -->
    <main class="container-fluid mt-4">
      <div class="row">
        <!-- 侧边栏（管理员可见） -->
        <div v-if="isAdmin" class="col-md-3 col-lg-2 d-md-block sidebar">
          <div class="position-sticky pt-3">
            <h6 class="sidebar-heading d-flex justify-content-between align-items-center px-3 mt-4 mb-1 text-muted">
              <span>管理功能</span>
            </h6>
            <ul class="nav flex-column mb-2">
              <li class="nav-item">
                <router-link class="nav-link" to="/admin/books">
                  <i class="bi bi-book me-1"></i>图书管理
                </router-link>
              </li>
              <li class="nav-item">
                <router-link class="nav-link" to="/admin/users">
                  <i class="bi bi-people me-1"></i>用户管理
                </router-link>
              </li>
              <li class="nav-item">
                <router-link class="nav-link" to="/admin/statistics">
                  <i class="bi bi-pie-chart me-1"></i>借阅统计
                </router-link>
              </li>
              <li class="nav-item">
                <router-link class="nav-link" to="/admin/reminders">
                  <i class="bi bi-bell me-1"></i>提醒管理
                </router-link>
              </li>
            </ul>
          </div>
        </div>
        
        <!-- 路由视图 -->
        <div :class="isAdmin ? 'col-md-9 col-lg-10 ms-sm-auto' : 'col-12'">
          <div class="container-fluid">
            <!-- 全局消息提示 -->
            <div v-if="globalMessage" 
                 :class="['alert', messageType === 'success' ? 'alert-success' : 'alert-danger', 'alert-dismissible fade show']" 
                 role="alert">
              {{ globalMessage }}
              <button type="button" class="btn-close" @click="clearGlobalMessage"></button>
            </div>
            
            <!-- 路由出口 -->
            <router-view />
          </div>
        </div>
      </div>
    </main>
    
    <!-- 页脚 -->
    <footer class="footer mt-auto py-3 bg-light border-top">
      <div class="container text-center">
        <span class="text-muted">© 2023 学生图书借阅管理系统 | 基于 Vue 3 + FastAPI 构建</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'

const router = useRouter()
const authStore = useAuthStore()

// 从store中获取状态
const { isAuthenticated, userInfo } = storeToRefs(authStore)

// 全局消息状态
const globalMessage = ref('')
const messageType = ref('success') // 'success' 或 'error'

// 计算属性
const isAdmin = computed(() => {
  return userInfo.value?.role === 'admin'
})

// 方法
const handleLogout = async () => {
  try {
    await authStore.logout()
    showMessage('已成功退出登录', 'success')
    router.push('/login')
  } catch (error) {
    showMessage('退出登录失败: ' + error.message, 'error')
  }
}

const showMessage = (message, type = 'success') => {
  globalMessage.value = message
  messageType.value = type
  // 5秒后自动清除消息
  setTimeout(() => {
    clearGlobalMessage()
  }, 5000)
}

const clearGlobalMessage = () => {
  globalMessage.value = ''
}

// 全局错误处理
const setupGlobalErrorHandling = () => {
  // 可以在这里添加全局错误处理逻辑
  window.addEventListener('unhandledrejection', (event) => {
    console.error('未处理的Promise拒绝:', event.reason)
    showMessage('操作失败: ' + (event.reason?.message || '未知错误'), 'error')
  })
}

// 生命周期钩子
onMounted(() => {
  // 检查本地存储中是否有token，尝试自动登录
  authStore.checkAuthStatus()
  
  // 设置全局错误处理
  setupGlobalErrorHandling()
  
  // 监听路由变化，清除全局消息
  router.afterEach(() => {
    clearGlobalMessage()
  })
})

// 暴露方法给子组件使用（如果需要）
defineExpose({
  showMessage,
  clearGlobalMessage
})
</script>

<style scoped>
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.navbar {
  box-shadow: 0 2px 4px rgba(0,0,0,.1);
}

.sidebar {
  position: fixed;
  top: 56px; /* 导航栏高度 */
  bottom: 0;
  left: 0;
  z-index: 100;
  padding: 48px 0 0;
  box-shadow: inset -1px 0 0 rgba(0, 0, 0, .1);
  background-color: #f8f9fa;
  overflow-y: auto;
}

.sidebar .nav-link {
  font-weight: 500;
  color: #333;
  padding: 0.5rem 1rem;
}

.sidebar .nav-link:hover {
  color: #007bff;
  background-color: rgba(0, 123, 255, 0.1);
}

.sidebar .nav-link.router-link-active {
  color: #007bff;
  background-color: rgba(0, 123, 255, 0.1);
  border-left: 3px solid #007bff;
}

.sidebar-heading {
  font-size: .75rem;
  text-transform: uppercase;
}

main {
  flex: 1;
  padding-top: 1rem;
}

.footer {
  margin-top: auto;
}

@media (max-width: 767.98px) {
  .sidebar {
    position: static;
    height: auto;
    padding-top: 0;
  }
  
  .sidebar .nav-link {
    padding: 0.5rem;
  }
}

.alert {
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    transform: translateY(-20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
</style>
