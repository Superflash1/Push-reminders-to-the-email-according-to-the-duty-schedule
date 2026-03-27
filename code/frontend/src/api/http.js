import axios from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

http.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error?.response?.data?.detail
    const message = Array.isArray(detail)
      ? detail.map((x) => x.msg).join('；')
      : detail || error.message || '请求失败'
    ElMessage.error(message)
    return Promise.reject(error)
  },
)

export default http