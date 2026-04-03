import axios from 'axios'

const isProd = import.meta.env.PROD

const API_BASE = isProd ? '/StockSelector/api' : '/api'

export async function fetchFromJson() {
  const jsonPath = isProd ? '/StockSelector/data/stocks.json' : '/data/stocks.json'
  try {
    const res = await axios.get(jsonPath, { timeout: 3000 })
    return { success: true, data: res.data.data, timestamp: res.data.timestamp }
  } catch (e) {
    console.log('JSON file not found, trying API...')
  }
  return { success: false }
}

export async function fetchStockData() {
  try {
    const res = await axios.get(`${API_BASE}/cache`)
    if (res.data.success) {
      return { success: true, data: res.data.data, timestamp: res.data.timestamp }
    }
  } catch (e) {
    console.error('Fetch from API failed:', e)
  }
  return { success: false }
}

export async function runSelection(params) {
  const res = await axios.post(`${API_BASE}/select`, params)
  return res.data
}