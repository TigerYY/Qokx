// 测试前端API调用
const axios = require('axios');

// 模拟前端API配置
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

async function testFrontendAPICalls() {
  console.log('🚀 开始测试前端API调用...');
  
  try {
    // 测试实时价格API
    console.log('\n📊 测试实时价格API...');
    const tickerResponse = await api.get('/market/ticker', {
      params: { symbol: 'BTC-USDT' }
    });
    
    if (tickerResponse.data.success) {
      console.log('✅ 实时价格API调用成功');
      console.log(`当前价格: $${tickerResponse.data.data.last.toLocaleString()}`);
      console.log(`24h变化: ${(tickerResponse.data.data.changePercent24h * 100).toFixed(2)}%`);
    } else {
      console.log('❌ 实时价格API返回失败:', tickerResponse.data.message);
    }
    
    // 测试价格图表API
    console.log('\n📈 测试价格图表API...');
    const chartResponse = await api.get('/market/price-chart', {
      params: { 
        symbol: 'BTC-USDT', 
        timeframe: '1H', 
        limit: 5 
      }
    });
    
    if (chartResponse.data.success) {
      console.log('✅ 价格图表API调用成功');
      console.log(`获取到 ${chartResponse.data.data.length} 条K线数据`);
      console.log(`最新价格: $${chartResponse.data.data[chartResponse.data.data.length - 1]?.price?.toLocaleString()}`);
    } else {
      console.log('❌ 价格图表API返回失败:', chartResponse.data.message);
    }
    
    // 测试市场数据API
    console.log('\n📊 测试市场数据API...');
    const marketResponse = await api.get('/market/data', {
      params: { 
        symbol: 'BTC-USDT', 
        timeframe: '1H', 
        limit: 3 
      }
    });
    
    if (marketResponse.data.success) {
      console.log('✅ 市场数据API调用成功');
      console.log(`获取到 ${marketResponse.data.data.length} 条市场数据`);
    } else {
      console.log('❌ 市场数据API返回失败:', marketResponse.data.message);
    }
    
    console.log('\n🎉 所有API调用测试完成！');
    
  } catch (error) {
    console.error('❌ API调用测试失败:', error.message);
    if (error.response) {
      console.error('响应状态:', error.response.status);
      console.error('响应数据:', error.response.data);
    }
  }
}

// 执行测试
testFrontendAPICalls();
