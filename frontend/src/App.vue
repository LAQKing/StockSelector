<template>
  <div class="app-container">
    <div v-if="pageLoading" class="page-loading">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>
    
    <div v-else class="page-content" :class="{ 'fade-in': !pageLoading }">
    <div class="header">
      <h1>A股智能选股系统</h1>
      <p>技术面 + 基本面综合评分</p>
    </div>

    <div class="controls">
      <el-form :inline="true" :model="form" class="control-form">
        <el-form-item label="返回数量">
          <el-input-number v-model="form.top" :min="1" :max="100" />
        </el-form-item>
        <el-form-item label="最低得分">
          <el-input-number v-model="form.minScore" :min="0" :max="100" :step="5" />
        </el-form-item>
        <el-form-item label="技术面权重">
          <el-input-number v-model="form.techWeight" :min="0" :max="1" :step="0.1" :precision="1" />
        </el-form-item>
        <el-form-item label="基本面权重">
          <el-input-number v-model="form.fundWeight" :min="0" :max="1" :step="0.1" :precision="1" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleRun" :loading="loading">开始选股</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- <el-alert v-if="message" :title="message" :type="messageType" show-icon :closable="false" class="alert" /> -->

    <div v-if="loading" class="loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      <p>正在分析 A 股市场，请稍候...</p>
    </div>

    <div v-else-if="stocks.length > 0" class="results">
      <div class="results-header">
        <h2>选股结果</h2>
        <span class="timestamp">更新时间: {{ timestamp }}</span>
      </div>

      <div class="summary">
        <div class="summary-card">
          <div class="label">选出股票</div>
          <div class="value">{{ stocks.length }} 只</div>
        </div>
        <div class="summary-card">
          <div class="label">平均涨幅</div>
          <div class="value">{{ avgChange }}%</div>
        </div>
        <div class="summary-card">
          <div class="label">最高涨幅</div>
          <div class="value">{{ maxChange }}%</div>
        </div>
        <div class="summary-card">
          <div class="label">平均综合分</div>
          <div class="value">{{ avgScore }}</div>
        </div>
      </div>

      <div class="content-wrapper">
        <el-table :data="stocks" stripe class="stock-table" :cell-class-name="getCellClass">
          <el-table-column prop="index" label="排名" min-width="70">
            <template #default="{ $index }">
              <span class="rank" :class="{ 'top-3': $index < 3 }">{{ $index + 1 }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="code" label="代码" min-width="120" />
          <el-table-column prop="name" label="名称" min-width="100" />
          <el-table-column label="价格" min-width="100">
            <template #default="{ row }">
              ¥{{ row.price?.toFixed(2) || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="涨跌幅" min-width="100">
            <template #default="{ row }">
              <span :class="row.pct_change >= 0 ? 'pct-up' : 'pct-down'">
                {{ formatPct(row.pct_change) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="pe" label="市盈率" min-width="90">
            <template #default="{ row }">
              {{ row.pe ? row.pe.toFixed(2) : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="pb" label="市净率" min-width="90">
            <template #default="{ row }">
              {{ row.pb ? row.pb.toFixed(2) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="市值(亿)" min-width="90">
            <template #default="{ row }">
              {{ formatMarketCap(row.market_cap) }}
            </template>
          </el-table-column>
          <el-table-column label="换手率" min-width="80">
            <template #default="{ row }">
              {{ row.turnover_rate ? row.turnover_rate.toFixed(2) + '%' : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="技术分" min-width="90">
            <template #default="{ row }">
              <el-tag :type="getScoreType(row.tech_score)">{{ row.tech_score }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="基本分" min-width="90">
            <template #default="{ row }">
              <el-tag :type="getScoreType(row.fund_score)">{{ row.fund_score }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="综合分" min-width="90">
            <template #default="{ row }">
              <el-tag type="primary">{{ row.total_score }}</el-tag>
            </template>
          </el-table-column>
        </el-table>

        <div class="card-list">
          <div v-for="(stock, index) in stocks" :key="stock.code" class="stock-card">
            <div class="stock-card-header">
              <div class="stock-card-left">
                <span class="rank" :class="{ 'top-3': index < 3 }">{{ index + 1 }}</span>
                <div>
                  <div class="stock-card-code">{{ stock.code }}</div>
                  <div class="stock-card-name">{{ stock.name }}</div>
                </div>
              </div>
              <div style="text-align: right">
                <div class="stock-card-price">¥{{ stock.price?.toFixed(2) || '-' }}</div>
                <div class="stock-card-pct" :class="stock.pct_change >= 0 ? 'pct-up' : 'pct-down'">
                  {{ formatPct(stock.pct_change) }}
                </div>
              </div>
            </div>
            <div class="stock-card-detail">
              <div class="stock-card-item">
                <div class="label">市盈率</div>
                <div class="val">{{ stock.pe ? stock.pe.toFixed(2) : '-' }}</div>
              </div>
              <div class="stock-card-item">
                <div class="label">市净率</div>
                <div class="val">{{ stock.pb ? stock.pb.toFixed(2) : '-' }}</div>
              </div>
              <div class="stock-card-item">
                <div class="label">市值(亿)</div>
                <div class="val">{{ formatMarketCap(stock.market_cap) }}</div>
              </div>
              <div class="stock-card-item">
                <div class="label">换手率</div>
                <div class="val">{{ stock.turnover_rate ? stock.turnover_rate.toFixed(2) + '%' : '-' }}</div>
              </div>
              <div class="stock-card-item">
                <div class="label">收益率</div>
                <div class="val">{{ formatPct(stock.pct_change) }}</div>
              </div>
              <div class="stock-card-item">
                <div class="label">流动性</div>
                <div class="val">{{ stock.turnover_rate ? stock.turnover_rate.toFixed(1) : '-' }}</div>
              </div>
              <div class="stock-card-item">
                <div class="label">技术分</div>
                <div class="val">{{ stock.tech_score }}</div>
              </div>
              <div class="stock-card-item">
                <div class="label">基本面</div>
                <div class="val">{{ stock.fund_score }}</div>
              </div>
              <div class="stock-card-item">
                <div class="label">综合分</div>
                <div class="val" style="color: #667eea">{{ stock.total_score }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="empty">
      <p>点击"开始选股"运行分析</p>
    </div>

    <div class="footer">
      <p>评分标准：根据估值、盈利能力、成长性、流动性，去掉 ST / *ST / 退市、涨停/跌停、价格 > 1 元、成交额 > 1000万；计分权重：技术分 0.6，基本面 0.4</p>
      <p>提示：智能选股仅供学习、参考，请勿用于实盘交易</p>
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { fetchStockData, runSelection, fetchFromJson } from './api/index.js'

const form = ref({
  top: 10,
  minScore: 20,
  techWeight: 0.6,
  fundWeight: 0.4
})

const loading = ref(false)
const pageLoading = ref(true)
const stocks = ref([])
const timestamp = ref('')
const message = ref('')
const messageType = ref('info')

const avgChange = computed(() => {
  if (!stocks.value.length) return '0.00'
  const sum = stocks.value.reduce((acc, s) => acc + (s.pct_change || 0), 0)
  return (sum / stocks.value.length).toFixed(2)
})

const maxChange = computed(() => {
  if (!stocks.value.length) return '0.00'
  const max = Math.max(...stocks.value.map(s => s.pct_change || 0))
  return max.toFixed(2)
})

const avgScore = computed(() => {
  if (!stocks.value.length) return '0.0'
  const sum = stocks.value.reduce((acc, s) => acc + (s.total_score || 0), 0)
  return (sum / stocks.value.length).toFixed(1)
})

function formatPct(val) {
  if (!val && val !== 0) return '-'
  const sign = val > 0 ? '+' : ''
  return `${sign}${val.toFixed(2)}%`
}

function formatMarketCap(val) {
  if (!val || val === 0) return '-'
  return (val / 1e8).toFixed(1)
}

function getScoreType(score) {
  if (score >= 70) return 'success'
  if (score >= 50) return 'warning'
  return 'danger'
}

function getCellClass({ columnIndex }) {
  if (columnIndex === 4) return 'pct-cell'
  return ''
}

async function loadData() {
  try {
    const result = await fetchFromJson()
    if (result.success) {
      stocks.value = result.data || []
      timestamp.value = result.timestamp || ''
      return
    }
    const result2 = await fetchStockData()
    if (result2.success) {
      stocks.value = result2.data || []
      timestamp.value = result2.timestamp || ''
    }
  } finally {
    pageLoading.value = false
  }
}

async function handleRun() {
  loading.value = true
  message.value = ''
  try {
    const res = await runSelection({
      top: form.value.top,
      min_score: form.value.minScore,
      tech_weight: form.value.techWeight,
      fund_weight: form.value.fundWeight
    })
    if (res.success) {
      stocks.value = res.data || []
      timestamp.value = res.timestamp || ''
      message.value = `选股完成，共找到 ${res.count} 只股票`
      messageType.value = 'success'
    } else {
      message.value = res.message || '选股失败'
      messageType.value = 'error'
    }
  } catch (e) {
    message.value = `请求失败: ${e.message}`
    messageType.value = 'error'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  padding: 20px;
}

.app-container {
  max-width: 1400px;
  margin: 0 auto;
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  overflow: hidden;
  position: relative;
  min-height: 100vh;
}

.page-loading {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  z-index: 1000;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.page-loading p {
  margin-top: 16px;
  font-size: 16px;
}

.page-content.fade-in {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 30px;
  text-align: center;
}

.header h1 {
  font-size: 32px;
  margin-bottom: 8px;
}

.header p {
  opacity: 0.9;
  font-size: 14px;
}

.controls {
  padding: 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.control-form {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.alert {
  margin: 20px;
}

.loading {
  text-align: center;
  padding: 60px;
  color: #6c757d;
}

.loading .el-icon {
  font-size: 40px;
  color: #667eea;
}

.results {
  padding: 20px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.results-header h2 {
  color: #212529;
  font-size: 20px;
}

.timestamp {
  color: #6c757d;
  font-size: 14px;
}

.summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 10px;
}

.summary-card {
  background: white;
  padding: 15px;
  border-radius: 10px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.summary-card .label {
  font-size: 12px;
  color: #6c757d;
  margin-bottom: 5px;
}

.summary-card .value {
  font-size: 20px;
  font-weight: 700;
  color: #667eea;
}

.stock-table {
  min-width: 100%;
}

.stock-table .pct-cell {
  font-weight: 600;
}

.pct-up {
  color: #dc3545;
}

.pct-down {
  color: #28a745;
}

.rank {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  font-weight: bold;
  font-size: 12px;
}

.rank.top-3 {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.empty {
  text-align: center;
  padding: 60px;
  color: #6c757d;
}

.footer {
  padding: 20px;
  background: linear-gradient(135deg, #fff3cd 0%, #ffeeba 100%);
  color: #856404;
  font-size: 12px;
  text-align: center;
  border-top: 3px solid #ffc107;
}

.footer p {
  margin-bottom: 8px;
}

.footer p:last-child {
  color: #dc3545;
  font-weight: 600;
}

.card-list {
  display: none;
}

@media (max-width: 768px) {
  body {
    padding: 10px;
  }

  .header h1 {
    font-size: 20px;
  }

  .controls {
    padding: 15px;
    display: none;
  }

  .control-form {
    flex-direction: column;
    align-items: stretch;
  }

  .control-form .el-form-item {
    margin-bottom: 10px;
  }

  .stock-table {
    display: none;
  }

  .card-list {
    display: block;
  }

  .summary {
    grid-template-columns: repeat(2, 1fr);
    padding: 15px;
  }

  .results-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
}

.stock-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.stock-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.stock-card-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stock-card-code {
  font-size: 13px;
  color: #6c757d;
}

.stock-card-name {
  font-size: 16px;
  font-weight: 600;
}

.stock-card-price {
  font-size: 18px;
  font-weight: 700;
}

.stock-card-pct {
  font-size: 16px;
  font-weight: 600;
}

.stock-card-detail {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  font-size: 12px;
}

.stock-card-item {
  text-align: center;
}

.stock-card-item .label {
  color: #6c757d;
  margin-bottom: 2px;
}

.stock-card-item .val {
  font-weight: 600;
}
</style>