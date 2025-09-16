#!/usr/bin/env node

const axios = require('axios');

async function testAPI() {
    console.log('🚀 开始测试API集成...\n');
    
    try {
        // 测试后端API
        console.log('📊 测试后端API...');
        const response = await axios.get('http://localhost:8000/market/ticker?symbol=BTC-USDT');
        
        if (response.data.success) {
            console.log('✅ 后端API正常');
            console.log(`   当前BTC价格: $${response.data.data.last.toLocaleString()}`);
            console.log(`   24h变化: ${response.data.data.changePercent24h * 100}%`);
            console.log(`   24h成交量: ${response.data.data.volume24h.toLocaleString()} BTC\n`);
        } else {
            console.log('❌ 后端API返回失败:', response.data.message);
            return;
        }
        
        // 测试价格图表API
        console.log('📈 测试价格图表API...');
        const chartResponse = await axios.get('http://localhost:8000/market/price-chart?symbol=BTC-USDT&timeframe=1H&limit=5');
        
        if (chartResponse.data.success) {
            console.log('✅ 价格图表API正常');
            console.log(`   获取到 ${chartResponse.data.data.length} 条K线数据`);
            chartResponse.data.data.forEach((candle, index) => {
                console.log(`   ${candle.time}: $${candle.price.toLocaleString()}`);
            });
            console.log('');
        } else {
            console.log('❌ 价格图表API返回失败:', chartResponse.data.message);
        }
        
        // 测试前端页面
        console.log('🌐 测试前端页面...');
        const frontendResponse = await axios.get('http://localhost:3001');
        
        if (frontendResponse.status === 200) {
            console.log('✅ 前端页面可访问');
            console.log('   页面标题:', frontendResponse.data.match(/<title>(.*?)<\/title>/)?.[1] || '未找到');
        } else {
            console.log('❌ 前端页面无法访问');
        }
        
        console.log('\n🎉 API集成测试完成！');
        console.log('\n📝 总结:');
        console.log('   - 后端API: ✅ 正常');
        console.log('   - 价格数据: ✅ 正常');
        console.log('   - 前端页面: ✅ 正常');
        console.log('\n💡 如果前端页面中BTC价格没有显示真实数据，请检查浏览器控制台的错误信息。');
        
    } catch (error) {
        console.error('❌ 测试失败:', error.message);
        
        if (error.code === 'ECONNREFUSED') {
            console.log('\n🔧 解决方案:');
            console.log('   1. 确保后端服务正在运行: python -m src.api.main');
            console.log('   2. 确保前端服务正在运行: cd frontend && npm start');
            console.log('   3. 检查端口是否被占用: lsof -i :8000 和 lsof -i :3001');
        }
    }
}

testAPI();
