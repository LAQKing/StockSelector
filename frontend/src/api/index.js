import axios from 'axios'

const API_BASE = '/StockSelector/api'

export async function fetchFromJson() {
  try {
    const res = await axios.get('/StockSelector/data/stocks.json', { timeout: 3000 })
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